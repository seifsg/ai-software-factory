"""Small valid screenshots for tests of image publication."""
import struct
import zlib


def png(path, width=64, height=32, color=0, blank=False, transparent=False):
    """Write a static RGB PNG with visible content unless a blank is requested."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            ink = 255 if not blank and 4 <= x < width - 4 and 4 <= y < height - 4 and (x + y) % 3 else 0
            rows.extend(((ink + color) % 256, ink, ink))
            if transparent:
                rows.append(0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6 if transparent else 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
