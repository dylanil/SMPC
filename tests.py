"""Contract + error-path test suite (RB-19 / RB-33 / RB-34).

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
import json
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.asymmetric import ec

from verify_round import (BASE, SCALE, api, api_status, mine_pow, b64, raw_pub,
                          sign_raw, canonical, derive_mask)

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


def main():
    test_contract_vector()
    test_n_sweep()
    ctx = run_round(3)
    test_first_write_wins(ctx)
    test_malformed_share(ctx)
    test_bearer_tamper(ctx)
    test_pow()
    test_body_and_json()
    print(f"\nALL {_passed} CHECKS PASSED")


if __name__ == "__main__":
    main()
