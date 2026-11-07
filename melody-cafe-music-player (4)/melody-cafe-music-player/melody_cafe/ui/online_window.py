# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""The 'Online music' window: search YouTube for full-length songs,
Jamendo for free Creative Commons full songs, or Deezer/iTunes for 30s previews."""

import os
import queue
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog

from ..online import (search_sources, download_track, jamendo, youtube, OnlineError)
from ..audio.clip import safe_name, unique_path
from ..utils import fmt
from .colors import UI_FONT, SERIF, mix, round_rect


class OnlineWindow:
    def __init__(self, app):
        self.app = app
        self.c = app.c
        self.tracks = []
        self.q = queue.Queue()
        self.alive = True
        c = self.c

        self.win = tk.Toplevel(app.root)
        self.win.title("Online Music Hub - Full Songs & Previews")
        self.win.geometry("740x660")
        self.win.minsize(640, 580)
        self.win.configure(bg=c["bg"])
        self.win.transient(app.root)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

        # Header
        head = tk.Frame(self.win, bg=c["bg"])
        head.pack(fill="x", padx=22, pady=(16, 6))
        tk.Label(head, text="\u266a  Online Music Hub", font=(SERIF, 18, "bold"),
                 bg=c["bg"], fg=c["accent"]).pack(anchor="w")
        tk.Label(head, text="Search YouTube for full songs (no 30s limit), Jamendo CC music, or Deezer/iTunes previews.",
                 font=(UI_FONT, 9), bg=c["bg"], fg=c["muted"]).pack(anchor="w", pady=(2, 0))

        # Search box row
        srow = tk.Frame(self.win, bg=c["bg"])
        srow.pack(fill="x", padx=22, pady=(8, 4))
        
        entry_wrap = tk.Frame(srow, bg=c["panel2"], highlightthickness=1,
                              highlightbackground=c["line"], highlightcolor=c["accent"])
        entry_wrap.pack(side="left", fill="x", expand=True)
        
        tk.Label(entry_wrap, text=" \U0001f50d ", font=(UI_FONT, 11), bg=c["panel2"],
                 fg=c["muted"]).pack(side="left", padx=(6, 2))
        self.entry = tk.Entry(entry_wrap, font=(UI_FONT, 11), bg=c["panel2"], fg=c["text"],
                              insertbackground=c["text"], relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.do_search())
        
        self.search_btn = self.button(srow, "  Search  ", self.do_search, primary=True)
        self.search_btn.pack(side="left", padx=(10, 0))

        # Filter options
        opts = tk.Frame(self.win, bg=c["panel2"], highlightthickness=1, highlightbackground=c["line"])
        opts.pack(fill="x", padx=22, pady=(8, 10), ipady=4)
        
        # Source options
        top_opts = tk.Frame(opts, bg=c["panel2"])
        top_opts.pack(fill="x", padx=12, pady=(4, 2))
        tk.Label(top_opts, text="Source:", font=(UI_FONT, 9, "bold"), bg=c["panel2"], fg=c["accent"]).pack(side="left")
        
        default_source = "youtube" if youtube.is_available() else "full"
        self.source = tk.StringVar(value=default_source)
        
        if youtube.is_available():
            self.radio(top_opts, "\u2605 YouTube (Full songs)", self.source, "youtube").pack(side="left", padx=(10, 0))
        self.radio(top_opts, "\u266c Jamendo (Full CC)", self.source, "jamendo").pack(side="left", padx=(10, 0))
        self.radio(top_opts, "\u26a1 Deezer/iTunes (30s previews)", self.source, "preview").pack(side="left", padx=(10, 0))

        # Download format options
        bot_opts = tk.Frame(opts, bg=c["panel2"])
        bot_opts.pack(fill="x", padx=12, pady=(2, 4))
        tk.Label(bot_opts, text="Download mode:", font=(UI_FONT, 9, "bold"), bg=c["panel2"], fg=c["muted"]).pack(side="left")
        self.radio(bot_opts, "Full song (Default)", app.download_mode, "full").pack(side="left", padx=(10, 0))
        self.radio(bot_opts, "10 second clip", app.download_mode, "10s").pack(side="left", padx=(10, 0))

        # Results box with custom scrollbar
        box = tk.Frame(self.win, bg=c["line"], bd=0)
        box.pack(fill="both", expand=True, padx=22, pady=(0, 10))
        sb = tk.Scrollbar(box)
        sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(box, font=(UI_FONT, 10), bg=c["panel"], fg=c["text"],
                                  selectbackground=c["accent"], selectforeground=c["btn_text"],
                                  activestyle="none", relief="flat", bd=0, highlightthickness=0,
                                  selectmode="extended", yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", lambda e: self.add_selected())

        # Action Buttons bar
        bar = tk.Frame(self.win, bg=c["bg"])
        bar.pack(fill="x", padx=22, pady=(0, 6))
        self.button(bar, "+ Add to playlist", self.add_selected, primary=True).pack(side="left")
        self.button(bar, "\u2b07 Download to folder...", self.download_selected).pack(side="left", padx=8)
        self.button(bar, "\u25b6 Preview audio", self.preview_selected).pack(side="left", padx=2)
        if not jamendo.get_key():
            self.button(bar, "\U0001f511 Jamendo key", self.set_key).pack(side="left", padx=6)
        self.button(bar, "Close", self.close).pack(side="right")

        # Status Line
        self.status = tk.Label(self.win, text="Ready. Type an artist or song name and press Search.",
                               font=(UI_FONT, 9), bg=c["bg"], fg=c["muted"], anchor="w", justify="left",
                               wraplength=680)
        self.status.pack(fill="x", padx=22, pady=(2, 12))

        if youtube.is_available():
            self.set_status("\u2728 YouTube is active: search any song to get the complete FULL-LENGTH audio with no 30s limit!")
        elif not jamendo.get_key():
            self.set_status("Tip: for full songs, use YouTube (via yt-dlp) or set a Jamendo key. Otherwise Deezer/iTunes give 30s previews.")
        
        self.entry.focus_set()
        self.poll()

    # ----- widget helpers -----
    def button(self, parent, text, command, primary=False):
        c = self.c
        bg, fg = (c["button"], c["btn_text"]) if primary else (c["panel2"], c["text"])
        btn = tk.Button(parent, text=text, command=command, font=(UI_FONT, 9, "bold"),
                        bg=bg, fg=fg, activebackground=c["accent"], activeforeground=c["btn_text"],
                        relief="flat", bd=0, padx=12, pady=6, cursor="hand2")
        return btn

    def radio(self, parent, text, var, value):
        c = self.c
        return tk.Radiobutton(parent, text=text, variable=var, value=value, font=(UI_FONT, 9),
                              bg=c["panel2"], fg=c["text"], selectcolor=c["panel"],
                              activebackground=c["panel2"], activeforeground=c["accent"],
                              highlightthickness=0, bd=0, cursor="hand2")

    def set_status(self, text):
        self.status.config(text=text)

    # ----- search -----
    def do_search(self):
        text = self.entry.get().strip()
        if not text:
            return
        src = self.source.get()
        source_label = "YouTube" if src == "youtube" else ("Jamendo" if src == "jamendo" else "Previews")
        self.set_status(f"Searching {source_label} for '{text}' ...")
        threading.Thread(target=self.search_worker, args=(text, src), daemon=True).start()

    def search_worker(self, text, src):
        try:
            if src == "youtube" and youtube.is_available():
                tracks = youtube.search(text, limit=20)
                notice = "YouTube full-length songs. "
            elif src == "jamendo":
                tracks = jamendo.search(text, limit=25)
                notice = "Jamendo free full songs. "
            elif src == "preview":
                from ..online import deezer
                tracks = deezer.search_any(text, limit=25)
                notice = "30-second previews from Deezer/iTunes. "
            else:
                tracks, notice = search_sources(text, prefer_full=True)
            self.q.put(("results", text, tracks, notice))
        except OnlineError as e:
            self.q.put(("error", str(e)))
        except Exception as e:
            self.q.put(("error", "Search failed: " + str(e)))

    def show_results(self, text, tracks, notice):
        self.tracks = tracks
        self.listbox.delete(0, "end")
        for t in tracks:
            is_full = t.get("full", False)
            dur = t.get("duration", 0)
            tag = f"[FULL \u2022 {fmt(dur)}]" if is_full else f"[30s PREVIEW \u2022 {fmt(30)}]"
            source_tag = t.get("source", "").upper()
            line = f"  {t['title']}  \u2014  {t['artist']}   {tag}   ({source_tag})"
            self.listbox.insert("end", line)
        if tracks:
            self.set_status(notice + str(len(tracks)) + " results found for '" + text
                            + "'. Double-click or select to add to playlist or download.")
        else:
            self.set_status(notice + "No playable results for '" + text + "'. Try another query or source.")

    def picks(self):
        chosen = [self.tracks[i] for i in self.listbox.curselection()]
        if not chosen:
            self.set_status("Click one or more songs in the list first.")
        return chosen

    # ----- preview audio -----
    def preview_selected(self):
        chosen = self.picks()
        if not chosen:
            return
        track = chosen[0]
        self.set_status(f"Buffering preview for '{track['title']}' ...")
        def play_worker():
            try:
                path, secs = download_track(track, mode="full")
                self.q.put(("play_preview", track, path))
            except Exception as e:
                self.q.put(("error", f"Could not preview audio: {e}"))
        threading.Thread(target=play_worker, daemon=True).start()

    # ----- add to playlist -----
    def add_selected(self):
        chosen = self.picks()
        if not chosen:
            return
        mode = self.app.download_mode.get()
        self.set_status("Downloading " + str(len(chosen)) + " song(s) ("
                        + ("full song" if mode == "full" else "10 second clip") + ") ...")
        threading.Thread(target=self.fetch_worker, args=(chosen, mode, None), daemon=True).start()

    # ----- download to a folder -----
    def download_selected(self):
        chosen = self.picks()
        if not chosen:
            return
        start = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        folder = filedialog.askdirectory(parent=self.win, initialdir=start, title="Save songs into folder")
        if not folder:
            return
        mode = self.app.download_mode.get()
        self.set_status("Downloading " + str(len(chosen)) + " song(s) to " + folder + " ...")
        threading.Thread(target=self.fetch_worker, args=(chosen, mode, folder), daemon=True).start()

    def fetch_worker(self, chosen, mode, folder):
        for t in chosen:
            try:
                path, seconds = download_track(t, mode)
                if folder:
                    ext = os.path.splitext(path)[1]
                    base = safe_name(t["artist"] + " - " + t["title"]) + (" (10 sec)" if mode == "10s" else "")
                    dst = unique_path(folder, base, ext)
                    shutil.copy2(path, dst)
                    self.q.put(("saved", t, dst))
                else:
                    self.q.put(("added", t, path, seconds))
            except Exception as e:
                self.q.put(("fail", t, str(e)))

    # ----- Jamendo key -----
    def set_key(self):
        key = simpledialog.askstring(
            "Jamendo key",
            "Paste your free Jamendo Client ID.\n(Get one at https://devportal.jamendo.com)",
            parent=self.win)
        if key and key.strip():
            jamendo.save_key(key.strip())
            self.set_status("Jamendo key saved. You can now search Jamendo for full songs.")

    # ----- poll queue -----
    def poll(self):
        if not self.alive:
            return
        try:
            while True:
                msg = self.q.get_nowait()
                kind = msg[0]
                if kind == "results":
                    self.show_results(msg[1], msg[2], msg[3])
                elif kind == "error":
                    self.set_status(msg[1])
                elif kind == "play_preview":
                    track, path = msg[1], msg[2]
                    self.app.audio.play(path)
                    self.set_status(f"\u25b6 Now playing preview: '{track['title']}' by {track['artist']}.")
                elif kind == "added":
                    self.app.add_online_song(msg[1], msg[2], msg[3])
                    is_full = msg[1].get("full") and msg[3] > 30
                    full_str = "Full song" if is_full else fmt(msg[3])
                    self.set_status(f"\u2714 Added '{msg[1]['title']}' to your playlist ({full_str})!")
                elif kind == "saved":
                    self.set_status("\u2714 Saved to folder: " + msg[2])
                elif kind == "fail":
                    self.set_status("Could not get '" + msg[1]["title"] + "': " + msg[2])
        except queue.Empty:
            pass
        self.win.after(100, self.poll)

    def close(self):
        self.alive = False
        self.win.destroy()
