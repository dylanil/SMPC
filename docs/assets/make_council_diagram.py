#!/usr/bin/env python3
"""Generate the review-council flow diagram.

Single editable source of truth for one committed asset (no build step - run by
hand if the council process changes, like the other docs/assets generators):

  docs/assets/review-council.png  - how a proposal flows through the
                                     /review-council skill (owner -> manager ->
                                     isolated reviewers + challenger -> debate ->
                                     adjudication -> recommendation -> owner)

Requires Pillow (dev-only; NOT a server dependency):  pip install Pillow
Run:  python docs/assets/make_council_diagram.py

It mirrors the private review-council process used for larger changes; keep the
two in sync if the council mechanics change. Palette = the site's :root accent
tokens; ASCII hyphens in prose; U+00B7 middot only as a list separator.
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1060, 900
SS = 2

# ---- palette (matches the site's :root accent tokens) ----------------------
BG     = (12, 12, 13)
PANEL  = (22, 22, 24)
PANEL2 = (30, 30, 32)
BORDER = (44, 44, 48)
TEXT   = (237, 237, 238)
MUTED  = (152, 152, 158)
AGG    = (255, 122, 24)
OK     = (105, 213, 138)
DANGER = (255, 122, 138)
ROLE = [(242, 198, 75), (207, 138, 217), (95, 207, 128), (239, 111, 154),
        (207, 209, 82), (224, 98, 92), (79, 199, 189), (199, 154, 107)]  # --a..--h


def _font(names, size):
    for n in names:
        for p in (n, os.path.join("C:/Windows/Fonts", n)):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


UI  = lambda s: _font(["segoeui.ttf", "Arial.ttf", "DejaVuSans.ttf"], s * SS)
UIB = lambda s: _font(["segoeuib.ttf", "Arial_Bold.ttf", "DejaVuSans-Bold.ttf"], s * SS)


def _r(*v):
    return [x * SS for x in v]


def text(d, cx, cy, s, font, fill, anchor="mm"):
    d.text((cx * SS, cy * SS), s, font=font, fill=fill, anchor=anchor)


def box(d, cx, cy, w, h, title, sub=None, accent=BORDER, title_col=TEXT, aw=1):
    """Rounded box centred on (cx, cy). Returns (top, bottom) for arrow chaining."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d.rounded_rectangle(_r(x0, y0, x1, y1), radius=10 * SS, fill=PANEL, outline=accent, width=aw * SS)
    if sub:
        text(d, cx, cy - 9, title, UIB(16), title_col)
        text(d, cx, cy + 12, sub, UI(12.5), MUTED)
    else:
        text(d, cx, cy, title, UIB(16), title_col)
    return cy - h / 2, cy + h / 2


def chip(d, cx, cy, label, col, w, dashed=False):
    h = 34
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d.rounded_rectangle(_r(x0, y0, x1, y1), radius=8 * SS, fill=PANEL2,
                        outline=(col if dashed else BORDER), width=(2 if dashed else 1) * SS)
    dot = cx - w / 2 + 16
    d.ellipse(_r(dot - 5, cy - 5, dot + 5, cy + 5), fill=col)
    text(d, dot + 14, cy, label, UIB(13), TEXT, anchor="lm")


def varrow(d, cx, y0, y1, col=MUTED):
    d.line(_r(cx, y0, cx, y1 - 4), fill=col, width=2 * SS)
    a = 6
    d.polygon(_r(cx, y1, cx - a, y1 - a * 1.3, cx + a, y1 - a * 1.3), fill=col)


def render():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)
    cx = W / 2

    text(d, cx, 44, "Review Council", UIB(30), TEXT)
    text(d, cx, 74, "A gated, proportionate review of ONE proposed change - before any code is written.",
         UI(14), MUTED)

    # 1. Owner proposes
    box(d, cx, 124, 320, 44, "Owner proposes a change")
    varrow(d, cx, 146, 176)

    # 2. Manager convenes
    box(d, cx, 208, 600, 60,
        "Manager  (the driving session)",
        "Convenes only the domains the proposal touches - and, always, a challenger.",
        accent=AGG, title_col=AGG, aw=2)
    varrow(d, cx, 238, 286)

    # 3. Isolated opinions panel
    px0, py0, px1, py1 = 60, 292, 1000, 470
    d.rounded_rectangle(_r(px0, py0, px1, py1), radius=12 * SS, fill=(16, 16, 18), outline=BORDER, width=1 * SS)
    text(d, cx, 312, "ISOLATED OPINIONS  -  in parallel, no cross-talk", UIB(12), MUTED)
    text(d, cx, 330, "each domain expert returns ONE verdict:  support  /  support-with-changes  /  oppose",
         UI(11.5), MUTED)

    domains = ["security", "crypto", "QA", "legal", "UX", "product", "graphics", "+ dimensions"]
    cols = [196 + i * 156 for i in range(4)]          # 4 columns
    for i, name in enumerate(domains):
        c = cols[i % 4]
        row_y = 364 if i < 4 else 402
        chip(d, c, row_y, name, ROLE[i], 140)

    # challenger - distinct, adversarial
    chip(d, cx, 444, "CHALLENGER  -  argues the strongest case against / the best alternative",
         DANGER, 560, dashed=True)
    varrow(d, cx, 470, 500)

    # 4. Debate
    box(d, cx, 528, 760, 56, "Debate  -  only where opinions collide",
        "the manager relays each position to the other, iterating until resolved or genuinely stuck")
    varrow(d, cx, 556, 588)

    # 5. Adjudicate
    box(d, cx, 618, 760, 60, "Manager adjudicates",
        "weighs every view through four lenses:  actuary  ·  developer  ·  business  ·  product-design",
        accent=AGG, title_col=AGG, aw=2)
    varrow(d, cx, 648, 680)

    # 6. Recommendation - three pills
    text(d, cx, 700, "ONE RECOMMENDATION", UIB(12), MUTED)
    pills = [("GO", OK), ("REVISE", AGG), ("NO-GO", DANGER)]
    for i, (lab, col) in enumerate(pills):
        pcx = cx - 170 + i * 170
        d.rounded_rectangle(_r(pcx - 66, 718, pcx + 66, 752), radius=17 * SS, fill=PANEL2, outline=col, width=2 * SS)
        text(d, pcx, 735, lab, UIB(16), col)
    varrow(d, cx, 760, 790)

    # 7. Owner approves -> implement
    box(d, cx - 175, 818, 300, 46, "Owner approves")
    box(d, cx + 175, 818, 300, 46, "Implement  (commit per workflow)")
    d.line(_r(cx - 25, 818, cx + 25 - 4, 818), fill=MUTED, width=2 * SS)
    d.polygon(_r(cx + 25, 818, cx + 25 - 9, 818 - 6, cx + 25 - 9, 818 + 6), fill=MUTED)
    text(d, cx, 858, "Code is written only after the owner approves.  Scale the council to the proposal's blast radius.",
         UI(12), MUTED)

    return img.resize((W, H), Image.LANCZOS)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "review-council.png")
    render().save(out, optimize=True)
    print("wrote", out, "(%dx%d)" % (W, H))


if __name__ == "__main__":
    main()
