#!/usr/bin/env python3
"""Generate the social/share preview card (Open Graph image).

Single editable source of truth for one committed asset (no build step - run by
hand when the page copy or branding changes, exactly like make_protocol_diagram.py):

  public/static/og-preview.png   - the og:image referenced in all three pages'
                                    <head> (and the README link unfurl)

Requires Pillow (dev-only; NOT a server dependency):  pip install Pillow
Run:  python docs/assets/make_og_preview.py

Why this script exists (RB-45 / GFX-02): the card used to be a hand-exported
screenshot that drifted from the site - it baked in em dashes (against the
ASCII-hyphen convention) and a stale disclaimer footer. This generator is now the
only way the card is produced, so regenerating it is a one-command, no-drift step.

Anti-drift contract (keep these in sync with the live pages when you edit copy):
  * TITLE mirrors the <h1> / og:title (home.html:94, :8).
  * TAGLINE is the value prop, deliberately phrased so it is true in EVERY mode
    incl. the solo demo ("crosses the wire", not "leaves their browser" - LEG-06).
  * DISCLAIMER is a short, honest summary of the always-visible footer
    (home.html:157) - not a copy of the full legal paragraph (too long for a card).
  * Prose uses ASCII hyphens; only real math uses U+2212. Palette = the site's
    :root accent tokens (matches make_protocol_diagram.py).
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ---- canvas (standard Open Graph size, rendered at 2x then downscaled) ------
W, H = 1200, 630
SS = 2  # supersample factor

# ---- palette (matches the site's :root accent tokens) ----------------------
BG     = (12, 12, 13)       # --bg #0c0c0d
PANEL  = (22, 22, 24)       # --panel #161618
PANEL2 = (30, 30, 32)       # --panel-2 #1e1e20
BORDER = (44, 44, 48)       # --border #2c2c30
TEXT   = (237, 237, 238)    # --text #ededee
MUTED  = (152, 152, 158)    # --muted #98989e
AGG    = (255, 122, 24)     # --agg #ff7a18
OK     = (105, 213, 138)    # --ok #69d58a
A_COL  = (242, 198, 75)     # --a
B_COL  = (207, 138, 217)    # --b
C_COL  = (95, 207, 128)     # --c

# ---- copy (mirror the live pages - see the anti-drift contract above) ------
WORDMARK   = "SMPC"
TITLE      = "Secure Multi-Party Average"
TAGLINE    = "3 to 10 participants compute an average - no raw figure ever crosses the wire."
PILLS      = [("Pairwise masks cancel", A_COL),
              ("ECDSA-signed shares", B_COL),
              ("Independently verifiable", OK)]
DISCLAIMER = "Educational demonstration only - not production-secure. Do not enter real figures."
URL        = "fl-wg-smpc.fly.dev"


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


def _s(v):
    return v * SS


def text_c(d, xy, s, font, fill, anchor="mm"):
    d.text((_s(xy[0]), _s(xy[1])), s, font=font, fill=fill, anchor=anchor)


def text_w(d, s, font):
    """Width of a string in 1x px."""
    l, _, r, _ = d.textbbox((0, 0), s, font=font)
    return (r - l) / SS


def wrap(d, s, font, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(d, trial, font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def logo(d, cx, cy):
    """Favicon-style mark (rounded orange tile + dark Sigma) + wordmark, centred on (cx, cy)."""
    tile, gap = 60, 18
    wm_font = UIB(34)
    wm_w = text_w(d, WORDMARK, wm_font)
    total = tile + gap + wm_w
    left = cx - total / 2
    # tile
    tb = [_s(left), _s(cy - tile / 2), _s(left + tile), _s(cy + tile / 2)]
    d.rounded_rectangle(tb, radius=_s(14), fill=AGG)
    text_c(d, (left + tile / 2, cy - 1), "Σ", UIB(34), BG)  # Sigma
    # wordmark
    text_c(d, (left + tile + gap, cy), WORDMARK, wm_font, TEXT, anchor="lm")


def pill(d, cx, cy, label, dot_col):
    """Rounded chip with a colour dot + label, centred on (cx, cy). Returns 1x width."""
    font = UI(23)
    pad_x, dot, dot_gap = 22, 13, 12
    label_w = text_w(d, label, font)
    w = pad_x + dot + dot_gap + label_w + pad_x
    h = 52
    left = cx - w / 2
    bb = [_s(left), _s(cy - h / 2), _s(left + w), _s(cy + h / 2)]
    d.rounded_rectangle(bb, radius=_s(h / 2), fill=PANEL2, outline=BORDER, width=_s(1))
    dcx = left + pad_x + dot / 2
    d.ellipse([_s(dcx - dot / 2), _s(cy - dot / 2), _s(dcx + dot / 2), _s(cy + dot / 2)], fill=dot_col)
    text_c(d, (left + pad_x + dot + dot_gap, cy), label, font, TEXT, anchor="lm")
    return w


def render():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    cx = W / 2

    # subtle top hairline in the brand accent
    d.rectangle([0, 0, _s(W), _s(6)], fill=AGG)

    logo(d, cx, 92)

    text_c(d, (cx, 214), TITLE, UIB(64), TEXT)

    # short accent rule under the title
    rule_w = 132
    d.rounded_rectangle([_s(cx - rule_w / 2), _s(262), _s(cx + rule_w / 2), _s(266)],
                        radius=_s(2), fill=AGG)

    # tagline (wrap defensively, though it fits one line at this width)
    tag_font = UI(28)
    lines = wrap(d, TAGLINE, tag_font, max_w=960)
    ty = 312
    for ln in lines:
        text_c(d, (cx, ty), ln, tag_font, MUTED)
        ty += 40

    # feature pills - measure then place (two-pass so the row is perfectly centred)
    gap = 22
    measure_font = UI(23)
    pill_ws = []
    for lbl, _ in PILLS:
        pill_ws.append(22 + 13 + 12 + text_w(d, lbl, measure_font) + 22)
    row_w = sum(pill_ws) + gap * (len(PILLS) - 1)
    x = cx - row_w / 2
    py = 420
    for (lbl, col), w in zip(PILLS, pill_ws):
        pill(d, x + w / 2, py, lbl, col)
        x += w + gap

    # disclaimer + url at the foot
    text_c(d, (cx, 540), DISCLAIMER, UI(20), MUTED)
    text_c(d, (cx, 584), URL, MONO(24), AGG)

    return img.resize((W, H), Image.LANCZOS)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "..", "public", "static"))
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "og-preview.png")
    render().save(path, optimize=True)
    print("wrote", path, "(%dx%d)" % (W, H))


if __name__ == "__main__":
    main()
