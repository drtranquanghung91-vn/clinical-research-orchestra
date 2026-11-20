"""Shared HTTP GET with the project User-Agent."""
import urllib.request

UA = "clinical-research-orchestra/0.1 (+https://github.com/drtranquanghung91-vn/clinical-research-orchestra)"


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
