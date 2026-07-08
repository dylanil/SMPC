"""Contract + error-path test suite (RB-19 / RB-33 / RB-34).

(The auth layer - passwords, cookies, bearer/PoW internals - lives in
tests_auth.py, which spawns its own server and never touches this suite's
rate windows.)

Goes beyond verify_round.py's single happy-path round:
  - a pinned protocol **contract vector** (canonical message, signed-64-bit
    conversion, ECDH+HKDF mask, and a full SHA-256 digest) so a drift on either
    side fails loudly - the digest is the one a JS harness (pow.js' hand-rolled
    SHA-256) must also reproduce (RB-33);
  - the **error-path matrix** the happy path never exercises: first-write-wins
    (200/200/409), malformed share rejected at write time, PoW replay/garbage
    -> 401, tampered bearer -> 403, oversized body -> 413, bad JSON -> 400;
  - an **N=3..10 sweep** of full rounds.

The contract-critical crypto (canonical message, HKDF derivation, sign convention,
signed-64 conversion) is imported from verify_round.py - the independent second
implementation - so it stays single-sourced. Run with the server up:

    python server.py            # in one shell
    python tests.py             # in another
"""
import hashlib
import http.client
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives.asymmetric import ec

from verify_round import (BASE, SCALE, api, api_status, mine_pow, b64, raw_pub,
                          sign_raw, canonical, derive_mask,
                          check_transcript, format_average_fixed)
from server import _leading_zero_bits  # the real server bit-count rule (RB-48)

# A >64-byte input so SHA-256 spans multiple blocks - pow.js' hand-rolled
# sha256Hex must reproduce this digest (the single-block vector above can't
# catch a multi-block padding bug). See RB-48.
MULTIBLOCK = ("SMPC-contract-vector multiblock v1: this string is deliberately "
              "longer than sixty-four bytes so SHA-256 spans multiple blocks.")

_passed = 0


def check(name, cond):
    global _passed
    if not cond:
        raise AssertionError("FAIL: " + name)
    _passed += 1
    print("PASS:", name)


def raw_post(path, raw):
    """POST raw bytes (not necessarily JSON); return the status code."""
    req = urllib.request.Request(
        BASE + path, data=raw, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


# --- Contract vector (no server needed) ------------------------------------
# Pinned literals: any drift in the canonical format, the signed-64 conversion,
# the ECDH+HKDF mask, or SHA-256 changes one of these and fails loudly.

def test_contract_vector():
    check("canonical message format",
          canonical("share", "ABCDEF", "A", "123") == "share|ABCDEF|A|123")

    u = int.from_bytes(b"\x80\x00\x00\x00\x00\x00\x00\x00", "big")
    signed = u - (1 << 64) if u >= (1 << 63) else u
    check("signed-64 big-endian conversion", signed == -9223372036854775808)

    check("SHA-256 digest (must match pow.js sha256Hex)",
          hashlib.sha256(b"SMPC-contract-vector v1").hexdigest()
          == "8daf9b4afa1031808e15d1756a5b611089f9866f96890ec45e0d08ca5b081529")

    # RB-48: pin a MULTI-BLOCK digest (pow.js' multi-block padding loop must
    # reproduce it) and the leading-zero-bit rule itself (server-side function),
    # so a drift in the hand-rolled SHA-256 or the difficulty metric fails here.
    check("multi-block SHA-256 digest (must match pow.js sha256Hex)",
          hashlib.sha256(MULTIBLOCK.encode()).hexdigest()
          == "8fb355047678afde0e3f4844bb2688f740b077c897585343fc73b54c0af7111b")
    check("leading-zero-bit count rule (0x000f… -> 12)",
          _leading_zero_bits(bytes.fromhex("000f" + "ff" * 30)) == 12)

    k1 = ec.derive_private_key(0x1111111111111111111111111111111111111111111111111111111111111111, ec.SECP256R1())
    k2 = ec.derive_private_key(0x2222222222222222222222222222222222222222222222222222222222222222, ec.SECP256R1())
    m_a = derive_mask(k1, b64(raw_pub(k2)), "A", "B")
    m_b = derive_mask(k2, b64(raw_pub(k1)), "A", "B")
    check("ECDH+HKDF pair mask is symmetric", m_a == m_b)
    check("ECDH+HKDF pair mask pinned value", m_a == 5107112043798890199)


# --- Full-round helper (reuses verify_round's contract crypto) --------------

def run_round(n):
    """Drive a full n-party round; return a context dict for further probes."""
    sess = api("/api/session/new", {"n": n, "metric": "t", **mine_pow()})
    code, tokens, parties = sess["code"], sess["tokens"], sess["parties"]
    figures = {p: 10.0 * (i + 1) for i, p in enumerate(parties)}
    sign_keys, ecdh_keys, bearer = {}, {}, {}
    for p in parties:
        sign_keys[p] = ec.generate_private_key(ec.SECP256R1())
        j = api("/api/join", {"session": code, "party": p, "token": tokens[p],
                              "vk": b64(raw_pub(sign_keys[p])), **mine_pow()})
        bearer[p] = j["server_token"]
    for p in parties:
        ecdh_keys[p] = ec.generate_private_key(ec.SECP256R1())
        pub = b64(raw_pub(ecdh_keys[p]))
        api("/api/pubkey", {"server_token": bearer[p], "pubkey": pub,
                            "sig": sign_raw(sign_keys[p], canonical("pubkey", code, p, pub))})
    shares = {}
    for p in parties:
        others = api(f"/api/pubkeys?for={p}&session={code}")["pubkeys"]
        share = int(round(figures[p] * SCALE))
        for item in others:
            o = item["party"]
            if o == p:
                continue
            lo, hi = min(p, o), max(p, o)
            share += (1 if p < o else -1) * derive_mask(ecdh_keys[p], item["pubkey"], lo, hi)
        shares[p] = str(share)
        api("/api/share", {"server_token": bearer[p], "share": shares[p],
                           "sig": sign_raw(sign_keys[p], canonical("share", code, p, shares[p]))})
    result = api(f"/api/result?session={code}")
    avg = sum(int(result["shares"][p]) for p in parties) / SCALE / len(parties)
    return {"code": code, "tokens": tokens, "parties": parties, "figures": figures,
            "sign_keys": sign_keys, "ecdh_keys": ecdh_keys, "bearer": bearer,
            "shares": shares, "avg": avg}


def test_n_sweep():
    for n in (3, 10):  # extremes; the per-IP rate limits cap how many rounds fit in a window
        ctx = run_round(n)
        expected = sum(ctx["figures"].values()) / n
        check(f"N={n} round: masks cancel (avg {ctx['avg']})", abs(ctx["avg"] - expected) < 1e-9)


def test_first_write_wins(ctx):
    code, parties = ctx["code"], ctx["parties"]
    a = parties[0]

    # join: identical vk -> idempotent 200; different vk -> 409.
    same_vk = b64(raw_pub(ctx["sign_keys"][a]))
    st, _ = api_status("/api/join", {"session": code, "party": a, "token": ctx["tokens"][a], "vk": same_vk, **mine_pow()})
    check("FWW join idempotent (same vk -> 200)", st == 200)
    other_vk = b64(raw_pub(ec.generate_private_key(ec.SECP256R1())))
    st, _ = api_status("/api/join", {"session": code, "party": a, "token": ctx["tokens"][a], "vk": other_vk, **mine_pow()})
    check("FWW join conflict (different vk -> 409)", st == 409)

    # pubkey: identical -> 200; different (validly signed) -> 409.
    same_pub = b64(raw_pub(ctx["ecdh_keys"][a]))
    st, _ = api_status("/api/pubkey", {"server_token": ctx["bearer"][a], "pubkey": same_pub,
                                       "sig": sign_raw(ctx["sign_keys"][a], canonical("pubkey", code, a, same_pub))})
    check("FWW pubkey idempotent (same -> 200)", st == 200)
    new_pub = b64(raw_pub(ec.generate_private_key(ec.SECP256R1())))
    st, _ = api_status("/api/pubkey", {"server_token": ctx["bearer"][a], "pubkey": new_pub,
                                       "sig": sign_raw(ctx["sign_keys"][a], canonical("pubkey", code, a, new_pub))})
    check("FWW pubkey conflict (different -> 409)", st == 409)

    # share: identical -> 200; different (validly signed) -> 409.
    same_share = ctx["shares"][a]
    st, _ = api_status("/api/share", {"server_token": ctx["bearer"][a], "share": same_share,
                                      "sig": sign_raw(ctx["sign_keys"][a], canonical("share", code, a, same_share))})
    check("FWW share idempotent (same -> 200)", st == 200)
    other_share = str(int(same_share) + 1)
    st, _ = api_status("/api/share", {"server_token": ctx["bearer"][a], "share": other_share,
                                      "sig": sign_raw(ctx["sign_keys"][a], canonical("share", code, a, other_share))})
    check("FWW share conflict (different -> 409)", st == 409)


def test_transcript(ctx):
    # Offline transcript pin: the dict below mirrors exactly what the aggregator's
    # "Download transcript" button emits from the /api/result payload. It must
    # verify via check_transcript, and a forged share must fail the signature
    # check even when the forger keeps the sum self-consistent (the same lie the
    # tamper card demonstrates).
    result = api(f"/api/result?session={ctx['code']}")
    t = {"format": "cravage-transcript-1", "session": ctx["code"],
         "parties": result["parties"], "scale": str(SCALE),
         "shares": result["shares"], "share_sigs": result["share_sigs"],
         "vks": result["vks"], "sum": result["sum"],
         "average": format_average_fixed(int(result["sum"]), len(result["parties"]))}
    check("transcript verifies offline (signatures + sum + average)",
          check_transcript(t) == [])
    forged = json.loads(json.dumps(t))  # deep copy
    p0 = forged["parties"][0]
    forged["shares"][p0] = str(int(forged["shares"][p0]) + SCALE)
    forged["sum"] = str(int(forged["sum"]) + SCALE)
    forged["average"] = format_average_fixed(int(forged["sum"]), len(forged["parties"]))
    fails = check_transcript(forged)
    check("forged self-consistent share fails the offline signature check",
          len(fails) == 1 and fails[0].startswith(f"{p0}: signature"))


def test_malformed_share(ctx):
    a = ctx["parties"][0]
    for bad in ("²", "١٠", "12.5", "0x10", "abc"):
        st, _ = api_status("/api/share", {"server_token": ctx["bearer"][a], "share": bad, "sig": ""})
        check(f"malformed share {ascii(bad)} rejected at write time (400)", st == 400)
    check("/api/result still healthy after malformed probes", api(f"/api/result?session={ctx['code']}")["ready"])


def test_pow():
    p = mine_pow()
    st, _ = api_status("/api/session/new", {"n": 3, **p})
    check("PoW: fresh solution accepted (200)", st == 200)
    st, _ = api_status("/api/session/new", {"n": 3, **p})
    check("PoW: replayed solution rejected (401)", st == 401)
    st, _ = api_status("/api/session/new", {"n": 3, "challenge": "garbage", "pow_nonce": 0})
    check("PoW: garbage challenge rejected (401)", st == 401)


def test_bearer_tamper(ctx):
    a = ctx["parties"][0]
    good = ctx["bearer"][a]
    tampered = good[:-2] + ("AA" if good[-2:] != "AA" else "BB")
    st, _ = api_status("/api/share", {"server_token": tampered, "share": "1", "sig": ""})
    check("tampered bearer rejected (403)", st == 403)


def test_body_and_json():
    st, _ = api_status("/api/share", {"server_token": "x", "share": "1" * 20000, "sig": ""})
    check("oversized body rejected before auth (413)", st == 413)
    check("bad JSON rejected (400)", raw_post("/api/join", b"{not json") == 400)


def test_signature_reject():
    """RB-49: the headline integrity branch - a validly-formatted but wrongly-
    signed share/pubkey must be rejected (the old probes used sig="" and
    short-circuited on the format check before signature verification)."""
    sess = api("/api/session/new", {"n": 3, **mine_pow()})
    code, tokens, parties = sess["code"], sess["tokens"], sess["parties"]
    a = parties[0]
    sk = ec.generate_private_key(ec.SECP256R1())
    j = api("/api/join", {"session": code, "party": a, "token": tokens[a],
                          "vk": b64(raw_pub(sk)), **mine_pow()})
    bearer = j["server_token"]
    wrong = ec.generate_private_key(ec.SECP256R1())  # not the vk registered at join

    share = "5000000"  # valid decimal, so it passes the format check and reaches verify
    st, _ = api_status("/api/share", {"server_token": bearer, "share": share,
                                      "sig": sign_raw(wrong, canonical("share", code, a, share))})
    check("share signed by a non-registered key rejected (403)", st == 403)

    pub = b64(raw_pub(ec.generate_private_key(ec.SECP256R1())))
    st, _ = api_status("/api/pubkey", {"server_token": bearer, "pubkey": pub,
                                       "sig": sign_raw(wrong, canonical("pubkey", code, a, pub))})
    check("pubkey signed by a non-registered key rejected (403)", st == 403)

    st, _ = api_status("/api/pubkey", {"server_token": bearer, "pubkey": "not-base64!!", "sig": ""})
    check("malformed pubkey rejected at write time (400)", st == 400)


def _signed_share_round(share_ints):
    """Lean round: join len(share_ints) parties and submit the given (already
    chosen) signed share integers, skipping the pubkey/mask step - the server
    sums share strings directly, so this exercises its arithmetic for any total.
    Returns /api/result."""
    n = len(share_ints)
    sess = api("/api/session/new", {"n": n, **mine_pow()})
    code, tokens, parties = sess["code"], sess["tokens"], sess["parties"]
    for p, val in zip(parties, share_ints):
        sk = ec.generate_private_key(ec.SECP256R1())
        j = api("/api/join", {"session": code, "party": p, "token": tokens[p],
                              "vk": b64(raw_pub(sk)), **mine_pow()})
        s = str(val)
        api("/api/share", {"server_token": j["server_token"], "share": s,
                           "sig": sign_raw(sk, canonical("share", code, p, s))})
    return api(f"/api/result?session={code}")


def _raw_get(path):
    """GET with the path sent verbatim (urllib normalises '..' away, which
    would test the client, not the server's traversal guard)."""
    host = urllib.parse.urlparse(BASE)
    conn = http.client.HTTPConnection(host.hostname, host.port, timeout=10)
    try:
        conn.request("GET", path)
        r = conn.getresponse()
        return r.status, dict(r.getheaders())
    finally:
        conn.close()


def test_static_and_headers():
    """GAP-T2: the /static/ allowlist branches and the security headers.
    All GETs - none of these consume a rate window."""
    for path, why in (("/static/notes.txt", "disallowed extension"),
                      ("/static/.hidden.js", "dotfile"),
                      ("/static/sub/x.js", "subdirectory"),
                      ("/static/../server.py", "traversal")):
        st, _ = _raw_get(path)
        check(f"static route rejects {why} (404)", st == 404)
    st, headers = _raw_get("/healthz")
    check("X-Frame-Options: DENY on every response", headers.get("X-Frame-Options") == "DENY")
    check("X-Content-Type-Options: nosniff on every response",
          headers.get("X-Content-Type-Options") == "nosniff")


def test_metric_innerhtml_tripwire():
    """GAP-S6 tripwire: the metric label is aggregator-supplied text rendered
    on other people's screens and must only ever reach the DOM via
    textContent/placeholder - never interpolated into an innerHTML template
    (RB-47 discipline). This scans every innerHTML template literal (and the
    log-helper calls that feed innerHTML) and fails if any ${...} expression
    mentions the metric. It is a TRIPWIRE, not a proof: a renamed binding
    (const m = ROUND_METRIC) evades it. Zero requests."""
    root = os.path.dirname(os.path.abspath(__file__))
    templates = []
    for page in ("party.html", "aggregator.html"):
        src = open(os.path.join(root, "public", page), encoding="utf-8").read()
        templates += re.findall(r"innerHTML\s*=\s*`(.*?)`", src, re.DOTALL)
        templates += re.findall(r"(?:demoLine|tamperLine)\(\s*`(.*?)`", src, re.DOTALL)
        templates += re.findall(r"logLine\(\s*'[^']*'\s*,\s*`(.*?)`", src, re.DOTALL)
    offenders = [expr for t in templates
                 for expr in re.findall(r"\$\{([^}]*)\}", t)
                 if re.search(r"metric", expr, re.IGNORECASE)]
    check("metric never interpolates into an innerHTML sink "
          f"({len(templates)} templates scanned)", not offenders)


def test_reset_and_rate_limit(ctx):
    """GAP-T2: /api/reset semantics, then - LAST, because it exhausts reset's
    own 30/min window - an actual 429. Reset is the only endpoint where a 429
    probe is affordable: per-path counters mean nothing else is disturbed."""
    code = ctx["code"]
    st, body = api_status("/api/reset", {"session": code})
    check("reset deletes an existing session (200 ok)", st == 200 and json.loads(body).get("ok") is True)
    st, _ = api_status("/api/reset", {"session": code})
    check("reset of a missing session rejected (403)", st == 403)
    saw_429 = False
    for _ in range(40):
        st, _ = api_status("/api/reset", {"session": "ZZZZZZ"})
        if st == 429:
            saw_429 = True
            break
    check("sliding-window rate limit fires (429 on reset flood)", saw_429)


def test_sum_zero_and_negative():
    """RB-49: the happy path only ever uses positive figures. One lean round with
    a negative share AND a zero total exercises both the negative-value path and
    the zero-average case (kept to a single round so the suite stays inside the
    per-IP /api/share window - see RB-54)."""
    r = _signed_share_round([10 * SCALE, 5 * SCALE, -15 * SCALE])  # negative share, total 0
    check("round with a negative share and zero total: server sum == 0", int(r["sum"]) == 0)


def main():
    test_contract_vector()
    test_n_sweep()
    ctx = run_round(3)
    test_first_write_wins(ctx)
    test_transcript(ctx)
    test_malformed_share(ctx)
    test_bearer_tamper(ctx)
    test_signature_reject()
    test_sum_zero_and_negative()
    test_pow()
    test_body_and_json()
    test_static_and_headers()
    test_metric_innerhtml_tripwire()
    test_reset_and_rate_limit(ctx)  # last: floods reset's own rate window
    print(f"\nALL {_passed} CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        # RB-54: the per-IP rate limits cap how many rounds fit in a window, and a
        # fresh server does NOT reset them (only ~60s of quiet does). Turn the
        # otherwise-opaque urllib traceback into an actionable hint.
        if e.code == 429:
            raise SystemExit(
                "\nHIT RATE LIMIT (429). This suite must run against a freshly-"
                "started server with a quiet per-IP window - wait ~60s and retry, "
                "or restart the server, then run tests.py on its own.")
        raise
