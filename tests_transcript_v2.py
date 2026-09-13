"""Offline tests for verify_round.py's cravage-transcript-2 mode. No server needed:

    python tests_transcript_v2.py

examples/cravage-transcript-2.json was exported by the Cravage iPhone app's own Swift code
(CravageCore's RoundEngine and Transcript, a three-party round with figures 10, 20 and 30), so
accepting it is a cross-language check, not a self-check.
"""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile

from verify_round import (V2_CLAIM, V2_FORMAT, check_transcript, check_transcript_v2,
                          verify_transcript)

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "examples", "cravage-transcript-2.json"), encoding="utf-8") as f:
    GOLDEN = json.load(f)

_passed = 0


def check(name, cond):
    global _passed
    if not cond:
        raise SystemExit(f"FAIL: {name}")
    _passed += 1
    print(f"PASS: {name}")


def tampered(change):
    t = copy.deepcopy(GOLDEN)
    change(t)
    return check_transcript_v2(t)


def main():
    check("app-exported v2 transcript verifies", check_transcript_v2(GOLDEN) == [])
    check("check_transcript routes v2 by format", check_transcript(GOLDEN) == [])
    check("golden is the expected round", GOLDEN["average"] == "20" and GOLDEN["format"] == V2_FORMAT
          and GOLDEN["claim"] == V2_CLAIM)

    # v1 behaviour is untouched: a v1-shaped dict still goes down the v1 path.
    v1 = {"format": "cravage-transcript-1", "session": "ABCDEF", "parties": ["A"],
          "shares": {"A": "1"}, "share_sigs": {"A": "AAAA"}, "vks": {"A": "AAAA"}, "sum": "1"}
    fails = check_transcript(v1)
    check("v1 transcripts still use the v1 checks", len(fails) == 1 and fails[0].startswith("A: malformed"))

    # A forger who keeps sum and average self-consistent is caught only by signatures.
    def forge(t):
        t["shares"]["B"] = str(int(t["shares"]["B"]) + 5_000_000)
        values = [int(t["shares"][p]) for p in t["parties"]]
        total = sum(values) % (1 << 64)
        total = total - (1 << 64) if total >= (1 << 63) else total
        from verify_round import format_average_fixed
        t["sum"], t["average"] = str(total), format_average_fixed(total, 3)
    check("self-consistent forged share fails only its signature",
          tampered(forge) == ["B: share signature does not verify under the listed key"])

    cases = [
        ("claim does not match the pinned text", lambda t: t.update(claim=V2_CLAIM + " It proves identity.")),
        ("modulus is not 2^64", lambda t: t.update(modulus=str(1 << 63))),
        ("scale is not 1000000", lambda t: t.update(scale="100")),
        ("shares sum (mod 2^64) differs from the stated sum", lambda t: t.update(sum="60000001")),
        ("stated average does not follow from the sum", lambda t: t.update(average="20.01")),
        ("session is not a roster-bound session id", lambda t: t.update(session=t["session"].split(".")[0])),
        ("parties must be the letters A.. in order, three to eight of them", lambda t: t.update(parties=["B", "A", "C"])),
        ("B: share is not a canonical 64-bit decimal", lambda t: t["shares"].update(B="0" + t["shares"]["B"])),
        ("A: room code signature does not cover this label and roster", lambda t: t.update(label="Something else")),
        ("C: agreement signature does not cover this exact set of shares", lambda t: t["confirms"].update(C=t["confirms"]["A"])),
        ("roomcode_confirms does not have exactly one entry per party", lambda t: t["roomcode_confirms"].pop("B")),
    ]
    for expected, change in cases:
        check("tamper named: " + expected, expected in tampered(change))
    check("a changed label fails every room code signature",
          tampered(lambda t: t.update(label="Something else")) ==
          [p + ": room code signature does not cover this label and roster" for p in GOLDEN["parties"]])
    check("non-object input is a failure, not a crash", check_transcript_v2([]) == ["not a JSON object"])

    # The command-line entry point returns 0 for the golden file and 1 for a tampered copy.
    with contextlib.redirect_stdout(io.StringIO()) as out:
        code = verify_transcript(os.path.join(HERE, "examples", "cravage-transcript-2.json"))
    check("CLI accepts the golden file and states its scope", code == 0 and "Scope: " + V2_CLAIM in out.getvalue())
    bad = copy.deepcopy(GOLDEN)
    bad["average"] = "999"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(bad, f)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = verify_transcript(f.name)
    finally:
        os.unlink(f.name)
    check("CLI rejects a tampered file", code == 1)

    print(f"\nALL {_passed} TRANSCRIPT V2 CHECKS PASSED")


if __name__ == "__main__":
    sys.exit(main())
