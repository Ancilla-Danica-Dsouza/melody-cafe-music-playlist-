# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021

"""The main window with enhanced visual design and interactive turntable."""

import os
import math
import time
import random
import tkinter as tk
from tkinter import filedialog, messagebox

from ..core import Playlist
from ..audio import (Audio, make_melody_file, file_length_seconds, export_song, ClipError,
                     AUDIO_OK, PYGAME_ERROR)
from ..utils import fmt
from .colors import UI_FONT, SERIF, mix, derive, round_rect
from .themes import THEMES
from .widgets import Pill, RoundIcon, Slider, Swatches, PlaylistView
from .online_window import OnlineWindow
from ..online import PREVIEW_SECONDS


class PlayerApp:
    DEMO_SECONDS = 10
    BARS = 28

    def __init__(self, root):
        self.root = root
        root.title("Melody Cafe Music Player")
        root.geometry("1140x750")
        root.minsize(1040, 700)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.themed = []                 # (widget, role) pairs recoloured when the theme changes
        self.customs = []                # custom canvas widgets that redraw themselves
        self.theme_name = tk.StringVar(value="Cafe Brown")
        self.download_mode = tk.StringVar(value="full")   # "full" (default) or "10s"
        self.c = derive(THEMES["Cafe Brown"])
        self.playlist = Playlist(log=self.write_log)
        self.audio = Audio()
        self.current = None
        self.playing = False
        self.paused = False
        self.start_time = 0.0
        self.pause_time = 0.0
        self.shuffle = False
        self.repeat_one = False
        self.demo_mode = False           # Full songs play by default with no premature cut-off
        self.volume = 80.0
        self.is_muted = False
        self.pre_mute_vol = 80.0
        self.volume_warned = False
        self.spin = 0
        self.frame = 0
        self.arm_x = 190.0
        self.arm_y = 140.0
        self.eq_mode = "bars"            # "bars" or "wave"
        self.eq_heights = [4.0] * self.BARS
        self.eq_peaks = [6.0] * self.BARS

        self.build_ui()
        self.apply_theme("Cafe Brown")
        self.bind_keys()
        if AUDIO_OK:
            self.write_log("Audio ready. Search online music or press Demo songs to begin.")
        else:
            self.write_log("Audio is OFF. Run: python -m pip install pygame (then restart). "
                           "Details: " + PYGAME_ERROR)
        self.refresh_all()
        self.tick()
        self.animate()

    # ---------- building blocks ----------
    def reg(self, widget, role):
        self.themed.append((widget, role))
        return widget

    def label(self, parent, text, role, font, **kw):
        return self.reg(tk.Label(parent, text=text, font=font, bd=0, **kw), role)

    def field(self, parent, width_chars):
        f = self.reg(tk.Frame(parent, bd=0), "field")
        e = self.reg(tk.Entry(f, bd=0, relief="flat", font=(UI_FONT, 11), width=width_chars), "entry_in")
        e.pack(fill="x", padx=10, pady=7)
        e.bind("<FocusIn>", lambda ev: f.config(highlightbackground=self.c["accent"]))
        e.bind("<FocusOut>", lambda ev: f.config(highlightbackground=self.c["line"]))
        return f, e

    def build_ui(self):
        r = self.root
        self.reg(r, "bg")

        # ----- header -----
        head = self.reg(tk.Frame(r, bd=0), "bg")
        head.pack(fill="x", padx=26, pady=(16, 0))
        hl = self.reg(tk.Frame(head, bd=0), "bg")
        hl.pack(side="left")
        self.title_label = self.label(hl, "", "title", (SERIF, 24, "bold"), anchor="w")
        self.title_label.pack(anchor="w")
        self.label(hl, "Ancilla Danica Dsouza   |   PRN: 25070721021", "bgtext",
                   (SERIF, 11), anchor="w").pack(anchor="w")
        hr = self.reg(tk.Frame(head, bd=0), "bg")
        hr.pack(side="right")
        self.swatches = Swatches(hr, self, tuple(THEMES.keys()))
        self.swatches.pack(anchor="e")
        self.theme_label = self.label(hr, "", "bgmuted", (SERIF, 10, "italic"), anchor="e")
        self.theme_label.pack(anchor="e", pady=(2, 0))

        self.stripe = tk.Canvas(r, height=4, highlightthickness=0, bd=0)
        self.stripe.pack(fill="x", padx=26, pady=(12, 0))
        self.stripe.bind("<Configure>", self.draw_stripe)

        # ----- status bar (bottom) -----
        self.status = self.label(r, "", "bgmuted", (UI_FONT, 9), anchor="nw", justify="left",
                                 height=2, wraplength=1040)
        self.status.pack(side="bottom", fill="x", padx=26, pady=(0, 10))

        # ----- body -----
        body = self.reg(tk.Frame(r, bd=0), "bg")
        body.pack(fill="both", expand=True, padx=26, pady=(14, 8))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ===== left: now playing card =====
        pcard = self.reg(tk.Frame(body, width=380, bd=0), "card")
        pcard.grid(row=0, column=0, sticky="ns")
        pcard.pack_propagate(False)

        # Header status pill
        pill_row = self.reg(tk.Frame(pcard, bd=0), "panel")
        pill_row.pack(fill="x", padx=20, pady=(14, 0))
        self.status_pill = self.label(pill_row, " \u25a0 IDLE ", "pmuted", (UI_FONT, 9, "bold"))
        self.status_pill.pack(side="left")
        self.mode_tag = self.label(pill_row, "FULL AUDIO", "pmuted", (UI_FONT, 8, "bold"))
        self.mode_tag.pack(side="right")

        # Turntable disc & tonearm canvas
        self.disc = tk.Canvas(pcard, width=220, height=216, highlightthickness=0, bd=0)
        self.reg(self.disc, "panel")
        self.disc.pack(pady=(4, 6))

        # Track metadata
        self.now_label = self.label(pcard, "Nothing playing", "paccent", (SERIF, 17, "bold"),
                                    wraplength=340, justify="center")
        self.now_label.pack(padx=16)
        self.next_label = self.label(pcard, "Add songs and press play", "pmuted", (UI_FONT, 9))
        self.next_label.pack(pady=(2, 6))

        # Progress slider & timestamps
        self.progress = Slider(pcard, self, interactive=True, command=self.on_seek, height=16)
        self.progress.pack(fill="x", padx=22)
        trow = self.reg(tk.Frame(pcard, bd=0), "panel")
        trow.pack(fill="x", padx=26, pady=(1, 4))
        self.elapsed_label = self.label(trow, "0:00", "pmuted", (UI_FONT, 9))
        self.elapsed_label.pack(side="left")
        self.total_label = self.label(trow, "0:00", "pmuted", (UI_FONT, 9))
        self.total_label.pack(side="right")

        # Playback control buttons
        crow = self.reg(tk.Frame(pcard, bd=0), "panel")
        crow.pack(pady=(4, 6))
        RoundIcon(crow, self, "prev", self.prev_song, 44).pack(side="left", padx=6)
        self.play_btn = RoundIcon(crow, self, "play", self.toggle_play, 64, kind="primary")
        self.play_btn.pack(side="left", padx=6)
        RoundIcon(crow, self, "next", self.next_song_manual, 44).pack(side="left", padx=6)
        RoundIcon(crow, self, "stop", self.stop, 44).pack(side="left", padx=6)

        # Toggle modes row
        orow = self.reg(tk.Frame(pcard, bd=0), "panel")
        orow.pack(pady=(0, 6))
        self.shuffle_btn = Pill(orow, self, "Shuffle", self.toggle_shuffle, 96, 28, kind="toggle", size=9)
        self.shuffle_btn.pack(side="left", padx=3)
        self.repeat_btn = Pill(orow, self, "Repeat one", self.toggle_repeat, 102, 28, kind="toggle", size=9)
        self.repeat_btn.pack(side="left", padx=3)
        self.demo_btn = Pill(orow, self, "Quick demo", self.toggle_demo, 100, 28, kind="toggle", size=9)
        self.demo_btn.pack(side="left", padx=3)

        # Volume row with clickable mute/unmute
        vrow = self.reg(tk.Frame(pcard, bd=0), "panel")
        vrow.pack(fill="x", padx=24, pady=(0, 4))
        self.vol_icon_btn = tk.Label(vrow, text="\U0001f50a", font=(UI_FONT, 11), bd=0, cursor="hand2")
        self.reg(self.vol_icon_btn, "pmuted")
        self.vol_icon_btn.pack(side="left", padx=(0, 4))
        self.vol_icon_btn.bind("<Button-1>", lambda e: self.toggle_mute())
        
        self.vol_slider = Slider(vrow, self, interactive=True, command=self.on_volume, height=20, value=80)
        self.vol_slider.pack(side="left", fill="x", expand=True, padx=6)
        self.vol_label = self.label(vrow, "80%", "pmuted", (UI_FONT, 9), width=4)
        self.vol_label.pack(side="right")

        # Equalizer / Waveform visualizer canvas (clickable to switch mode!)
        eq_box = self.reg(tk.Frame(pcard, bd=0), "panel")
        eq_box.pack(fill="x", padx=22, pady=(2, 10))
        
        eq_head = self.reg(tk.Frame(eq_box, bd=0), "panel")
        eq_head.pack(fill="x")
        self.eq_title = self.label(eq_head, "AUDIO VISUALIZER", "pmuted", (UI_FONT, 8, "bold"))
        self.eq_title.pack(side="left")
        self.eq_mode_btn = self.label(eq_head, "[click to switch view]", "pmuted", (UI_FONT, 8), cursor="hand2")
        self.eq_mode_btn.pack(side="right")
        self.eq_mode_btn.bind("<Button-1>", lambda e: self.toggle_eq_mode())

        self.eq = tk.Canvas(eq_box, height=36, highlightthickness=0, bd=0, cursor="hand2")
        self.reg(self.eq, "panel")
        self.eq.pack(fill="x", pady=(2, 0))
        self.eq.bind("<Button-1>", lambda e: self.toggle_eq_mode())

        # ===== right column =====
        right = self.reg(tk.Frame(body, bd=0), "bg")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        # Playlist card
        lcard = self.reg(tk.Frame(right, bd=0), "card")
        lcard.pack(fill="both", expand=True)
        hrow = self.reg(tk.Frame(lcard, bd=0), "panel")
        hrow.pack(fill="x", padx=18, pady=(14, 6))
        self.label(hrow, "Playlist Queue", "ptext", (SERIF, 16, "bold")).pack(side="left")
        self.stats_label = self.label(hrow, "", "pmuted", (UI_FONT, 10))
        self.stats_label.pack(side="right")

        # Search bar
        srow = self.reg(tk.Frame(lcard, bd=0), "panel")
        srow.pack(fill="x", padx=18, pady=(0, 6))
        sf, self.search_entry = self.field(srow, 10)
        sf.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.do_search())
        Pill(srow, self, "Find song", self.do_search, 90, 34, kind="primary").pack(side="left", padx=(8, 0))
        Pill(srow, self, "\u2605 Online music", self.open_online, 126, 34, kind="soft").pack(side="left", padx=(8, 0))

        # Custom Playlist View (doubly circular linked list)
        self.listview = PlaylistView(lcard, self)
        self.listview.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # Playlist actions toolbar
        tool = self.reg(tk.Frame(lcard, bd=0), "panel")
        tool.pack(fill="x", padx=14, pady=(2, 12))
        for text, cmd, w in (("Remove", self.ui_remove, 74), ("Forward", self.playlist.displayForward, 80),
                             ("Backward", self.playlist.displayBackward, 86), ("Demo songs", self.load_test, 98),
                             ("Save", self.save_playlist, 60), ("Load", self.load_playlist, 60),
                             ("Test sound", self.test_sound, 92)):
            Pill(tool, self, text, cmd, w, 30, kind="soft", size=9).pack(side="left", padx=3)

        # Add song input card
        acard = self.reg(tk.Frame(right, bd=0), "card")
        acard.pack(fill="x", pady=(12, 0))
        ai = self.reg(tk.Frame(acard, bd=0), "panel")
        ai.pack(fill="x", padx=18, pady=(12, 12))
        ai.columnconfigure(0, weight=3)
        ai.columnconfigure(2, weight=3)
        self.label(ai, "Title", "pmuted", (UI_FONT, 9)).grid(row=0, column=0, sticky="w")
        self.label(ai, "Seconds", "pmuted", (UI_FONT, 9)).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.label(ai, "Audio file (optional)", "pmuted", (UI_FONT, 9)).grid(row=0, column=2, sticky="w", padx=(8, 0))
        tf, self.title_entry = self.field(ai, 12)
        tf.grid(row=1, column=0, sticky="ew")
        df, self.dur_entry = self.field(ai, 6)
        df.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        ff, self.file_entry = self.field(ai, 12)
        ff.grid(row=1, column=2, sticky="ew", padx=(8, 0))
        Pill(ai, self, "Browse", self.browse, 80, 34, kind="soft").grid(row=1, column=3, padx=(8, 0))
        
        brow = self.reg(tk.Frame(ai, bd=0), "panel")
        brow.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))
        Pill(brow, self, "Add to end", self.ui_add, 110, 36, kind="primary").pack(side="left")
        Pill(brow, self, "Insert after selected", self.ui_insert, 160, 36, kind="soft").pack(side="left", padx=8)
        Pill(brow, self, "Save copy", self.save_copy_selected, 96, 36, kind="soft").pack(side="left")
        self.mode_btn = Pill(brow, self, "Download: Full song", self.toggle_download_mode, 160, 36, kind="soft")
        self.mode_btn.pack(side="left", padx=8)
        self.download_mode.trace_add("write", lambda *a: self.sync_mode_button())

        r.bind("<Configure>", self.on_resize)

    def on_resize(self, e):
        if e.widget == self.root:
            self.status.config(wraplength=max(e.width - 60, 300))

    def bind_keys(self):
        r = self.root

        def typing():
            return isinstance(r.focus_get(), tk.Entry)
        r.bind("<space>", lambda e: None if typing() else self.toggle_play())
        r.bind("<Right>", lambda e: None if typing() else self.next_song_manual())
        r.bind("<Left>", lambda e: None if typing() else self.prev_song())
        r.bind("<Up>", lambda e: None if typing() else self.listview.move(-1))
        r.bind("<Down>", lambda e: None if typing() else self.listview.move(1))
        r.bind("<Delete>", lambda e: None if typing() else self.ui_remove())
        r.bind_all("<MouseWheel>", self.on_wheel)
        r.bind_all("<Button-4>", lambda e: self.on_wheel(e, 1))
        r.bind_all("<Button-5>", lambda e: self.on_wheel(e, -1))

    def on_wheel(self, e, direction=None):
        w = self.root.winfo_containing(e.x_root, e.y_root)
        if w == self.listview:
            if direction is None:
                direction = 1 if e.delta > 0 else -1
            self.listview.scroll_by(-direction * 44)

    # ---------- themes ----------
    def hint_theme(self, name):
        if name is None:
            name = self.theme_name.get()
        self.theme_label.config(text=name + "   \u2022   " + THEMES[name].get("tagline", ""))

    def apply_theme(self, name):
        self.theme_name.set(name)
        t = THEMES[name]
        self.theme = t
        c = derive(t)
        self.c = c
        for w, role in self.themed:
            try:
                if role == "bg":
                    w.configure(bg=c["bg"])
                elif role == "bgtext":
                    w.configure(bg=c["bg"], fg=c["text"])
                elif role == "bgmuted":
                    w.configure(bg=c["bg"], fg=c["muted"])
                elif role == "title":
                    w.configure(bg=c["bg"], fg=c["accent"])
                elif role == "card":
                    w.configure(bg=c["panel"], highlightthickness=1, highlightbackground=c["line"])
                elif role == "panel":
                    w.configure(bg=c["panel"])
                elif role == "ptext":
                    w.configure(bg=c["panel"], fg=c["text"])
                elif role == "pmuted":
                    w.configure(bg=c["panel"], fg=c["muted"])
                elif role == "paccent":
                    w.configure(bg=c["panel"], fg=c["accent"])
                elif role == "field":
                    w.configure(bg=c["panel2"], highlightthickness=1, highlightbackground=c["line"],
                                highlightcolor=c["accent"])
                elif role == "entry_in":
                    w.configure(bg=c["panel2"], fg=c["text"], insertbackground=c["text"],
                                selectbackground=c["accent"], selectforeground=c["btn_text"])
            except tk.TclError:
                pass
        d = t.get("deco", "")
        self.title_label.config(text=(d + "  " if d else "") + "Melody Cafe Music Player" + ("  " + d if d else ""))
        self.hint_theme(None)
        for w in self.customs:
            w.restyle(c)
        self.draw_stripe()
        self.update_toggles()
        self.update_play_icon()
        self.refresh_all()
        self.draw_disc()
        self.draw_eq()

    def draw_stripe(self, event=None):
        cv = self.stripe
        t = self.theme if hasattr(self, "theme") else THEMES["Cafe Brown"]
        c = self.c
        cv.delete("all")
        w = cv.winfo_width()
        if w < 10:
            w = 900
        flag = t.get("flag", False)
        h = 22 if flag else 4
        if int(float(cv.cget("height"))) != h:
            cv.config(height=h)
        cv.config(bg=c["bg"])
        if flag:
            fw, fh = 34, 22
            cv.create_rectangle(0, 0, fw, fh, fill="#ffffff", outline="")
            cv.create_rectangle(9, 0, fw, fh // 3, fill="#00732f", outline="")
            cv.create_rectangle(9, 2 * fh // 3, fw, fh, fill="#111111", outline="")
            cv.create_rectangle(0, 0, 9, fh, fill="#e60012", outline="")
            cv.create_rectangle(0, 0, fw - 1, fh - 1, outline="#b0b0b0")
            segs = ("#e60012", "#00732f", "#111111")
            x = fw + 10
            seg_w = max(w - x, 10) / len(segs)
            for i in range(len(segs)):
                cv.create_rectangle(x + i * seg_w, fh // 2 - 2, x + (i + 1) * seg_w, fh // 2 + 2,
                                    fill=segs[i], outline="")
        else:
            segs = t.get("stripe", (c["accent"],))
            seg_w = w / len(segs)
            for i in range(len(segs)):
                round_rect(cv, i * seg_w, 0, (i + 1) * seg_w, h, 2, fill=segs[i], outline="")

    # ---------- turntable & visualizer ----------
    def draw_disc(self):
        cv = self.disc
        c = self.c
        cv.delete("all")
        W = cv.winfo_width()
        H = cv.winfo_height()
        if W < 50 or H < 50:
            W, H = 220, 216
        cx = 100
        cy = 105
        R = 86

        # 1. Turntable platter base & brushed rim
        Rp = 93
        cv.create_oval(cx - Rp, cy - Rp, cx + Rp, cy + Rp, fill="#1c1c24", outline="#30303c", width=2)
        cv.create_oval(cx - Rp + 2, cy - Rp + 2, cx + Rp - 2, cy + Rp - 2, fill="#15151c", outline="")

        # 2. Outer speed strobe dots
        th = self.spin
        active = self.playing and not self.paused
        dot_count = 20
        for i in range(dot_count):
            ang = math.radians(th + i * (360 / dot_count))
            dx = math.cos(ang) * (Rp - 2)
            dy = math.sin(ang) * (Rp - 2)
            dot_color = c["accent"] if (active and i % 2 == 0) else "#353544"
            cv.create_oval(cx + dx - 1.2, cy + dy - 1.2, cx + dx + 1.2, cy + dy + 1.2, fill=dot_color, outline="")

        # 3. Vinyl record disc surface
        cv.create_oval(cx - R, cy - R, cx + R, cy + R, fill="#111116", outline="#252530", width=1.5)

        # 4. Realistic concentric micro-grooves
        groove_radii = (0.50, 0.56, 0.62, 0.68, 0.74, 0.80, 0.86, 0.92)
        for gr in groove_radii:
            rr = R * gr
            cv.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline="#1c1c24", width=1)

        # 5. Glossy rotating specular light reflections (sheen arcs)
        for off in (0, 90, 180, 270):
            w_arc = 3 if off in (0, 180) else 2
            col = "#545464" if off in (0, 180) else "#363644"
            extent = 32 if off in (0, 180) else 22
            rr = R * 0.82
            cv.create_arc(cx - rr, cy - rr, cx + rr, cy + rr, start=th + off, extent=extent,
                          style="arc", outline=col, width=w_arc)
            rr2 = R * 0.64
            cv.create_arc(cx - rr2, cy - rr2, cx + rr2, cy + rr2, start=th + off + 30, extent=extent - 6,
                          style="arc", outline=col, width=w_arc)

        # 6. Center label
        L = R * 0.38
        if self.theme.get("flag", False):
            cols = ("#e60012", "#00732f", "#ffffff", "#111111")
            for i in range(4):
                cv.create_arc(cx - L, cy - L, cx + L, cy + L, start=th + 90 * i, extent=90,
                              fill=cols[i], outline="")
        else:
            cv.create_oval(cx - L, cy - L, cx + L, cy + L, fill=c["accent"],
                           outline=c.get("highlight", c["accent"]), width=1)
            l2 = L * 0.62
            cv.create_oval(cx - l2, cy - l2, cx + l2, cy + l2, fill=mix(c["accent"], "#ffffff", 0.35), outline="")
            deco = self.theme.get("deco", "\u266a")
            cv.create_text(cx, cy, text=deco, fill=c["btn_text"], font=(UI_FONT, 10, "bold"))

        # Center spindle hole with silver metallic bevel
        cv.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#d6d6d6", outline="#3b3b44", width=1.5)
        cv.create_oval(cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5, fill="#111116", outline="")

        # 7. Animated Tonearm
        px, py = 188, 30    # pivot coordinates
        rest_x, rest_y = 190, 140

        if active and self.current is not None:
            elapsed = max(0.0, time.time() - self.start_time)
            dur = max(self.play_limit(), 1.0)
            ratio = min(1.0, max(0.0, elapsed / dur))
            nr = R * (0.88 - 0.44 * ratio)
            ang = math.radians(18 + 12 * ratio)
            target_x = cx + nr * math.cos(ang)
            target_y = cy + nr * math.sin(ang)
        else:
            target_x, target_y = rest_x, rest_y

        self.arm_x = self.arm_x * 0.82 + target_x * 0.18
        self.arm_y = self.arm_y * 0.82 + target_y * 0.18

        # Tonearm rest bracket
        cv.create_rectangle(187, 134, 193, 148, fill="#282834", outline="")
        cv.create_rectangle(184, 134, 196, 137, fill="#4c4c5c", outline="")

        # Tonearm pivot base
        cv.create_oval(px - 10, py - 10, px + 10, py + 10, fill="#252530", outline="#404050", width=1.5)
        cv.create_oval(px - 5, py - 5, px + 5, py + 5, fill="#cfd2dc", outline="")
        cv.create_rectangle(px + 4, py - 12, px + 12, py + 2, fill="#191922", outline="#484856")

        # Tonearm rod / tube
        cv.create_line(px, py, self.arm_x, self.arm_y, fill="#d2d5de", width=2.5, capstyle="round")

        # Headshell / cartridge
        hx, hy = self.arm_x, self.arm_y
        arm_angle = math.atan2(hy - py, hx - px)
        c_len = 10
        c_dx = math.cos(arm_angle + 0.3) * c_len
        c_dy = math.sin(arm_angle + 0.3) * c_len
        cv.create_line(hx, hy, hx + c_dx, hy + c_dy, fill="#1c1c24", width=5, capstyle="round")
        tip_col = c["accent"] if active else "#909090"
        cv.create_oval(hx + c_dx - 1.5, hy + c_dy - 1.5, hx + c_dx + 1.5, hy + c_dy + 1.5,
                       fill=tip_col, outline="")

    def toggle_eq_mode(self):
        self.eq_mode = "wave" if self.eq_mode == "bars" else "bars"
        self.eq_mode_btn.config(text="[mode: Waveform]" if self.eq_mode == "wave" else "[mode: Equalizer]")
        self.draw_eq()
        self.write_log("Visualizer switched to " + ("Liquid Waveform" if self.eq_mode == "wave" else "Studio Equalizer") + ".")

    def draw_eq(self):
        cv = self.eq
        c = self.c
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 40 or h < 10:
            return

        active = self.playing and not self.paused

        if self.eq_mode == "wave":
            # Liquid Waveform mode
            cy = h / 2
            cv.create_line(6, cy, w - 6, cy, fill=c["line"], dash=(2, 4))
            pts1, pts2 = [], []
            step = max(3, int(w / 60))
            amp = (h / 2 - 3) if active else 3
            for x in range(6, int(w) - 6, step):
                freq1, freq2 = 0.04, 0.07
                t = self.frame * 0.15
                if active:
                    y1 = cy + math.sin(x * freq1 + t) * amp * 0.8 + math.sin(x * freq2 - t * 0.7) * (amp * 0.3)
                    y2 = cy + math.cos(x * freq2 - t * 0.5) * amp * 0.6
                else:
                    y1 = cy + math.sin(x * 0.05) * 2
                    y2 = cy + math.cos(x * 0.08) * 1.5
                pts1.extend([x, y1])
                pts2.extend([x, y2])
            
            if len(pts2) >= 4:
                cv.create_line(pts2, fill=c.get("accent_soft", c["panel2"]), width=2, smooth=True)
            if len(pts1) >= 4:
                cv.create_line(pts1, fill=c["accent"], width=2.5, smooth=True)
                for j in range(0, len(pts1), 16):
                    cv.create_oval(pts1[j] - 2, pts1[j + 1] - 2, pts1[j] + 2, pts1[j + 1] + 2,
                                   fill=c.get("highlight", c["accent"]), outline="")
        else:
            # Studio Equalizer Bars mode with falling peak caps
            gap = 3
            bw = (w - gap * (self.BARS - 1)) / self.BARS
            cols = self.theme.get("bars", self.theme.get("stripe", (c["accent"],)))

            for i in range(self.BARS):
                if active:
                    curve = 1.0 - 0.35 * (i / self.BARS) + 0.25 * math.sin(i * 0.5 + self.frame * 0.2)
                    target = random.uniform(6, (h - 4) * max(0.2, min(1.0, curve)))
                    self.eq_heights[i] = self.eq_heights[i] * 0.60 + target * 0.40
                    self.eq_peaks[i] = max(self.eq_heights[i], self.eq_peaks[i] - 1.1)
                else:
                    idle = 4 + (i % 4) * 2
                    self.eq_heights[i] = self.eq_heights[i] * 0.85 + idle * 0.15
                    self.eq_peaks[i] = max(self.eq_heights[i], self.eq_peaks[i] - 0.5)

                bar = max(3, int(self.eq_heights[i]))
                peak = max(bar, int(self.eq_peaks[i]))
                colour = cols[i % len(cols)]
                if colour.lower() == "#ffffff":
                    colour = c["accent"]
                
                x0 = i * (bw + gap)
                round_rect(cv, x0, h - bar, x0 + bw, h, 2, fill=colour, outline="")
                if active and peak > bar + 2:
                    cap_y = max(1, h - peak)
                    round_rect(cv, x0, cap_y, x0 + bw, cap_y + 2, 1, fill=c.get("highlight", c["accent"]), outline="")

    # ---------- toggles ----------
    def update_toggles(self):
        self.shuffle_btn.set_active(self.shuffle)
        self.repeat_btn.set_active(self.repeat_one)
        self.demo_btn.set_active(self.demo_mode)
        if hasattr(self, "mode_tag"):
            self.mode_tag.config(text="QUICK DEMO (10s)" if self.demo_mode else "FULL AUDIO")

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.update_toggles()
        self.refresh_next_label()

    def toggle_repeat(self):
        self.repeat_one = not self.repeat_one
        self.update_toggles()
        self.refresh_next_label()

    def toggle_demo(self):
        self.demo_mode = not self.demo_mode
        self.update_toggles()
        if self.demo_mode:
            self.write_log("Quick demo enabled: each song plays for 10 seconds.")
        else:
            self.write_log("Full length play enabled: songs play their complete duration.")

    # ---------- display helpers ----------
    def write_log(self, msg):
        self.status.config(text=msg)

    def refresh_all(self):
        self.listview.clamp_selection()
        self.listview.draw()
        n = self.playlist.count()
        self.stats_label.config(text=str(n) + (" song" if n == 1 else " songs") + "   \u2022   total "
                                + fmt(self.playlist.totalDuration()))
        self.refresh_next_label()

    def refresh_list(self):
        self.listview.draw()

    def refresh_next_label(self):
        if self.current is None or self.playlist.head is None:
            self.next_label.config(text="Add songs and press play")
            return
        if self.repeat_one:
            text = "Repeating this song"
        elif self.shuffle:
            text = "Up next: a random song"
        else:
            text = "Up next: " + self.playlist.playNext(self.current).title
        self.next_label.config(text=text)

    def selected_node(self):
        i = self.listview.sel
        if i < 0 or i >= self.playlist.count():
            return None
        return self.playlist.nodeAt(i)

    def on_select(self):
        pass

    def do_search(self):
        text = self.search_entry.get().strip()
        if text == "":
            return
        idx = self.playlist.search(text)
        if idx < 0:
            self.write_log("No song matching '" + text + "' was found.")
            return
        self.listview.sel = idx
        self.listview.see(idx)
        self.write_log("Found '" + self.playlist.nodeAt(idx).title + "' at position " + str(idx + 1) + ".")

    # ---------- inputs ----------
    def read_inputs(self):
        title = self.title_entry.get().strip()
        path = self.file_entry.get().strip() or None
        dur_text = self.dur_entry.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please enter a song title.")
            return None
        if dur_text == "" and path:
            secs = file_length_seconds(path)
            if secs:
                dur_text = str(secs)
        if not dur_text.isdigit() or int(dur_text) <= 0:
            messagebox.showwarning("Invalid duration",
                                   "Type the duration as a whole number of seconds "
                                   "(it could not be read from the file).")
            return None
        return title, int(dur_text), path

    def clear_inputs(self):
        self.title_entry.delete(0, "end")
        self.dur_entry.delete(0, "end")
        self.file_entry.delete(0, "end")

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("All files", "*.*")])
        if path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            if self.title_entry.get().strip() == "":
                self.title_entry.insert(0, os.path.splitext(os.path.basename(path))[0][:30])
            if self.dur_entry.get().strip() == "":
                secs = file_length_seconds(path)
                if secs:
                    self.dur_entry.insert(0, str(secs))
                else:
                    self.write_log("Could not read the length of that file. Please type the duration in seconds.")

    # ---------- playlist actions ----------
    def ui_add(self):
        data = self.read_inputs()
        if data:
            self.playlist.addSong(*data)
            self.clear_inputs()
            self.refresh_all()
            self.listview.see(self.playlist.count() - 1)
            self.write_log("Added '" + data[0][:30] + "' at the end of the playlist.")

    def ui_insert(self):
        key = self.selected_node()
        if key is None:
            messagebox.showinfo("Select a song", "Click a song in the playlist first, then insert after it.")
            return
        data = self.read_inputs()
        if data:
            self.playlist.insertAfter(key.title, *data)
            self.clear_inputs()
            self.refresh_all()
            self.write_log("Inserted '" + data[0][:30] + "' after '" + key.title + "'.")

    def ui_remove(self):
        node = self.selected_node()
        if node is None:
            return
        title = node.title
        was_current = (node == self.current)
        was_playing = self.playing
        replacement = None
        if was_current and node.next != node:
            replacement = node.next
        self.playlist.removeSong(title)
        if was_current:
            self.stop()
            self.current = replacement
            if replacement is not None and was_playing:
                self.start_song(replacement)
        self.refresh_all()
        self.write_log("Removed '" + title + "'.")

    def open_online(self):
        """Open the online search window (only one at a time)."""
        win = getattr(self, "online_win", None)
        if win is not None and win.alive:
            win.win.lift()
            return
        self.online_win = OnlineWindow(self)

    def add_online_song(self, track, path, seconds=PREVIEW_SECONDS):
        """Called with a downloaded song: add it to the end of the linked list."""
        title = (track["title"] + " - " + track["artist"])[:30]
        self.playlist.addSong(title, int(seconds), path)
        self.refresh_all()
        self.listview.see(self.playlist.count() - 1)
        kind = "full song" if track.get("full") and seconds > 30 else str(int(seconds)) + " second clip"
        self.write_log("Added '" + title + "' from online music (" + kind + ").")

    # ---------- download / save a copy ----------
    def sync_mode_button(self):
        full = self.download_mode.get() == "full"
        self.mode_btn.set_text("Download: Full song" if full else "Download: 10 sec")

    def toggle_download_mode(self):
        self.download_mode.set("10s" if self.download_mode.get() == "full" else "full")

    def save_copy_selected(self):
        node = self.selected_node()
        if node is None:
            messagebox.showinfo("Select a song", "Click a song in the playlist first, then press Save copy.")
            return
        start = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = filedialog.askdirectory(initialdir=start, title="Save a copy of '" + node.title + "' into")
        if not folder:
            return
        mode = self.download_mode.get()
        try:
            if node.audio_file and os.path.exists(node.audio_file):
                src = node.audio_file
            else:
                src = make_melody_file(node.title, node.duration)
            dst = export_song(src, node.title, mode, folder)
            self.write_log(("Saved full song to " if mode == "full" else "Saved 10 second clip to ") + dst)
        except ClipError as e:
            self.write_log("Could not save: " + str(e))
            messagebox.showwarning("Could not save", str(e))

    def load_test(self):
        p = self.playlist
        p.addSong("Sunrise", 210)
        p.addSong("Desert Rain", 185)
        p.addSong("Marina Lights", 240)
        p.insertAfter("Sunrise", "Skyline", 200)
        p.insertAfter("Marina Lights", "Night Drive", 195)
        self.refresh_all()
        self.write_log("Demo songs added.")

    def save_playlist(self):
        if self.playlist.head is None:
            self.write_log("Nothing to save: the playlist is empty.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="melody_playlist.txt",
                                            filetypes=[("Text file", "*.txt")])
        if not path:
            return
        f = open(path, "w", encoding="utf-8")
        cur = self.playlist.head
        while True:
            f.write(cur.title + "|" + str(cur.duration) + "|" + (cur.audio_file or "") + "\n")
            cur = cur.next
            if cur == self.playlist.head:
                break
        f.close()
        self.write_log("Playlist saved to " + path)

    def load_playlist(self):
        path = filedialog.askopenfilename(filetypes=[("Text file", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        added = 0
        f = open(path, "r", encoding="utf-8")
        for line in f:
            line = line.rstrip("\n")
            if line.count("|") < 2:
                continue
            title, dur, audio = line.rsplit("|", 2)
            if dur.isdigit():
                self.playlist.addSong(title, int(dur), audio or None)
                added += 1
        f.close()
        self.refresh_all()
        self.write_log("Loaded " + str(added) + " songs from " + path)

    def test_sound(self):
        if not AUDIO_OK:
            messagebox.showerror("No audio", "Audio is off. Run: python -m pip install pygame\n" + PYGAME_ERROR)
            return
        try:
            how = self.audio.play(make_melody_file("SoundTest", 4))
            self.write_log("Test melody started using " + how + ". If silent, check volume / output device.")
        except Exception as e:
            self.write_log("Test sound failed: " + str(e))

    # ---------- playback ----------
    def on_seek(self, percent):
        if self.current is not None:
            limit = self.play_limit()
            target = (percent / 100.0) * limit
            self.start_time = time.time() - target
            self.elapsed_label.config(text=fmt(target))
            self.audio.seek(target)

    def on_volume(self, value):
        self.volume = value
        self.vol_label.config(text=str(int(value)) + "%")
        self.sync_vol_icon()
        supported = self.audio.set_volume(value / 100.0)
        if not supported and self.audio.using == "native" and not self.volume_warned:
            self.volume_warned = True
            self.write_log("This sound player cannot change volume here. Use your system volume.")

    def sync_vol_icon(self):
        if hasattr(self, "vol_icon_btn"):
            if self.volume <= 0 or self.is_muted:
                self.vol_icon_btn.config(text="\U0001f507")
            elif self.volume < 33:
                self.vol_icon_btn.config(text="\U0001f508")
            elif self.volume < 67:
                self.vol_icon_btn.config(text="\U0001f509")
            else:
                self.vol_icon_btn.config(text="\U0001f50a")

    def toggle_mute(self):
        if not self.is_muted:
            self.pre_mute_vol = self.volume
            self.is_muted = True
            self.vol_slider.set(0.0)
            self.on_volume(0.0)
        else:
            self.is_muted = False
            restored = self.pre_mute_vol if self.pre_mute_vol > 5 else 80.0
            self.vol_slider.set(restored)
            self.on_volume(restored)

    def play_limit(self):
        if self.current is None:
            return 1
        if self.demo_mode:
            return min(self.DEMO_SECONDS, self.current.duration)
        return self.current.duration

    def update_play_icon(self):
        is_playing = (self.playing and not self.paused)
        self.play_btn.set_icon("pause" if is_playing else "play")
        if hasattr(self, "status_pill"):
            if is_playing:
                self.status_pill.config(text=" \u25cf PLAYING ", fg=self.c.get("success", self.c["accent"]))
            elif self.paused:
                self.status_pill.config(text=" \u23f8 PAUSED ", fg=self.c.get("warning", self.c["accent"]))
            else:
                self.status_pill.config(text=" \u25a0 IDLE ", fg=self.c["muted"])

    def start_song(self, node):
        self.current = node
        self.playing = True
        self.paused = False
        self.start_time = time.time()
        if AUDIO_OK:
            try:
                if node.audio_file and os.path.exists(node.audio_file):
                    path = node.audio_file
                else:
                    path = make_melody_file(node.title, self.play_limit() + 2)
                self.audio.volume = self.volume / 100.0
                self.audio.play(path)
            except Exception as e:
                self.write_log("Could not play '" + node.title + "': " + str(e))
        self.now_label.config(text=node.title)
        self.total_label.config(text=fmt(self.play_limit()))
        self.update_play_icon()
        self.refresh_all()

    def toggle_play(self):
        if self.playlist.head is None:
            return
        if not self.playing:
            self.start_song(self.selected_node() or self.current or self.playlist.head)
        elif self.paused:
            self.paused = False
            self.start_time += time.time() - self.pause_time
            if AUDIO_OK:
                self.audio.resume()
        else:
            self.paused = True
            self.pause_time = time.time()
            if AUDIO_OK:
                self.audio.pause()
        self.update_play_icon()

    def play_selected(self, event=None):
        node = self.selected_node()
        if node:
            self.start_song(node)

    def choose_next(self):
        if self.shuffle:
            return self.playlist.randomOther(self.current)
        return self.playlist.playNext(self.current)

    def next_song_manual(self):
        if self.playlist.head is None:
            return
        self.start_song(self.choose_next())

    def prev_song(self):
        if self.playlist.head is None:
            return
        base = self.current if self.current else self.playlist.head
        self.start_song(base.prev)

    def stop(self):
        self.playing = False
        self.paused = False
        self.audio.stop()
        self.now_label.config(text="Nothing playing" if self.current is None else self.current.title)
        self.progress.set(0)
        self.elapsed_label.config(text="0:00")
        self.update_play_icon()

    def tick(self):
        if self.playing and not self.paused and self.current is not None:
            elapsed = time.time() - self.start_time
            limit = self.play_limit()
            self.progress.set(100.0 * elapsed / limit)
            self.elapsed_label.config(text=fmt(elapsed))
            self.total_label.config(text=fmt(limit))
            if elapsed >= limit:
                if self.repeat_one:
                    self.start_song(self.current)
                else:
                    self.start_song(self.choose_next())
        self.root.after(250, self.tick)

    def animate(self):
        """Spinning turntable, tonearm tracking, and dancing visualizer bars."""
        self.frame += 1
        if self.playing and not self.paused:
            self.spin = (self.spin + 4) % 360
        self.draw_disc()
        self.draw_eq()
        self.root.after(45, self.animate)

    def close(self):
        self.audio.stop()
        self.root.destroy()
