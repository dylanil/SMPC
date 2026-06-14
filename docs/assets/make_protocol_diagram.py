#!/usr/bin/env python3
"""Generate the "how the masks cancel" protocol schematic.

Single editable source of truth for two committed assets (no build step - run by
hand when the protocol notation changes):

  public/static/masks.gif        - animated, used on the README and the website
  public/static/masks-still.png  - final/resolved frame, the prefers-reduced-motion
                                   fallback on the website and a crisp still

Requires Pillow (dev-only; NOT a server dependency):  pip install Pillow
Run:  python docs/assets/make_protocol_diagram.py

Crypto-accuracy invariants the council fixed (do not regress):
  * masks are DERIVED INDEPENDENTLY and NEVER sent - mask links are dashed and
    labelled "derived, never sent"; only the masked shares travel (solid arrows).
  * the +/- sign convention is explicit and the masks visibly cancel.
  * the aggregator only ever sees masked shares - raw figures stay in the nodes.
Honesty caveats (honest-but-curious, no input validation, no impersonation
defence) live in the caption text next to the asset, not baked into the image.
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ---- canvas (rendered at 2x then downscaled for anti-aliasing) -------------
W, H = 920, 560
SS = 2  # supersample factor

# ---- palette (matches the site's :root accent tokens) ---------------------
BG     = (12, 12, 13)       # --bg #0c0c0d
PANEL  = (22, 22, 24)       # --panel #161618
BORDER = (44, 44, 48)       # --border #2c2c30
TEXT   = (237, 237, 238)    # --text
MUTED  = (152, 152, 158)    # --muted
A_COL  = (242, 198, 75)     # --a
B_COL  = (207, 138, 217)    # --b
C_COL  = (95, 207, 128)     # --c
AGG    = (255, 122, 24)     # --agg
MASK   = (143, 163, 191)    # neutral slate - a shared secret, not a party
GOOD   = (95, 207, 128)

# ---- illustrative numbers (small + concrete so the cancellation clicks) ----
xA, xB, xC = 12, 30, 9
rAB, rAC, rBC = 5, 8, 3
sA = xA + rAB + rAC     # 25   (A is lower in both its pairs -> adds)
sB = xB - rAB + rBC     # 28
sC = xC - rAC - rBC     # -2
TOTAL = sA + sB + sC    # 51 == xA+xB+xC
N = 3
AVG = TOTAL // N        # 17


def sn(v):
    """Signed int with a typographic minus (U+2212) to match the +/- mask labels."""
    return str(v).replace("-", "-")


def _font(names, size):
    for n in names:
        for p in (n, os.path.join("C:/Windows/Fonts", n)):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


UI   = lambda s: _font(["segoeui.ttf", "Arial.ttf", "DejaVuSans.ttf"], s * SS)
UIB  = lambda s: _font(["segoeuib.ttf", "Arial_Bold.ttf", "DejaVuSans-Bold.ttf"], s * SS)
MONO = lambda s: _font(["consola.ttf", "DejaVuSansMono.ttf"], s * SS)

# node centres (in 1x coords)
A = (460, 130)
B = (215, 350)
C = (705, 350)
G = (460, 478)
R = 52


def _s(p):
    return (p[0] * SS, p[1] * SS)


def text_c(d, xy, s, font, fill, anchor="mm"):
    d.text(_s(xy), s, font=font, fill=fill, anchor=anchor)


def chip(d, center, s, font, fg, border):
    """A filled pill behind a label so connecting lines never obscure it."""
    x, y = _s(center)
    l, t, r, b = d.textbbox((x, y), s, font=font, anchor="mm")
    px, py = 9 * SS, 5 * SS
    d.rounded_rectangle([l - px, t - py, r + px, b + py], radius=7 * SS,
                        fill=PANEL, outline=border, width=2 * SS)
    d.text((x, y), s, font=font, fill=fg, anchor="mm")


def legend(d):
    """Persistent key - a fresh viewer doesn't know x / r / s."""
    lx, ly, lw, lh = 622, 58, 276, 116
    bb = [_s((lx, ly))[0], _s((lx, ly))[1], _s((lx + lw, ly + lh))[0], _s((lx + lw, ly + lh))[1]]
    d.rounded_rectangle(bb, radius=10 * SS, fill=PANEL, outline=BORDER, width=1 * SS)
    text_c(d, (lx + 16, ly + 17), "KEY", UIB(12), MUTED, anchor="lm")
    rows = [("x", TEXT, "each party's private figure"),
            ("r", MASK, "pairwise mask - never sent"),
            ("s", TEXT, "masked share  (x ± masks)")]
    yy = ly + 46
    for sym, col, desc in rows:
        text_c(d, (lx + 20, yy), sym, MONO(16), col, anchor="lm")
        text_c(d, (lx + 44, yy), desc, UI(13), MUTED, anchor="lm")
        yy += 27


def dashed(d, p1, p2, fill, width, dash=14, gap=10, alpha=1.0):
    import math
    x1, y1 = _s(p1); x2, y2 = _s(p2)
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    ux, uy = dx / dist, dy / dist
    step = (dash + gap) * SS
    n = int(dist / step) + 1
    col = tuple(int(BG[i] + (fill[i] - BG[i]) * alpha) for i in range(3))
    t = 0.0
    for _ in range(n):
        sx, sy = x1 + ux * t, y1 + uy * t
        e = min(t + dash * SS, dist)
        ex, ey = x1 + ux * e, y1 + uy * e
        d.line([(sx, sy), (ex, ey)], fill=col, width=width * SS)
        t += step


def arrow(d, p1, center, fill, width, progress=1.0, shrink=R, box=(84, 32)):
    """Arrow from party node p1 to the aggregator box centred at `center`.
    The tip is clipped to the box edge facing the party (box = half-width, half-height)
    so every arrow touches the box regardless of approach angle (vertical or diagonal)."""
    import math
    dx, dy = center[0] - p1[0], center[1] - p1[1]
    dist = math.hypot(dx, dy)
    ux, uy = dx / dist, dy / dist
    x1, y1 = p1[0] + ux * shrink, p1[1] + uy * shrink  # start: off the party node
    hw, hh = box                                        # end: on the box edge toward p1
    t_edge = min(hw / abs(ux) if ux else 1e9, hh / abs(uy) if uy else 1e9)
    ex, ey = center[0] - ux * (t_edge - 1), center[1] - uy * (t_edge - 1)
    x2 = x1 + (ex - x1) * progress
    y2 = y1 + (ey - y1) * progress
    d.line([_s((x1, y1)), _s((x2, y2))], fill=fill, width=width * SS)
    if progress > 0.6:
        ah = 11
        lx, ly = ux * ah, uy * ah
        px, py = -uy * ah * 0.6, ux * ah * 0.6
        d.polygon([_s((x2, y2)), _s((x2 - lx + px, y2 - ly + py)),
                   _s((x2 - lx - px, y2 - ly - py))], fill=fill)


def node(d, ctr, col, letter, line2):
    x, y = ctr
    bb = [_s((x - R, y - R))[0], _s((x - R, y - R))[1],
          _s((x + R, y + R))[0], _s((x + R, y + R))[1]]
    d.ellipse(bb, fill=PANEL, outline=col, width=4 * SS)
    text_c(d, (x, y - 16), letter, UIB(26), col)
    text_c(d, (x, y + 17), line2, MONO(17), TEXT)


def base():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)
    text_c(d, (40, 34), "Secure average - how the pairwise masks cancel",
           UIB(19), TEXT, anchor="lm")
    legend(d)
    return img, d


def midpt(p1, p2, t=0.5):
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


def mask_edge(d, p1, p2, plus_lo, minus_hi, alpha=1.0):
    """Dashed link between a pair; +r near the lower-letter end, -r near higher."""
    dashed(d, p1, p2, MASK, 3, alpha=alpha)
    if alpha < 0.5:
        return
    lo = midpt(p1, p2, 0.30)
    hi = midpt(p1, p2, 0.70)
    chip(d, lo, plus_lo, MONO(17), TEXT, MASK)
    chip(d, hi, minus_hi, MONO(17), TEXT, MASK)


def caption(d, line):
    text_c(d, (W // 2, 530), line, UI(15), TEXT)


def render(stage, prog=1.0):
    """stage: figures | masks | shares | cancel | average"""
    img, d = base()

    # mask links
    if stage in ("masks", "compute"):
        mask_edge(d, A, B, "+5", "-5", alpha=prog)
        mask_edge(d, A, C, "+8", "-8", alpha=prog)
        mask_edge(d, B, C, "+3", "-3", alpha=prog)
    elif stage in ("shares", "still"):
        a = 0.6 if stage == "still" else 0.4
        mask_edge(d, A, B, "+5", "-5", alpha=a)
        mask_edge(d, A, C, "+8", "-8", alpha=a)
        mask_edge(d, B, C, "+3", "-3", alpha=a)

    # aggregator box dimensions (widens for the worked-sum beat, then collapses)
    gw, gh = (344 if stage == "cancel" else 168), 64

    # share arrows to the aggregator (only the masked shares travel) - clipped to the box edge
    if stage in ("shares", "cancel", "average", "still"):
        p = prog if stage == "shares" else 1.0
        for ctr, col in ((A, A_COL), (B, B_COL), (C, C_COL)):
            arrow(d, ctr, G, col, 3, progress=p, box=(gw / 2, gh / 2))

    gbb = [_s((G[0] - gw / 2, G[1] - gh / 2))[0], _s((G[0] - gw / 2, G[1] - gh / 2))[1],
           _s((G[0] + gw / 2, G[1] + gh / 2))[0], _s((G[0] + gw / 2, G[1] + gh / 2))[1]]
    lit = stage in ("cancel", "average", "still")
    d.rounded_rectangle(gbb, radius=14 * SS, fill=PANEL,
                        outline=AGG, width=(4 if lit else 3) * SS)

    if stage == "average":
        text_c(d, (G[0], G[1] - 11), f"Total {TOTAL}  ÷  {N} parties", MONO(13), MUTED)
        text_c(d, (G[0], G[1] + 12), f"average = {AVG}", UIB(20), AGG)
    elif stage == "still":
        text_c(d, (G[0], G[1] - 11), "masks cancel", MONO(15), GOOD)
        text_c(d, (G[0], G[1] + 12), f"average = {AVG}", UIB(20), AGG)
    elif stage == "cancel":
        text_c(d, (G[0], G[1] - 11), f"Σ shares = {sA} + {sB} + ({sn(sC)}) = {TOTAL}", MONO(16), TEXT)
        text_c(d, (G[0], G[1] + 13), "(+5-5) + (+8-8) + (+3-3) = 0", MONO(14), GOOD)
    else:
        text_c(d, G, "Aggregator", UI(17), AGG)

    # party nodes (raw figure stays inside until masked)
    if stage in ("figures", "masks", "compute"):
        node(d, A, A_COL, "A", f"x = {xA}")
        node(d, B, B_COL, "B", f"x = {xB}")
        node(d, C, C_COL, "C", f"x = {xC}")
    else:
        node(d, A, A_COL, "A", f"s = {sn(sA)}")
        node(d, B, B_COL, "B", f"s = {sn(sB)}")
        node(d, C, C_COL, "C", f"s = {sn(sC)}")

    # beat 3 - each party turns its figure into a masked share: s = x ± its masks
    if stage == "compute":
        chip(d, (460, 74),  f"s = {xA} + {rAB} + {rAC} = {sn(sA)}", MONO(15), TEXT, A_COL)
        chip(d, (150, 414), f"s = {xB} - {rAB} + {rBC} = {sn(sB)}", MONO(15), TEXT, B_COL)
        chip(d, (772, 414), f"s = {xC} - {rAC} - {rBC} = {sn(sC)}", MONO(15), TEXT, C_COL)

    cap = {
        "figures": "1.  Every party has a private figure x - it never leaves their browser.",
        "masks":   "2.  Each pair shares a secret mask r - derived by both, never sent. One adds it, the other subtracts.",
        "compute": "3.  Each party adds its masks to its own figure - one sign per pair - to get its masked share s.",
        "shares":  "4.  Each party sends only its masked share s. On its own, s looks like a random number.",
        "cancel":  "5.  The aggregator adds the shares - every +mask meets its -mask and cancels to zero.",
        "average": "6.  Only the true total is left; divide by the number of parties to get the average.",
        "still":   "Masks are added by one side and subtracted by the other, so the shares sum to the true total - the average.",
    }[stage]
    caption(d, cap)

    return img.resize((W, H), Image.LANCZOS)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "..", "public", "static"))
    os.makedirs(out, exist_ok=True)

    # (stage, hold_ms) - short partial frames give a sense of motion; long holds so a
    # first-time viewer can actually read each step (owner feedback: slow it down).
    seq = [
        (render("figures"), 3000),
        (render("masks", 0.5), 350),
        (render("masks"), 3600),
        (render("compute"), 4400),
        (render("shares", 0.55), 380),
        (render("shares"), 3000),
        (render("cancel"), 4000),
        (render("average"), 4400),
    ]
    frames = [f for f, _ in seq]
    durations = [ms for _, ms in seq]

    gif_path = os.path.join(out, "masks.gif")
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True, disposal=2)

    still = render("still")
    still.save(os.path.join(out, "masks-still.png"), optimize=True)

    print("wrote", gif_path, "(%d frames)" % len(frames))
    print("wrote", os.path.join(out, "masks-still.png"))


if __name__ == "__main__":
    main()
