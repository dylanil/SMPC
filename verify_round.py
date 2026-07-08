"""Headless 3-party protocol round against a running server.

Re-implements the browser client (smpc-core.js) with `cryptography` to prove
the wire contract - PoW, canonical messages, ECDH+HKDF mask derivation, raw
r||s ECDSA signatures, sign convention - still matches end-to-end. Exits 0 and
prints the average if every step verifies.

Offline mode: `verify_round.py --transcript <file.json>` checks a round
transcript downloaded from the aggregator's result card - it re-verifies every
share signature against the verifying key registered at join and recomputes
the sum and displayed average, with no server running and trusting nothing but
the file. Runs from the repo; not served by the app.
"""
import base64
import hashlib
import json
import sys
import unicodedata
import urllib.error
import urllib.request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature, encode_dss_signature)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BASE = "http://127.0.0.1:8765"
SCALE = 1_000_000
# Round size comes from argv (default 3); figures are 10, 20, 30, … so the
# expected average is always computable by eye. N=10 doubles as an empirical
# check of the demo-mode rate budget: this script produces the same traffic
# pattern from one IP as the aggregator's simulator.
N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3


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


def format_average_fixed(sum_fixed, n, max_dp=2):
    """Mirror smpc-core.js formatAverageFixed exactly: render (sum_fixed / n)
    at up to max_dp decimal places, rounded half away from zero, trailing
    zeros stripped, never "-0". Pure integer math - no float precision loss."""
    neg = sum_fixed < 0
    abs_v = -sum_fixed if neg else sum_fixed
    divisor = n * SCALE
    units, rem = divmod(abs_v * 10 ** max_dp, divisor)
    if rem * 2 >= divisor:
        units += 1
    if units == 0:
        return "0"
    whole, frac_units = divmod(units, 10 ** max_dp)
    frac = str(frac_units).zfill(max_dp).rstrip("0")
    return ("-" if neg else "") + str(whole) + ("." + frac if frac else "")


def check_transcript(t):
    """Verify a parsed transcript dict; return a list of failure strings
    (empty means everything checks out). Pure function - no printing, no
    network - so tests can pin it directly."""
    code, parties = t["session"], t["parties"]
    failures = []
    for p in parties:
        try:
            share = t["shares"][p]
            raw = base64.b64decode(t["share_sigs"][p])
            der = encode_dss_signature(int.from_bytes(raw[:32], "big"),
                                       int.from_bytes(raw[32:], "big"))
            vk = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), base64.b64decode(t["vks"][p]))
            vk.verify(der, canonical("share", code, p, share).encode(),
                      ec.ECDSA(hashes.SHA256()))
        except InvalidSignature:
            failures.append(f"{p}: signature does not verify - the share or its "
                            "signature doesn't match the key registered at join")
        except (KeyError, ValueError) as e:
            failures.append(f"{p}: malformed transcript entry ({e})")
    total = sum(int(t["shares"][p]) for p in parties)
    if total != int(t["sum"]):
        failures.append(f"shares sum to {total} but the transcript says {t['sum']}")
    stated = t.get("average")
    if stated is not None and stated != format_average_fixed(total, len(parties)):
        failures.append(f"recomputed average {format_average_fixed(total, len(parties))} "
                        f"!= stated average {stated}")
    return failures


def _clean(s, max_len=300):
    """Strip Unicode control characters (category Cc) before printing. The
    transcript is a user-supplied file (GAP-S4 lens): don't let a crafted
    session/metric/share string smuggle ANSI escapes into the terminal."""
    out = "".join(ch for ch in str(s) if unicodedata.category(ch) != "Cc")
    return out[:max_len]


def verify_transcript(path):
    with open(path, encoding="utf-8") as f:
        t = json.load(f)
    metric = f" metric {_clean(t['metric'])!r}" if t.get("metric") else ""
    print(f"transcript: session {_clean(t['session'])} "
          f"parties {[_clean(p, 20) for p in t['parties']]}{metric}")
    failures = check_transcript(t)
    if failures:
        for line in failures:
            print("FAIL:", _clean(line))
        return 1
    total = sum(int(t["shares"][p]) for p in t["parties"])
    avg = format_average_fixed(total, len(t["parties"]))
    print(f"PASS: all {len(t['parties'])} signatures verify; "
          f"sum recomputed from the shares; average = {avg}")
    return 0


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
    if len(sys.argv) > 1 and sys.argv[1] == "--transcript":
        if len(sys.argv) != 3:
            print("usage: verify_round.py --transcript <file.json>")
            sys.exit(2)
        sys.exit(verify_transcript(sys.argv[2]))
    sys.exit(main())
