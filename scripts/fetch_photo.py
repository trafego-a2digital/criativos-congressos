"""
Fetches royalty-free background photos for a client's creatives.

Tries Pexels first (simpler free API, no attribution required for most uses),
falls back to Unsplash if PEXELS_API_KEY isn't set.

Env vars expected (set as GitHub Actions secrets):
  PEXELS_API_KEY
  UNSPLASH_ACCESS_KEY
"""
import os
import requests

PEXELS_KEY = os.environ.get("PEXELS_API_KEY")
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")

# how many of the top (most relevant) results to consider per search --
# keeps loosely-related results (curtains, generic interiors, etc.) out
TOP_N = 4


def _search_pexels(query, orientation="squarish", per_page=8, page=1):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_KEY}
    params = {"query": query, "orientation": orientation, "per_page": per_page, "page": page}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    photos = r.json().get("photos", [])
    return [p["src"]["large"] for p in photos[:TOP_N]]


def _search_unsplash(query, orientation="squarish", per_page=8, page=1):
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    params = {"query": query, "orientation": orientation, "per_page": per_page, "page": page}
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [p["urls"]["regular"] for p in results[:TOP_N]]


def _search(query, orientation, page):
    urls = []
    if PEXELS_KEY:
        urls = _search_pexels(query, orientation, page=page)
    if not urls and UNSPLASH_KEY:
        urls = _search_unsplash(query, orientation, page=page)
    return urls


def _download(url, cache_path):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(cache_path, "wb") as f:
        f.write(resp.content)
    return cache_path


def fetch_background_photo(queries, orientation="squarish", cache_path=None):
    """Single photo (kept for backwards compatibility / quick tests)."""
    for query in queries:
        urls = _search(query, orientation, page=1)
        if urls:
            return _download(urls[0], cache_path or "/tmp/bg_photo.jpg")
    raise RuntimeError(
        "No photo found and/or no API key configured. "
        "Set PEXELS_API_KEY or UNSPLASH_ACCESS_KEY as a secret."
    )


def fetch_multiple_backgrounds(queries, count, orientation="squarish", cache_prefix="/tmp/bg"):
    """
    Returns `count` DIFFERENT local photo paths, one per creative in a batch.
    Cycles through the configured queries and paginates (page=1, then 2, ...)
    to pull fresh results instead of reusing the same handful every time,
    and skips any URL already picked so the batch doesn't repeat a photo.
    """
    picked_urls = []
    paths = []
    query_idx = 0
    page = 1
    attempts = 0
    max_attempts = count * 4  # generous ceiling so a bad query can't loop forever

    while len(paths) < count and attempts < max_attempts:
        attempts += 1
        query = queries[query_idx % len(queries)]
        urls = _search(query, orientation, page=page)

        new_url = next((u for u in urls if u not in picked_urls), None)
        if new_url:
            picked_urls.append(new_url)
            idx = len(paths)
            paths.append(_download(new_url, f"{cache_prefix}_{idx}.jpg"))
        else:
            # this query/page combo is exhausted or repeats -- move on
            pass

        query_idx += 1
        if query_idx % len(queries) == 0:
            page += 1

    if not paths:
        raise RuntimeError(
            "No photos found and/or no API key configured. "
            "Set PEXELS_API_KEY or UNSPLASH_ACCESS_KEY as a secret."
        )

    # if we couldn't find enough distinct photos, pad by reusing the last one
    while len(paths) < count:
        paths.append(paths[-1])

    return paths


if __name__ == "__main__":
    paths = fetch_multiple_backgrounds(["physiotherapy session"], count=5)
    print("saved:", paths)
