"""Headless 3-party protocol round against a running server.

Re-implements the browser client (smpc-core.js) with `cryptography` to prove
the wire contract — PoW, canonical messages, ECDH+HKDF mask derivation, raw
r||s ECDSA signatures, sign convention — still matches end-to-end. Exits 0 and
prints the average if every step verifies. Dev tool only; not shipped.
"""
import base64
import hashlib
import json
import sys
import urllib.error
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BASE = "http://127.0.0.1:8765"
SCALE = 1_000_000
# Round size comes from argv (default 3); figures are 10, 20, 30, … so the
# expected average is always computable by eye. N=10 doubles as an empirical
# check of the demo-mode rate budget: this script produces the same traffic
# pattern from one IP as the aggregator's simulator.
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3


def api(path, body=None):
    if body is None:
        req = urllib.request.Request(BASE + path)
    else:
        req = urllib.request.Request(
            BASE + path, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def mine_pow():
    ch = api("/api/pow-challenge")
    challenge, difficulty = ch["challenge"], ch["difficulty"]
    n = 0
    while True:
        h = hashlib.sha256(f"{challenge}:{n}".encode()).digest()
        bits = 0
        for byte in h:
            if byte == 0:
                bits += 8
                continue
            bits += 8 - byte.bit_length()
            break
        if bits >= difficulty:
            return {"challenge": challenge, "pow_nonce": n}
        n += 1


def api_status(path, body):
    """POST and return the HTTP status code (no exception on 4xx/5xx)."""
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def b64(raw):
    return base64.b64encode(raw).decode()


def raw_pub(key):
    return key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def sign_raw(sk, msg: str):
    der = sk.sign(msg.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return b64(r.to_bytes(32, "big") + s.to_bytes(32, "big"))


def canonical(action, session, party, content):
    return f"{action}|{session}|{party}|{content}"


def derive_mask(my_ecdh, their_pub_b64, lo, hi):
    their = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), base64.b64decode(their_pub_b64))
    shared = my_ecdh.exchange(ec.ECDH(), their)
    out = HKDF(algorithm=hashes.SHA256(), length=8, salt=b"",
               info=b"SMPC mask " + (lo + hi).encode()).derive(shared)
    u = int.from_bytes(out, "big")
    return u - (1 << 64) if u >= (1 << 63) else u


METRIC = "Average claim severity (£)"


def main():
    sess = api("/api/session/new", {"n": N, "metric": METRIC, **mine_pow()})
    code, tokens, parties = sess["code"], sess["tokens"], sess["parties"]
    assert sess.get("metric") == METRIC, "metric missing from creation response"
    state = api(f"/api/state?session={code}")
    assert state.get("metric") == METRIC, "metric missing from /api/state"
    figures = {p: 10.0 * (i + 1) for i, p in enumerate(parties)}
    print(f"session {code} parties {parties} metric {sess['metric']!r}")

    sign_keys, ecdh_keys, bearer = {}, {}, {}
    for p in parties:
        sign_keys[p] = ec.generate_private_key(ec.SECP256R1())
        j = api("/api/join", {"session": code, "party": p, "token": tokens[p],
                              "vk": b64(raw_pub(sign_keys[p])), **mine_pow()})
        bearer[p] = j["server_token"]
        assert j.get("metric") == METRIC, "metric missing from join response"
        print(f"  {p} joined")

    for p in parties:
        ecdh_keys[p] = ec.generate_private_key(ec.SECP256R1())
        pub = b64(raw_pub(ecdh_keys[p]))
        api("/api/pubkey", {"server_token": bearer[p], "pubkey": pub,
                            "sig": sign_raw(sign_keys[p], canonical("pubkey", code, p, pub))})
        print(f"  {p} published pubkey")

    for p in parties:
        others = api(f"/api/pubkeys?for={p}&session={code}")["pubkeys"]
        share = int(round(figures[p] * SCALE))
        for item in others:
            o = item["party"]
            if o == p:
                continue
            lo, hi = min(p, o), max(p, o)
            sign = 1 if p < o else -1
            share += sign * derive_mask(ecdh_keys[p], item["pubkey"], lo, hi)
        s = str(share)
        api("/api/share", {"server_token": bearer[p], "share": s,
                           "sig": sign_raw(sign_keys[p], canonical("share", code, p, s))})
        print(f"  {p} submitted share {s[:20]}…")

    result = api(f"/api/result?session={code}")
    assert result["ready"], "result not ready"
    total = sum(int(result["shares"][p]) for p in parties)
    assert total == int(result["sum"]), "local/server sum mismatch"
    avg = total / SCALE / len(parties)
    expected = sum(figures.values()) / len(figures)
    assert abs(avg - expected) < 1e-9, f"average {avg} != {expected}"
    print(f"PASS: masks cancelled exactly; average = {avg} (expected {expected})")

    # RB-01 regression: a non-ASCII "digit" share must be rejected at /api/share write
    # time (str.isdigit() accepts these, but int()/BigInt() then choke), and /api/result
    # must stay healthy afterwards rather than crashing the request thread.
    for bad in ("²", "١٠", "०४", "３"):  # ²  ١٠  ०४  ３
        st, body = api_status("/api/share", {"server_token": bearer[parties[0]], "share": bad, "sig": ""})
        assert st == 400, f"non-ASCII share {bad!r} accepted ({st} {body!r}), expected 400"
    assert api(f"/api/result?session={code}")["ready"], "/api/result broke after bad-share probe"
    print("PASS: non-ASCII-digit shares rejected at /api/share; /api/result intact (RB-01)")


if __name__ == "__main__":
    sys.exit(main())
