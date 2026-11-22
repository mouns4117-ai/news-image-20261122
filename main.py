#!/usr/bin/env python3
"""news-image-20261122: render a 1024x1024 front-page poster summing up
Sunday 22 November 2026 in one image, and write it to /output/entry.png.

Python 3.13 standard library only; no network; deterministic: two runs
write identical bytes.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (20, 24, 30)
NAVY = (18, 33, 61)
NAVY2 = (28, 48, 88)
GOLD = (198, 148, 52)
RED = (178, 44, 36)
TEAL = (24, 110, 104)
SKY = (168, 205, 226)
LEAF = (72, 140, 66)
SAND = (224, 205, 168)
GREY = (110, 112, 118)
LIGHT = (232, 226, 212)
WHITE = (255, 255, 255)
BLUE = (52, 96, 158)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows, each a 5-bit number (bit 4 = leftmost column).
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "*": (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    "_": (0, 0, 0, 0, 0, 0, 0x1F),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "@": (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
}

# ------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, filled=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d2 <= r * r:
                        self.set(xx, yy, c)
                else:
                    if abs(d2 - r * r) <= r * 2:
                        self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            self.circle(cx, cy, r - k, c, filled=False)

    def triangle(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin, ymax = min(y0, y1, y2), max(y0, y1, y2)
        for yy in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by):
                    xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.set(xx, yy, c)

    # ------------------------------------------------------------ text
    def glyph(self, x, y, ch, s, c):
        rows = FONT.get(ch.upper(), FONT["?"])
        for r, bits in enumerate(rows):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    self.fill(x + col * s, y + r * s, s, s, c)

    def text(self, x, y, s, c, msg):
        cx = x
        for ch in msg:
            self.glyph(cx, y, ch, s, c)
            cx += 6 * s
        return cx

    def text_w(self, s, msg):
        return len(msg) * 6 * s - s

    def centre(self, cx, y, s, c, msg):
        self.text(cx - self.text_w(s, msg) // 2, y, s, c, msg)

    def wrap(self, msg, s, maxw):
        """Word-wrap msg into lines of at most maxw pixels at scale s."""
        words = msg.split(" ")
        lines, cur = [], ""
        for wd in words:
            trial = (cur + " " + wd) if cur else wd
            if self.text_w(s, trial) <= maxw:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, c, msg, maxw, leading=None):
        ld = leading if leading is not None else 10 * s
        for ln in self.wrap(msg, s, maxw):
            self.text(x, y, s, c, ln)
            y += ld
        return y


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ------------------------------------------------------- story artwork
def draw_globe(cv, cx, cy, r):
    """Stylised planet: blue disc, green land blobs, gold sun behind."""
    cv.circle(cx - 26, cy - 30, 16, GOLD)
    cv.circle(cx, cy, r, BLUE)
    cv.circle(cx, cy, r, SKY, filled=False)
    # land blobs
    cv.circle(cx - 22, cy - 18, 14, LEAF)
    cv.circle(cx + 18, cy + 6, 17, LEAF)
    cv.circle(cx + 4, cy - 26, 10, LEAF)
    cv.circle(cx - 8, cy + 24, 11, LEAF)
    cv.circle(cx + 28, cy - 20, 8, LEAF)
    # orbit ring
    cv.ring(cx, cy, r + 8, GOLD, 2)


def draw_burst(cv, x, y, s):
    """Explosion / strike starburst."""
    cx, cy, r = x + 22, y + 20, 22
    c = RED
    for k in range(8):
        ang = k * 3.14159 / 4
        import math
        r2 = r * (1.0 if k % 2 == 0 else 0.55)
        x2 = int(cx + r2 * math.cos(ang))
        y2 = int(cy + r2 * math.sin(ang))
        cv.line(cx, cy, x2, y2, c)
    cv.circle(cx, cy, r // 3, c)


def draw_ship(cv, x, y, s):
    """Small cargo ship on waves."""
    cv.fill(x, y + 14 * s // 4, 44 * s // 4, 8 * s // 4, INK)
    cv.fill(x + 6 * s // 4, y + 6 * s // 4, 10 * s // 4, 8 * s // 4, RED)
    cv.fill(x + 20 * s // 4, y + 8 * s // 4, 12 * s // 4, 6 * s // 4, GOLD)
    cv.fill(x + 34 * s // 4, y + 4 * s // 4, 4 * s // 4, 10 * s // 4, INK)
    for k in range(3):
        cv.line(x - 4 + k * 18, y + 26 * s // 4, x + 12 + k * 18, y + 26 * s // 4, BLUE)


def draw_flags(cv, x, y, s):
    """Two crossed flags on poles."""
    cv.line(x + 8, y, x + 8, y + 34 * s // 4, INK)
    cv.line(x + 30, y, x + 30, y + 34 * s // 4, INK)
    cv.triangle([(x + 8, y), (x + 28, y + 6), (x + 8, y + 12)], (255, 153, 51))
    cv.triangle([(x + 30, y), (x + 50, y + 6), (x + 30, y + 12)], (0, 104, 71))


def draw_bat(cv, x, y, s):
    """Cricket bat and ball."""
    cv.line(x + 6, y + 26 * s // 4, x + 26, y + 2 * s // 4, INK)
    cv.fill(x + 20, y, 12 * s // 4, 8 * s // 4, SAND)
    cv.circle(x + 38, y + 26, 7, RED)
    cv.hline(x, y + 34 * s // 4, 48 * s // 4, LEAF, 3)


def draw_shield(cv, x, y, s):
    """Shield / alliance emblem."""
    cv.triangle([(x + 22, y), (x + 44, y + 8), (x + 22, y + 44)], NAVY2)
    cv.triangle([(x, y), (x + 22, y), (x + 22, y + 44)], BLUE)
    cv.circle(x + 22, y + 18, 6, WHITE)


# ------------------------------------------------------------ poster
def build():
    cv = Canvas(W, H, PAPER)

    # --- masthead
    cv.fill(0, 0, W, 118, NAVY)
    cv.hline(0, 118, W, GOLD, 5)
    cv.centre(W // 2, 22, 6, WHITE, "THE WORLD IN ONE IMAGE")
    cv.centre(W // 2, 76, 3, GOLD, "SUNDAY, 22 NOVEMBER 2026")

    # --- lead story: COP31
    lx, ly, lw, lh = 36, 146, 952, 300
    cv.fill(lx, ly, lw, lh, WHITE)
    cv.vline(lx, ly, lh, GOLD, 6)
    cv.fill(lx + 300, ly, 2, lh, LIGHT)
    # artwork: globe + sun over a green horizon
    draw_globe(cv, lx + 150, ly + 130, 74)
    cv.fill(lx + 300, ly + 236, lw - 300, 4, LEAF)
    cv.text(lx + 330, ly + 18, 2, RED, "LEAD  -  CLIMATE")
    cv.para(lx + 330, ly + 48, 4, INK,
            "COP31 NEARS A DEAL", lw - 360)
    cv.para(lx + 330, ly + 108, 2, INK,
            "After talks ran past their Friday deadline and through the "
            "night, summit presidents put a new package to nearly 200 "
            "nations in Antalya and called a Sunday session to approve it.",
            lw - 360)
    cv.text(lx + 330, ly + 252, 2, GREY, "REUTERS  -  ANTALYA, TURKIYE")

    # --- five more stories: 2 x 2 grid + one wide strip
    stories = [
        ("WAR IN UKRAINE",
         "Russian strikes kill at least two across Ukraine",
         "Overnight attacks hit towns across the country; Kyiv counts "
         "the dead at dawn.",
         "WIRE REPORTS", draw_burst),
        ("BALTIC SEA",
         "Drones hit Russian ship; Finland tightens security",
         "A merchant ship burned after a likely drone hit; Helsinki "
         "tightens security.",
         "YLE / TIMES OF INDIA", draw_ship),
        ("WASHINGTON",
         "Pentagon curbs US-Canada military ties",
         "Defence chief Hegseth limits informal contact between US "
         "and Canadian troops.",
         "WIRE REPORTS", draw_shield),
        ("SOUTH ASIA",
         "Nepal's PM arrives in Delhi for first visit",
         "Rapper-turned-premier Balendra Shah starts a two-day state "
         "visit; Modi talks follow.",
         "REUTERS", draw_flags),
    ]
    gx, gy = 36, 470
    cw, ch, gap = 468, 196, 16
    for i, (kicker, head, deck, src, art) in enumerate(stories):
        x = gx + (i % 2) * (cw + gap)
        y = gy + (i // 2) * (ch + gap)
        cv.fill(x, y, cw, ch, WHITE)
        cv.hline(x, y, cw, GOLD, 4)
        art(cv, x + 18, y + 34, 4)
        cv.text(x + 96, y + 16, 2, RED, kicker)
        y2 = cv.para(x + 96, y + 44, 2, INK, head, cw - 116, leading=20)
        cv.para(x + 96, y2 + 8, 2, INK, deck, cw - 116, leading=18)
        cv.text(x + 96, y + ch - 26, 2, GREY, src)

    # --- wide strip: cricket
    sx, sy, sw, sh = 36, 878, 952, 84
    cv.fill(sx, sy, sw, sh, NAVY2)
    draw_bat(cv, sx + 16, sy + 22, 4)
    cv.text(sx + 92, sy + 14, 2, GOLD, "SPORT  -  WELLINGTON")
    cv.text(sx + sw - 12 - cv.text_w(2, "ESPNCRICINFO"), sy + 14, 2,
            GOLD, "ESPNCRICINFO")
    cv.para(sx + 92, sy + 42, 2, WHITE,
            "India press on in the Wellington Test: Pant's hundred takes "
            "the tourists to 589/5, a lead of 221 over New Zealand.",
            sw - 120, leading=20)

    # --- footer
    cv.hline(36, 986, 952, GOLD, 3)
    cv.centre(W // 2, 996, 1, GREY,
              "SOURCES: REUTERS - AP - BBC - ESPNCRICINFO - THE HINDU BUSINESSLINE")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    for name in os.listdir(outdir):
        path = os.path.join(outdir, name)
        if os.path.isfile(path):
            os.remove(path)
    cv = build()
    data = png_bytes(cv)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()

