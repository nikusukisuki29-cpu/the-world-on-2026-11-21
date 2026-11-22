#!/usr/bin/env python3
"""The world on Saturday 21 November 2026, in one picture.

Standard library only. Reads art.png (next to this file), decodes it with
zlib + scanline unfiltering, cuts the five motifs out, scales each one into a
big circular "globe", and letters every headline with a stroke font drawn in
code. Writes /output/entry.png (fallback ./output/entry.png), deterministic.
"""
import math
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
W = H = 1024
WHITE = (255, 255, 255)
BLACK = (14, 14, 14)
RED = (227, 18, 11)  # #E3120B

# Globe circle.
CX, CY, CR = 512.0, 630.0, 376.0


# --------------------------------------------------------------------------
# PNG decoding (stdlib only)
# --------------------------------------------------------------------------

def _add_bytes(x, y, n):
    """Byte-wise (x + y) mod 256 on two equal-length rows, via big ints."""
    m7 = int.from_bytes(b"\x7f" * n, "big")
    m8 = int.from_bytes(b"\x80" * n, "big")
    a = int.from_bytes(x, "big")
    b = int.from_bytes(y, "big")
    s = ((a & m7) + (b & m7)) ^ ((a ^ b) & m8)
    return bytearray(s.to_bytes(n, "big"))


def read_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    idat = []
    w = h = depth = ctype = interlace = None
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    if depth != 8 or interlace != 0 or ctype not in (0, 2, 4, 6):
        raise ValueError("unsupported PNG format")
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            line = _add_bytes(line, prev, stride)
        elif f == 3:
            for i in range(bpp):
                line[i] = (line[i] + (prev[i] >> 1)) & 255
            for i in range(bpp, stride):
                line[i] = (line[i] + ((line[i - bpp] + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(bpp):
                line[i] = (line[i] + prev[i]) & 255
            for i in range(bpp, stride):
                a = line[i - bpp]
                b = prev[i]
                c = prev[i - bpp]
                pa = b - c
                pb = a - c
                pc = pa + pb
                if pa < 0:
                    pa = -pa
                if pb < 0:
                    pb = -pb
                if pc < 0:
                    pc = -pc
                if pa <= pb and pa <= pc:
                    line[i] = (line[i] + a) & 255
                elif pb <= pc:
                    line[i] = (line[i] + b) & 255
                else:
                    line[i] = (line[i] + c) & 255
        rows.append(line)
        prev = line
    # Normalise to RGB rows (alpha composited over white).
    out = []
    for line in rows:
        if ctype == 2:
            out.append(bytes(line))
            continue
        rgb = bytearray(w * 3)
        for x in range(w):
            if ctype == 6:
                r, g, b, a = line[4 * x:4 * x + 4]
            elif ctype == 4:
                r = g = b = line[2 * x]
                a = line[2 * x + 1]
            else:
                r = g = b = line[x]
                a = 255
            k = 255 - a
            rgb[3 * x] = (r * a + 255 * k) // 255
            rgb[3 * x + 1] = (g * a + 255 * k) // 255
            rgb[3 * x + 2] = (b * a + 255 * k) // 255
        out.append(bytes(rgb))
    return w, h, out


def _weights(n_src, n_out):
    ratio = n_src / n_out
    res = []
    for o in range(n_out):
        a = o * ratio
        b = a + ratio
        i = int(a)
        ws = []
        while i < b and i < n_src:
            ov = min(b, i + 1) - max(a, i)
            if ov > 1e-9:
                ws.append((i, ov / ratio))
            i += 1
        res.append(ws)
    return res


def resample(rows, box, scale):
    """Area-average the crop box (x0, y0, x1, y1) by `scale`.

    Returns (w, h, pixels) where pixels is a list of rows of (r, g, b) floats.
    """
    x0, y0, x1, y1 = box
    sw, sh = x1 - x0, y1 - y0
    ow = max(1, int(round(sw * scale)))
    oh = max(1, int(round(sh * scale)))
    wx = _weights(sw, ow)
    wy = _weights(sh, oh)
    hrows = []
    for y in range(y0, y1):
        row = rows[y]
        rr = row[3 * x0:3 * x1:3]
        gg = row[3 * x0 + 1:3 * x1:3]
        bb = row[3 * x0 + 2:3 * x1:3]
        hr = []
        hg = []
        hb = []
        for ws in wx:
            sr = sg = sb = 0.0
            for i, wgt in ws:
                sr += rr[i] * wgt
                sg += gg[i] * wgt
                sb += bb[i] * wgt
            hr.append(sr)
            hg.append(sg)
            hb.append(sb)
        hrows.append((hr, hg, hb))
    out = []
    for ws in wy:
        acc_r = [0.0] * ow
        acc_g = [0.0] * ow
        acc_b = [0.0] * ow
        for j, wgt in ws:
            hr, hg, hb = hrows[j]
            for x in range(ow):
                acc_r[x] += hr[x] * wgt
                acc_g[x] += hg[x] * wgt
                acc_b[x] += hb[x] * wgt
        out.append(list(zip(acc_r, acc_g, acc_b)))
    return ow, oh, out


def duotone(r, g, b):
    """Re-ink an RGB pixel as white paper + black ink + #E3120B ink."""
    q = (r - g) / (RED[0] - RED[1])
    if q < 0.0:
        q = 0.0
    elif q > 1.0:
        q = 1.0
    paper = (g - RED[1] * q) / 255.0
    if paper < 0.0:
        paper = 0.0
    if paper > 1.0 - q:
        paper = 1.0 - q
    k = 1.0 - q - paper
    return (255 * paper + RED[0] * q + BLACK[0] * k,
            255 * paper + RED[1] * q + BLACK[1] * k,
            255 * paper + RED[2] * q + BLACK[2] * k)


# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(b"\xff" * (w * h * 3))

    def blend(self, cov, color):
        px = self.px
        cr, cg, cb = color
        for idx, a in cov.items():
            o = idx * 3
            if a >= 1.0:
                px[o] = cr
                px[o + 1] = cg
                px[o + 2] = cb
            else:
                ia = 1.0 - a
                px[o] = int(px[o] * ia + cr * a + 0.5)
                px[o + 1] = int(px[o + 1] * ia + cg * a + 0.5)
                px[o + 2] = int(px[o + 2] * ia + cb * a + 0.5)

    def rect(self, x0, y0, x1, y1, color):
        cov = {}
        for y in range(y0, y1):
            for x in range(x0, x1):
                cov[y * self.w + x] = 1.0
        self.blend(cov, color)

    def multiply_image(self, img, ox, oy, clip):
        """Multiply-composite a float RGB image at (ox, oy), clipped by clip()."""
        iw, ih, pix = img
        px = self.px
        for j in range(ih):
            y = oy + j
            if y < 0 or y >= self.h:
                continue
            row = pix[j]
            for i in range(iw):
                x = ox + i
                if x < 0 or x >= self.w:
                    continue
                r, g, b = row[i]
                if r > 253.5 and g > 253.5 and b > 253.5:
                    continue
                a = clip(x + 0.5, y + 0.5)
                if a <= 0.0:
                    continue
                r, g, b = duotone(r, g, b)
                o = (y * self.w + x) * 3
                px[o] = int(px[o] * (1.0 - a * (1.0 - r / 255.0)) + 0.5)
                px[o + 1] = int(px[o + 1] * (1.0 - a * (1.0 - g / 255.0)) + 0.5)
                px[o + 2] = int(px[o + 2] * (1.0 - a * (1.0 - b / 255.0)) + 0.5)

    def to_png(self):
        rows = []
        stride = self.w * 3
        px = self.px
        prev = bytes(stride)
        for y in range(self.h):
            line = px[y * stride:(y + 1) * stride]
            # Filter "Up" (type 2): cheap, deterministic, compresses well here.
            diff = bytearray(stride)
            for i in range(stride):
                diff[i] = (line[i] - prev[i]) & 255
            rows.append(b"\x02" + bytes(diff))
            prev = line
        raw = b"".join(rows)

        def chunk(typ, body):
            crc = zlib.crc32(typ + body) & 0xFFFFFFFF
            return struct.pack(">I", len(body)) + typ + body + struct.pack(">I", crc)

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def circle_alpha(x, y):
    d = math.hypot(x - CX, y - CY)
    a = CR - d + 0.5
    if a >= 1.0:
        return 1.0
    return a if a > 0.0 else 0.0


def no_clip(x, y):
    return 1.0


# --------------------------------------------------------------------------
# Stroke font: glyphs on a grid 0..width x 0..10 (y down, 10 = baseline)
# --------------------------------------------------------------------------

def arc(cx, cy, rx, ry, a0, a1, step=10.0):
    n = max(3, int(abs(a1 - a0) / step + 0.999))
    pts = []
    for k in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


def stadium(x0, x1, top, bot):
    r = (x1 - x0) / 2.0
    c = (x0 + x1) / 2.0
    return (arc(c, top + r, r, r, 180, 360) + [(x1, bot - r)]
            + arc(c, bot - r, r, r, 0, 180) + [(x0, top + r)])


def _build_font():
    g = {}
    g["A"] = (6, [[(0, 10), (3, 0), (6, 10)], [(1.05, 6.5), (4.95, 6.5)]])
    g["B"] = (6, [[(0, 5), (3.4, 5)] + arc(3.4, 7.5, 2.6, 2.5, -90, 90)
                  + [(0, 10), (0, 0), (3.1, 0)] + arc(3.1, 2.5, 2.4, 2.5, -90, 90)])
    g["C"] = (6, [arc(3, 3, 3, 3, 335, 180) + arc(3, 7, 3, 3, 180, 25)])
    g["D"] = (6, [[(0, 0), (2.8, 0)] + arc(2.8, 3.2, 3.2, 3.2, 270, 360)
                  + arc(2.8, 6.8, 3.2, 3.2, 0, 90) + [(0, 10), (0, 0)]])
    g["E"] = (5.4, [[(5.4, 0), (0, 0), (0, 10), (5.4, 10)], [(0, 4.9), (4.6, 4.9)]])
    g["F"] = (5.4, [[(5.4, 0), (0, 0), (0, 10)], [(0, 4.9), (4.6, 4.9)]])
    g["G"] = (6, [arc(3, 3, 3, 3, 335, 180) + arc(3, 7, 3, 3, 180, 0)
                  + [(6, 5.2), (3.4, 5.2)]])
    g["H"] = (6, [[(0, 0), (0, 10)], [(6, 0), (6, 10)], [(0, 5), (6, 5)]])
    g["I"] = (0, [[(0, 0), (0, 10)]])
    g["J"] = (5.4, [[(5.4, 0), (5.4, 7.3)] + arc(2.7, 7.3, 2.7, 2.7, 0, 165)])
    g["K"] = (6, [[(0, 0), (0, 10)], [(6, 0), (0, 6.3)], [(2.2, 4.0), (6, 10)]])
    g["L"] = (5.2, [[(0, 0), (0, 10), (5.2, 10)]])
    g["M"] = (7.4, [[(0, 10), (0, 0), (3.7, 7.2), (7.4, 0), (7.4, 10)]])
    g["N"] = (6, [[(0, 10), (0, 0), (6, 10), (6, 0)]])
    g["O"] = (6, [stadium(0, 6, 0, 10)])
    g["P"] = (6, [[(0, 10), (0, 0), (3.2, 0)] + arc(3.2, 2.8, 2.8, 2.8, -90, 90)
                  + [(0, 5.6)]])
    g["Q"] = (6, [stadium(0, 6, 0, 10), [(3.6, 7.2), (6.2, 10.4)]])
    g["R"] = (6, [[(0, 10), (0, 0), (3.2, 0)] + arc(3.2, 2.8, 2.8, 2.8, -90, 90)
                  + [(0, 5.6)], [(2.9, 5.6), (6, 10)]])
    g["S"] = (6, [arc(3, 2.5, 3, 2.5, 330, 90) + arc(3, 7.5, 3, 2.5, 270, 510)])
    g["T"] = (6, [[(0, 0), (6, 0)], [(3, 0), (3, 10)]])
    g["U"] = (6, [[(0, 0)] + arc(3, 7, 3, 3, 180, 0) + [(6, 0)]])
    g["V"] = (6.2, [[(0, 0), (3.1, 10), (6.2, 0)]])
    g["W"] = (8, [[(0, 0), (1.9, 10), (4, 2.6), (6.1, 10), (8, 0)]])
    g["X"] = (6, [[(0, 0), (6, 10)], [(6, 0), (0, 10)]])
    g["Y"] = (6.2, [[(0, 0), (3.1, 5.2), (6.2, 0)], [(3.1, 5.2), (3.1, 10)]])
    g["Z"] = (5.6, [[(0, 0), (5.6, 0), (0, 10), (5.6, 10)]])
    g["0"] = (6, [stadium(0, 6, 0, 10)])
    g["1"] = (3.6, [[(0, 2.2), (3.0, 0), (3.0, 10)]])
    g["2"] = (6, [arc(3, 3, 3, 3, 190, 380) + [(0, 10), (6, 10)]])
    g["3"] = (6, [arc(3, 2.5, 2.8, 2.5, 200, 450) + arc(3, 7.5, 3, 2.5, 270, 520)])
    g["4"] = (6, [[(4.6, 10), (4.6, 0), (0, 7), (6, 7)]])
    g["5"] = (6, [[(5.6, 0), (0.5, 0), (0.2, 4.6)] + arc(2.9, 6.9, 3.1, 3.1, 235, 515)])
    g["6"] = (6, [arc(3, 3, 3, 3, 330, 180) + [(0, 7)] + arc(3, 7, 3, 3, 180, 540)])
    g["7"] = (6, [[(0, 0), (6, 0), (2.2, 10)]])
    g["8"] = (6, [arc(3, 2.55, 2.65, 2.55, 90, 450), arc(3, 7.4, 3, 2.6, -90, 270)])
    g["9"] = (6, [arc(3, 3, 3, 3, 0, 360) + [(6, 7)] + arc(3, 7, 3, 3, 0, 150)])
    g["-"] = (3.4, [[(0, 5.6), (3.4, 5.6)]])
    g["·"] = (0, [[(0, 5.2), (0, 5.2)]])
    g["."] = (0, [[(0, 10), (0, 10)]])
    g[","] = (0.8, [[(0.8, 9.6), (0, 11.8)]])
    g["%"] = (7, [[(0.4, 10), (6.6, 0)], arc(1.5, 2.0, 1.5, 2.0, 0, 360),
                  arc(5.5, 8.0, 1.5, 2.0, 0, 360)])
    g["&"] = (6.6, [[(6.6, 10), (1.5, 3.9)] + arc(2.9, 2.3, 1.9, 2.3, 140, 400)
                    + arc(2.9, 7.6, 2.5, 2.4, 200, -15) + [(6.4, 5.6)]])
    g[" "] = (4.2, [])
    return g


FONT = _build_font()


class Style:
    def __init__(self, cap, stroke, cond=1.0, track=None):
        self.cap = float(cap)
        self.stroke = float(stroke)
        self.cond = cond
        self.unit = (self.cap - self.stroke) / 10.0
        self.track = self.stroke * 0.55 if track is None else track

    def advance(self, ch):
        uw = FONT[ch][0]
        if ch == " ":
            return uw * self.unit * self.cond
        return uw * self.unit * self.cond + self.stroke + self.track

    def width(self, text):
        if not text:
            return 0.0
        return sum(self.advance(c) for c in text) - self.track


def text_segments(text, style, x, y):
    """Line segments (px) for `text` with its cap-top-left at (x, y)."""
    segs = []
    half = style.stroke / 2.0
    u = style.unit
    sx = u * style.cond
    pen = x
    for ch in text:
        uw, polys = FONT[ch]
        for poly in polys:
            pts = [(pen + half + px * sx, y + half + py * u) for px, py in poly]
            if len(pts) == 1:
                pts = pts * 2
            for k in range(len(pts) - 1):
                segs.append(pts[k] + pts[k + 1])
        pen += style.advance(ch)
    return segs


def rasterize(segs, radius, cov, w=W, h=H):
    for x1, y1, x2, y2 in segs:
        minx = max(0, int(math.floor(min(x1, x2) - radius - 1)))
        maxx = min(w - 1, int(math.ceil(max(x1, x2) + radius + 1)))
        miny = max(0, int(math.floor(min(y1, y2) - radius - 1)))
        maxy = min(h - 1, int(math.ceil(max(y1, y2) + radius + 1)))
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx * dx + dy * dy
        lim = radius + 0.5
        for py in range(miny, maxy + 1):
            cy = py + 0.5
            base = py * w
            for px in range(minx, maxx + 1):
                cx = px + 0.5
                if l2 > 0.0:
                    t = ((cx - x1) * dx + (cy - y1) * dy) / l2
                    if t < 0.0:
                        t = 0.0
                    elif t > 1.0:
                        t = 1.0
                    ex = x1 + t * dx - cx
                    ey = y1 + t * dy - cy
                else:
                    ex = x1 - cx
                    ey = y1 - cy
                d = math.sqrt(ex * ex + ey * ey)
                a = lim - d
                if a <= 0.0:
                    continue
                if a > 1.0:
                    a = 1.0
                idx = base + px
                if cov.get(idx, 0.0) < a:
                    cov[idx] = a


def draw_text(cv, text, style, x, y, color, align="center", halo=0.0):
    """Draw text; x is the centre (align=center) or left edge; y is cap top."""
    tw = style.width(text)
    if align == "center":
        x = x - tw / 2.0
    elif align == "right":
        x = x - tw
    segs = text_segments(text, style, x, y)
    if halo > 0:
        hc = {}
        rasterize(segs, style.stroke / 2.0 + halo, hc)
        cv.blend(hc, WHITE)
    cov = {}
    rasterize(segs, style.stroke / 2.0, cov)
    cv.blend(cov, color)
    return tw


def fit_cond(text, cap, stroke, target, track=None):
    """Horizontal condense factor that makes `text` exactly `target` wide."""
    s = Style(cap, stroke, 1.0, track)
    units = sum(FONT[c][0] for c in text)
    fixed = s.width(text) - units * s.unit
    return (target - fixed) / (units * s.unit)


# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------

# Motif crops in art.png pixels -> scale and top-left placement on the page.
MOTIFS = [
    # COP31: globe + thermometer + melting ice (top centre)
    {"box": (570, 125, 1028, 705), "scale": 0.48, "at": (408, 262)},
    # Mexico: handcuffs + police badge (upper left)
    {"box": (105, 388, 570, 812), "scale": 0.46, "at": (160, 400)},
    # Kryvyi Rih: missile, red burst, skyline (upper right)
    {"box": (1030, 340, 1505, 900), "scale": 0.42, "at": (644, 370)},
    # BepiColombo: spacecraft + Mercury (lower left)
    {"box": (135, 862, 715, 1372), "scale": 0.40, "at": (200, 664)},
    # Dengue: mosquito, shield, virus (lower right)
    {"box": (735, 1000, 1450, 1392), "scale": 0.40, "at": (556, 700)},
]

# (headline lines, sublabel lines, centre x, cap-top y)
LABELS = [
    (["COP31 TALKS", "RUN INTO OVERTIME"], ["ANTALYA · NO FOSSIL-FUEL DEAL"], 512, 548),
    (["MEXICO CAPTURES", "CARTEL BOSS"], ["EL CHAPO ISIDRO · FBI MOST WANTED"], 266, 604),
    (["RUSSIAN STRIKE", "HITS KRYVYI RIH"], ["2 KILLED · 60 WOUNDED"], 748, 614),
    (["BEPICOLOMBO", "REACHES MERCURY"], ["8-YEAR VOYAGE · ESA & JAXA"], 406, 874),
    (["MOSQUITOES CUT", "DENGUE 69%"], ["BRAZIL TRIAL · 5,700 CHILDREN"], 642, 866),
]

LABEL_STYLE = Style(21, 4.5, 0.70)
SUB_STYLE = Style(11, 2.1, 0.80)


def draw_label(cv, heads, subs, cx, y):
    for line in heads:
        draw_text(cv, line, LABEL_STYLE, cx, y, BLACK, halo=2.5)
        y += LABEL_STYLE.cap + 5.5
    y += 2
    for line in subs:
        draw_text(cv, line, SUB_STYLE, cx, y, RED, halo=2.0)
        y += SUB_STYLE.cap + 4


def compose():
    cv = Canvas(W, H)

    # Masthead: small solid red block with a white caption.
    cap_style = Style(13, 2.6, 0.9)
    caption = "ONE DAY · ONE PICTURE"
    cw = cap_style.width(caption)
    bx0 = int(512 - cw / 2 - 16)
    bx1 = int(512 + cw / 2 + 16)
    cv.rect(bx0, 14, bx1, 44, RED)
    draw_text(cv, caption, cap_style, 512, 22.5, WHITE)

    # Headline, two lines, heavy and condensed; the date is the biggest thing.
    l1 = "THE WORLD ON"
    l2 = "21 NOVEMBER 2026"
    s1 = Style(62, 15.5, fit_cond(l1, 62, 15.5, 500, 4.5), 4.5)
    s2 = Style(84, 19.0, fit_cond(l2, 84, 19.0, 840, 5.5), 5.5)
    draw_text(cv, l1, s1, 512, 54, BLACK)
    draw_text(cv, l2, s2, 512, 122, BLACK)

    # Teaser line naming the five stories.
    teaser = ("MEXICO CARTEL ARREST · KRYVYI RIH STRIKE · COP31 OVERTIME · "
              "BEPICOLOMBO AT MERCURY · DENGUE CUT 69%")
    ts = Style(12, 2.2, fit_cond(teaser, 12, 2.2, 880), None)
    draw_text(cv, teaser, ts, 512, 223, BLACK)

    # Art: decode, cut out each motif, scale, multiply into the globe.
    _, _, rows = read_png(os.path.join(HERE, "art.png"))
    for m in MOTIFS:
        img = resample(rows, m["box"], m["scale"])
        cv.multiply_image(img, m["at"][0], m["at"][1], circle_alpha)
    del rows

    for heads, subs, cx, y in LABELS:
        draw_label(cv, heads, subs, cx, y)

    # Footer inside the bottom of the globe.
    fs = Style(10.5, 2.1, 0.80)
    draw_text(cv, "SATURDAY · FIVE STORIES · ONE DAY", fs, 512, 972, BLACK)

    # Globe outline.
    ring = {}
    rasterize(arc_segments(CX, CY, CR, 360), 2.0, ring)
    cv.blend(ring, BLACK)
    return cv


def arc_segments(cx, cy, r, n):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
           for k in range(n + 1)]
    return [pts[k] + pts[k + 1] for k in range(n)]


def main():
    png = compose().to_png()
    for d in ("/output", os.path.join(HERE, "output")):
        try:
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, "entry.png")
            with open(path, "wb") as fh:
                fh.write(png)
            os.chmod(path, 0o644)
            print("wrote", path, len(png), "bytes")
            return
        except OSError:
            continue
    raise SystemExit("could not write entry.png")


if __name__ == "__main__":
    main()
