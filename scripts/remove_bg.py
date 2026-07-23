"""
Remove a flat/near-flat background color from a logo image so it can be
composited cleanly onto any creative background.

Works well for logos exported with a solid or near-solid background color
(sampled automatically from the corners). Not a substitute for a real
transparent PNG from the brand -- use the original asset if you have one.
"""
import numpy as np
from PIL import Image


def remove_flat_background(image_path, low=40, high=95, corner_margin=5):
    """
    Returns an RGBA PIL.Image with the background color keyed out.

    low / high: distance thresholds (0-441 range for RGB euclidean distance).
        Pixels within `low` of the sampled background are fully transparent.
        Pixels beyond `high` are fully opaque. In between is a soft feather
        so edges don't look jagged.
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).astype(float)
    h, w, _ = arr.shape
    m = corner_margin

    corners = np.array([
        arr[m, m], arr[m, w - m - 1],
        arr[h - m - 1, m], arr[h - m - 1, w - m - 1],
    ])
    bg_ref = corners.mean(axis=0)

    dist = np.sqrt(((arr - bg_ref) ** 2).sum(axis=2))
    alpha = np.clip((dist - low) / (high - low), 0, 1) * 255

    rgba = np.dstack([arr.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    import sys
    src, dst = sys.argv[1], sys.argv[2]
    out = remove_flat_background(src)
    out.save(dst)
    print(f"saved {dst}")
