# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""Custom canvas widgets: Pill, RoundIcon, Slider, Swatches, PlaylistView."""

import math
import random
import tkinter as tk

from ..utils import fmt
from .colors import UI_FONT, SERIF, mix, round_rect
from .themes import THEMES


class Pill(tk.Canvas):
    """A polished modern rounded button. kind: primary, soft, toggle, or danger."""
    def __init__(self, parent, app, text, command, w=100, h=34, kind="soft", surface="panel", size=10):
        tk.Canvas.__init__(self, parent, width=w, height=h, highlightthickness=0, bd=0, cursor="hand2")
        self.app = app
        self.c = app.c
        self.text = text
        self.command = command
        self.kind = kind
        self.surface = surface
        self.size = size
        self.active = False
        self.hover = False
        self.pressed = False
        self._pw = w
        self._ph = h
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        app.customs.append(self)

    def on_enter(self, e):
        self.hover = True
        self.draw()

    def on_leave(self, e):
        self.hover = False
        self.pressed = False
        self.draw()

    def on_press(self, e):
        self.pressed = True
        self.draw()

    def on_release(self, e):
        was_pressed = self.pressed
        self.pressed = False
        self.draw()
        if was_pressed and self.hover and self.command:
            self.command()

    def set_active(self, v):
        self.active = v
        self.draw()

    def set_text(self, text):
        self.text = text
        self.draw()

    def restyle(self, c):
        self.c = c
        self.config(bg=c.get(self.surface, c["panel"]))
        self.draw()

    def draw(self):
        self.delete("all")
        c = self.c
        w, h = self._pw, self._ph
        r = h / 2

        if self.kind == "primary":
            if self.pressed:
                fill = mix(c["accent"], "#000000", 0.2)
            elif self.hover:
                fill = c.get("highlight", mix(c["accent"], "#ffffff", 0.2))
            else:
                fill = c["button"]
            fg = c["btn_text"]
            outline = mix(c["accent"], "#ffffff", 0.3) if self.hover else ""
        elif self.kind == "toggle" and self.active:
            fill = mix(c["accent"], "#000000", 0.15) if self.pressed else c["accent"]
            fg = c["btn_text"]
            outline = c.get("highlight", c["accent"])
        else:
            if self.pressed:
                fill = mix(c["panel2"], c["accent"], 0.35)
            elif self.hover:
                fill = mix(c["panel2"], c["accent"], 0.20)
            else:
                fill = c["panel2"]
            fg = c["text"]
            outline = c["accent"] if self.hover else c["line"]

        # Base pill
        round_rect(self, 1, 1, w - 1, h - 1, r, fill=fill, outline=outline, width=1.2 if outline else 0)

        # Active indicator dot for toggles
        text_x = w / 2
        if self.kind == "toggle" and self.active:
            dot_color = c["btn_text"]
            self.create_oval(10, h / 2 - 3, 16, h / 2 + 3, fill=dot_color, outline="")
            text_x = w / 2 + 5

        self.create_text(text_x, h / 2, text=self.text, fill=fg,
                         font=(UI_FONT, self.size, "bold" if (self.kind == "primary" or self.active) else "normal"))


class RoundIcon(tk.Canvas):
    """A circular modern button with an icon: prev, play, pause, next, or stop."""
    def __init__(self, parent, app, icon, command, size=46, kind="soft", surface="panel"):
        tk.Canvas.__init__(self, parent, width=size, height=size, highlightthickness=0, bd=0, cursor="hand2")
        self.app = app
        self.c = app.c
        self.icon = icon
        self.command = command
        self.kind = kind
        self.surface = surface
        self._size = size
        self.hover = False
        self.pressed = False
        self.bind("<Enter>", lambda e: self.set_hover(True))
        self.bind("<Leave>", lambda e: self.set_hover(False))
        self.bind("<Button-1>", lambda e: self.set_pressed(True))
        self.bind("<ButtonRelease-1>", self.on_release)
        app.customs.append(self)

    def set_hover(self, v):
        self.hover = v
        self.draw()

    def set_pressed(self, v):
        self.pressed = v
        self.draw()

    def on_release(self, e):
        was = self.pressed
        self.pressed = False
        self.draw()
        if was and self.hover and self.command:
            self.command()

    def set_icon(self, icon):
        self.icon = icon
        self.draw()

    def restyle(self, c):
        self.c = c
        self.config(bg=c.get(self.surface, c["panel"]))
        self.draw()

    def draw(self):
        self.delete("all")
        c = self.c
        S = self._size
        cx, cy = S / 2, S / 2

        if self.kind == "primary":
            # Play/Pause centerpiece button
            if self.hover:
                # Soft glowing aura
                self.create_oval(2, 2, S - 2, S - 2, fill=c.get("accent_glow", c["panel"]), outline="")
            
            fill = mix(c["accent"], "#000000", 0.15) if self.pressed else (c.get("highlight", c["accent"]) if self.hover else c["button"])
            fg = c["btn_text"]
            outline = mix(c["accent"], "#ffffff", 0.4) if self.hover else c["accent"]
            self.create_oval(4, 4, S - 4, S - 4, fill=fill, outline=outline, width=1.5)
        else:
            fill = mix(c["panel2"], c["accent"], 0.28) if (self.hover or self.pressed) else c["panel2"]
            fg = c["accent"] if self.hover else c["text"]
            outline = c["accent"] if self.hover else c["line"]
            self.create_oval(2, 2, S - 2, S - 2, fill=fill, outline=outline, width=1.2)

        s = S * 0.18
        ic = self.icon
        if ic == "play":
            # Polished triangular play symbol slightly offset to center
            self.create_polygon(cx - s * 0.6, cy - s * 1.15,
                                cx - s * 0.6, cy + s * 1.15,
                                cx + s * 1.25, cy,
                                fill=fg, outline=fg, width=1)
        elif ic == "pause":
            # Two rounded vertical bars
            round_rect(self, cx - s * 0.95, cy - s * 1.1, cx - s * 0.25, cy + s * 1.1, 2, fill=fg, outline=fg)
            round_rect(self, cx + s * 0.25, cy - s * 1.1, cx + s * 0.95, cy + s * 1.1, 2, fill=fg, outline=fg)
        elif ic == "next":
            self.create_polygon(cx - s * 0.9, cy - s, cx - s * 0.9, cy + s, cx + s * 0.5, cy,
                                fill=fg, outline=fg)
            round_rect(self, cx + s * 0.65, cy - s, cx + s * 0.95, cy + s, 1.5, fill=fg, outline=fg)
        elif ic == "prev":
            self.create_polygon(cx + s * 0.9, cy - s, cx + s * 0.9, cy + s, cx - s * 0.5, cy,
                                fill=fg, outline=fg)
            round_rect(self, cx - s * 0.95, cy - s, cx - s * 0.65, cy + s, 1.5, fill=fg, outline=fg)
        else: # stop
            round_rect(self, cx - s * 0.85, cy - s * 0.85, cx + s * 0.85, cy + s * 0.85, 2,
                       fill=fg, outline=fg)


class Slider(tk.Canvas):
    """An elegant rounded track slider. Supports click-and-drag scrubbing."""
    PAD = 10

    def __init__(self, parent, app, interactive=False, command=None, width=200, height=22, value=0):
        tk.Canvas.__init__(self, parent, width=width, height=height, highlightthickness=0, bd=0,
                           cursor="hand2" if interactive else "")
        self.app = app
        self.c = app.c
        self.interactive = interactive
        self.command = command
        self.value = value
        self.hover = False
        self.dragging = False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Enter>", lambda e: self.set_hover(True))
        self.bind("<Leave>", lambda e: self.set_hover(False))
        self.bind("<Button-1>", self.on_start)
        self.bind("<B1-Motion>", self.move)
        self.bind("<ButtonRelease-1>", self.on_stop)
        app.customs.append(self)

    def set_hover(self, v):
        self.hover = v
        self.draw()

    def on_start(self, e):
        self.dragging = True
        self.move(e)

    def on_stop(self, e):
        self.dragging = False
        self.draw()

    def move(self, e):
        w = self.winfo_width()
        v = 100.0 * (e.x - self.PAD) / max(w - 2 * self.PAD, 1)
        self.value = min(max(v, 0.0), 100.0)
        self.draw()
        if self.command:
            self.command(self.value)

    def set(self, v):
        if not self.dragging:
            self.value = min(max(v, 0.0), 100.0)
            self.draw()

    def restyle(self, c):
        self.c = c
        self.config(bg=c["panel"])
        self.draw()

    def draw(self):
        self.delete("all")
        c = self.c
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 20:
            return
        y = h / 2
        th = 4 if not (self.hover and self.interactive) else 6
        x = self.PAD + (w - 2 * self.PAD) * (self.value / 100.0)

        # Background track
        round_rect(self, self.PAD, y - th / 2, w - self.PAD, y + th / 2, th / 2,
                   fill=c.get("line", "#444444"), outline="")

        # Active progress track
        if x > self.PAD:
            fill_col = c.get("highlight", c["accent"]) if self.hover else c["accent"]
            round_rect(self, self.PAD, y - th / 2, max(x, self.PAD + th), y + th / 2, th / 2,
                       fill=fill_col, outline="")

        # Thumb handle
        if self.interactive:
            tr = 7 if (self.hover or self.dragging) else 5.5
            # Glow halo
            if self.hover or self.dragging:
                self.create_oval(x - tr - 3, y - tr - 3, x + tr + 3, y + tr + 3,
                                 fill=c.get("accent_glow", c["panel2"]), outline="")
            self.create_oval(x - tr, y - tr, x + tr, y + tr,
                             fill=c.get("highlight", c["accent"]), outline=c["panel"], width=2)
            self.create_oval(x - 2, y - 2, x + 2, y + 2, fill=c["panel"], outline="")


class Swatches(tk.Canvas):
    """A row of small circular theme previews with smooth halos."""
    D = 18
    GAP = 7

    def __init__(self, parent, app, names):
        n = len(names)
        width = min(n * (self.D + self.GAP) + self.GAP, 520)
        tk.Canvas.__init__(self, parent, width=width, height=self.D + 10,
                           highlightthickness=0, bd=0, cursor="hand2")
        self.app = app
        self.c = app.c
        self.names = names
        self.bind("<Motion>", self.on_motion)
        self.bind("<Leave>", lambda e: app.hint_theme(None))
        self.bind("<Button-1>", self.on_click)
        app.customs.append(self)

    def index_at(self, x):
        i = int((x - self.GAP / 2) // (self.D + self.GAP))
        return i if 0 <= i < len(self.names) else -1

    def on_motion(self, e):
        i = self.index_at(e.x)
        self.app.hint_theme(self.names[i] if i >= 0 else None)

    def on_click(self, e):
        i = self.index_at(e.x)
        if i >= 0:
            self.app.apply_theme(self.names[i])

    def restyle(self, c):
        self.c = c
        self.config(bg=c["bg"])
        self.draw()

    def draw(self):
        self.delete("all")
        current = self.app.theme_name.get()
        y0 = 5
        for i in range(len(self.names)):
            name = self.names[i]
            t = THEMES[name]
            x0 = self.GAP + i * (self.D + self.GAP)
            if x0 + self.D > self.winfo_width() and self.winfo_width() > 50:
                break
            if name == current:
                # Active selection halo
                self.create_oval(x0 - 4, y0 - 4, x0 + self.D + 4, y0 + self.D + 4,
                                 outline=self.c["accent"], width=2)
            self.create_oval(x0, y0, x0 + self.D, y0 + self.D, fill=t["bg"], outline=t["muted"], width=1)
            self.create_oval(x0 + 4, y0 + 4, x0 + self.D - 4, y0 + self.D - 4, fill=t["accent"], outline="")


class PlaylistView(tk.Canvas):
    """The song list. Walks the doubly circular linked list to draw each row."""
    ROW = 46

    def __init__(self, parent, app):
        tk.Canvas.__init__(self, parent, highlightthickness=0, bd=0)
        self.app = app
        self.c = app.c
        self.offset = 0
        self.sel = -1
        self.hover = -1
        self.drag = False
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Button-1>", self.on_click)
        self.bind("<Double-Button-1>", self.on_double)
        self.bind("<Motion>", self.on_motion)
        self.bind("<Leave>", self.on_leave)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        app.customs.append(self)

    def restyle(self, c):
        self.c = c
        self.config(bg=c["panel"])
        self.draw()

    def count(self):
        return self.app.playlist.count()

    def max_offset(self):
        return max(0, self.count() * self.ROW - self.winfo_height())

    def scroll_by(self, px):
        self.offset += px
        self.draw()

    def see(self, idx):
        top = idx * self.ROW
        bottom = top + self.ROW
        h = self.winfo_height()
        if top < self.offset:
            self.offset = top
        elif bottom > self.offset + h:
            self.offset = bottom - h
        self.draw()

    def move(self, step):
        n = self.count()
        if n == 0:
            return
        if self.sel < 0:
            self.sel = 0
        else:
            self.sel = min(max(self.sel + step, 0), n - 1)
        self.see(self.sel)

    def clamp_selection(self):
        n = self.count()
        if self.sel >= n:
            self.sel = n - 1

    def in_scrollbar(self, x):
        return self.max_offset() > 0 and x > self.winfo_width() - 16

    def index_at(self, y):
        idx = int((y + self.offset) // self.ROW)
        return idx if 0 <= idx < self.count() else -1

    def on_click(self, e):
        if self.in_scrollbar(e.x):
            self.drag = True
            self.drag_to(e.y)
            return
        idx = self.index_at(e.y)
        if idx >= 0:
            self.sel = idx
            self.draw()

    def on_double(self, e):
        idx = self.index_at(e.y)
        if idx >= 0 and not self.in_scrollbar(e.x):
            self.sel = idx
            self.draw()
            self.app.play_selected()

    def on_drag(self, e):
        if self.drag:
            self.drag_to(e.y)

    def on_release(self, e):
        self.drag = False

    def drag_to(self, y):
        h = max(self.winfo_height(), 1)
        self.offset = (y / h) * self.max_offset()
        self.draw()

    def on_motion(self, e):
        idx = -1 if self.in_scrollbar(e.x) else self.index_at(e.y)
        if idx != self.hover:
            self.hover = idx
            self.draw()

    def on_leave(self, e):
        self.hover = -1
        self.draw()

    def draw(self):
        self.delete("all")
        c = self.c
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 30 or h < 30:
            return
        pl = self.app.playlist
        n = pl.count()
        if n == 0:
            # Welcoming modern empty state
            cy = h / 2
            self.create_text(w / 2, cy - 24, text="\u2615  \u266a", fill=c["accent"],
                             font=(SERIF, 24, "bold"))
            self.create_text(w / 2, cy + 8, text="Your playlist is empty", fill=c["text"],
                             font=(SERIF, 15, "bold"))
            self.create_text(w / 2, cy + 32, text="Search Online Music or press Demo songs to begin",
                             fill=c["muted"], font=(UI_FONT, 10))
            return

        self.offset = min(max(self.offset, 0), self.max_offset())
        first = int(self.offset // self.ROW)
        y = first * self.ROW - self.offset
        node = pl.nodeAt(first)
        i = first
        while y < h and i < n:
            self.draw_row(i, node, y, w)
            node = node.next
            i += 1
            y += self.ROW

        # Modern pill scrollbar thumb
        if self.max_offset() > 0:
            total = n * self.ROW
            th = max(36, h * h / total)
            ty = (self.offset / self.max_offset()) * (h - th)
            sb_fill = mix(c["panel"], c["accent"], 0.4) if self.drag else mix(c["panel"], c["text"], 0.3)
            round_rect(self, w - 8, ty + 2, w - 3, ty + th - 2, 2.5, fill=sb_fill, outline="")

    def draw_row(self, i, node, y, w):
        c = self.c
        R = self.ROW
        right = w - (18 if self.max_offset() > 0 else 8)
        cur = (node == self.app.current)
        playing_now = cur and self.app.playing and not self.app.paused

        # Row background card
        if i == self.sel:
            round_rect(self, 6, y + 2, right, y + R - 2, 8,
                       fill=c["soft_sel"], outline=c["accent"], width=1.5)
        elif i == self.hover:
            round_rect(self, 6, y + 2, right, y + R - 2, 8,
                       fill=c.get("panel_hover", c["panel2"]), outline=c["line"], width=1)
        elif cur:
            round_rect(self, 6, y + 2, right, y + R - 2, 8,
                       fill=mix(c["panel"], c["accent"], 0.12), outline=c.get("accent_soft", c["accent"]), width=1)

        cy = y + R / 2

        # Left track icon / number
        if cur:
            # Animated mini dancing equalizer bars
            frame = getattr(self.app, "frame", 0)
            bar_heights = [
                6 + int(5 * math.sin(frame * 0.35 + 0.5)),
                12 + int(6 * math.sin(frame * 0.4 + 1.2)),
                8 + int(5 * math.sin(frame * 0.3 + 2.0)),
            ] if playing_now else [4, 11, 7]
            for k in range(3):
                hh = max(3, bar_heights[k])
                bx = 20 + k * 6
                round_rect(self, bx, cy + 6 - hh, bx + 3.5, cy + 6, 1.5,
                           fill=c["accent"], outline="")
        else:
            self.create_text(26, cy, text=str(i + 1), fill=c["muted"], font=(UI_FONT, 10, "bold"))

        # Title text
        font_weight = "bold" if cur else "normal"
        text_color = c["accent"] if cur else c["text"]
        
        # Determine source badge tag
        path = getattr(node, "audio_file", "") or ""
        tag = ""
        if "youtube_" in path:
            tag = " \u2022 YouTube"
        elif "deezer_" in path:
            tag = " \u2022 Preview"
        elif "jamendo_" in path:
            tag = " \u2022 Jamendo"
        elif path.endswith(".wav") and "UnitTest" not in path:
            tag = " \u2022 Audio"
        
        self.create_text(52, cy - (2 if tag else 0), text=node.title, anchor="w",
                         fill=text_color, font=(UI_FONT, 11, font_weight))
        
        if tag:
            self.create_text(52, cy + 10, text=tag.lstrip(" \u2022 "), anchor="w",
                             fill=c["muted"], font=(UI_FONT, 8))

        # Duration badge
        self.create_text(right - 12, cy, text=fmt(node.duration), anchor="e",
                         fill=c["accent"] if cur else c["muted"], font=(UI_FONT, 10))
