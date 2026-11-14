#!/usr/bin/env python3
"""Shrink a flat-colour PNG by reducing it to a small palette (needs Pillow).

Usage: python3 docs/media-src/squash.py IN.png OUT.png [COLOURS=128]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        return 2
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    colours = int(sys.argv[3]) if len(sys.argv) == 4 else 128
    image = Image.open(source).convert("RGB")
    small = image.quantize(
        colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
    )
    small.save(target, optimize=True)
    print(f"wrote {target}: {target.stat().st_size // 1024} KB, {image.width}x{image.height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
