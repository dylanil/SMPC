"""Auth-layer + pure-function tests (GAP-T1).

Covers the surface the main battery never enters: the HMAC token/cookie layer
(bearer round-trip/tamper/expiry - the live auth path of every round), PoW
verification branches including expiry (previously covered nowhere), the
reaper functions, sanitize_metric, the session cap, and - via ONE spawned
dual-password server - all three credential forms for both gates plus the
AC-14 two-gate composition and the cookie-survives-restart property.

Deliberately consumes NONE of the manual battery's per-IP rate windows:
half 1 is in-process (import server), half 2 talks only to its own scratch
subprocess. Run any time, no pre-running server needed:

    python tests_auth.py
"""
import base64
import hashlib
import hmac as hmac_mod
import http.client
import json
import os
import socket
import subprocess
import sys
import time

# Env BEFORE import: AGGREGATOR_PASSWORD/_COOKIE_HMAC_KEY/_SITE_COOKIE_KEY all
# bind at module import (server.py reads them at top level).
AGG_PW = "agg-pw-test"
SITE_PW = "site-pw-test"
os.environ["AGGREGATOR_PASSWORD"] = AGG_PW
os.environ["SITE_PASSWORD"] = SITE_PW

import server  # noqa: E402

_passed = 0


def check(name, cond):
    global _passed
    if not cond:
        raise AssertionError("FAIL: " + name)
    _passed += 1
    print("PASS:", name)


def flip_tail(token):
    # Flip a char WELL inside the b64url signature: the final character's low
    # bits are stripped-padding remainder, so flipping it can decode to the
    # same bytes and the HMAC would still verify.
    i = len(token) - 6
    return token[:i] + ("A" if token[i] != "A" else "B") + token[i + 1:]


# --- Half 1: in-process units -----------------------------------------------

def test_bearer():
    vk = "x" * 88
    tok = server.mint_bearer_token("ABCDEF", "A", vk)
    p = server.verify_bearer_token(tok)
    check("bearer round-trip carries (session, party, vk)",
          p is not None and (p["session"], p["party"], p["vk"]) == ("ABCDEF", "A", vk))
    check("bearer tamper -> None", server.verify_bearer_token(flip_tail(tok)) is None)
    check("bearer expiry -> None",
          server.verify_bearer_token(server.mint_bearer_token("ABCDEF", "A", vk, ttl=-1)) is None)
    check("bearer with out-of-universe party -> None",
          server.verify_bearer_token(server.mint_bearer_token("ABCDEF", "Z", vk)) is None)


def test_cookies():
    c = server.mint_aggregator_cookie()
    check("agg cookie round-trip", server.verify_aggregator_cookie(c))
    check("agg cookie tamper -> False", not server.verify_aggregator_cookie(flip_tail(c)))
    check("agg cookie expiry -> False",
          not server.verify_aggregator_cookie(server.mint_aggregator_cookie(ttl=-1)))
    s = server.mint_site_cookie()
    check("site cookie round-trip", server.verify_site_cookie(s))
    check("site cookie tamper -> False", not server.verify_site_cookie(flip_tail(s)))
    check("site cookie expiry -> False",
          not server.verify_site_cookie(server.mint_site_cookie(ttl=-1)))


def mine(challenge, difficulty):
    n = 0
    while server._leading_zero_bits(
            hashlib.sha256(f"{challenge}:{n}".encode()).digest()) < difficulty:
        n += 1
    return n


def test_pow_branches():
    ch, _ = server.mint_pow_challenge(difficulty=1)
    n = mine(ch, 1)
    check("PoW accept at difficulty 1", server.verify_pow(ch, n))
    check("PoW replay -> False (in-process spend-once)", not server.verify_pow(ch, n))
    # Expiry branch: HMAC-valid but exp in the past. verify_pow checks exp
    # before difficulty, so nonce 0 suffices - no mining.
    raw = json.dumps({"nonce": "deadbeefdeadbeef", "exp": int(time.time()) - 10,
                      "difficulty": 1}, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac_mod.new(server.SERVER_HMAC_KEY, raw, hashlib.sha256).digest()
    expired = server._b64url_encode(raw) + "." + server._b64url_encode(sig)
    check("PoW expired challenge -> False", not server.verify_pow(expired, 0))


def _synthetic_session(created_at):
    return {"parties": ["A", "B", "C"], "pubkeys": {}, "shares": {},
            "share_sigs": {}, "vks": {}, "tokens": {}, "metric": "",
            "created_at": created_at}


def test_reapers():
    server.sessions["STALE0"] = _synthetic_session(time.time() - 10 * server.SESSION_TTL_SECS)
    server.sessions["FRESH0"] = _synthetic_session(time.time())
    reaped = server.reap_old_sessions()
    check("session reaper drops stale, keeps fresh",
          reaped == 1 and "FRESH0" in server.sessions and "STALE0" not in server.sessions)
    server.sessions.pop("FRESH0", None)

    now = server.time.monotonic()
    server.rate_counters[("/api/join", "198.51.100.1")].append(now - 10_000)
    server.rate_counters[("/api/join", "198.51.100.2")].append(now)
    server.rate_counters[("/bogus", "198.51.100.3")].append(now)
    dropped = server.reap_old_rate_counters()
    check("rate-counter reaper drops stale + unknown-path, keeps fresh",
          dropped == 2 and ("/api/join", "198.51.100.2") in server.rate_counters)
    server.rate_counters.pop(("/api/join", "198.51.100.2"), None)


def test_sanitize_metric():
    # chr() codepoints, never escape/literal characters, in test data too.
    rlo, esc, rlm = chr(0x202E), chr(0x1B), chr(0x200F)
    check("sanitize_metric strips bidi overrides",
          server.sanitize_metric("a" + rlo + "b") == "ab")
    check("sanitize_metric strips Cc (ANSI escape)",
          server.sanitize_metric("a" + esc + "[31mb") == "a[31mb")
    check("sanitize_metric keeps direction marks (RTL-legit)",
          server.sanitize_metric("a" + rlm + "b") == "a" + rlm + "b")
    check("sanitize_metric passes the demo prefill through unchanged",
          server.sanitize_metric("Average claim severity (£)")
          == "Average claim severity (£)")


def test_session_cap():
    old = server.MAX_LIVE_SESSIONS
    try:
        server.MAX_LIVE_SESSIONS = 0
        check("session cap: new_session refuses at the cap",
              server.new_session(3) == (None, None, None))
    finally:
        server.MAX_LIVE_SESSIONS = old


# --- Half 2: one dual-password server subprocess ------------------------------

PORT = 8797
HOST = "127.0.0.1"


def req(method, path, headers=None, body=None):
    """Raw request; returns (status, headers dict, body str). Never raises on
    4xx/5xx (unlike urllib), and never follows redirects."""
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    try:
        payload = json.dumps(body).encode() if body is not None else None
        h = dict(headers or {})
        if payload is not None:
            h.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=payload, headers=h)
        r = conn.getresponse()
        return r.status, dict(r.getheaders()), r.read().decode("utf-8", "replace")
    finally:
        conn.close()


def basic(pw):
    return "Basic " + base64.b64encode(b"x:" + pw.encode()).decode()


def cookie_of(headers, name):
    sc = headers.get("Set-Cookie", "")
    assert sc.startswith(name + "="), f"expected {name}= cookie, got: {sc!r}"
    return sc.split(";", 1)[0]


def test_gates():
    st, _, _ = req("GET", "/healthz")
    check("/healthz is open under the site lock", st == 200)

    st, h, _ = req("GET", "/")
    check("site lock: no auth -> 401 + Basic challenge",
          st == 401 and "Basic" in h.get("WWW-Authenticate", ""))

    st, h, _ = req("GET", "/", {"Authorization": basic(SITE_PW)})
    check("site lock: Basic site password -> 200", st == 200)
    site_cookie = cookie_of(h, server.SITE_COOKIE_NAME)

    st, _, _ = req("GET", "/", {"Cookie": site_cookie})
    check("site lock: signed site cookie alone -> 200", st == 200)
    st, _, _ = req("GET", "/", {"Authorization": "Bearer " + SITE_PW})
    check("site lock: Bearer site password -> 200", st == 200)

    st, h, _ = req("GET", "/aggregator", {"Cookie": site_cookie})
    check("aggregator gate is distinct: site cookie alone -> 401 agg realm",
          st == 401 and "aggregator" in h.get("WWW-Authenticate", ""))

    st, h, _ = req("GET", "/aggregator",
                   {"Cookie": site_cookie, "Authorization": basic(AGG_PW)})
    check("aggregator: site cookie + Basic agg password -> 200", st == 200)
    agg_cookie = cookie_of(h, server.AGGREGATOR_COOKIE_NAME)

    # AC-14, executed: one credential cannot clear two gates. A bare agg
    # Authorization header (no site cookie) dies at the SITE gate.
    st, h, _ = req("POST", "/api/session/new", {"Authorization": basic(AGG_PW)},
                   {"n": 3})
    check("AC-14: agg password alone hits the site gate (401 private realm)",
          st == 401 and "private" in h.get("WWW-Authenticate", ""))

    # Same request + site cookie clears both gates and reaches the PoW check
    # (401 with proof-of-work copy, no Basic challenge header) - both auth
    # layers passed without spending any mining.
    st, h, body = req("POST", "/api/session/new",
                      {"Cookie": site_cookie, "Authorization": basic(AGG_PW)},
                      {"n": 3})
    check("two gates cleared -> next failure is PoW, not auth",
          st == 401 and "proof-of-work" in body and "WWW-Authenticate" not in h)

    # Full happy path once: mined PoW + Bearer agg + site cookie -> 200.
    st, _, body = req("GET", "/api/pow-challenge", {"Cookie": site_cookie})
    ch = json.loads(body)
    nonce = mine(ch["challenge"], ch["difficulty"])
    st, _, body = req("POST", "/api/session/new",
                      {"Cookie": site_cookie, "Authorization": "Bearer " + AGG_PW},
                      {"n": 3, "challenge": ch["challenge"], "pow_nonce": nonce})
    check("session created via Bearer agg + site cookie + PoW", st == 200
          and len(json.loads(body).get("tokens", {})) == 3)

    st, _, _ = req("POST", "/api/session/new", {"Cookie": site_cookie}, {"n": 3})
    check("site cookie without agg credential -> 401", st == 401)

    # Rotation / survives-restart property, cross-process: a cookie minted by
    # THIS process (same password -> same derived key) is accepted by the
    # subprocess; one signed under a different password is rejected.
    local_cookie = f"{server.AGGREGATOR_COOKIE_NAME}={server.mint_aggregator_cookie()}"
    st, _, _ = req("GET", "/aggregator", {"Cookie": site_cookie + "; " + local_cookie})
    check("agg cookie minted in another process (same password) -> accepted",
          st == 200)

    other_key = hashlib.sha256(b"smpc-aggregator-cookie\x00" + b"rotated-pw").digest()
    raw = json.dumps({"agg": True, "exp": int(time.time()) + 600},
                     separators=(",", ":"), sort_keys=True).encode()
    sig = hmac_mod.new(other_key, raw, hashlib.sha256).digest()
    forged = (f"{server.AGGREGATOR_COOKIE_NAME}="
              f"{server._b64url_encode(raw)}.{server._b64url_encode(sig)}")
    st, _, _ = req("GET", "/aggregator", {"Cookie": site_cookie + "; " + forged})
    check("agg cookie signed under a rotated password -> 401", st == 401)

    # RB-55 regression + input validation (no PoW needed: n/metric checks
    # precede verify_pow). Budget note: session/new is 10/min; this file's
    # total is 8 POSTs to it, inside the subprocess's virgin window.
    auth = {"Cookie": site_cookie, "Authorization": "Bearer " + AGG_PW}
    st, _, _ = req("POST", "/api/session/new", auth, {"n": True})
    check("n=true (bool) rejected (400, RB-55)", st == 400)
    st, _, _ = req("POST", "/api/session/new", auth, {"n": 2})
    check("n=2 rejected (400)", st == 400)
    st, _, _ = req("POST", "/api/session/new", auth, {"n": 11})
    check("n=11 rejected (400)", st == 400)
    st, _, _ = req("POST", "/api/session/new", auth, {"n": 3, "metric": "x" * 81})
    check("metric over 80 chars rejected (400)", st == 400)


def main():
    test_bearer()
    test_cookies()
    test_pow_branches()
    test_reapers()
    test_sanitize_metric()
    test_session_cap()

    env = dict(os.environ, HOST=HOST, PORT=str(PORT),
               AGGREGATOR_PASSWORD=AGG_PW, SITE_PASSWORD=SITE_PW)
    proc = subprocess.Popen([sys.executable, "server.py"], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                socket.create_connection((HOST, PORT), 0.2).close()
                break
            except OSError:
                time.sleep(0.2)
        test_gates()
    finally:
        proc.terminate()
    print(f"\nALL {_passed} AUTH CHECKS PASSED")


if __name__ == "__main__":
    main()
