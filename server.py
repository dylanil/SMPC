#!/usr/bin/env python3
"""
SMPC coordination server for an N-party pairwise-mask average (3 ≤ N ≤ 10),
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

  4. First-write-wins (FWW) on /api/join, /api/pubkey, /api/share. The first
     value committed for a slot is locked in; a subsequent POST with byte-
     identical content succeeds idempotently (so honest network retries still
     work), but a POST with different content gets 409 Conflict. This closes
     the share-rewriting / steering attack: a participant cannot wait for
     others to land then overwrite their own share to nudge the average.

  5. Proof of work on /api/session/new and /api/join. Each call must include
     a fresh server-signed challenge plus a nonce that makes
     SHA-256(challenge:nonce) clear a configurable difficulty bar. Caps the
     per-request cost an attacker pays for memory-DoS via session creation
     and brute-force invite-token guessing — orthogonal to per-IP rate
     limits, since PoW costs the attacker compute regardless of source IP.

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
      created_at  : unix timestamp; reaped after SESSION_TTL_SECS
  Plus the per-process HMAC secret for bearer tokens. None of this survives a
  restart.

A daemon thread (started in main()) reaps expired sessions every minute, so
memory stays bounded even under sustained (rate-limited) session creation.

All figure arithmetic is in fixed-point (x * 1_000_000) so decimals work with
BigInt on the client.
"""

import base64
import collections
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
# Optional shared secret that gates aggregator-only endpoints (session creation
# and reset). Empty/unset disables the check, preserving the local-dev experience.
# Read once at import time so per-request lookups are constant-time.
AGGREGATOR_PASSWORD = os.environ.get("AGGREGATOR_PASSWORD", "").strip()
# Set to a non-empty value only when Cloudflare fronts the deployment: rate
# limiting then keys on CF-Connecting-IP (the real client) instead of
# Fly-Client-IP (which would be a shared Cloudflare egress IP). Must stay off
# otherwise — fly's edge passes unknown client headers through, so trusting
# CF-Connecting-IP unconditionally would let clients spoof their rate-limit
# identity, the exact bug this knob's plumbing replaced.
TRUST_CF_CONNECTING_IP = bool(os.environ.get("TRUST_CF_CONNECTING_IP", "").strip())
# Universe of role letters. A session uses parties[:n] for n in [MIN_N, MAX_N].
MAX_PARTIES = list("ABCDEFGHIJ")
MIN_N = 3
MAX_N = len(MAX_PARTIES)
DEFAULT_N = 3
SESSION_ALPHABET = string.ascii_uppercase + string.digits
SESSION_LEN = 6
# Generous ceiling for any legitimate POST. Pubkey + sig + token ~ 500 bytes.
MAX_BODY_BYTES = 16 * 1024
# Optional per-session "what's being benchmarked" label, set by the aggregator
# at session creation and shown on participant pages. Display metadata only —
# never part of the signed canonical message. Length-capped because it's
# aggregator-supplied text rendered on other people's screens (clients must
# additionally render it with textContent, never innerHTML).
MAX_METRIC_LEN = 80
# Raw uncompressed P-256 public key: 0x04 || X(32) || Y(32) = 65 bytes -> 88 b64 chars.
PUBKEY_RAW_LEN = 65
PUBKEY_B64_LEN = 88
# Bearer-token TTL. Generous because rounds can take minutes if humans are slow.
SERVER_TOKEN_TTL_SECS = 30 * 60
# How long the `agg` cookie minted on a successful Basic-Auth page load
# stays valid. Subsequent same-origin POSTs to gated endpoints can present
# this cookie instead of an Authorization header — needed because browsers
# don't pre-emptively attach Basic Auth creds to fetch() requests.
AGGREGATOR_COOKIE_NAME = "agg"
AGGREGATOR_COOKIE_TTL_SECS = 30 * 60
# Session TTL: a background reaper deletes sessions older than this. Bounded
# memory under sustained (rate-limited) session creation, and matches the
# bearer-token TTL so an expiring bearer aligns with an expiring session.
SESSION_TTL_SECS = 30 * 60
SESSION_REAPER_INTERVAL_SECS = 60

# Per-process HMAC secret for server-signed bearer tokens. Regenerated on
# every restart, which invalidates any in-flight tokens — fine because the
# in-memory session state also doesn't survive restart.
SERVER_HMAC_KEY = secrets.token_bytes(32)

# Per-endpoint, per-IP rate limits: (max_requests, window_seconds). All caps
# sit comfortably above any legitimate usage pattern (a participant makes
# ~1 join + 1 pubkey + 1 share per round) but tight enough to make brute-force
# token guessing and memory-DoS via session creation impractical.
RATE_LIMITS = {
    "/api/session/new":   (10, 60),  # 10/min — caps memory growth
    "/api/join":          (30, 60),  # 30/min — caps brute-force + race-bot speed
    "/api/pubkey":        (30, 60),  # 30/min — caps signature-verify CPU
    "/api/share":         (30, 60),  # 30/min — caps signature-verify CPU
    "/api/reset":         (30, 60),  # 30/min — caps reset spam
    "/api/pow-challenge": (60, 60),  # 60/min — generous, each session/join needs one
}
# Read endpoints (/api/state, /api/result, /api/pubkeys, /healthz) are deliberately NOT
# rate-limited: they're polled sub-second by the pages and do no expensive per-request work.
# A future agent may be tempted to add a cap "for safety" — but the trade-off (session-code
# enumeration leaks round metadata, never raw figures) is accepted and tracked as RB-32/AC,
# not an oversight. See CLAUDE.md *Rate limiting*.

# Proof-of-work tuning. Each session/join request must include a successfully
# mined challenge + nonce. Difficulty 14 ≈ 16K SHA-256 hashes ≈ 30–80ms on a
# typical browser using the pure-JS miner in /static/pow.js — fast enough to
# feel instant in a demo while still being real per-request CPU work. Bump
# toward 18–22 if you start seeing botnet abuse.
POW_DIFFICULTY = 14
POW_CHALLENGE_TTL = 60  # seconds — long enough for a slow phone, short enough to limit pre-mining

rate_lock = threading.Lock()
# (path, ip) -> deque of monotonic timestamps within the active window.
rate_counters = collections.defaultdict(collections.deque)


def rate_limit_check(path, ip):
    """Sliding-window rate limit. Returns True if the request is within the
    cap (and records its timestamp), False if it should be 429'd. No-op for
    paths not in RATE_LIMITS."""
    cfg = RATE_LIMITS.get(path)
    if cfg is None:
        return True
    max_reqs, window = cfg
    now = time.monotonic()
    with rate_lock:
        q = rate_counters[(path, ip)]
        cutoff = now - window
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= max_reqs:
            return False
        q.append(now)
        return True


# --- Proof of work ---------------------------------------------------------

# Spent challenge IDs (the inner `nonce` field of the challenge payload).
# Tracking them stops a successfully-mined challenge from being replayed for
# many session creations. Cleaned periodically; bounded by challenge TTL.
USED_CHALLENGES = {}
USED_CHALLENGES_LOCK = threading.Lock()
LAST_POW_CLEANUP = [0.0]


def _cleanup_used_challenges():
    now = time.time()
    if now - LAST_POW_CLEANUP[0] < 30:
        return
    LAST_POW_CLEANUP[0] = now
    with USED_CHALLENGES_LOCK:
        for n in [n for n, exp in USED_CHALLENGES.items() if now > exp]:
            USED_CHALLENGES.pop(n, None)


def mint_pow_challenge(difficulty=POW_DIFFICULTY):
    """Issue a fresh challenge: HMAC-signed payload that the client must mine
    against. The signature stops attackers from forging easy challenges; the
    `exp` field caps pre-mining; the `nonce` field is the spend-once ID."""
    payload = {
        "nonce": secrets.token_hex(16),
        "exp": int(time.time()) + POW_CHALLENGE_TTL,
        "difficulty": difficulty,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(SERVER_HMAC_KEY, raw, hashlib.sha256).digest()
    return _b64url_encode(raw) + "." + _b64url_encode(sig), payload


def _leading_zero_bits(b):
    n = 0
    for byte in b:
        if byte == 0:
            n += 8
            continue
        n += 8 - byte.bit_length()
        return n
    return n


def verify_pow(challenge, pow_nonce):
    """Validate a (challenge, pow_nonce) pair: HMAC checks out, not expired,
    not already spent, and SHA-256(challenge:pow_nonce) clears the difficulty
    bar. Marks the challenge spent on success."""
    if not isinstance(challenge, str) or "." not in challenge:
        return False
    try:
        pow_nonce = int(pow_nonce)
    except (TypeError, ValueError):
        return False
    try:
        raw_b64, sig_b64 = challenge.split(".", 1)
        raw = _b64url_decode(raw_b64)
        sig = _b64url_decode(sig_b64)
    except Exception:
        return False
    expected = hmac.new(SERVER_HMAC_KEY, raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return False
    if int(time.time()) > int(payload.get("exp", 0)):
        return False
    difficulty = int(payload.get("difficulty", POW_DIFFICULTY))
    h = hashlib.sha256(f"{challenge}:{pow_nonce}".encode("utf-8")).digest()
    if _leading_zero_bits(h) < difficulty:
        return False
    challenge_id = payload.get("nonce", "")
    _cleanup_used_challenges()
    with USED_CHALLENGES_LOCK:
        if challenge_id in USED_CHALLENGES:
            return False
        USED_CHALLENGES[challenge_id] = payload["exp"]
    return True


def generate_code():
    return "".join(secrets.choice(SESSION_ALPHABET) for _ in range(SESSION_LEN))


state_lock = threading.Lock()
# code -> {parties, pubkeys, shares, share_sigs, vks, tokens, metric, created_at}
sessions = {}


def new_session(n, metric=""):
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
                    "metric": metric,
                    "created_at": time.time(),
                }
                return code, tokens, parties


def delete_session(code):
    with state_lock:
        return sessions.pop(code, None) is not None


def reap_old_sessions(ttl_secs=SESSION_TTL_SECS):
    """Drop sessions whose age exceeds ttl_secs. Returns count reaped."""
    cutoff = time.time() - ttl_secs
    with state_lock:
        expired = [c for c, s in sessions.items() if s.get("created_at", 0) < cutoff]
        for c in expired:
            del sessions[c]
    return len(expired)


def reap_old_rate_counters():
    """Drop rate_counters entries whose deque is now fully stale. The
    sliding-window check in rate_limit_check pops expired timestamps but
    never deletes the dict entry itself, so without this sweep every
    distinct IP that ever hit a rate-limited endpoint leaves a permanent
    key behind. On a public deployment scraped by botnets that's a slow
    memory leak. Returns count dropped."""
    now = time.monotonic()
    with rate_lock:
        to_drop = []
        for key, q in rate_counters.items():
            cfg = RATE_LIMITS.get(key[0])
            if cfg is None:
                to_drop.append(key)
                continue
            cutoff = now - cfg[1]
            while q and q[0] <= cutoff:
                q.popleft()
            if not q:
                to_drop.append(key)
        for key in to_drop:
            del rate_counters[key]
    return len(to_drop)


def start_session_reaper():
    """Start a daemon thread that periodically reaps expired sessions,
    sweeps stale rate-counter entries, and clears expired PoW
    used-challenge markers. Each step is best-effort; exceptions never
    escape the loop so a transient bug can't crash the reaper."""
    def loop():
        while True:
            time.sleep(SESSION_REAPER_INTERVAL_SECS)
            try:
                reap_old_sessions()
            except Exception:
                pass
            try:
                reap_old_rate_counters()
            except Exception:
                pass
            try:
                _cleanup_used_challenges()
            except Exception:
                pass
    t = threading.Thread(target=loop, name="session-reaper", daemon=True)
    t.start()
    return t


def is_decimal_string(s):
    # ASCII-only: str.isdigit() is True for non-ASCII digits ('²', Arabic-Indic '١٠',
    # Devanagari '५', fullwidth '３'…), which pass validation but then crash int() server-side
    # or throw in the participants' BigInt() — silently desyncing a round (RB-01). The
    # isascii() guard tightens the CHARSET only; there is deliberately NO value/magnitude cap
    # here (AC-01 — any figure scale must work; the 16 KB body cap stands).
    if not isinstance(s, str) or not s or not s.isascii():
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


def _cookie_hmac_key():
    """HMAC key for the aggregator cookie, derived from AGGREGATOR_PASSWORD
    so the cookie survives server restarts (fly redeploys, machine recycles)
    as long as the password itself is unchanged. Rotating the password
    invalidates every outstanding cookie, which is exactly what we want.
    Falls back to SERVER_HMAC_KEY when no password is set — in that mode the
    cookie is unused anyway because _check_aggregator_auth short-circuits
    True before consulting it."""
    if not AGGREGATOR_PASSWORD:
        return SERVER_HMAC_KEY
    return hashlib.sha256(b"smpc-aggregator-cookie\x00" + AGGREGATOR_PASSWORD.encode("utf-8")).digest()


_COOKIE_HMAC_KEY = _cookie_hmac_key()


def mint_aggregator_cookie(ttl=AGGREGATOR_COOKIE_TTL_SECS):
    """Sign a small `{exp}` payload that proves the bearer cleared the
    Basic-Auth gate at /aggregator. Stateless — verified by re-running the
    HMAC. Used because browsers don't pre-emptively attach Basic Auth to
    fetch() requests, so a cookie is the cleanest way to ride the page-load
    auth across to subsequent API POSTs."""
    payload = {"agg": True, "exp": int(time.time()) + ttl}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_COOKIE_HMAC_KEY, raw, hashlib.sha256).digest()
    return _b64url_encode(raw) + "." + _b64url_encode(sig)


def verify_aggregator_cookie(token):
    if not isinstance(token, str) or "." not in token:
        return False
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = _b64url_decode(raw_b64)
        sig = _b64url_decode(sig_b64)
    except Exception:
        return False
    expected = hmac.new(_COOKIE_HMAC_KEY, raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return False
    return payload.get("agg") is True and int(time.time()) <= int(payload.get("exp", 0))


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

# Paths excluded from the access log unconditionally — even errors. These are
# polled sub-second by the pages (party.html's Step 6 retries /api/result
# every 700ms forever, including against reaped sessions), so logging them,
# even at >= 400, floods stdout at ~85 lines/min per abandoned tab.
QUIET_LOG_PATHS = {"/api/state", "/api/result", "/api/pubkeys", "/healthz"}


class Handler(http.server.BaseHTTPRequestHandler):
    # RB-16: socket read timeout. Without it a client that sends headers (or a
    # Content-Length) but then stalls mid-body ties up a handler thread forever
    # (slowloris); ThreadingHTTPServer spawns one thread per connection, so this
    # bypasses the body cap, PoW, and rate limiting. The timeout bounds every
    # method (GET and POST), closing a stalled connection instead of leaking a
    # thread. Generous enough for a slow phone on a real request.
    timeout = 30

    def log_message(self, fmt, *args):
        return  # quiet — log_request below is the only logger

    def log_request(self, code="-", size="-"):
        # Minimal abuse-visibility log, readable via `fly logs`: POSTs and
        # error responses only, never the polled read endpoints. The line
        # carries timestamp/IP/method/path/status — never bodies (tokens,
        # shares) and never the query string (?session=CODE is a read
        # capability; invite tokens already ride in URL fragments, which
        # never reach the server).
        try:
            path = urlparse(self.path).path
            if path in QUIET_LOG_PATHS:
                return
            status = int(code)
            if self.command != "POST" and status < 400:
                return
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            print(f"{ts} {self._client_ip()} {self.command} {path} {status}", flush=True)
        except Exception:
            pass  # logging must never break request handling

    # --- response helpers -------------------------------------------------
    def _emit_security_headers(self):
        """Defense-in-depth headers applied to every response. Currently
        just X-Frame-Options to block clickjacking — an attacker would
        otherwise be able to put the aggregator UI invisibly inside a
        bait page (e.g. 'Click to claim your prize') so a misclick fires
        the real Create-session button. There's no legitimate reason to
        iframe our own pages, so DENY has no downside. CSP/HSTS are a
        larger commitment (see CLAUDE.md) and not added here."""
        self.send_header("X-Frame-Options", "DENY")
        # RB-17: stop browsers MIME-sniffing a response into a type we didn't
        # declare (defence in depth; cheap, no downside). CSP/HSTS still omitted.
        self.send_header("X-Content-Type-Options", "nosniff")

    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._emit_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type="text/html; charset=utf-8", extra_headers=None):
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
        self._emit_security_headers()
        if extra_headers:
            for name, value in extra_headers:
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _client_ip(self):
        # Rate-limit identity. We deliberately ignore X-Forwarded-For: fly's
        # edge *appends* to it rather than replacing it, so the first entry is
        # client-controlled and a spoofer could mint a fresh identity per
        # request. Fly-Client-IP is set authoritatively by fly-proxy on every
        # request (the machine isn't reachable except through it, so a client
        # can't inject the header), making it safe to prefer without any
        # trusted-proxy CIDR machinery. Remaining spoof surface is other
        # machines on our own fly private network — acceptable for a demo.
        # CF-Connecting-IP is only honoured behind the explicit env knob; see
        # TRUST_CF_CONNECTING_IP above. Local dev has neither header and
        # falls back to the socket peer.
        if TRUST_CF_CONNECTING_IP:
            ip = self.headers.get("CF-Connecting-IP", "").strip()
            if ip:
                return ip
        ip = self.headers.get("Fly-Client-IP", "").strip()
        if ip:
            return ip
        return self.client_address[0]

    def _reject(self):
        return self._send_json(403, {"error": "invalid session, token, or signature"})

    def _cookie(self, name):
        """Pull a single cookie value by name from the Cookie header. Avoids
        bringing in http.cookies just for one parse."""
        header = self.headers.get("Cookie", "")
        if not header:
            return ""
        for kv in header.split(";"):
            n, _, v = kv.strip().partition("=")
            if n == name:
                return v
        return ""

    def _check_aggregator_auth(self):
        """Returns True if the request is authorized to hit aggregator-only
        endpoints. Three accepted forms when AGGREGATOR_PASSWORD is set:
          - `Authorization: Bearer <password>` (curl / scripts)
          - `Authorization: Basic <b64(user:pw)>` (browser auth dialog;
            username is ignored, only the password matters)
          - `Cookie: agg=<signed>` (auto-sent by the browser after the
            /aggregator page-load Basic-Auth cleared, since browsers don't
            pre-emptively attach Basic Auth to fetch() requests)
        Returns True unconditionally when no password is configured so dev
        setups keep working."""
        if not AGGREGATOR_PASSWORD:
            return True
        header = self.headers.get("Authorization", "")
        expected = AGGREGATOR_PASSWORD.encode("utf-8")
        if header.startswith("Bearer "):
            supplied = header[len("Bearer "):].encode("utf-8")
            if hmac.compare_digest(supplied, expected):
                return True
        if header.startswith("Basic "):
            try:
                decoded = base64.b64decode(header[len("Basic "):], validate=True)
            except Exception:
                decoded = b""
            # Basic Auth format is `username:password`; we accept any username.
            if b":" in decoded:
                supplied = decoded.split(b":", 1)[1]
                if hmac.compare_digest(supplied, expected):
                    return True
        cookie = self._cookie(AGGREGATOR_COOKIE_NAME)
        if cookie and verify_aggregator_cookie(cookie):
            return True
        return False

    def _send_basic_auth_challenge(self):
        body = b'{"error": "aggregator password required"}'
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("WWW-Authenticate", 'Basic realm="SMPC aggregator", charset="UTF-8"')
        self._emit_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _conflict(self, what):
        # FWW: a different value was already committed for this slot. Honest
        # network retries with byte-identical content succeed (200); rewrites
        # land here.
        return self._send_json(409, {"error": f"{what} already committed with different content"})

    # --- GET --------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Static routes
        if path in ("/", "/index.html"):
            return self._send_file(os.path.join(PUBLIC_DIR, "home.html"))
        if path == "/aggregator":
            if not self._check_aggregator_auth():
                return self._send_basic_auth_challenge()
            extra_headers = []
            if AGGREGATOR_PASSWORD:
                # The browser caches Basic Auth credentials but refuses to
                # attach them pre-emptively to fetch() requests. Hand back a
                # signed cookie so subsequent same-origin POSTs to gated
                # endpoints can ride that auth without the JS doing anything.
                # Secure flag only when the front edge says we're on HTTPS
                # (X-Forwarded-Proto on fly.io / proxies); skipping it on
                # plain HTTP local dev so the cookie still lands.
                cookie_value = mint_aggregator_cookie()
                attrs = [
                    f"{AGGREGATOR_COOKIE_NAME}={cookie_value}",
                    "HttpOnly",
                    "SameSite=Strict",
                    "Path=/",
                    f"Max-Age={AGGREGATOR_COOKIE_TTL_SECS}",
                ]
                if self.headers.get("X-Forwarded-Proto", "") == "https":
                    attrs.append("Secure")
                extra_headers.append(("Set-Cookie", "; ".join(attrs)))
            return self._send_file(os.path.join(PUBLIC_DIR, "aggregator.html"), extra_headers=extra_headers)
        parts = path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "party" and parts[1].upper() in MAX_PARTIES:
            return self._send_file(os.path.join(PUBLIC_DIR, "party.html"))

        # Static assets shipped to the browser. Tightly scoped: only a flat
        # `.js` (PoW miner, protocol crypto) or `.png` (the og:image preview)
        # filename out of public/static/ — no subdirs, no dotfiles, no traversal.
        if path.startswith("/static/"):
            name = path[len("/static/"):]
            if not name or "/" in name or name.startswith(".") or not (name.endswith(".js") or name.endswith(".png")):
                return self.send_error(404)
            full = os.path.join(PUBLIC_DIR, "static", name)
            if not os.path.isfile(full):
                return self.send_error(404)
            ctype = "image/png" if name.endswith(".png") else "application/javascript; charset=utf-8"
            return self._send_file(full, content_type=ctype)

        # Unprotected health check for platform liveness probes.
        if path == "/healthz":
            return self._send_json(200, {"ok": True})

        # PoW challenge issuance. Rate-limited; clients call this once per
        # /api/session/new or /api/join.
        if path == "/api/pow-challenge":
            if not rate_limit_check(path, self._client_ip()):
                return self._send_json(429, {"error": "rate limit exceeded; slow down"})
            challenge, payload = mint_pow_challenge()
            return self._send_json(200, {
                "challenge": challenge,
                "difficulty": payload["difficulty"],
                "expires_in": POW_CHALLENGE_TTL,
            })

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
                    "metric": sess.get("metric", ""),
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
                # Readiness is keyed on share COUNT, not pubkey-completeness. This is a
                # deliberate decision (AC-11): a party that can submit a wrong share can
                # already steer the result, so enforcing pubkey-before-share buys nothing
                # cryptographically. Do not "fix" it into a fail-closed gate without cause.
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
                    # Defence in depth for RB-01: shares are now ASCII-validated at /api/share
                    # write time, so this should never raise — but guard anyway so a corrupt
                    # stored share can never crash the request thread + flood stderr on every poll.
                    try:
                        total = sum(int(v) for v in shares.values())
                    except ValueError:
                        return self._send_json(500, {"error": "a stored share is not a valid integer"})
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

        # Per-IP rate limit. Cheap to check; bails out before any crypto.
        if not rate_limit_check(path, self._client_ip()):
            return self._send_json(429, {"error": "rate limit exceeded; slow down"})

        # /api/session/new: requires PoW + optional {n}. Default to DEFAULT_N.
        if path == "/api/session/new":
            if not self._check_aggregator_auth():
                return self._send_json(401, {"error": "aggregator password required"})
            n = DEFAULT_N
            metric = ""
            challenge = ""
            pow_nonce = None
            if length > 0:
                try:
                    body = self._read_json()
                except Exception:
                    return self._send_json(400, {"error": "bad json"})
                raw_n = body.get("n", DEFAULT_N)
                if not isinstance(raw_n, int):
                    return self._send_json(400, {"error": f"n must be an integer in [{MIN_N},{MAX_N}]"})
                n = raw_n
                metric = str(body.get("metric", "")).strip()
                challenge = body.get("challenge", "")
                pow_nonce = body.get("pow_nonce", None)
            if not (MIN_N <= n <= MAX_N):
                return self._send_json(400, {"error": f"n must be between {MIN_N} and {MAX_N}"})
            if len(metric) > MAX_METRIC_LEN:
                return self._send_json(400, {"error": f"metric too long ({MAX_METRIC_LEN} chars max)"})
            if not verify_pow(challenge, pow_nonce):
                return self._send_json(401, {"error": "invalid or missing proof-of-work"})
            code, tokens, parties = new_session(n, metric)
            return self._send_json(200, {"code": code, "tokens": tokens, "parties": parties, "metric": metric})

        try:
            body = self._read_json()
        except Exception:
            return self._send_json(400, {"error": "bad json"})

        # /api/join: party redeems an invite token and registers their signing
        # vk. Returns a server-signed bearer token bound to (session, party,
        # vk) plus the session's parties list so the client knows the roster.
        # PoW-gated to make brute-force token guessing expensive per-attempt.
        if path == "/api/join":
            session_code = str(body.get("session", "")).upper()
            party = str(body.get("party", "")).upper()
            invite_token = str(body.get("token", "")).upper()
            vk = body.get("vk", "")
            challenge = body.get("challenge", "")
            pow_nonce = body.get("pow_nonce", None)
            if party not in MAX_PARTIES:
                return self._reject()
            if not is_pubkey_b64(vk):
                return self._send_json(400, {"error": "vk must be base64-encoded uncompressed P-256 (65 bytes)"})
            if not verify_pow(challenge, pow_nonce):
                return self._send_json(401, {"error": "invalid or missing proof-of-work"})
            with state_lock:
                sess = sessions.get(session_code)
                if sess is None or sess["tokens"].get(party) != invite_token:
                    return self._reject()
                existing_vk = sess["vks"].get(party)
                if existing_vk is not None and existing_vk != vk:
                    return self._conflict("participant slot")
                sess["vks"][party] = vk  # idempotent if same vk
                parties = list(sess["parties"])
                metric = sess.get("metric", "")
            bearer = mint_bearer_token(session_code, party, vk)
            return self._send_json(200, {"server_token": bearer, "parties": parties, "metric": metric})

        # Delete a session (aggregator abandoning a round). Gated by the same
        # aggregator password as session creation so a leaked code doesn't let
        # anyone wipe an in-flight round.
        if path == "/api/reset":
            if not self._check_aggregator_auth():
                return self._send_json(401, {"error": "aggregator password required"})
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
                existing = sess["pubkeys"].get(party)
                if existing is not None and existing != pubkey:
                    return self._conflict("pubkey")
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
                existing = sess["shares"].get(party)
                if existing is not None and existing != share:
                    return self._conflict("share")
                sess["shares"][party] = share
                sess["share_sigs"][party] = sig
            return self._send_json(200, {"ok": True})

        self.send_error(404)


def main():
    if not os.path.isdir(PUBLIC_DIR):
        raise SystemExit(f"Missing public dir: {PUBLIC_DIR}")
    httpd = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    display_host = "127.0.0.1" if HOST in ("0.0.0.0", "::") else HOST
    start_session_reaper()
    print(f"SMPC server listening on {HOST}:{PORT}")
    print(f"  Home:       http://{display_host}:{PORT}/")
    print(f"  Aggregator: http://{display_host}:{PORT}/aggregator")
    print(f"  Participant pages at /party/A through /party/{MAX_PARTIES[-1]} (session size {MIN_N}-{MAX_N})")
    print(f"  Session TTL: {SESSION_TTL_SECS}s; reaper interval: {SESSION_REAPER_INTERVAL_SECS}s")
    print(f"  Aggregator password: {'required (AGGREGATOR_PASSWORD set)' if AGGREGATOR_PASSWORD else 'not set — session creation is open'}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
