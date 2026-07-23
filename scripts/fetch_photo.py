"""
Fetches a royalty-free background photo for a client's creative.

Tries Pexels first (simpler free API, no attribution required for most uses),
falls back to Unsplash if PEXELS_API_KEY isn't set.

Env vars expected (set as GitHub Actions secrets):
  PEXELS_API_KEY
  UNSPLASH_ACCESS_KEY
"""
import os
import random
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")


def _fetch_pexels(query, orientation="squarish", per_page=10):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "orientation": orientation, "per_page": per_page}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    photos = r.json().get("photos", [])
    if not photos:
        return None
    photo = random.choice(photos)
    return photo["src"]["large"]


def _fetch_unsplash(query, orientation="squarish", per_page=10):
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    params = {"query": query, "orientation": orientation, "per_page": per_page}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None
    photo = random.choice(results)
    return photo["urls"]["regular"]


def fetch_background_photo(queries, orientation="squarish", cache_path=None):
    """
    queries: list of search terms, tried in order until one returns a result.
    Returns local file path to the downloaded image.
    """
    query = random.choice(queries)
    img_url = None

    if PEXELS_KEY:
        img_url = _fetch_pexels(query, orientation)
    if img_url is None and UNSPLASH_KEY:
        img_url = _fetch_unsplash(query, orientation)

    if img_url is None:
        raise RuntimeError(
            "No photo found and/or no API key configured. "
            "Set PEXELS_API_KEY or UNSPLASH_ACCESS_KEY as a secret."
        )

    resp = requests.get(img_url, timeout=30)
    resp.raise_for_status()

    cache_path = cache_path or "/tmp/bg_photo.jpg"
    with open(cache_path, "wb") as f:
        f.write(resp.content)
    return cache_path


if __name__ == "__main__":
    path = fetch_background_photo(["physiotherapy session"])
    print(f"saved to {path}")
