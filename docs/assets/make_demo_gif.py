#!/usr/bin/env python3
"""Generate the README hero GIF by recording the REAL app, not by hand-grabbing.

Single editable source of truth for docs/assets/demo-round.gif: a headless
browser loads the real aggregator on a local server, creates a session, runs
the real solo-demo round (real PoW, join, ECDH, signed masked shares over the
wire), clicks the tamper check, and captures viewport frames along the way.
The "camera" follows the newest visible card, so the GIF shows the round
unfolding exactly as a visitor sees it. Like the other asset scripts, a faked
recording would misrepresent the UI and drift from it - re-running this
re-captures whatever the app actually does today.

Requires (dev-only; NOT server deps):
  pip install playwright pillow
  # plus a Chromium-family browser - uses installed Microsoft Edge by default,
  # like make_screenshots.py; change CHANNEL below if needed.

Run:  python docs/assets/make_demo_gif.py
"""

import os
import io
import socket
import subprocess
import sys
import time
import urllib.request

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "demo-round.gif")

HOST = "127.0.0.1"          # a secure context, so WebCrypto (crypto.subtle) works
PORT = 8797                 # off 8765 (dev) and 8799 (make_screenshots)
BASE = f"http://{HOST}:{PORT}"
CHANNEL = "msedge"

VIEW_W, VIEW_H = 980, 800   # viewport = frame size; README column is ~880 wide
FRAME_MS = 400              # capture cadence while the round runs
STALL_CAP_MS = 2000         # compress idle gaps to this; also the dwell time
                            # a settled beat (result, reveal) stays on screen
FINAL_HOLD_MS = 3200        # hold on the finished state before looping
COLORS = 128                # dark UI quantizes fine at 128 colours

# Follow-the-action camera: keep the bottom of the last visible card in view.
SCROLL_JS = """() => {
  const cards = [...document.querySelectorAll('.card:not(.hidden)')];
  if (cards.length) cards[cards.length - 1].scrollIntoView({block: 'end'});
}"""


def wait_health(timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/healthz", timeout=1) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("server did not come up on /healthz")


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        if s.connect_ex((HOST, PORT)) == 0:
            raise RuntimeError(f"{HOST}:{PORT} is already in use - stop the other server first")
    env = dict(os.environ)
    env.update(HOST=HOST, PORT=str(PORT))
    for k in ("SITE_PASSWORD", "AGGREGATOR_PASSWORD", "TRUST_CF_CONNECTING_IP"):
        env.pop(k, None)
    proc = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_health()
    return proc


class Recorder:
    def __init__(self, page):
        self.page = page
        self.frames = []       # PIL images (RGB)
        self.stamps = []       # monotonic capture times

    def snap(self):
        self.page.evaluate(SCROLL_JS)
        img = Image.open(io.BytesIO(self.page.screenshot())).convert("RGB")
        # drop consecutive duplicates; the gap is folded into the previous
        # frame's duration (then capped, so mining stalls don't drag)
        if self.frames and img.tobytes() == self.frames[-1].tobytes():
            return
        self.frames.append(img)
        self.stamps.append(time.monotonic())

    def record_until(self, predicate_js, timeout_s=90):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.snap()
            if self.page.evaluate(predicate_js):
                return
            time.sleep(FRAME_MS / 1000)
        raise RuntimeError(f"timed out waiting for {predicate_js}")

    def hold(self, n=2):
        for _ in range(n):
            time.sleep(FRAME_MS / 1000)
            self.snap()


def main():
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=CHANNEL, headless=True)
            page = browser.new_context(
                viewport={"width": VIEW_W, "height": VIEW_H}, device_scale_factor=1,
                reduced_motion="no-preference").new_page()
            rec = Recorder(page)

            page.goto(f"{BASE}/aggregator", wait_until="networkidle")
            rec.snap()

            page.click("#createBtn")
            page.wait_for_selector("#codeRow:not(.hidden)", timeout=30000)
            rec.hold(1)

            page.click("#demoBtn")
            rec.record_until(
                "() => !document.getElementById('revealCard').classList.contains('hidden')"
                " && document.getElementById('avgValue').textContent.trim() !== '-'")
            page.wait_for_timeout(600)  # let the poll-driven render settle
            rec.hold(2)

            page.click("#tamperBtn")
            rec.record_until(
                "() => !document.getElementById('tamperNote').classList.contains('hidden')",
                timeout_s=20)
            rec.hold(2)

            browser.close()

        frames, stamps = rec.frames, rec.stamps
        durations = []
        for i in range(len(frames) - 1):
            durations.append(min(int((stamps[i + 1] - stamps[i]) * 1000), STALL_CAP_MS))
        durations.append(FINAL_HOLD_MS)

        quantized = [f.quantize(colors=COLORS, method=Image.MEDIANCUT) for f in frames]
        quantized[0].save(OUT, save_all=True, append_images=quantized[1:],
                          duration=durations, loop=0, optimize=True)
        total = sum(durations) / 1000
        print(f"wrote {OUT}: {len(frames)} frames, {total:.1f}s loop, "
              f"{os.path.getsize(OUT) / 1e6:.2f} MB")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
