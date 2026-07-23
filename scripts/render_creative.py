"""
Renders a 1080x1080 ad creative for a given client, using:
  - the client's colors/copy from clients.json
  - this week's headline/subtext from generate_copy.py
  - a background photo from fetch_photo.py
  - the client's logo (background removed via remove_bg.py if needed)
"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

from remove_bg import remove_flat_background

W = H = 1080
FONT_B = "assets/fonts/DejaVuSans-Bold.ttf"
FONT_R = "assets/fonts/DejaVuSans.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def render(client_config, copy, photo_path, logo_path, logo_needs_bg_removal=True):
    colors = client_config["colors"]
    offer = client_config["offer"]
    bg_start = tuple(colors["bg_start"])
    bg_end = tuple(colors["bg_end"])
    wave_color = tuple(colors["wave"])
    accent = tuple(colors["accent"])
    text_muted = tuple(colors["text_muted"])
    white = (255, 255, 255)

    # 1) diagonal gradient background
    base = Image.new("RGB", (W, H), bg_start)
    px = base.load()
    for y in range(H):
        for x in range(0, W, 2):
            t = (x / W) * 0.5 + (y / H) * 0.5
            r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * t)
            g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * t)
            b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * t)
            px[x, y] = (r, g, b)
            if x + 1 < W:
                px[x + 1, y] = (r, g, b)

    # 2) faded real/stock photo as texture
    photo = Image.open(photo_path).convert("RGB")
    photo = ImageOps.fit(photo, (W, H), method=Image.LANCZOS, centering=(0.5, 0.4))
    photo = ImageEnhance.Color(photo).enhance(0.55)
    photo = ImageEnhance.Brightness(photo).enhance(0.75)

    img = base.convert("RGBA")
    photo_rgba = photo.convert("RGBA")
    photo_rgba.putalpha(70)
    img = Image.alpha_composite(img, photo_rgba)

    wash = Image.new("RGBA", (W, H), (*bg_start, 130))
    img = Image.alpha_composite(img, wash)
    d = ImageDraw.Draw(img, "RGBA")

    # 3) bottom wave band
    wave_top_y = 995
    points_top = [(x, wave_top_y + int(12 * math.sin(x / 180))) for x in range(0, W + 1, 20)]
    poly = [(0, H)] + points_top + [(W, H)]
    wave_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wave_layer).polygon(poly, fill=(*wave_color, 255))
    img.paste(wave_layer, (0, 0), wave_layer)
    d = ImageDraw.Draw(img, "RGBA")
    stripe = [(x, y - 14) for x, y in points_top] + [(x, y + 14) for x, y in reversed(points_top)]
    d.polygon(stripe, fill=(*accent, 235))

    # 4) logo, background removed so it blends in
    if logo_needs_bg_removal:
        logo = remove_flat_background(logo_path)
    else:
        logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail((430, 430), Image.LANCZOS)
    img.paste(logo, (50, 55), logo)

    # 5) headline (2-3 lines, last word of the last line highlighted)
    hx, hy = 60, 500
    line_h = 68
    lines = copy["headline_lines"]
    for i, line in enumerate(lines):
        y = hy + i * line_h
        if i == len(lines) - 1 and copy.get("highlight_word") and copy["highlight_word"] in line:
            hw = copy["highlight_word"]
            before = line.split(hw)[0]
            d.text((hx, y), before, font=F(FONT_B, 56), fill=white)
            tw = d.textlength(before, font=F(FONT_B, 56))
            d.text((hx + tw, y), hw, font=F(FONT_B, 56), fill=accent)
        else:
            d.text((hx, y), line, font=F(FONT_B, 56), fill=white)

    d.text((hx, hy + len(lines) * line_h + 15), copy["subtext"],
            font=F(FONT_R, 28), fill=text_muted)

    # 6) info pills
    def icon_pill(x, y, w, label, value, icon="calendar"):
        h = 74
        d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                             outline=(*accent, 200), width=2, fill=(*bg_start, 90))
        cx, cy, r = x + 37, y + h // 2, 27
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
        if icon == "calendar":
            d.rounded_rectangle([cx - 13, cy - 11, cx + 13, cy + 13], radius=3, outline=white, width=2)
            d.line([cx - 13, cy - 3, cx + 13, cy - 3], fill=white, width=2)
        elif icon == "tag":
            d.polygon([(cx - 13, cy - 10), (cx + 4, cy - 10), (cx + 14, cy),
                       (cx + 4, cy + 10), (cx - 13, cy + 10)], outline=white, width=2)
            d.ellipse([cx - 9, cy - 4, cx - 3, cy + 2], fill=white)
        d.text((x + 82, y + 12), label, font=F(FONT_B, 22), fill=accent)
        d.text((x + 82, y + 40), value, font=F(FONT_R, 24), fill=white)

    py = 800
    icon_pill(60, py, 460, "Data:", offer["date_label"], "calendar")
    icon_pill(60, py + 84, 460, "Desconto:", f"{offer['discount_label']} - {offer['installments']}", "tag")

    # 7) CTA button
    btn_w, btn_h = 460, 74
    bx, by = W - btn_w - 60, 990
    d.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=37, fill=white)
    label = offer["cta_label"]
    f = F(FONT_B, 30)
    tw2 = d.textlength(label, font=f)
    d.text((bx + (btn_w - tw2) / 2, by + (btn_h - 36) / 2), label, font=f, fill=(80, 40, 20))

    return img.convert("RGB")
