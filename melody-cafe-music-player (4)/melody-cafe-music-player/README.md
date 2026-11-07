# 🎵 Melody Cafe Music Player

A desktop music player in Python (tkinter) built on a **hand-made doubly circular linked list**. No arrays or Python lists hold the songs.

**Author:** Ancilla Danica Dsouza  |  **PRN:** 25070721021

## Features
- Doubly circular linked list: `addSong`, `insertAfter`, `removeSong`, `displayForward`, `displayBackward`, `playNext`
- Play / pause / stop / next / previous, shuffle, repeat-one, interactive progress scrubbing & volume with mute toggle
- **Realistic Turntable**: spinning vinyl microgrooves, rotating glossy specular light reflections, speed strobe dots, and smooth animated tonearm tracking across the record
- **Dual Visualizer**: Physics-based Studio Equalizer with floating falling peak caps OR Liquid Waveform mode (click visualizer to toggle)
- Search, save and load playlists with live dancing mini-equalizer queue indicators
- **Online Music Hub**: Free **full songs** from YouTube (via `yt-dlp`), Creative Commons songs from Jamendo, or 30-second previews from Deezer / iTunes
- **Download as Full song (default) or 10 second clip**, online or offline: `Save copy` button + Online window (see `docs/ONLINE.md`)
- Plays real mp3 / m4a / wav files, or makes a melody from the song title
- **19 stunning themes** (including Cyberpunk Neon, Dark Espresso, Nordic Frost, Emerald Velvet, Sunset Boulevard, plus 6 UAE-inspired themes)

## Project structure
```
melody-cafe-music-player/
├── main.py                  start here
├── run.bat / run.sh         double-click launchers
├── run_tests.bat / .sh      run the unit tests
├── requirements.txt         optional pygame
├── pyproject.toml
├── melody_cafe/             the app package
│   ├── core/                Song + Playlist (the linked list)
│   ├── audio/               backends, player, melody generator, clip/save copy
│   ├── ui/                  themes, colours, widgets, main window
│   ├── utils.py
│   └── cli.py               --test / --sound-test / open GUI
├── tests/                   unit tests
├── data/sample_playlist.txt a playlist you can load with the Load button
├── docs/                    ARCHITECTURE, THEMES, CHANGELOG, screenshots/
├── assets/                  put icons / sample audio here
├── scripts/                 setup.bat / setup.sh (virtual environment)
├── .github/workflows/       automatic tests on GitHub
├── LICENSE
└── .gitignore
```

## Run locally

Needs Python 3.8+. tkinter is included with Python on Windows and macOS (Linux: `sudo apt install python3-tk`).

```bash
# 1. open a terminal inside the project folder
cd melody-cafe-music-player

# 2. start the app
python main.py            # Windows
python3 main.py           # Mac / Linux
```

Or just double-click `run.bat` (Windows) or run `./run.sh` (Mac/Linux).

### Optional: virtual environment + pygame
```bash
scripts\setup.bat         # Windows
./scripts/setup.sh        # Mac / Linux
```
Then use `run.bat` / `run.sh` as normal; they pick up `.venv` automatically.

### Other commands
```bash
python main.py --test          # console test of the linked list (Part C)
python main.py --sound-test    # check that audio works
python main.py --online-test "daft punk"   # check the online music connection
python -m melody_cafe          # same as main.py
python -m unittest discover -v # run all unit tests
```

## Using the app
1. Press **Demo songs**, or press **Load** and pick `data/sample_playlist.txt`.
2. Double-click a song to play it. **Quick demo** limits each song to 10 seconds; turn it off to play full length.
3. Click **Online music**, search a song or artist, and add results to your playlist (needs internet; see `docs/ONLINE.md`).
4. Click a coloured dot at the top right to change theme.

Keys: `Space` play/pause, `←` `→` previous/next, `↑` `↓` select, `Delete` remove.

## Push to GitHub
```bash
git init
git add .
git commit -m "Melody Cafe Music Player"
git branch -M main
git remote add origin https://github.com/<your-username>/melody-cafe-music-player.git
git push -u origin main
```

See `docs/ARCHITECTURE.md` for how the code is organised.
