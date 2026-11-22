#!/usr/bin/env python3
"""The world on Saturday 21 November 2026, in one picture.

Standard library only. The poster itself (lettering included) was generated
ahead of time and committed as poster.png next to this file; this program is
a faithful carrier. It decodes poster.png with zlib + scanline unfiltering,
composites any transparency onto white, box-averages it down to fit
1024 x 1024 if needed, and re-encodes it as an 8-bit RGB PNG with fixed
settings at /output/entry.png (fallback ./output/entry.png), guaranteed to
be at most 1 MiB. Same input, same bytes out: no randomness, no timestamps.
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "poster.png")
MAX_SIDE = 1024
MAX_BYTES = 1048576
ZLIB_LEVEL = 9
PNG_SIG = b"\x89PNG\r\n\x1a\n"

# Colour type -> samples per pixel.
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


# --------------------------------------------------------------------------
# PNG decoding
# --------------------------------------------------------------------------

def read_chunks(data):
    """Yield (type, body) for every chunk, checking length and CRC."""
    if data[:8] != PNG_SIG:
        raise ValueError("not a PNG file")
    pos = 8
    while pos + 12 <= len(data):
        length, = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        if len(body) != length or zlib.crc32(ctype + body) != crc:
            raise ValueError("corrupt chunk %r" % ctype)
        yield ctype, body
        pos += 12 + length
        if ctype == b"IEND":
            return
    raise ValueError("PNG ends without IEND")


def unfilter(raw, width, height, bpp, stride):
    """Undo the per-scanline filters; return a list of row bytearrays."""
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if len(line) != stride:
            raise ValueError("image data too short")
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                if i >= bpp:
                    a = line[i - bpp]
                    c = prev[i - bpp]
                else:
                    a = c = 0
                b = prev[i]
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc:
                    pred = a
                elif pb <= pc:
                    pred = b
                else:
                    pred = c
                line[i] = (line[i] + pred) & 255
        elif ftype != 0:
            raise ValueError("bad filter type %d" % ftype)
        rows.append(line)
        prev = line
    return rows


def unpack_low_depth(line, width, depth):
    """Expand 1/2/4-bit samples of one row to one byte per sample."""
    per_byte = 8 // depth
    mask = (1 << depth) - 1
    out = bytearray()
    for byte in line:
        for k in range(per_byte):
            out.append((byte >> (8 - depth * (k + 1))) & mask)
    return out[:width]


def decode_png(data):
    """Return (width, height, rgb) with rgb a bytes object, 3 bytes/pixel."""
    ihdr = None
    palette = None
    trns = None
    idat = []
    for ctype, body in read_chunks(data):
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif ctype == b"PLTE":
            palette = body
        elif ctype == b"tRNS":
            trns = body
        elif ctype == b"IDAT":
            idat.append(body)
    if ihdr is None or not idat:
        raise ValueError("PNG lacks IHDR or IDAT")
    width, height, depth, ctype, comp, filt, interlace = ihdr
    if ctype not in CHANNELS or comp != 0 or filt != 0:
        raise ValueError("unsupported PNG header %r" % (ihdr,))
    if interlace != 0:
        raise ValueError("interlaced PNGs are not supported")
    if depth not in (1, 2, 4, 8, 16) or (depth < 8 and ctype not in (0, 3)):
        raise ValueError("unsupported bit depth %d" % depth)
    if ctype == 3 and palette is None:
        raise ValueError("palette image without PLTE")

    nch = CHANNELS[ctype]
    bits_per_pixel = nch * depth
    bpp = max(1, bits_per_pixel // 8)
    stride = (width * bits_per_pixel + 7) // 8
    rows = unfilter(zlib.decompress(b"".join(idat)), width, height, bpp, stride)

    # Alpha compositing onto white, as a lookup: COMP[a][c].
    comp = [bytes((c * a + 255 * (255 - a) + 127) // 255 for c in range(256))
            for a in range(256)]

    if ctype == 3:
        # Palette entries, already composited onto white.
        alphas = trns or b""
        lut = []
        for i in range(256):
            if 3 * i + 3 <= len(palette):
                r, g, b = palette[3 * i:3 * i + 3]
            else:
                r = g = b = 0
            a = alphas[i] if i < len(alphas) else 255
            lut.append(bytes((comp[a][r], comp[a][g], comp[a][b])))
    key = None
    if trns and ctype in (0, 2):
        # tRNS colour key: matching pixels are fully transparent -> white.
        key = trns[:2] if ctype == 0 else trns[:6]

    out = bytearray()
    for line in rows:
        if depth < 8:
            samples = unpack_low_depth(line, width, depth)
            if ctype == 3:
                out += b"".join(lut[s] for s in samples)
            else:
                scale = 255 // ((1 << depth) - 1)
                keyval = int.from_bytes(key, "big") if key else -1
                for s in samples:
                    v = 255 if s == keyval else s * scale
                    out += bytes((v, v, v))
            continue
        if depth == 16:
            keyed = line
            line = line[0::2]  # high byte of every sample
        else:
            keyed = None
        if ctype == 2:
            if key is None:
                out += line
            else:
                size = 6 if depth == 16 else 3
                src = keyed if depth == 16 else line
                want = key if depth == 16 else bytes(key[1::2])
                for x in range(width):
                    if src[x * size:(x + 1) * size] == want:
                        out += b"\xff\xff\xff"
                    else:
                        out += line[3 * x:3 * x + 3]
        elif ctype == 0:
            if key is None:
                for v in line:
                    out += bytes((v, v, v))
            else:
                size = 2 if depth == 16 else 1
                src = keyed if depth == 16 else line
                want = key if depth == 16 else key[1:2]
                for x in range(width):
                    v = 255 if src[x * size:(x + 1) * size] == want else line[x]
                    out += bytes((v, v, v))
        elif ctype == 3:
            out += b"".join(lut[s] for s in line)
        elif ctype == 4:
            for x in range(width):
                v = comp[line[2 * x + 1]][line[2 * x]]
                out += bytes((v, v, v))
        else:  # ctype == 6
            for x in range(width):
                i = 4 * x
                t = comp[line[i + 3]]
                out += bytes((t[line[i]], t[line[i + 1]], t[line[i + 2]]))
    return width, height, bytes(out)


# --------------------------------------------------------------------------
# Deterministic resampling and quantisation
# --------------------------------------------------------------------------

def box_taps(n, m):
    """Area weights for shrinking n samples to m (m <= n), all integers.

    Output i covers source span [i*n, (i+1)*n) in units of 1/m; source j
    covers [j*m, (j+1)*m). Each output's weights sum to n exactly.
    """
    taps = []
    for i in range(m):
        lo, hi = i * n, (i + 1) * n
        row = []
        for j in range(lo // m, (hi - 1) // m + 1):
            w = min(hi, (j + 1) * m) - max(lo, j * m)
            if w > 0:
                row.append((j, w))
        taps.append(row)
    return taps


def shrink(width, height, rgb, new_w, new_h):
    """Integer box-average an RGB image down to new_w x new_h."""
    if (new_w, new_h) == (width, height):
        return rgb
    stride = 3 * width
    # Vertical pass: weighted sums of whole rows.
    vt = box_taps(height, new_h)
    half_h = height // 2
    rows = []
    for taps in vt:
        acc = [0] * stride
        for j, w in taps:
            src = rgb[j * stride:(j + 1) * stride]
            acc = [a + v * w for a, v in zip(acc, src)]
        rows.append(bytes((a + half_h) // height for a in acc))
    # Horizontal pass, vectorised per tap slot (missing taps weigh 0).
    ht = box_taps(width, new_w)
    slots = max(len(t) for t in ht)
    idx = [[t[k][0] if k < len(t) else 0 for t in ht] for k in range(slots)]
    wts = [[t[k][1] if k < len(t) else 0 for t in ht] for k in range(slots)]
    half_w = width // 2
    out = bytearray(3 * new_w * new_h)
    for y, row in enumerate(rows):
        base = 3 * new_w * y
        for ch in range(3):
            plane = row[ch::3]
            acc = [0] * new_w
            for k in range(slots):
                acc = [a + plane[j] * w for a, j, w in zip(acc, idx[k], wts[k])]
            out[base + ch:base + 3 * new_w:3] = bytes(
                (a + half_w) // width for a in acc)
    return bytes(out)


def fit_size(width, height, limit):
    """Largest size within limit x limit with the same aspect ratio."""
    if width <= limit and height <= limit:
        return width, height
    if width >= height:
        return limit, max(1, (height * limit + width // 2) // width)
    return max(1, (width * limit + height // 2) // height), limit


def quantise(rgb, step):
    """Snap every channel value to the centre of its step-wide bucket."""
    if step <= 1:
        return rgb
    table = bytes(min(255, (v // step) * step + step // 2) for v in range(256))
    return rgb.translate(table)


# --------------------------------------------------------------------------
# PNG encoding
# --------------------------------------------------------------------------

def chunk(ctype, body):
    return (struct.pack(">I", len(body)) + ctype + body
            + struct.pack(">I", zlib.crc32(ctype + body)))


def encode_png(width, height, rgb):
    """8-bit RGB PNG; every row uses filter 2 (Up); zlib level fixed."""
    stride = 3 * width
    raw = bytearray()
    prev = bytes(stride)
    for y in range(height):
        line = rgb[y * stride:(y + 1) * stride]
        raw.append(2)
        raw += bytes((a - b) & 255 for a, b in zip(line, prev))
        prev = line
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (PNG_SIG + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), ZLIB_LEVEL))
            + chunk(b"IEND", b""))


def encode_palette(width, height, rgb):
    """8-bit palette PNG if the image has <= 256 colours, else None.

    The palette is sorted by colour value, so it never depends on pixel order
    or hashing. Rows use filter 0: indices compress best unfiltered.
    """
    colours = set()
    for i in range(0, len(rgb), 3):
        colours.add(rgb[i:i + 3])
        if len(colours) > 256:
            return None
    palette = sorted(colours)
    index = {c: i for i, c in enumerate(palette)}
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        base = 3 * width * y
        raw += bytes(index[rgb[i:i + 3]]
                     for i in range(base, base + 3 * width, 3))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 3, 0, 0, 0)
    return (PNG_SIG + chunk(b"IHDR", ihdr)
            + chunk(b"PLTE", b"".join(palette))
            + chunk(b"IDAT", zlib.compress(bytes(raw), ZLIB_LEVEL))
            + chunk(b"IEND", b""))


def candidates(width, height, rgb):
    """Encodings to try, best quality first: full RGB, then coarser colours.

    Once quantisation leaves at most 256 colours the palette form is tried
    too; it is usually far smaller, so resolution survives longer.
    """
    for step in (1, 2, 4, 8, 16, 32, 64):
        pixels = quantise(rgb, step)
        yield pixels, encode_png(width, height, pixels)
        if step >= 8:
            png = encode_palette(width, height, pixels)
            if png is not None:
                yield pixels, png


def encode_within_limit(width, height, rgb):
    """Encode, then coarsen colours and finally shrink until <= MAX_BYTES.

    Every accepted encoding is decoded again and compared with the pixels it
    was made from, so a broken file can never be written.
    """
    while True:
        for pixels, png in candidates(width, height, rgb):
            if len(png) <= MAX_BYTES:
                if decode_png(png) != (width, height, pixels):
                    raise RuntimeError("re-encoded PNG does not round-trip")
                return width, height, png
        if width == 1 and height == 1:
            raise RuntimeError("cannot fit even a 1x1 image")  # unreachable
        new_w = max(1, width * 3 // 4)
        new_h = max(1, height * 3 // 4)
        rgb = shrink(width, height, rgb, new_w, new_h)
        width, height = new_w, new_h


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_output(png):
    for folder in ("/output", os.path.join(os.getcwd(), "output")):
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "entry.png")
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(png)
            os.chmod(tmp, 0o644)
            os.replace(tmp, path)
            return path
        except OSError:
            continue
    raise OSError("could not write entry.png to /output or ./output")


def main():
    with open(SOURCE, "rb") as f:
        data = f.read()
    width, height, rgb = decode_png(data)
    new_w, new_h = fit_size(width, height, MAX_SIDE)
    rgb = shrink(width, height, rgb, new_w, new_h)
    width, height, png = encode_within_limit(new_w, new_h, rgb)
    path = write_output(png)
    print("wrote %s: %dx%d, %d bytes" % (path, width, height, len(png)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
