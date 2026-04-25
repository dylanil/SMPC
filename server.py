#!/usr/bin/env python3
"""
SMPC coordination server for an N-party pairwise-mask average (2 ≤ N ≤ 10),
using ECDH-derived masks so the server never sees any mask value.

Roles:
  - Participants A, B, ... up to J: each runs in their own browser, generates
    an ECDH P-256 keypair locally for mask derivation AND a separate ECDSA
    P-256 signing keypair for share authentication. Public halves of both go
    to the server; private halves never leave the browser.
  - Aggregator: a separate page that creates a session (specifying N, minting
    a unique code and one per-party invite token), shares each invite
    out-of-band with the matching participant, and then fetches the masked
    shares and computes the average. The aggregator never sees raw inputs,
    private keys, or pairwise masks.

Protocol (ECDH + HKDF mask derivation):
  Each pair (i, j) with i < j independently derives the same pairwise mask r_ij:
      shared = ECDH(priv_i, pub_j) = ECDH(priv_j, pub_i)
      r_ij   = HKDF(shared, info="SMPC mask " + i + j)[0:8]   # 64-bit signed BigInt
  Each party i then computes:
      s_i = x_i + (sum of r_ij for j > i) - (sum of r_ji for j < i)
  Summing all N masked shares cancels every mask (each appears once with +
  and once with -), yielding sum(x_i). Average = sum / N.

Identity / integrity stack (atop the existing pairwise-mask protocol):

  1. Per-party invite tokens (capability layer). The aggregator's session
     creation mints a 6-char tokens[X] for each party X in the session.
     POSTing /api/join with the right (session, party, token) is what binds
     party X's signing verifying key (vk) to slot X for this session.

  2. Server-signed bearer tokens (HMAC-SHA256 over a per-process secret).
     /api/join returns a tamper-proof token containing {session, party, vk,
     exp}. All subsequent party-scoped POSTs (/api/pubkey, /api/share) carry
     this token in place of the raw invite.

  3. Signed shares (ECDSA P-256 over SHA-256). Each /api/pubkey and /api/share
     POST carries a signature over a canonical "<action>|<session>|<party>|
     <content>" message. The server verifies it against the vk extracted from
     the bearer token. /api/result returns share+sig+vk so observers can
     independently re-verify and recompute the sum.

  IMPORTANT: this stack does NOT solve session-time impersonation while vks
  are session-ephemeral. A token-interceptor who races the legitimate
  participant to /api/join publishes their own vk, and signatures verify
  cleanly under it. Closing that gap requires a long-term per-participant
  key registry (or two-channel delivery, or an IdP) — out of scope here.

Wire-level state held by this server:
  - sessions: dict keyed by 6-char session code. Each session holds:
      parties     : list of role letters in this session, e.g. ["A","B","C"]
      pubkeys     : {role -> base64 ECDH pubkey}
      shares      : {role -> decimal-string masked share}
      share_sigs  : {role -> base64 ECDSA signature over canonical share msg}
      vks         : {role -> base64 ECDSA verifying key, captured at /api/join}
      tokens      : {role -> 6-char invite token}
  Plus the per-process HMAC secret for bearer tokens. None of this survives a
  restart.

All figure arithmetic is in fixed-point (x * 1_000_000) so decimals work with
BigInt on the client.
"""

import base64
import hashlib
import hmac
import http.server
import json
import os
import secrets
import string
import threading
import time
from urllib.parse import urlparse, parse_qs

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
# Universe of role letters. A session uses parties[:n] for n in [MIN_N, MAX_N].
MAX_PARTIES = list("ABCDEFGHIJ")
MIN_N = 2
MAX_N = len(MAX_PARTIES)
DEFAULT_N = 3
SESSION_ALPHABET = string.ascii_uppercase + string.digits
SESSION_LEN = 6
# Generous ceiling for any legitimate POST. Pubkey + sig + token ~ 500 bytes.
MAX_BODY_BYTES = 16 * 1024
# Raw uncompressed P-256 public key: 0x04 || X(32) || Y(32) = 65 bytes -> 88 b64 chars.
PUBKEY_RAW_LEN = 65
PUBKEY_B64_LEN = 88
# Bearer-token TTL. Generous because rounds can take minutes if humans are slow.
SERVER_TOKEN_TTL_SECS = 30 * 60

# Per-process HMAC secret for server-signed bearer tokens. Regenerated on
# every restart, which invalidates any in-flight tokens — fine because the
# in-memory session state also doesn't survive restart.
SERVER_HMAC_KEY = secrets.token_bytes(32)


def generate_code():
    return "".join(secrets.choice(SESSION_ALPHABET) for _ in range(SESSION_LEN))


state_lock = threading.Lock()
# code -> {parties, pubkeys, shares, share_sigs, vks, tokens}
sessions = {}


def new_session(n):
    """Mint a session for n participants. Returns (code, tokens, parties)."""
    parties = MAX_PARTIES[:n]
    with state_lock:
        # 36^6 is vast but still retry on the astronomically unlikely collision.
        while True:
            code = generate_code()
            if code not in sessions:
                tokens = {p: generate_code() for p in parties}
                sessions[code] = {
                    "parties": parties,
                    "pubkeys": {},
                    "shares": {},
                    "share_sigs": {},
                    "vks": {},
                    "tokens": tokens,
                }
                return code, tokens, parties


def delete_session(code):
    with state_lock:
        return sessions.pop(code, None) is not None


def is_decimal_string(s):
    if not isinstance(s, str) or not s:
        return False
    return s.lstrip("-").isdigit() and not (s == "-" or s.startswith("--"))


def is_pubkey_b64(s):
    """Lightweight shape check: base64 of a 65-byte uncompressed P-256 point.
    The browser still has to import the bytes as a real curve point — we don't
    re-validate the curve here, just the format."""
    if not isinstance(s, str) or len(s) != PUBKEY_B64_LEN:
        return False
    try:
        raw = base64.b64decode(s, validate=True)
    except Exception:
        return False
    return len(raw) == PUBKEY_RAW_LEN and raw[0] == 0x04


# --- Server-signed bearer tokens (HMAC-SHA256) -----------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def mint_bearer_token(session_code, party, vk_b64, ttl=SERVER_TOKEN_TTL_SECS):
    """Mint an HMAC-signed token committing to (session, party, vk) for ttl
    seconds. Stateless — the server does not need to remember it."""
    payload = {
        "session": session_code,
        "party": party,
        "vk": vk_b64,
        "exp": int(time.time()) + ttl,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(SERVER_HMAC_KEY, raw, hashlib.sha256).digest()
    return _b64url_encode(raw) + "." + _b64url_encode(sig)


def verify_bearer_token(token):
    """Return the payload dict if the token's HMAC checks out and it hasn't
    expired, else None. Constant-time signature compare."""
    if not isinstance(token, str) or "." not in token:
        return None
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = _b64url_decode(raw_b64)
        sig = _b64url_decode(sig_b64)
    except Exception:
        return None
    expected = hmac.new(SERVER_HMAC_KEY, raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return None
    if int(time.time()) > int(payload.get("exp", 0)):
        return None
    if payload.get("party") not in MAX_PARTIES:
        return None
    return payload


# --- ECDSA P-256 signature verification ------------------------------------

def verify_share_signature(vk_b64, sig_b64, msg_bytes):
    """Verify an ECDSA P-256 / SHA-256 signature produced by WebCrypto.

    WebCrypto returns ECDSA sigs as raw r||s (64 bytes); the `cryptography`
    library expects DER-encoded ASN.1, so we convert."""
    try:
        vk_raw = base64.b64decode(vk_b64, validate=True)
        sig_raw = base64.b64decode(sig_b64, validate=True)
    except Exception:
        return False
    if len(vk_raw) != PUBKEY_RAW_LEN or vk_raw[0] != 0x04:
        return False
    if len(sig_raw) != 64:
        return False
    try:
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), vk_raw
        )
        r = int.from_bytes(sig_raw[:32], "big")
        s = int.from_bytes(sig_raw[32:], "big")
        sig_der = encode_dss_signature(r, s)
        public_key.verify(sig_der, msg_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError):
        return False


def canonical_message(action, session_code, party, content):
    """Bytes both sides must agree on for a signed POST. Includes the action
    so a pubkey signature can't be replayed as a share signature."""
    return f"{action}|{session_code}|{party}|{content}".encode("utf-8")


# --- HTTP handler ----------------------------------------------------------

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return  # quiet

    # --- response helpers -------------------------------------------------
    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type="text/html; charset=utf-8"):
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _reject(self):
        return self._send_json(403, {"error": "invalid session, token, or signature"})

    # --- GET --------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Static routes
        if path in ("/", "/index.html"):
            return self._send_file(os.path.join(PUBLIC_DIR, "home.html"))
        if path == "/aggregator":
            return self._send_file(os.path.join(PUBLIC_DIR, "aggregator.html"))
        parts = path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "party" and parts[1].upper() in MAX_PARTIES:
            return self._send_file(os.path.join(PUBLIC_DIR, "party.html"))

        # Unprotected health check for platform liveness probes.
        if path == "/healthz":
            return self._send_json(200, {"ok": True})

        # Read-only session-scoped APIs (any session-code holder can observe).
        # Participants use these to independently verify the aggregator's
        # result; the aggregator polls them to render its own UI.
        supplied = (qs.get("session", [""])[0] or "").upper()

        if path == "/api/state":
            with state_lock:
                sess = sessions.get(supplied)
                data = None if sess is None else {
                    "parties": list(sess["parties"]),
                    "pubkeys_published": sorted(sess["pubkeys"].keys()),
                    "shares_submitted": sorted(sess["shares"].keys()),
                }
            if data is None:
                return self._reject()
            return self._send_json(200, data)

        if path == "/api/pubkeys":
            requester = (qs.get("for", [""])[0] or "").upper()
            with state_lock:
                sess = sessions.get(supplied)
                if sess is None or requester not in sess["parties"]:
                    return self._reject()
                others = [
                    {"party": p, "pubkey": v}
                    for p, v in sess["pubkeys"].items()
                    if p != requester
                ]
            return self._send_json(200, {"pubkeys": others})

        if path == "/api/result":
            with state_lock:
                sess = sessions.get(supplied)
                if sess is None:
                    return self._reject()
                parties = list(sess["parties"])
                submitted = sorted(sess["shares"].keys())
                if len(submitted) < len(parties):
                    payload = {
                        "ready": False,
                        "parties": parties,
                        "shares_submitted": submitted,
                    }
                else:
                    shares = {p: sess["shares"][p] for p in parties}
                    sigs = {p: sess["share_sigs"][p] for p in parties}
                    vks = {p: sess["vks"][p] for p in parties}
                    total = sum(int(v) for v in shares.values())
                    payload = {
                        "ready": True,
                        "parties": parties,
                        "shares": shares,
                        "share_sigs": sigs,
                        "vks": vks,
                        "sum": str(total),
                    }
            return self._send_json(200, payload)

        self.send_error(404)

    # --- POST -------------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Body-size cap. Applies to any POST that has a body.
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_BODY_BYTES:
            return self._send_json(413, {"error": "body too large"})

        # /api/session/new: optional {n} body. Default to DEFAULT_N if absent.
        if path == "/api/session/new":
            n = DEFAULT_N
            if length > 0:
                try:
                    body = self._read_json()
                except Exception:
                    return self._send_json(400, {"error": "bad json"})
                raw_n = body.get("n", DEFAULT_N)
                if not isinstance(raw_n, int):
                    return self._send_json(400, {"error": f"n must be an integer in [{MIN_N},{MAX_N}]"})
                n = raw_n
            if not (MIN_N <= n <= MAX_N):
                return self._send_json(400, {"error": f"n must be between {MIN_N} and {MAX_N}"})
            code, tokens, parties = new_session(n)
            return self._send_json(200, {"code": code, "tokens": tokens, "parties": parties})

        try:
            body = self._read_json()
        except Exception:
            return self._send_json(400, {"error": "bad json"})

        # /api/join: party redeems an invite token and registers their signing
        # vk. Returns a server-signed bearer token bound to (session, party,
        # vk) plus the session's parties list so the client knows the roster.
        if path == "/api/join":
            session_code = str(body.get("session", "")).upper()
            party = str(body.get("party", "")).upper()
            invite_token = str(body.get("token", "")).upper()
            vk = body.get("vk", "")
            if party not in MAX_PARTIES:
                return self._reject()
            if not is_pubkey_b64(vk):
                return self._send_json(400, {"error": "vk must be base64-encoded uncompressed P-256 (65 bytes)"})
            with state_lock:
                sess = sessions.get(session_code)
                if sess is None or sess["tokens"].get(party) != invite_token:
                    return self._reject()
                sess["vks"][party] = vk
                parties = list(sess["parties"])
            bearer = mint_bearer_token(session_code, party, vk)
            return self._send_json(200, {"server_token": bearer, "parties": parties})

        # Delete a session (aggregator abandoning a round). Session code alone
        # suffices — anyone in the round can end it.
        if path == "/api/reset":
            supplied = str(body.get("session", "")).upper()
            return self._send_json(200, {"ok": True}) if delete_session(supplied) else self._reject()

        # Everything below requires a server-signed bearer token + a signature
        # over the canonical message.
        bearer = body.get("server_token", "")
        payload = verify_bearer_token(bearer)
        if payload is None:
            return self._reject()
        session_code = payload["session"]
        party = payload["party"]
        vk = payload["vk"]

        if path == "/api/pubkey":
            pubkey = body.get("pubkey", "")
            sig = body.get("sig", "")
            if not is_pubkey_b64(pubkey):
                return self._send_json(400, {"error": "pubkey must be base64-encoded uncompressed P-256 (65 bytes)"})
            msg = canonical_message("pubkey", session_code, party, pubkey)
            if not verify_share_signature(vk, sig, msg):
                return self._reject()
            with state_lock:
                sess = sessions.get(session_code)
                if sess is None or sess["vks"].get(party) != vk or party not in sess["parties"]:
                    return self._reject()
                sess["pubkeys"][party] = pubkey
            return self._send_json(200, {"ok": True})

        if path == "/api/share":
            share = body.get("share", "")
            sig = body.get("sig", "")
            if not is_decimal_string(share):
                return self._send_json(400, {"error": "share must be a decimal string"})
            msg = canonical_message("share", session_code, party, share)
            if not verify_share_signature(vk, sig, msg):
                return self._reject()
            with state_lock:
                sess = sessions.get(session_code)
                if sess is None or sess["vks"].get(party) != vk or party not in sess["parties"]:
                    return self._reject()
                sess["shares"][party] = share
                sess["share_sigs"][party] = sig
            return self._send_json(200, {"ok": True})

        self.send_error(404)


def main():
    if not os.path.isdir(PUBLIC_DIR):
        raise SystemExit(f"Missing public dir: {PUBLIC_DIR}")
    httpd = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    display_host = "127.0.0.1" if HOST in ("0.0.0.0", "::") else HOST
    print(f"SMPC server listening on {HOST}:{PORT}")
    print(f"  Home:       http://{display_host}:{PORT}/")
    print(f"  Aggregator: http://{display_host}:{PORT}/aggregator")
    print(f"  Participant pages at /party/A through /party/{MAX_PARTIES[-1]} (session size 2-{MAX_N})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
