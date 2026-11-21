#!/usr/bin/env python3
"""Write 07_present/figures/F1.png: a 600 x 400 px raster (a fictional app screenshot) for the poster-87dpi scenario.

Standard library only (zlib + struct), deterministic: the committed PNG is the output of this script.
Placed 17.5 cm wide on the poster, 600 px give 600 / (17.5 / 2.54) = 87 dpi (E-PRINT block below 100 dpi).
"""
import struct
import zlib
from pathlib import Path

W, H = 600, 400


def pixel(x: int, y: int) -> tuple:
    if y < 48:                                   # title bar
        return (31, 78, 121)
    if x < 120:                                  # side menu
        return (227, 235, 243) if (y // 40) % 2 else (210, 222, 235)
    row = (y - 48) // 44
    if (y - 48) % 44 < 4:                        # row separators
        return (200, 200, 200)
    if 140 <= x < 140 + 60 + 37 * (row % 7) and 60 <= (y - 48) % 44 + 48 < 80:
        return (46, 125, 50) if row % 3 else (198, 40, 40)   # status bars
    return (250, 250, 250)


def png_bytes() -> bytes:
    raw = bytearray()
    for y in range(H):
        raw.append(0)                            # filter type 0 per row
        for x in range(W):
            raw.extend(pixel(x, y))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "07_present" / "figures" / "F1.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(png_bytes())
    print(f"wrote {out} ({W} x {H} px)")
