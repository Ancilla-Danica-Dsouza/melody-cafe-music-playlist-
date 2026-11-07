# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
from .common import OnlineError
from . import jamendo
from . import youtube
from .deezer import search_any as search, download_preview, parse_results, PREVIEW_SECONDS
from .download import download_track, available_seconds


def search_sources(query, prefer_full=True, limit=25, source="auto"):
    """Returns (tracks, notice).
    source can be "auto", "youtube", "jamendo", or "preview".
    prefer_full=True  -> free FULL songs from YouTube or Jamendo, falling back to
                         30 second previews from Deezer / iTunes with a notice.
    prefer_full=False -> 30 second previews only."""
    notice = ""
    query = query.strip()
    if not query:
        return [], ""

    if source == "youtube" or (source == "auto" and prefer_full and youtube.is_available() and not jamendo.get_key()):
        try:
            tracks = youtube.search(query, limit)
            if tracks:
                return tracks, ""
            notice = "No YouTube full songs found, falling back to previews. "
        except Exception as e:
            notice = f"YouTube search unavailable ({e}). Showing previews. "

    if prefer_full or source == "jamendo":
        if jamendo.get_key():
            try:
                tracks = jamendo.search(query, limit)
                if tracks:
                    return tracks, ""
                notice = "No free full-length songs matched, so these are 30 second previews. "
            except OnlineError as e:
                notice = "Full songs unavailable (" + str(e) + "). Showing 30 second previews. "
        elif source == "jamendo":
            raise OnlineError("Jamendo full songs need a Jamendo API key (press 'Set Jamendo key').")
        else:
            notice = ("Full songs need a free Jamendo key (press 'Set Jamendo key') or choose 'YouTube (Full)' in Search. "
                      "Showing 30 second previews for now. ")

    return search(query, limit), notice


__all__ = ["PREVIEW_SECONDS", "search", "search_sources", "download_preview", "download_track",
           "available_seconds", "parse_results", "OnlineError", "jamendo", "youtube"]
