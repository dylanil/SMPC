"""RB-37 - concurrency / capacity load test for the live instance.

The single in-memory `ThreadingHTTPServer` (server.py) spawns one thread per
connection and has never been load-tested. RB-37 asks: at what concurrency does
it degrade? This script answers it by hammering the **read path** - `/healthz` -
which is the right target because:
  - it's deliberately *unrate-limited* (RB-32/AC) and cheap (no crypto, no
    session state), so it's exactly what a traffic spike or bot sweep hits;
  - load on the POST endpoints would instead trip the per-IP rate limits and
    burn PoW/sessions - not a capacity measurement. DO NOT point this at POSTs.

The actual slowloris mitigation (RB-16, `Handler.timeout`) is the local /
direct-exposure guard and is already verified; behind fly, fly-proxy terminates
TLS and adds its own timeouts, so this script measures throughput/latency only.

USAGE (run a gentle ramp; ~20s each):
    python loadtest.py https://fl-wg-smpc.fly.dev/healthz 25  20
    python loadtest.py https://fl-wg-smpc.fly.dev/healthz 75  20
    python loadtest.py https://fl-wg-smpc.fly.dev/healthz 150 20

The realistic ceiling = the concurrency just before p95 latency or error count
climbs sharply. Watch the instance in another terminal: `fly status`, `fly logs`,
or the fly dashboard Metrics tab (CPU%, memory).

Responsible testing: it's a public box. Keep durations short, ramp gently, stop
if errors appear, and only hit /healthz. Record the ceiling as a one-line note
on RB-37 in docs/review/RELEASE_BOARD.md and that closes the item.
"""
import sys
import threading
import time
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "https://fl-wg-smpc.fly.dev/healthz"
CONC = int(sys.argv[2]) if len(sys.argv) > 2 else 50
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 20

lat, errs, lock, stop = [], [0], threading.Lock(), time.time() + DUR


def worker():
    while time.time() < stop:
        t = time.time()
        try:
            with urllib.request.urlopen(URL, timeout=10) as r:
                r.read()
            with lock:
                lat.append((time.time() - t) * 1000)
        except Exception:
            with lock:
                errs[0] += 1


def main():
    ths = [threading.Thread(target=worker) for _ in range(CONC)]
    t0 = time.time()
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    el = time.time() - t0
    lat.sort()
    n = len(lat)
    pct = lambda p: lat[min(n - 1, int(n * p / 100))] if n else 0
    print(f"conc={CONC} dur={el:.1f}s  ok={n} err={errs[0]}  {n / el:.0f} req/s")
    print(f"latency ms  p50={pct(50):.0f}  p95={pct(95):.0f}  p99={pct(99):.0f}  max={lat[-1] if n else 0:.0f}")


if __name__ == "__main__":
    main()
