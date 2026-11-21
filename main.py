"""VELMORA — a travel poster for a place that isn't there.

Pure-stdlib Python. Draws a 1024x1024 poster of a quiet cliff town with one
white tide tower, then writes it to /output/entry.png with a hand-rolled PNG
encoder (zlib + struct). No network, no randomness, no clock: run it twice
and the bytes are identical.
"""

import os
import struct
import sys
import zlib

# 5x7 bitmap font. Each glyph is 7 rows of 5 cells, "#" = ink, "." = blank.
# Hand-drawn for this poster; capitals, digits and a little punctuation.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
}

W = 1024
H = 1024

INK = (38, 50, 64)          # dark slate, for type and outlines
CREAM = (238, 228, 205)     # tower walls, sails, paper
SAND = (232, 214, 178)      # beach


def lerp(a, b, t):
    """Blend two RGB colours; t in [0, 1]."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_canvas():
    """A blank RGB canvas as a flat bytearray, row-major."""
    return bytearray(W * H * 3)


def put(px, x, y, colour):
    """Set one pixel, silently ignoring out-of-bounds writes."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = colour[0]
        px[i + 1] = colour[1]
        px[i + 2] = colour[2]


def blend(px, x, y, colour, alpha):
    """Paint a translucent pixel over what is already there."""
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        for c in range(3):
            px[i + c] = int(px[i + c] + (colour[c] - px[i + c]) * alpha)


def hline(px, x0, x1, y, colour):
    """A horizontal run of pixels, clipped to the canvas."""
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    for x in range(x0, x1 + 1):
        put(px, x, y, colour)


def rect(px, x0, y0, x1, y1, colour):
    """A filled axis-aligned rectangle."""
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(px, x0, x1, y, colour)


def vgrad(px, y0, y1, top, bottom):
    """Fill rows y0..y1 with a vertical colour gradient."""
    span = max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        hline(px, 0, W - 1, y, lerp(top, bottom, (y - y0) / span))


def disc(px, cx, cy, r, colour, alpha=1.0):
    """A filled circle, optionally translucent."""
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        for x in range(cx - dx, cx + dx + 1):
            if alpha >= 1.0:
                put(px, x, cy + dy, colour)
            else:
                blend(px, x, cy + dy, colour, alpha)


def poly(px, points, colour):
    """Fill a simple polygon with a scanline pass."""
    ys = [p[1] for p in points]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        nodes = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                nodes.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
        nodes.sort()
        for i in range(0, len(nodes) - 1, 2):
            hline(px, nodes[i], nodes[i + 1], y, colour)


def text_width(text, scale):
    """Pixel width of a string at a given font scale."""
    return len(text) * 6 * scale - scale


def draw_text(px, text, x, y, scale, colour):
    """Draw a string, top-left anchored, at a whole-number scale."""
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    rect(px, cx + col * scale, y + row * scale,
                         cx + col * scale + scale - 1,
                         y + row * scale + scale - 1, colour)
        cx += 6 * scale


def draw_centered(px, text, y, scale, colour):
    """Draw a string centred horizontally at height y."""
    draw_text(px, text, (W - text_width(text, scale)) // 2, y, scale, colour)

RIM = (104, 118, 132)        # pale edge on the cliff top
SEA_LIGHT = (150, 196, 190)
SEA_DEEP = (24, 70, 84)
GOLD = (255, 238, 190)


def draw_scene(px):
    """Paint the whole poster onto the canvas."""
    # Sky: pale blue-grey down to warm gold at the horizon.
    vgrad(px, 0, 300, (188, 210, 224), (246, 222, 182))
    vgrad(px, 300, 560, (246, 222, 182), (252, 196, 138))

    # Low sun, soft glow first so the disc sits on top of it.
    disc(px, 610, 480, 96, GOLD, 0.16)
    disc(px, 610, 480, 68, GOLD, 0.28)
    disc(px, 610, 480, 46, GOLD)

    # Three birds, high and far away.
    for bx, by in ((250, 180), (310, 150), (830, 210)):
        for k in range(8):
            put(px, bx - k, by + k, INK)
            put(px, bx + k, by + k, INK)

    # Sea: light at the horizon, deep toward the viewer.
    vgrad(px, 560, 860, SEA_LIGHT, SEA_DEEP)

    # Sunlight broken on the water, widening toward the viewer.
    for y in range(592, 841, 28):
        half = 20 + (y - 560) // 2
        for x in range(610 - half, 610 + half + 1):
            blend(px, x, y, (250, 220, 170), 0.5)
            blend(px, x, y + 1, (250, 220, 170), 0.5)

    # A few quiet streaks of light elsewhere on the water.
    for sx, sy, sw in ((200, 640, 90), (850, 690, 120),
                       (120, 760, 70), (900, 780, 90)):
        for x in range(sx, sx + sw):
            blend(px, x, sy, (140, 185, 180), 0.30)

    # The headland: one dark ridge, sea behind it, beach below.
    ridge = [(0, 712), (150, 668), (300, 700), (420, 648),
             (560, 692), (700, 646), (860, 700), (1024, 664)]
    poly(px, ridge + [(1024, 860), (0, 860)], (46, 58, 70))
    for (x0, y0), (x1, y1) in zip(ridge, ridge[1:]):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            x = int(x0 + (x1 - x0) * s / steps)
            y = int(y0 + (y1 - y0) * s / steps)
            put(px, x, y, RIM)
            put(px, x, y + 1, RIM)

    # The tide tower: one white tower, one green lamp, on the ridge.
    rect(px, 680, 430, 724, 650, CREAM)
    for band in (470, 510, 550, 590):
        rect(px, 680, band, 724, band + 6, INK)
    rect(px, 672, 644, 732, 652, INK)
    rect(px, 688, 408, 716, 430, (30, 44, 56))
    disc(px, 702, 410, 13, (30, 44, 56))
    disc(px, 702, 420, 16, (120, 220, 140), 0.30)
    disc(px, 702, 420, 5, (120, 220, 140))

    # A small sailboat on the water, the only other thing moving.
    poly(px, [(270, 626), (330, 626), (318, 640), (282, 640)], (30, 44, 56))
    rect(px, 299, 584, 300, 626, INK)
    poly(px, [(302, 588), (302, 624), (336, 624)], CREAM)

    # Beach: pale sand, a darker wet band where the sea lets go.
    vgrad(px, 860, 1024, SAND, (206, 182, 142))
    rect(px, 0, 860, 1023, 876, (196, 172, 132))

    # One person standing on the sand, looking at the tower.
    hline(px, 488, 512, 942, (180, 158, 118))
    disc(px, 500, 890, 6, INK)
    rect(px, 495, 896, 505, 924, INK)
    rect(px, 495, 924, 498, 940, INK)
    rect(px, 502, 924, 505, 940, INK)

    # Type: name, rule, where it is, and the invitation.
    draw_centered(px, "VELMORA", 60, 9, INK)
    rect(px, 372, 140, 652, 142, INK)
    poly(px, [(512, 136), (517, 141), (512, 146), (507, 141)], INK)
    draw_centered(px, "THE FAR COAST", 168, 3, INK)
    draw_centered(px, "WHERE THE TIDE COMES TO STAY", 962, 4, INK)

    # A thin dark frame, to hold the whole poster together.
    rect(px, 0, 0, 1023, 7, INK)
    rect(px, 0, 1016, 1023, 1023, INK)
    rect(px, 0, 0, 7, 1023, INK)
    rect(px, 1016, 0, 1023, 1023, INK)

def _chunk(kind, data):
    """One PNG chunk: length, type, data, CRC32."""
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, px):
    """Encode the canvas as a plain RGB PNG, filter 0 on every row."""
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    canvas = make_canvas()
    draw_scene(canvas)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, canvas)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
