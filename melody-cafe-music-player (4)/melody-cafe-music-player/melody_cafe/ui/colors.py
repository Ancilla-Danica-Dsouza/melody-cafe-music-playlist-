# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""Fonts and colour helpers."""

UI_FONT = "Segoe UI"
SERIF = "Georgia"


def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def mix(a, b, r):
    """Blend colour a towards colour b by ratio r (0 = a, 1 = b)."""
    ra = _rgb(a)
    rb = _rgb(b)
    r = max(0.0, min(1.0, float(r)))
    out = "#"
    for i in range(3):
        out += format(int(ra[i] + (rb[i] - ra[i]) * r), "02x")
    return out


def derive(t):
    c = dict(t)
    c["panel2"] = mix(t["panel"], t["text"], 0.07)
    c["line"] = mix(t["panel"], t["text"], 0.17)
    c["soft_sel"] = mix(t["panel"], t["accent"], 0.22)
    # Extra design tokens for enhanced visuals
    c["panel_hover"] = mix(t["panel"], t["accent"], 0.12)
    c["card_border"] = mix(t["panel"], t["text"], 0.18)
    c["accent_glow"] = mix(t["panel"], t["accent"], 0.35)
    c["accent_soft"] = mix(t["panel"], t["accent"], 0.15)
    c["highlight"] = mix(t["accent"], "#ffffff", 0.40)
    c["shadow"] = mix(t["bg"], "#000000", 0.45)
    c["success"] = "#22c55e"
    c["warning"] = "#f59e0b"
    return c


def round_rect(cv, x1, y1, x2, y2, r, **kw):
    """Draw a smooth rounded rectangle on a Tkinter canvas."""
    r = max(1, min(r, abs(x2 - x1) / 2, abs(y2 - y1) / 2))
    pts = (x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1)
    return cv.create_polygon(pts, smooth=True, **kw)
