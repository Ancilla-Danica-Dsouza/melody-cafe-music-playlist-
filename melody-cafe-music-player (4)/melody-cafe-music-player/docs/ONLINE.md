# Online music, downloads and saving copies

## Accessing Full Songs Online (No 30-Second Limit)

| Source | Audio Length | API Key Needed? | Description |
|---|---|---|---|
| **YouTube** (`yt-dlp`) | **Full length** (Complete songs) | **No key needed** | Search ANY song or artist on YouTube to download and play the full-length audio. |
| **Jamendo** | **Full length** | Free key | Creative Commons music from independent artists. |
| **Deezer** | 30 second preview | None | Official 30-second commercial clips. |
| **iTunes** | 30 second preview | None | Official 30-second commercial clips. |

> [!NOTE]
> **Why were songs previously 30 seconds?**
> Commercial music APIs like Deezer and Apple iTunes only provide 30-second sample previews (`preview.mp3`). With the newly integrated **YouTube (`yt-dlp`)** engine, you can search and download full songs of any length! In the Online Music window, ensure **"★ YouTube (Full songs)"** is selected.

### Download options: Full song (default) or 10 seconds
The mode is shown on the **Download: Full song / Download: 10 sec** button (under the song form) and as **Download: Full / 10 sec** choices inside the Online music window. **Full** is the default.

| Where | What it does |
|---|---|
| **Save copy** (main window) | Saves the selected playlist song to a folder you pick, as the full song or the first 10 seconds. Works **offline** for your own mp3/wav files and for built-in melody songs. |
| **Add to playlist** (Online window) | Downloads the song (full or 10 s) and adds it to your linked list. |
| **Download to folder...** (Online window) | Downloads the song (full or 10 s) straight into a folder as `Artist - Title.mp3` or `.m4a`. |

## Hearing the whole song
- **Quick demo**: Quick demo limits each song to 10 seconds for brief testing. In the latest version, this is **turned OFF by default** so your songs play for their complete duration. You can toggle it at any time with the "Quick demo" button.
- **Progress bar scrubbing**: Click or drag along the progress bar to seek to any point in the track in real-time.

## Where files go
Downloads are cached in `~/.melody_cafe/cache/`. "Save copy" and "Download to folder" write into the folder you choose (it starts in your Music folder).

## Check your connection
```bash
python main.py --online-test "daft punk"
```
