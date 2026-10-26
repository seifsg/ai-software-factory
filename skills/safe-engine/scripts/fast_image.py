"""Bounded PNG content check before publication; it cannot judge the right screen."""
from collections import Counter
from functools import lru_cache
from pathlib import Path
import struct
import zlib

MAX_BYTES, MAX_PIXELS = 16 * 1024 * 1024, 8_000_000


def require(ok, message):
    if not ok:
        raise ValueError("Picture: " + message)


def chunks(data):
    """Check every chunk, including CRCs, before trusting compressed pixels."""
    require(data.startswith(b'\x89PNG\r\n\x1a\n'), "use a PNG screenshot")
    offset = 8
    while offset < len(data):
        require(offset + 12 <= len(data), "truncated PNG chunk")
        size = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + size
        require(end <= len(data), "truncated PNG data")
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:end - 4]
        require(zlib.crc32(kind + payload) == struct.unpack_from('>I', data, end - 4)[0], "invalid PNG checksum")
        yield kind, payload
        offset = end
        if kind == b'IEND':
            require(not payload and offset == len(data), "unexpected data after PNG end")
            return
    require(False, "missing PNG end")


def paeth(a, b, c):
    p = a + b - c
    distances = abs(p - a), abs(p - b), abs(p - c)
    return (a, b, c)[distances.index(min(distances))]


def pixels(raw, width, height, channels):
    """Undo PNG scanline filters with one previous row, keeping memory bounded."""
    stride = width * channels
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        mode, row = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        require(mode <= 4, "unknown PNG row filter")
        if mode:
            for i in range(stride):
                a, b, c = (row[i - channels] if i >= channels else 0), previous[i], (previous[i - channels] if i >= channels else 0)
                predictor = a if mode == 1 else b if mode == 2 else (a + b) // 2 if mode == 3 else paeth(a, b, c)
                row[i] = (row[i] + predictor) & 255
        yield row
        previous = row


@lru_cache(maxsize=8)
def inspect_bytes(data):
    """Reject corruption and almost uniform/transparent captures, preserving sparse real content."""
    require(len(data) <= MAX_BYTES, "PNG exceeds 16 MiB; capture a smaller view")
    pieces = list(chunks(data))
    require(pieces and pieces[0][0] == b'IHDR' and len(pieces[0][1]) == 13, "missing PNG header")
    width, height, depth, colour, compression, filtering, interlace = struct.unpack('>IIBBBBB', pieces[0][1])
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(colour)
    require(width > 0 and height > 0 and width * height <= MAX_PIXELS, "capture exceeds 8 million pixels")
    require(depth == 8 and channels and not (compression or filtering or interlace), "convert to an 8-bit non-interlaced RGB/RGBA or grayscale PNG")
    require(all(k in (b'IHDR', b'IDAT', b'IEND') or k[0] & 32 for k, _ in pieces), "unsupported PNG critical chunk")
    require(sum(k == b'IHDR' for k, _ in pieces) == 1, "duplicate PNG header")
    require(not any(k in (b'tRNS', b'acTL') for k, _ in pieces), "convert transparency/animation to a static RGBA PNG")
    encoded = b''.join(v for k, v in pieces if k == b'IDAT')
    expected = height * (width * channels + 1)
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(encoded, expected + 1)
    except zlib.error as error:
        raise ValueError("Picture: corrupt PNG pixels") from error
    require(len(raw) == expected and decoder.eof and not decoder.unused_data, "invalid or oversized PNG pixel stream")
    colours = Counter()
    for row in pixels(raw, width, height, channels):
        for i in range(0, len(row), channels):
            alpha = row[i + channels - 1] if colour in (4, 6) else 255
            rgb = row[i:i + 3] if colour in (2, 6) else (row[i],) * 3
            colours[tuple((v * alpha + 255 * (255 - alpha)) // 1020 for v in rgb)] += 1
    background = colours.most_common(1)[0][0]
    contrast = sum(count for rgb, count in colours.items() if max(abs(a - b) for a, b in zip(rgb, background)) >= 3)
    require(contrast >= max(32, width * height // 10000), "blank or near-blank image; capture visible content and inspect it")
    return width, height


def check(path):
    """Validate current bytes; the small cache never trusts timestamps or filenames."""
    path = Path(path)
    require(path.stat().st_size <= MAX_BYTES, "PNG exceeds 16 MiB")
    return inspect_bytes(path.read_bytes())
