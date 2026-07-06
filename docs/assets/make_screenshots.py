#!/usr/bin/env python3
"""Generate the README screenshots by driving the REAL app, not by hand-grabbing.

Single editable source of truth for the three README hero screenshots (no manual
screen-grabbing - run by hand when the UI changes, like the other asset scripts):

  docs/assets/screenshot1.png  - aggregator SESSION card: invites + solo-demo button + demo log
  docs/assets/screenshot2.png  - STATUS + MASKED SHARES RECEIVED + AGGREGATION cards
  docs/assets/screenshot3.png  - RESULT + REVEAL (simulation-only) cards

These are CAPTURES OF THE ACTUAL RUNNING PAGE - a headless browser loads the real
aggregator on a local server, creates a session, runs the real solo-demo round
(real PoW, join, ECDH, signed masked shares over the wire), and screenshots the
cards. They are deliberately NOT hand-drawn mockups: a faked screenshot would
misrepresent the UI and drift from it - the whole point is that re-running this
re-captures whatever the app actually shows today.

Requires (dev-only; NOT server deps):
  pip install playwright          # the Python package
  # plus a Chromium-family browser. This script uses the installed Microsoft Edge
  # (channel="msedge"); change CHANNEL below if you have Chrome instead, or run
  # `playwright install chromium` and set CHANNEL=None to use Playwright's own build.

Run:  python docs/assets/make_screenshots.py
"""

import io
import os
import socket
import subprocess
import sys
import time
import urllib.request

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = HERE

HOST = "127.0.0.1"          # a secure context, so WebCrypto (crypto.subtle) works
PORT = 8799                 # off the default 8765 to dodge a stale dev server
BASE = f"http://{HOST}:{PORT}"
CHANNEL = "msedge"          # installed Edge; set to "chrome" or None as available
SCALE = 2                   # device pixel ratio -> crisp 2x screenshots
BG = (12, 12, 13)           # --bg #0c0c0d, the page background behind the cards


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
    if _port_open():
        raise RuntimeError(f"{HOST}:{PORT} is already in use - stop the other server first")
    env = dict(os.environ)
    env.update(HOST=HOST, PORT=str(PORT))
    # clean room: never capture behind a password gate or CF trust
    for k in ("SITE_PASSWORD", "AGGREGATOR_PASSWORD", "TRUST_CF_CONNECTING_IP"):
        env.pop(k, None)
    proc = subprocess.Popen([sys.executable, "server.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_health()
    return proc


def _port_open():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, PORT)) == 0


def shot(el):
    """Element screenshot -> PIL image."""
    return Image.open(io.BytesIO(el.screenshot()))


def stitch(images, gap=16, pad=24):
    """Stack card images vertically on the page background, with a gap between and
    a uniform margin around - reproduces the cards-on-dark-bg look of the page."""
    g, p = gap * SCALE, pad * SCALE
    w = max(im.width for im in images) + 2 * p
    h = sum(im.height for im in images) + g * (len(images) - 1) + 2 * p
    canvas = Image.new("RGB", (w, h), BG)
    y = p
    for im in images:
        canvas.paste(im, ((w - im.width) // 2, y))
        y += im.height + g
    return canvas


def main():
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=CHANNEL, headless=True)
            # reduced_motion pins every CSS animation to its settled end state
            # (via the theme.css kill), so stills are deterministic - and this
            # run doubles as the reduced-motion regression probe: it fails
            # loudly if rendering ever gates on an animation event.
            page = browser.new_context(viewport={"width": 1040, "height": 1400},
                                       device_scale_factor=SCALE,
                                       reduced_motion="reduce").new_page()
            page.goto(f"{BASE}/aggregator", wait_until="networkidle")

            # create a 3-party session (metric prefill + N=3 are the defaults)
            page.click("#createBtn")
            page.wait_for_selector("#codeRow:not(.hidden)", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#invites .invite-code').length >= 3")

            # run the real solo-demo round and wait for the reveal to land
            page.click("#demoBtn")
            page.wait_for_selector("#revealCard:not(.hidden)", timeout=90000)
            page.wait_for_function("document.querySelectorAll('#revealGrid .share-card,#revealGrid > *').length >= 3")
            page.wait_for_function("document.querySelector('#avgValue') && document.querySelector('#avgValue').textContent.trim() !== '-'")
            page.wait_for_timeout(600)  # let the poll-driven render settle

            # 1) session card (invites + demo button + demo log)
            shot(page.locator("#sessionCard")).save(os.path.join(OUT, "screenshot1.png"))
            # 2) status + masked shares + aggregation
            stitch([shot(page.locator(s)) for s in ("#statusCard", "#sharesCard", "#computeCard")]
                   ).save(os.path.join(OUT, "screenshot2.png"))
            # 3) result + reveal
            stitch([shot(page.locator(s)) for s in ("#resultCard", "#revealCard")]
                   ).save(os.path.join(OUT, "screenshot3.png"))

            browser.close()
        for n in (1, 2, 3):
            print("wrote", os.path.join(OUT, f"screenshot{n}.png"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
