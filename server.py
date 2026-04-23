#!/usr/bin/env python3
"""
SMPC coordination server for a 3-party pairwise-mask average,
using ECDH-derived masks so the server never sees any mask value.

Roles:
  - Insurer A, Insurer B, Insurer C: each runs in their own browser, generates
    an ECDH P-256 keypair locally, publishes the public key, fetches the others'
    public keys, derives pairwise masks via ECDH + HKDF, and submits its
    masked share. Private keys never leave the browser.
  - Aggregator: a separate page that creates a session (minting a unique code
    plus one per-party invite token), shares each invite out-of-band with the
    matching insurer, and then fetches the masked shares and computes the
    average. The aggregator never sees raw inputs, private keys, or pairwise
    masks.

Protocol (ECDH + HKDF mask derivation):
  Each pair (i, j) with i < j independently derives the same pairwise mask r_ij:
      shared = ECDH(priv_i, pub_j) = ECDH(priv_j, pub_i)
      r_ij   = HKDF(shared, info="SMPC mask " + i + j)[0:8]   # 64-bit signed BigInt
  Each party then computes:
      s_A = x_A + r_AB + r_AC
      s_B = x_B - r_AB + r_BC
      s_C = x_C - r_AC - r_BC
  Summing all three masked shares cancels every mask, yielding x_A + x_B + x_C.

Wire-level state held by this server:
  - sessions: dict keyed by 6-char session code. Each session holds pubkeys,
    shares, and a per-party token map {A|B|C -> 6-char token}. Claiming a party
    slot requires knowing that party's token, which binds the party label to
    the aggregator's out-of-band invite. Multiple independent sessions can
    coexist. The server cannot derive any pairwise mask — that requires at
    least one private key, which never leaves the originating browser.

All claim arithmetic is in fixed-point (x * 1_000_000) so decimals work with
BigInt on the client.
"""

import base64
import http.server
import json
import os
import secrets
import string
import threading
from urllib.parse import urlparse, parse_qs

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
PARTIES = ["A", "B", "C"]
SESSION_ALPHABET = string.ascii_uppercase + string.digits
SESSION_LEN = 6
# Generous ceiling for any legitimate POST (a pubkey body is ~150 bytes). Blocks
# memory-exhaustion DoS from clients declaring a huge Content-Length.
MAX_BODY_BYTES = 16 * 1024
# Raw uncompressed P-256 public key: 0x04 || X(32) || Y(32) = 65 bytes -> 88 b64 chars.
PUBKEY_RAW_LEN = 65
PUBKEY_B64_LEN = 88


def generate_code():
    return "".join(secrets.choice(SESSION_ALPHABET) for _ in range(SESSION_LEN))


state_lock = threading.Lock()
# code -> {"pubkeys": {...}, "shares": {...}, "tokens": {A: ..., B: ..., C: ...}}
sessions = {}


def new_session():
    with state_lock:
        # 36^6 is vast but still retry on the astronomically unlikely collision.
        while True:
            code = generate_code()
            if code not in sessions:
                tokens = {p: generate_code() for p in PARTIES}
                sessions[code] = {"pubkeys": {}, "shares": {}, "tokens": tokens}
                return code, tokens


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
        return self._send_json(403, {"error": "invalid session or token"})

    def _authorize_party(self, body):
        """Validate that (session, party, token) in `body` names a real session
        and matches the minted token for that party. Returns the session dict
        and party letter on success, else (None, None)."""
        code = str(body.get("session", "")).upper()
        party = str(body.get("party", "")).upper()
        token = str(body.get("token", "")).upper()
        if party not in PARTIES:
            return None, None
        with state_lock:
            sess = sessions.get(code)
            if sess is None or sess["tokens"].get(party) != token:
                return None, None
            return sess, party

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
        if len(parts) == 2 and parts[0] == "party" and parts[1].upper() in PARTIES:
            return self._send_file(os.path.join(PUBLIC_DIR, "party.html"))

        # Unprotected health check for platform liveness probes.
        if path == "/healthz":
            return self._send_json(200, {"ok": True})

        # Read-only session-scoped APIs (any session-code holder can observe).
        # Party identity isn't needed here: the aggregator polls these, and
        # insurers use them to independently verify the aggregator's result.
        supplied = (qs.get("session", [""])[0] or "").upper()

        if path == "/api/state":
            with state_lock:
                sess = sessions.get(supplied)
                data = None if sess is None else {
                    "pubkeys_published": sorted(sess["pubkeys"].keys()),
                    "shares_submitted": sorted(sess["shares"].keys()),
                }
            if data is None:
                return self._reject()
            return self._send_json(200, data)

        if path == "/api/pubkeys":
            requester = (qs.get("for", [""])[0] or "").upper()
            if requester not in PARTIES:
                return self._send_json(400, {"error": "invalid requester"})
            with state_lock:
                sess = sessions.get(supplied)
                if sess is None:
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
                submitted = sorted(sess["shares"].keys())
                if len(submitted) < 3:
                    payload = {"ready": False, "shares_submitted": submitted}
                else:
                    shares = {p: sess["shares"][p] for p in PARTIES}
                    total = sum(int(v) for v in shares.values())
                    payload = {"ready": True, "shares": shares, "sum": str(total)}
            return self._send_json(200, payload)

        self.send_error(404)

    # --- POST -------------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Create a new session. No auth — this IS the creation step.
        if path == "/api/session/new":
            code, tokens = new_session()
            return self._send_json(200, {"code": code, "tokens": tokens})

        # Reject oversized bodies before we allocate memory for them.
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_BODY_BYTES:
            return self._send_json(413, {"error": "body too large"})

        try:
            body = self._read_json()
        except Exception:
            return self._send_json(400, {"error": "bad json"})

        # Verify an invite code: (session, party, token) triple. Used by the
        # party page before it disables inputs.
        if path == "/api/verify":
            sess, _party = self._authorize_party(body)
            return self._send_json(200, {"ok": True}) if sess is not None else self._reject()

        # Delete a session (aggregator abandoning a round). Session code alone
        # suffices — anyone in the round can end it.
        if path == "/api/reset":
            supplied = str(body.get("session", "")).upper()
            return self._send_json(200, {"ok": True}) if delete_session(supplied) else self._reject()

        if path == "/api/pubkey":
            pubkey = body.get("pubkey", "")
            if not is_pubkey_b64(pubkey):
                return self._send_json(400, {"error": "pubkey must be base64-encoded uncompressed P-256 (65 bytes)"})
            sess, party = self._authorize_party(body)
            if sess is None:
                return self._reject()
            with state_lock:
                sess["pubkeys"][party] = pubkey
            return self._send_json(200, {"ok": True})

        if path == "/api/share":
            share = body.get("share", "")
            if not is_decimal_string(share):
                return self._send_json(400, {"error": "share must be a decimal string"})
            sess, party = self._authorize_party(body)
            if sess is None:
                return self._reject()
            with state_lock:
                sess["shares"][party] = share
            return self._send_json(200, {"ok": True})

        self.send_error(404)


def main():
    if not os.path.isdir(PUBLIC_DIR):
        raise SystemExit(f"Missing public dir: {PUBLIC_DIR}")
    httpd = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    display_host = "127.0.0.1" if HOST in ("0.0.0.0", "::") else HOST
    print(f"SMPC server listening on {HOST}:{PORT}")
    print(f"  Home:       http://{display_host}:{PORT}/")
    print(f"  Insurer A:  http://{display_host}:{PORT}/party/a")
    print(f"  Insurer B:  http://{display_host}:{PORT}/party/b")
    print(f"  Insurer C:  http://{display_host}:{PORT}/party/c")
    print(f"  Aggregator: http://{display_host}:{PORT}/aggregator")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
