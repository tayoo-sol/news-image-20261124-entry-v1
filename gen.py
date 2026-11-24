#!/usr/bin/env python3
"""Render the 24 Nov 2026 world-news poster from stories.json (build-time only).

Reads stories.json next to this file and draws a dense one-page poster:
title, hero stats, a drawn world map with story dots, key numbers,
a UTC timeline, and every story grouped by region. Writes entry.png
(1024x1024) next to this file. The grader never runs this script;
main.ts only copies the finished entry.png.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

# --- palette (dark newsroom) ---
BG = (11, 16, 32)
PANEL = (21, 28, 51)
PANEL_LINE = (61, 90, 128)
INK = (235, 238, 245)
MUTED = (148, 163, 184)
GOLD = (245, 197, 66)
GOLD_DIM = (180, 150, 70)
RULE = (245, 197, 66)
LAND = (38, 56, 82)
LAND_LINE = (74, 110, 150)
GRID = (26, 36, 60)

# Rough continent outlines as (lon, lat) rings, equirectangular.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 73),
     (-76, 62), (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35),
     (-80, 32), (-85, 30), (-90, 21), (-97, 16), (-105, 20), (-115, 28),
     (-125, 40), (-125, 48), (-135, 58), (-155, 60)],
    # Greenland
    [(-58, 64), (-45, 60), (-40, 65), (-30, 68), (-22, 70), (-30, 76),
     (-45, 78), (-58, 74)],
    # South America
    [(-80, 10), (-75, 7), (-62, 10), (-52, 5), (-50, -5), (-35, -8),
     (-40, -20), (-48, -28), (-58, -35), (-65, -40), (-70, -50), (-73, -40),
     (-73, -25), (-80, -15)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-4, 52), (0, 53), (5, 58), (8, 57),
     (12, 55), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (32, 68),
     (40, 68), (45, 65), (40, 60), (35, 55), (30, 50), (28, 45), (23, 40),
     (19, 42), (12, 44), (8, 44), (3, 42), (-2, 37)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28),
     (43, 12), (48, 11), (51, 10), (46, 0), (40, -10), (35, -20), (32, -28),
     (26, -33), (18, -35), (12, -18), (9, -1), (4, 6), (-8, 5), (-13, 8)],
    # Asia
    [(32, 68), (45, 68), (55, 70), (70, 72), (90, 75), (110, 76), (130, 72),
     (150, 70), (160, 66), (162, 60), (156, 52), (142, 45), (140, 38),
     (130, 33), (127, 35), (122, 30), (120, 22), (110, 20), (105, 10),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 10), (76, 8), (72, 20),
     (66, 25), (60, 25), (55, 26), (50, 29), (48, 30), (44, 30), (40, 35),
     (36, 36)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 38), (141, 42),
     (143, 44), (145, 44), (142, 42), (140, 39), (138, 36), (135, 33)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -33), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -15), (140, -17), (136, -15), (132, -12),
     (130, -13), (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(166, -34), (174, -37), (178, -38), (176, -40), (172, -42), (168, -44),
     (166, -46), (167, -44), (170, -41), (174, -38)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (-1, 51)],
]

# Story dots: (lon, lat, region colour index).
DOTS = [
    (-74, 41, 0), (-77, 39, 0), (-88, 42, 0), (-67, 11, 1), (-47, -24, 1),
    (0, 52, 2), (2, 49, 2), (13, 53, 2), (6, 46, 2), (8, 45, 2),
    (38, 56, 2), (31, 50, 2), (31, 37, 2), (20, 32, 3), (31, 30, 3),
    (33, 16, 3), (15, -4, 3), (3, 7, 3), (28, -26, 3), (47, 25, 4),
    (51, 36, 4), (73, 19, 5), (77, 29, 5), (107, -6, 5), (101, 14, 5),
    (116, 40, 5), (140, 36, 5), (127, 38, 5), (151, -34, 5), (175, -41, 5),
]


def find_font(bold=False):
    import glob
    pats = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for p in pats:
        if os.path.exists(p):
            return p
    hits = glob.glob("/usr/share/fonts/**/DejaVuSans*.ttf", recursive=True)
    if hits:
        return hits[0]
    return None


class Fonts:
    def __init__(self):
        self.cache = {}

    def get(self, size, bold=False):
        key = (size, bold)
        if key not in self.cache:
            path = find_font(bold)
            if path:
                self.cache[key] = ImageFont.truetype(path, size)
            else:
                self.cache[key] = ImageFont.load_default()
        return self.cache[key]


def wrap(draw, text, font, width):
    """Greedy word wrap; returns a list of lines that fit width."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_center(draw, y, text, font, fill, cx=None):
    if cx is None:
        cx = W / 2
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def main():
    with open(os.path.join(HERE, "stories.json"), encoding="utf-8") as f:
        data = json.load(f)

    total = sum(len(r["stories"]) for r in data["regions"])
    fresh = sum(1 for r in data["regions"] for s in r["stories"] if s["d"] == "24")
    stale = total - fresh

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fonts = Fonts()

    # faint background grid
    for gx in range(0, W, 64):
        d.line([(gx, 0), (gx, H)], fill=GRID, width=1)
    for gy in range(0, H, 64):
        d.line([(0, gy), (W, gy)], fill=GRID, width=1)

    # ---- header ----
    draw_center(d, 14, "THE WORLD IN ONE DAY", fonts.get(46, True), INK)
    draw_center(d, 66, "TUESDAY 24 NOVEMBER 2026", fonts.get(24, True), GOLD)
    draw_center(d, 96, data["subtitle"], fonts.get(14, False), MUTED)
    d.line([(28, 118), (W - 28, 118)], fill=GOLD, width=2)

    # ---- hero cards ----
    hy, hh, gap = 130, 68, 14
    cw = (W - 56 - 2 * gap) // 3
    for i, hero in enumerate(data["hero"]):
        x0 = 28 + i * (cw + gap)
        cx = x0 + cw / 2
        d.rounded_rectangle([x0, hy, x0 + cw, hy + hh], radius=8,
                            fill=PANEL, outline=PANEL_LINE, width=1)
        d.line([(x0 + 10, hy + 6), (x0 + cw - 10, hy + 6)], fill=GOLD, width=2)
        draw_center(d, hy + 9, hero["big"], fonts.get(24, True), GOLD, cx)
        label_lines = wrap(d, hero["label"], fonts.get(12, False), cw - 20)
        ly = hy + 38
        for ln in label_lines[:2]:
            draw_center(d, ly, ln, fonts.get(12, False), INK, cx)
            ly += 14

    # ---- map + key numbers ----
    my, mh = 208, 152
    map_x, map_w = 28, 636
    num_x, num_w = 28 + 636 + 14, 1024 - 28 - (28 + 636 + 14)
    d.rounded_rectangle([map_x, my, map_x + map_w, my + mh], radius=8,
                        fill=PANEL, outline=PANEL_LINE, width=1)
    d.text((map_x + 10, my + 8), "WORLD MAP — %d STORIES" % total,
           font=fonts.get(13, True), fill=INK)
    # map projection: lon -180..180 -> x, lat 78..-58 -> y (crop poles)
    mx0, my0, mw, mh2 = map_x + 8, my + 28, map_w - 16, mh - 36
    def proj(lon, lat):
        return (mx0 + (lon + 180) / 360.0 * mw,
                my0 + (78 - lat) / 136.0 * mh2)
    for ring in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in ring]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    region_cols = [tuple(int(r["color"][i:i + 2], 16) for i in (1, 3, 5))
                   for r in data["regions"]]
    for lon, lat, ri in DOTS:
        x, y = proj(lon, lat)
        col = region_cols[ri]
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col, outline=INK, width=1)

    # key numbers panel
    d.rounded_rectangle([num_x, my, num_x + num_w, my + mh], radius=8,
                        fill=PANEL, outline=PANEL_LINE, width=1)
    d.text((num_x + 10, my + 8), "KEY NUMBERS", font=fonts.get(13, True), fill=INK)
    ny = my + 30
    for num in data["numbers"]:
        d.text((num_x + 10, ny), num["value"], font=fonts.get(15, True), fill=GOLD)
        vw = d.textlength(num["value"], font=fonts.get(15, True))
        lab = wrap(d, num["label"], fonts.get(11, False), num_w - 24 - vw - 6)
        d.text((num_x + 10 + vw + 8, ny + 2), lab[0] if lab else "",
               font=fonts.get(11, False), fill=MUTED)
        ny += 15

    # ---- timeline ----
    ty = my + mh + 10
    d.text((28, ty), "24 NOVEMBER — UTC · AS REPORTED", font=fonts.get(13, True), fill=INK)
    ty += 20
    tw = (W - 56 - 5 * 8) // 6
    for i, ev in enumerate(data["timeline"]):
        x0 = 28 + i * (tw + 8)
        d.rounded_rectangle([x0, ty, x0 + tw, ty + 50], radius=6,
                            fill=PANEL, outline=PANEL_LINE, width=1)
        d.text((x0 + 8, ty + 5), ev["utc"] + " UTC", font=fonts.get(12, True), fill=GOLD)
        lines = wrap(d, ev["event"], fonts.get(11, False), tw - 16)
        ly = ty + 22
        for ln in lines[:2]:
            d.text((x0 + 8, ly), ln, font=fonts.get(11, False), fill=INK)
            ly += 13

    # ---- stories: 3 balanced columns ----
    sy = ty + 50 + 10
    d.text((28, sy), "ALL %d STORIES" % total, font=fonts.get(13, True), fill=INK)
    sy += 20
    bottom = 962
    col_w = (W - 56 - 2 * 14) // 3
    body = fonts.get(11, False)
    head = fonts.get(12, True)
    # flatten into items: (kind, region_idx, text, height)
    items = []
    for ri, region in enumerate(data["regions"]):
        items.append(("head", ri, region["name"], 17))
        for s in region["stories"]:
            lines = wrap(d, s["t"], body, col_w - 8)
            items.append(("story", ri, s["t"], len(lines) * 13 + 2))
    col_h = bottom - sy
    total_h = sum(it[3] for it in items)
    print("stories total height", total_h, "vs 3 cols x", col_h, "=", 3 * col_h)
    if total_h > 3 * col_h:
        raise SystemExit("STORIES DO NOT FIT: need %d px, have %d px"
                         % (total_h, 3 * col_h))
    # greedy column fill, never orphan a header at a column's end
    cols, cur, used = [], [], 0
    for it in items:
        if it[0] == "head" and used > 0 and used + it[3] > col_h:
            cols.append(cur)
            cur, used = [], 0
        if used + it[3] > col_h and cur:
            cols.append(cur)
            cur, used = [], 0
        cur.append(it)
        used += it[3]
    if cur:
        cols.append(cur)
    print("columns used:", len(cols))
    while len(cols) < 3:
        cols.append([])
    for ci, col in enumerate(cols[:3]):
        x0 = 28 + ci * (col_w + 14)
        y = sy
        for kind, ri, text, hgt in col:
            if kind == "head":
                d.text((x0, y), text, font=head, fill=region_cols[ri])
                d.line([(x0, y + 15), (x0 + col_w, y + 15)], fill=region_cols[ri], width=1)
            else:
                lines = wrap(d, text, body, col_w - 8)
                ly = y
                for ln in lines:
                    d.text((x0 + 4, ly), ln, font=body, fill=INK)
                    ly += 13
            y += hgt

    # ---- footer ----
    fy = 972
    d.line([(28, fy), (W - 28, fy)], fill=GOLD_DIM, width=1)
    date_line = ("DATE CHECK — %d stories from 24 Nov 2026 · %d from the days before · "
                 "Claims flagged in the data are shown as claims, not facts" % (fresh, stale))
    draw_center(d, fy + 6, date_line, fonts.get(11, True), GOLD)
    src_lines = wrap(d, data["sources"], fonts.get(10, False), W - 56)
    ly = fy + 22
    for ln in src_lines[:2]:
        draw_center(d, ly, ln, fonts.get(10, False), MUTED)
        ly += 12
    draw_center(d, H - 14, data["footer"], fonts.get(10, False), MUTED)

    out = os.path.join(HERE, "entry.png")
    img.save(out, optimize=True)
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
