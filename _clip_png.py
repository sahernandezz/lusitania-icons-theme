#!/usr/bin/env python3
"""
Post-process a square PNG so that pixels outside an inscribed rounded
rectangle become fully transparent.

``qlmanage -t`` (macOS Quick Look thumbnailer) consistently bakes opaque
white into the area outside an SVG clipPath, regardless of how the SVG
declares transparency. Using ``rsvg-convert`` / Inkscape / cairosvg would
avoid this but adds a dependency. This script runs in stock Python 3 —
just ``zlib`` and ``struct``.

What it does
------------
1. Decode the PNG: parse chunks, decompress IDAT, *fully* reverse every
   row's PNG filter (None / Sub / Up / Average / Paeth) into a raw RGBA
   buffer.
2. Zero out RGBA for every pixel whose centre falls outside an inscribed
   rounded rectangle.
3. Re-encode as a flat PNG with filter-type 0 on every row (simpler and
   smaller for RGBA where the row-to-row deltas barely help).

Usage::

    python3 _clip_png.py <png> [--radius-fraction 0.214]

Default radius matches lusitania-theme's icon (54.857/256 ≈ 0.2143).
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path


def _read_chunks(data: bytes) -> list[tuple[str, bytes]]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("not a PNG")
    chunks: list[tuple[str, bytes]] = []
    i = 8
    while i < len(data):
        length = struct.unpack(">I", data[i : i + 4])[0]
        ctype = data[i + 4 : i + 8].decode("ascii")
        body = data[i + 8 : i + 8 + length]
        chunks.append((ctype, body))
        i += 12 + length
        if ctype == "IEND":
            break
    return chunks


def _png_chunk(ctype: str, body: bytes) -> bytes:
    crc = zlib.crc32(ctype.encode("ascii") + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + ctype.encode("ascii") + body + struct.pack(">I", crc)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw: bytes, width: int, height: int) -> bytearray:
    """Reverse PNG row filters → raw RGBA buffer (height * width * 4 bytes)."""
    bpp = 4  # RGBA 8-bit
    stride = width * bpp
    out = bytearray(stride * height)
    prev = bytearray(stride)
    src = 0
    for y in range(height):
        ftype = raw[src]
        src += 1
        line_in = raw[src : src + stride]
        src += stride
        recon = bytearray(stride)

        if ftype == 0:
            recon[:] = line_in
        elif ftype == 1:  # Sub: a
            for x in range(stride):
                a = recon[x - bpp] if x >= bpp else 0
                recon[x] = (line_in[x] + a) & 0xFF
        elif ftype == 2:  # Up: b
            for x in range(stride):
                recon[x] = (line_in[x] + prev[x]) & 0xFF
        elif ftype == 3:  # Average: (a + b) // 2
            for x in range(stride):
                a = recon[x - bpp] if x >= bpp else 0
                b = prev[x]
                recon[x] = (line_in[x] + (a + b) // 2) & 0xFF
        elif ftype == 4:  # Paeth
            for x in range(stride):
                a = recon[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                recon[x] = (line_in[x] + _paeth(a, b, c)) & 0xFF
        else:
            raise SystemExit(f"unknown PNG filter type {ftype} at row {y}")

        out[y * stride : (y + 1) * stride] = recon
        prev = recon
    return out


def _refilter_none(buf: bytes, width: int, height: int) -> bytes:
    """Re-encode rows with filter-type 0 prefix."""
    stride = width * 4
    out = bytearray(height * (stride + 1))
    for y in range(height):
        out[y * (stride + 1)] = 0
        out[y * (stride + 1) + 1 : (y + 1) * (stride + 1)] = buf[y * stride : (y + 1) * stride]
    return bytes(out)


def round_corners(path: Path, radius_fraction: float = 54.857142857142854 / 256) -> None:
    chunks = _read_chunks(path.read_bytes())
    ihdr = next(b for c, b in chunks if c == "IHDR")
    width, height, bitdepth, colortype = struct.unpack(">IIBB", ihdr[:10])
    if (bitdepth, colortype) != (8, 6):
        raise SystemExit(f"need 8-bit RGBA PNG, got bitdepth={bitdepth} colortype={colortype}")
    if width != height:
        raise SystemExit(f"need square PNG, got {width}x{height}")

    idat = b"".join(b for c, b in chunks if c == "IDAT")
    raw_filtered = zlib.decompress(idat)
    pixels = _unfilter(raw_filtered, width, height)

    # Mask pixels outside the inscribed rounded rect.
    r = width * radius_fraction
    centre = width / 2.0
    inner_max = centre - r  # offset from canvas centre to corner-circle centre

    cleared = 0
    for y in range(height):
        for x in range(width):
            dx = max(abs(x + 0.5 - centre) - inner_max, 0)
            dy = max(abs(y + 0.5 - centre) - inner_max, 0)
            if dx * dx + dy * dy > r * r:
                p = y * width * 4 + x * 4
                pixels[p] = 0
                pixels[p + 1] = 0
                pixels[p + 2] = 0
                pixels[p + 3] = 0
                cleared += 1

    new_idat = zlib.compress(_refilter_none(pixels, width, height), 9)

    # Re-assemble PNG, replacing the IDAT stream.
    seen_idat = False
    rebuilt: list[tuple[str, bytes]] = []
    for c, b in chunks:
        if c == "IDAT":
            if not seen_idat:
                rebuilt.append(("IDAT", new_idat))
                seen_idat = True
        else:
            rebuilt.append((c, b))

    with path.open("wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        for c, b in rebuilt:
            f.write(_png_chunk(c, b))

    print(f"  {path.name}: cleared {cleared} corner pixels ({cleared * 100 / (width * height):.1f}%)")


def _parse_args(argv: list[str]) -> tuple[Path, float]:
    if not argv:
        raise SystemExit(__doc__)
    p = Path(argv[0])
    rf = 54.857142857142854 / 256
    if "--radius-fraction" in argv:
        rf = float(argv[argv.index("--radius-fraction") + 1])
    return p, rf


if __name__ == "__main__":
    path, rf = _parse_args(sys.argv[1:])
    round_corners(path, rf)
