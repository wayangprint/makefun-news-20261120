#!/usr/bin/env python3
"""makefun-news-20261120: a one-page newspaper front page summing up the
world news of Friday 20 November 2026, drawn with pure Python stdlib.

No dependencies, no network, no randomness, no clock: the same bytes are
produced on every run. Output: $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024).

Stories (all reported 20 Nov 2026, any timezone):
  * Trump, Xi and Putin hold the first three-way summit in Shenzhen,
    ending with a joint peace declaration (nuclear arms, energy, Ukraine).
  * The ICJ rules Myanmar committed genocide against the Rohingya.
  * Anthropic's IPO is the largest on record: about $81.3bn raised.
  * South Korea's annual exports pass $1 trillion for the first time.
  * Kyiv hit by four ballistic missiles; Houthi strikes on Saudi targets;
    tanker on fire after a mine blast near the Strait of Hormuz; Genoa
    airport halted by drones; India evacuates 80,000 as a cyclone nears
    Odisha; Europe ready for talks with Russia.
"""

import argparse
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 231)
CARD = (255, 253, 246)
WHITE = (255, 255, 255)
INK = (17, 17, 17)
RED = (185, 28, 28)
BLUE = (29, 78, 216)
SKY = (191, 219, 254)
GREY = (120, 113, 108)
ORANGE = (234, 88, 12)
GOLD = (250, 204, 21)
GREEN = (22, 163, 74)

# ---------------------------------------------------------------------------
# 5x7 pixel font. Each glyph is a tuple of seven 5-character rows, '#' for
# ink and '.' for blank, read top to bottom. Rows stored as text (instead of
# row bitmasks) keep the table readable: the letter is visible in the source.
# A-Z, 0-9 and punctuation. Uppercase only; text is uppercased on draw.
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "\u2022": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


class Raster:
    """RGB canvas backed by one flat bytearray.

    A run of identical colour is stamped in with one slice assignment per
    row instead of one byte at a time; the bytes landed are the same.
    """

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg * (w * h))

    def _span(self, x, y, w):
        """Clipped (start_x, length) of a horizontal run, or None."""
        if y < 0 or y >= self.h:
            return None
        x0 = max(0, x)
        x1 = min(self.w, x + w)
        if x1 <= x0:
            return None
        return x0, x1 - x0

    def dot(self, x, y, color):
        span = self._span(x, y, 1)
        if span is not None:
            i = (y * self.w + span[0]) * 3
            self.buf[i:i + 3] = bytes(color)

    def box(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        run = bytes(color)
        for yy in range(max(0, y), min(self.h, y + h)):
            span = self._span(x, yy, w)
            if span is None:
                continue
            i = (yy * self.w + span[0]) * 3
            self.buf[i:i + 3 * span[1]] = run * span[1]

    def hbar(self, x, y, w, color, thick=1):
        self.box(x, y, w, thick, color)

    def vbar(self, x, y, h, color, thick=1):
        self.box(x, y, thick, h, color)

    def frame(self, x, y, w, h, color, thick=2):
        self.box(x, y, w, thick, color)
        self.box(x, y + h - thick, w, thick, color)
        self.box(x, y, thick, h, color)
        self.box(x + w - thick, y, thick, h, color)

    def diag(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.box(x0, y0, thick, thick, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.hbar(cx - dx, cy + dy, 2 * dx + 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for a in range(360):
            rad = math.radians(a)
            self.box(int(cx + r * math.cos(rad)),
                     int(cy + r * math.sin(rad)), thick, thick, color)

    def tri(self, x0, y0, x1, y1, x2, y2, color):
        ys = sorted((y0, y1, y2))
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for ax, ay, bx, by in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                   (x2, y2, x0, y0)):
                if ay == by:
                    continue
                if min(ay, by) <= y <= max(ay, by):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            if len(xs) >= 2:
                xa, xb = int(min(xs)), int(max(xs))
                self.hbar(xa, y, xb - xa + 1, color)


def glyph_width(text, scale):
    return len(text.upper()) * 6 * scale - scale if text else 0


def split_lines(text, max_width, scale):
    words = text.upper().split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if glyph_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def blit(r, x, y, text, scale, color):
    cx = x
    for ch in text.upper():
        rows = GLYPHS.get(ch)
        if rows is None:
            cx += 6 * scale
            continue
        for row_i, row in enumerate(rows):
            for col, cell in enumerate(row):
                if cell == "#":
                    r.box(cx + col * scale, y + row_i * scale,
                          scale, scale, color)
        cx += 6 * scale
    return cx


def blit_centred(r, y, text, scale, color, x0=0, x1=W):
    w = glyph_width(text, scale)
    blit(r, x0 + (x1 - x0 - w) // 2, y, text, scale, color)


def blit_para(r, x, y, text, scale, color, max_width, gap=4):
    lines = split_lines(text, max_width, scale)
    for i, line in enumerate(lines):
        blit(r, x, y + i * (7 * scale + gap), line, scale, color)
    return y + len(lines) * (7 * scale + gap)


# ---------------------------------------------------------------------------
# Pictograms: simple shapes inside a 72x72 box at (x, y).
# ---------------------------------------------------------------------------
def pic_scales(r, x, y):
    r.box(x, y, 72, 72, WHITE)
    r.frame(x, y, 72, 72, INK, 2)
    cx = x + 36
    r.vbar(cx, y + 8, 44, INK, 3)
    r.hbar(x + 10, y + 10, 52, INK, 3)
    r.diag(x + 10, y + 12, x + 18, y + 30, INK, 2)
    r.diag(x + 62, y + 12, x + 54, y + 30, INK, 2)
    r.tri(x + 12, y + 30, x + 24, y + 30, cx - 12, y + 44, BLUE)
    r.tri(x + 48, y + 30, x + 60, y + 30, cx + 12, y + 44, BLUE)
    r.hbar(x + 12, y + 30, 13, INK, 2)
    r.hbar(x + 48, y + 30, 13, INK, 2)
    r.hbar(x + 14, y + 52, 44, INK, 3)


def pic_bolt(r, x, y):
    r.box(x, y, 72, 72, WHITE)
    r.frame(x, y, 72, 72, INK, 2)
    r.tri(x + 40, y + 8, x + 20, y + 40, x + 34, y + 40, GOLD)
    r.tri(x + 30, y + 32, x + 52, y + 32, x + 34, y + 64, ORANGE)
    r.hbar(x + 12, y + 58, 48, INK, 3)


def pic_chart(r, x, y):
    r.box(x, y, 72, 72, WHITE)
    r.frame(x, y, 72, 72, INK, 2)
    r.vbar(x + 12, y + 10, 50, INK, 3)
    r.hbar(x + 12, y + 58, 50, INK, 3)
    pts = [(x + 14, y + 50), (x + 26, y + 42), (x + 36, y + 46),
           (x + 46, y + 30), (x + 58, y + 16)]
    for i in range(len(pts) - 1):
        r.diag(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 3)
    r.diag(x + 58, y + 16, x + 52, y + 18, GREEN, 3)
    r.diag(x + 58, y + 16, x + 56, y + 23, GREEN, 3)
    for px, py in pts:
        r.disc(px, py, 3, RED)


def pic_globe(r, x, y):
    r.box(x, y, 72, 72, WHITE)
    r.frame(x, y, 72, 72, INK, 2)
    cx, cy = x + 36, y + 36
    r.ring(cx, cy, 24, BLUE, 3)
    r.vbar(cx, cy - 24, 48, BLUE, 2)
    r.hbar(cx - 24, cy, 48, BLUE, 2)
    r.disc(cx - 8, cy - 8, 5, GREEN)
    r.disc(cx + 10, cy + 8, 6, GREEN)
    r.disc(cx + 6, cy - 12, 3, GREEN)


# ---------------------------------------------------------------------------
# Flags for the lead story: three 304x52 panels.
# ---------------------------------------------------------------------------
def flag_usa(r, x, y, w, h):
    stripe = h // 7
    for i in range(7):
        r.box(x, y + i * stripe, w, stripe, RED if i % 2 == 0 else WHITE)
    r.box(x, y, w // 2, stripe * 4, BLUE)
    for row in range(3):
        for col in range(5):
            r.disc(x + 14 + col * 28, y + 6 + row * 9, 2, WHITE)


def flag_china(r, x, y, w, h):
    r.box(x, y, w, h, RED)
    r.disc(x + 56, y + h // 2, 10, GOLD)
    for dx, dy in ((100, -14), (118, -4), (118, 12), (100, 18)):
        r.disc(x + dx, y + h // 2 + dy, 4, GOLD)


def flag_russia(r, x, y, w, h):
    third = h // 3
    r.box(x, y, w, third, WHITE)
    r.box(x, y + third, w, third, BLUE)
    r.box(x, y + 2 * third, w, h - 2 * third, RED)


# ---------------------------------------------------------------------------
# PNG encoder: RGB 8-bit, zlib level 9, no time chunks, fully deterministic.
# ---------------------------------------------------------------------------
def _png_chunk(kind, data):
    body = kind + data
    return (struct.pack(">I", len(data)) + body +
            struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))


def write_png(r, path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    scanlines = [b"\x00" + bytes(r.buf[y * W * 3:(y + 1) * W * 3])
                 for y in range(H)]
    png = (b"\x89PNG\r\n\x1a\n"
           + _png_chunk(b"IHDR", ihdr)
           + _png_chunk(b"IDAT", zlib.compress(b"".join(scanlines), 9))
           + _png_chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def rule(r, y, thick, color, x=32, w=960):
    """Full-width horizontal rule."""
    r.box(x, y, w, thick, color)


def story_card(r, sx, sy, accent, headline, summary, pic):
    """One supporting-story card in the 2x2 grid."""
    r.box(sx, sy, 472, 188, CARD)
    r.frame(sx, sy, 472, 188, INK, 2)
    r.box(sx, sy, 472, 6, accent)
    blit_para(r, sx + 16, sy + 16, headline, 3, INK, 440, gap=4)
    pic(r, sx + 16, sy + 100)
    blit_para(r, sx + 104, sy + 102, summary, 2, INK, 352, gap=3)


# ---------------------------------------------------------------------------
# Layout: newspaper front page, 1024x1024.
# ---------------------------------------------------------------------------
def draw_page():
    r = Raster(W, H, PAPER)

    # Masthead
    blit_centred(r, 28, "THE WORLD IN ONE PAGE", 8, INK)
    rule(r, 104, 6, RED)
    rule(r, 114, 2, INK)
    blit_centred(r, 128, "FRIDAY 20 NOVEMBER 2026", 4, INK)
    blit_centred(r, 164, "ONE DAY - ONE IMAGE - THE WORLD'S NEWS", 2, RED)
    rule(r, 192, 2, INK)

    # Lead story box
    r.box(32, 200, 960, 250, CARD)
    r.frame(32, 200, 960, 250, INK, 3)
    blit(r, 48, 214, "LEAD STORY - SHENZHEN, CHINA", 2, RED)
    r.ring(936, 224, 15, BLUE, 2)
    r.vbar(936, 211, 26, BLUE, 2)
    r.hbar(923, 224, 26, BLUE, 2)
    blit(r, 48, 240, "TRUMP, XI AND PUTIN", 5, INK)
    blit(r, 48, 281, "IN FIRST THREE-WAY SUMMIT", 5, INK)
    blit_para(r, 48, 328,
              "JOINT PEACE DECLARATION AFTER HISTORIC APEC SIDELINES "
              "MEETING - NUCLEAR ARMS, ENERGY AND UKRAINE ON THE TABLE",
              2, INK, 928, gap=4)
    flag_usa(r, 48, 384, 304, 52)
    flag_china(r, 360, 384, 304, 52)
    flag_russia(r, 672, 384, 304, 52)
    r.frame(48, 384, 304, 52, INK, 2)
    r.frame(360, 384, 304, 52, INK, 2)
    r.frame(672, 384, 304, 52, INK, 2)

    # 2x2 grid of supporting stories
    stories = [
        (32, 466, RED, "ICJ: MYANMAR COMMITTED GENOCIDE",
         "UN COURT RULES AGAINST MYANMAR OVER THE 2017 ROHINGYA CRACKDOWN",
         pic_scales),
        (520, 466, BLUE, "ANTHROPIC IPO: LARGEST ON RECORD",
         "$81.3BN RAISED - VALUATION REPORTED NEAR $1.5 TRILLION",
         pic_chart),
        (32, 670, BLUE, "S. KOREA EXPORTS TOP $1 TRILLION",
         "FIRST TIME EVER, DRIVEN BY AI CHIP DEMAND AND SHIPMENTS",
         pic_globe),
        (520, 670, RED, "KYIV HIT BY FOUR BALLISTIC MISSILES",
         "MISSILES STRIKE CAPITAL - GENOA AIRPORT HALTED BY DRONES",
         pic_bolt),
    ]
    for sx, sy, accent, headline, summary, pic in stories:
        story_card(r, sx, sy, accent, headline, summary, pic)

    # Ticker bar
    r.box(32, 874, 960, 78, INK)
    blit_para(r, 48, 886,
              "HOUTHIS CLAIM STRIKES ON FOUR SAUDI TARGETS \u2022 TANKER "
              "ON FIRE AFTER MINE BLAST NEAR HORMUZ \u2022 GAZA: IDF "
              "COMPLETES GROUND PUSH PAST YELLOW LINE \u2022 INDIA "
              "EVACUATES 80,000 AS CYCLONE NEARS ODISHA \u2022 EUROPE "
              "READY FOR TALKS WITH RUSSIA",
              2, WHITE, 928, gap=4)

    # Footer
    rule(r, 962, 2, INK)
    blit_centred(r, 972, "SOURCES: BBC, REUTERS, AP, NYT - 20 NOV 2026",
                 2, GREY)
    return r


def parse_args(argv=None):
    """Command-line options for the front-page renderer.

    --output picks the directory that receives entry.png (it wins over
    MAKEFUN_OUTPUT_DIR); --check skips drawing and only inspects a PNG
    that is already on disk, so a finished page can be re-examined
    without redrawing it.
    """
    parser = argparse.ArgumentParser(
        description="Draw the 20 Nov 2026 front page as entry.png.")
    parser.add_argument("--output", metavar="DIR",
                        help="directory to write entry.png into")
    parser.add_argument("--check", action="store_true",
                        help="only verify an existing entry.png")
    return parser.parse_args(argv)


def verify_output(path):
    """Read a finished PNG back and check it looks like our page.

    Confirms the PNG signature, the IHDR width and height, and that the
    file is neither empty nor implausibly large for a 1024x1024 page.
    Prints one line per check and returns True when all of them pass.
    """
    with open(path, "rb") as f:
        data = f.read()
    ok = True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        print("signature: OK")
    else:
        print("signature: BAD")
        ok = False
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) == (W, H):
        print("dimensions: OK (%dx%d)" % (width, height))
    else:
        print("dimensions: BAD (%dx%d)" % (width, height))
        ok = False
    size = len(data)
    if 1000 < size < 1000000:
        print("file size: OK (%d bytes)" % size)
    else:
        print("file size: BAD (%d bytes)" % size)
        ok = False
    return ok


def print_stats(path):
    """Print a few facts about the page that was just drawn.

    Word count of the module docstring, glyph count of the pixel font,
    and the size of the raster buffer, next to the finished file size.
    Nothing here touches the drawing itself.
    """
    print("docstring words: %d" % len(__doc__.split()))
    print("font glyphs: %d" % len(GLYPHS))
    print("raster buffer: %d bytes" % (W * H * 3))
    print("entry.png: %d bytes" % os.path.getsize(path))


def main():
    args = parse_args()
    out_dir = args.output or os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    if args.check:
        if not os.path.exists(path):
            print("missing: %s" % path)
            sys.exit(1)
        sys.exit(0 if verify_output(path) else 1)
    write_png(draw_page(), path)
    verify_output(path)
    print_stats(path)


if __name__ == "__main__":
    main()
