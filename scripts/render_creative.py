"""
Renders a 1080x1080 ad creative for a given client, using:
  - the client's colors/copy from clients.json
  - this week's headline/subtext from generate_copy.py
  - a background photo from fetch_photo.py
  - the client's logo (background removed via remove_bg.py if needed)

Three layout compositions are available (see LAYOUTS at the bottom):
  - "classico"       -> logo top-left, faded photo texture, pills, bottom wave + CTA
  - "foto_destaque"   -> full-bleed photo hero, dark gradient panel with text at bottom
  - "selo_central"    -> no photo, centered poster/badge style with big discount seal
"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

from remove_bg import remove_flat_background

W = H = 1080
FONT_B = "assets/fonts/DejaVuSans-Bold.ttf"
FONT_R = "assets/fonts/DejaVuSans.ttf"
WHITE = (255, 255, 255)


def F(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_headline(draw, text, max_width, max_lines=3, start_size=56, min_size=34, step=4):
    size = start_size
    while size >= min_size:
        font = F(FONT_B, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines, size
        size -= step
    font = F(FONT_B, min_size)
    return font, wrap_text(draw, text, font, max_width), min_size


def draw_highlighted_lines(d, lines, font, hx, hy, line_h, highlight, white, accent, align="left", canvas_w=W):
    highlighted_done = False
    for i, line in enumerate(lines):
        y = hy + i * line_h
        if align == "center":
            lw = d.textlength(line, font=font)
            x0 = (canvas_w - lw) / 2
        else:
            x0 = hx
        if highlight and not highlighted_done and highlight in line:
            before, _, after = line.partition(highlight)
            x = x0
            if before:
                d.text((x, y), before, font=font, fill=white)
                x += d.textlength(before, font=font)
            d.text((x, y), highlight, font=font, fill=accent)
            x += d.textlength(highlight, font=font)
            if after:
                d.text((x, y), after, font=font, fill=white)
            highlighted_done = True
        else:
            d.text((x0, y), line, font=font, fill=white)


def build_gradient(bg_start, bg_end):
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
    return base


def load_logo(logo_path, logo_needs_bg_removal, size):
    if logo_needs_bg_removal:
        logo = remove_flat_background(logo_path)
    else:
        logo = Image.open(logo_path).convert("RGBA")
    logo.thumbnail(size, Image.LANCZOS)
    return logo


def icon_pill(d, x, y, w, label, value, accent, white, bg_ref, icon="calendar"):
    h = 74
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2,
                         outline=(*accent, 200), width=2, fill=(*bg_ref, 90))
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


# ---------------------------------------------------------------------------
# LAYOUT 1 -- classico: logo top-left, faded photo texture, pills, wave + CTA
# ---------------------------------------------------------------------------
def render_classico(client_config, copy, photo_path, logo_path, colors, logo_needs_bg_removal=True):
    offer = client_config["offer"]
    bg_start, bg_end = tuple(colors["bg_start"]), tuple(colors["bg_end"])
    wave_color, accent = tuple(colors["wave"]), tuple(colors["accent"])
    text_muted = tuple(colors["text_muted"])

    base = build_gradient(bg_start, bg_end)
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

    wave_top_y = 995
    points_top = [(x, wave_top_y + int(12 * math.sin(x / 180))) for x in range(0, W + 1, 20)]
    poly = [(0, H)] + points_top + [(W, H)]
    wave_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wave_layer).polygon(poly, fill=(*wave_color, 255))
    img.paste(wave_layer, (0, 0), wave_layer)
    d = ImageDraw.Draw(img, "RGBA")
    stripe = [(x, y - 14) for x, y in points_top] + [(x, y + 14) for x, y in reversed(points_top)]
    d.polygon(stripe, fill=(*accent, 235))

    logo = load_logo(logo_path, logo_needs_bg_removal, (430, 430))
    img.paste(logo, (50, 55), logo)

    hx, hy = 60, 500
    max_text_width = W - hx - 60
    headline_text = " ".join(copy["headline_lines"])
    headline_font, lines, size = fit_headline(d, headline_text, max_text_width)
    line_h = int(size * 1.25)
    draw_highlighted_lines(d, lines, headline_font, hx, hy, line_h,
                            copy.get("highlight_word", ""), WHITE, accent)

    headline_bottom = hy + len(lines) * line_h + 15
    subtext_font = F(FONT_R, 26)
    subtext_lines = wrap_text(d, copy["subtext"], subtext_font, max_text_width)[:2]
    for i, line in enumerate(subtext_lines):
        d.text((hx, headline_bottom + i * 34), line, font=subtext_font, fill=text_muted)

    py = 800
    icon_pill(d, 60, py, 460, "Data:", offer["date_label"], accent, WHITE, bg_start, "calendar")
    icon_pill(d, 60, py + 84, 460, "Desconto:", f"{offer['discount_label']} - {offer['installments']}",
              accent, WHITE, bg_start, "tag")

    btn_w, btn_h = 460, 74
    bx, by = W - btn_w - 60, 990
    d.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=37, fill=WHITE)
    label = offer["cta_label"]
    f = F(FONT_B, 30)
    tw2 = d.textlength(label, font=f)
    d.text((bx + (btn_w - tw2) / 2, by + (btn_h - 36) / 2), label, font=f, fill=(80, 40, 20))

    return img.convert("RGB")


# ---------------------------------------------------------------------------
# LAYOUT 2 -- foto_destaque: full-bleed photo hero, dark panel at the bottom
# ---------------------------------------------------------------------------
def render_foto_destaque(client_config, copy, photo_path, logo_path, colors, logo_needs_bg_removal=True):
    offer = client_config["offer"]
    accent = tuple(colors["accent"])
    text_muted = tuple(colors["text_muted"])
    bg_start = tuple(colors["bg_start"])

    src = Image.open(photo_path).convert("RGB")
    photo = ImageOps.fit(src, (W, H), method=Image.LANCZOS, centering=(0.5, 0.42))
    img = photo.convert("RGBA")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    top_h = 200
    for y in range(top_h):
        a = int(150 * (1 - y / top_h))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    bot_h = 620
    for y in range(bot_h):
        a = int(215 * (y / bot_h))
        yy = H - bot_h + y
        od.line([(0, yy), (W, yy)], fill=(*bg_start, a))
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img, "RGBA")

    logo = load_logo(logo_path, logo_needs_bg_removal, (150, 150))
    img.paste(logo, (55, 45), logo)
    d.text((225, 60), client_config["display_name"].split(" ")[0] + " " +
            client_config["display_name"].split(" ")[-1], font=F(FONT_B, 26), fill=WHITE)
    d.line([(225, 100), (400, 100)], fill=WHITE, width=2)

    tag_w, tag_h = 150, 52
    tx, ty = W - tag_w - 55, 50
    d.rectangle([tx, ty, tx + tag_w, ty + tag_h], fill=accent)
    d.text((tx + 18, ty + 12), offer["discount_label"], font=F(FONT_B, 24), fill=(20, 20, 20))

    hx = 60
    max_text_width = W - hx - 60
    headline_text = " ".join(copy["headline_lines"])
    headline_font, lines, size = fit_headline(d, headline_text, max_text_width, start_size=50)
    line_h = int(size * 1.25)
    hy = 660
    draw_highlighted_lines(d, lines, headline_font, hx, hy, line_h,
                            copy.get("highlight_word", ""), WHITE, accent)

    headline_bottom = hy + len(lines) * line_h + 10
    subtext_font = F(FONT_R, 24)
    subtext_lines = wrap_text(d, copy["subtext"], subtext_font, max_text_width)[:2]
    for i, line in enumerate(subtext_lines):
        d.text((hx, headline_bottom + i * 30), line, font=subtext_font, fill=text_muted)

    info_y = headline_bottom + len(subtext_lines) * 30 + 14
    info_font = F(FONT_R, 22)
    info_text = f"{offer['date_label']}  -  {offer['location_label']}"
    d.text((hx, info_y), info_text, font=info_font, fill=(210, 210, 210))

    bar_h = 110
    d.rectangle([0, H - bar_h, W, H], fill=accent)
    label = offer["cta_label"]
    f = F(FONT_B, 36)
    tw = d.textlength(label, font=f)
    d.text(((W - tw) / 2, H - bar_h + (bar_h - 44) / 2), label, font=f, fill=(25, 25, 25))

    return img.convert("RGB")


# ---------------------------------------------------------------------------
# LAYOUT 3 -- selo_central: no photo, centered poster/badge style
# ---------------------------------------------------------------------------
def render_selo_central(client_config, copy, photo_path, logo_path, colors, logo_needs_bg_removal=True):
    offer = client_config["offer"]
    bg_start, bg_end = tuple(colors["bg_start"]), tuple(colors["bg_end"])
    accent = tuple(colors["accent"])
    text_muted = tuple(colors["text_muted"])

    img = build_gradient(bg_start, bg_end).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    logo = load_logo(logo_path, logo_needs_bg_removal, (300, 300))
    lx = (W - logo.width) // 2
    logo_top = 40
    img.paste(logo, (lx, logo_top), logo)

    # big centered discount seal, with faint concentric rings radiating from it
    # (kept tight so they don't creep up into the logo above)
    seal_cy = logo_top + logo.height + 130
    seal_r = 110
    for ring_r in range(seal_r + 30, seal_r + 130, 35):
        d.ellipse([W / 2 - ring_r, seal_cy - ring_r, W / 2 + ring_r, seal_cy + ring_r],
                  outline=(*accent, 26), width=3)
    d.ellipse([W / 2 - seal_r, seal_cy - seal_r, W / 2 + seal_r, seal_cy + seal_r], fill=accent)
    d.ellipse([W / 2 - seal_r + 10, seal_cy - seal_r + 10, W / 2 + seal_r - 10, seal_cy + seal_r - 10],
              outline=(255, 255, 255, 90), width=3)
    discount_num = offer["discount_label"].replace("OFF", "").strip()
    f_num = F(FONT_B, 54)
    tw = d.textlength(discount_num, font=f_num)
    d.text((W / 2 - tw / 2, seal_cy - 42), discount_num, font=f_num, fill=(25, 25, 25))
    f_off = F(FONT_B, 24)
    tw2 = d.textlength("OFF", font=f_off)
    d.text((W / 2 - tw2 / 2, seal_cy + 14), "OFF", font=f_off, fill=(25, 25, 25))

    hx = 80
    max_text_width = W - hx * 2
    headline_text = " ".join(copy["headline_lines"])
    headline_font, lines, size = fit_headline(d, headline_text, max_text_width, start_size=48, max_lines=3)
    line_h = int(size * 1.25)
    hy = seal_cy + seal_r + 40
    draw_highlighted_lines(d, lines, headline_font, hx, hy, line_h,
                            copy.get("highlight_word", ""), WHITE, accent, align="center", canvas_w=W)

    headline_bottom = hy + len(lines) * line_h + 10
    subtext_font = F(FONT_R, 24)
    subtext_lines = wrap_text(d, copy["subtext"], subtext_font, max_text_width)[:2]
    for i, line in enumerate(subtext_lines):
        lw = d.textlength(line, font=subtext_font)
        d.text(((W - lw) / 2, headline_bottom + i * 32), line, font=subtext_font, fill=text_muted)

    pills_y = headline_bottom + len(subtext_lines) * 32 + 30
    pill_w = 460
    icon_pill(d, (W - pill_w) // 2, pills_y, pill_w, "Data:", offer["date_label"],
              accent, WHITE, bg_start, "calendar")

    btn_w, btn_h = 460, 78
    bx, by = (W - btn_w) // 2, H - 130
    d.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=39, fill=WHITE)
    label = offer["cta_label"]
    f = F(FONT_B, 32)
    tw3 = d.textlength(label, font=f)
    d.text((bx + (btn_w - tw3) / 2, by + (btn_h - 38) / 2), label, font=f, fill=(80, 40, 20))

    return img.convert("RGB")


LAYOUTS = {
    "classico": render_classico,
    "foto_destaque": render_foto_destaque,
    "selo_central": render_selo_central,
}


def render(client_config, copy, photo_path, logo_path, logo_needs_bg_removal=True,
           colors_override=None, layout="classico"):
    colors = colors_override or client_config["colors"]
    fn = LAYOUTS.get(layout, render_classico)
    return fn(client_config, copy, photo_path, logo_path, colors,
              logo_needs_bg_removal=logo_needs_bg_removal)
