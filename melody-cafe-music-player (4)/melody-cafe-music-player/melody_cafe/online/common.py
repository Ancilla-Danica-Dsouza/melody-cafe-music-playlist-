# Melody Cafe Music Player - Ancilla Danica Dsouza | PRN: 25070721021
"""Shared network helpers for the online music providers."""

import os
import ssl
import urllib.error
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (MelodyCafePlayer/1.1 student project)",
           "Accept": "application/json, audio/*;q=0.9, */*;q=0.5"}
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".melody_cafe", "cache")


class OnlineError(Exception):
    """Raised with a friendly message when the internet / a service fails."""


def _ssl_context():
    """Use certifi's certificates when installed (fixes many Windows / macOS Python problems)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def fetch_bytes(url, timeout=10, opener=urllib.request.urlopen):
    """Download a URL and return the bytes. Raises OnlineError with advice on failure."""
    req = urllib.request.Request(url, headers=HEADERS)
    kwargs = {"timeout": timeout}
    if opener is urllib.request.urlopen:
        ctx = _ssl_context()
        if ctx is not None:
            kwargs["context"] = ctx
    try:
        with opener(req, **kwargs) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise OnlineError("The service answered with HTTP error " + str(e.code) + ".")
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE" in str(reason).upper():
            raise OnlineError("Secure connection (SSL certificate) problem. Fix: run "
                              "'python -m pip install certifi' and try again. (" + str(reason) + ")")
        raise OnlineError("Could not reach the service. Check internet / firewall / VPN. ("
                          + str(reason) + ")")
    except (OSError, ValueError) as e:
        raise OnlineError("Network problem: " + str(e))
