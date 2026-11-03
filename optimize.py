"""
Image Optimizer - convert images to web-ready WebP.

Usage:
    python optimize.py <image> [more images...] [-q QUALITY]
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

OUTPUT_DIR_NAME = "optimized"


def optimize(src: Path, dest: Path, quality: int):
    with Image.open(src) as img:
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img.save(dest, format="WEBP", quality=quality, method=6)


def main():
    ap = argparse.ArgumentParser(description="Convert images to optimized WebP for the web.")
    ap.add_argument("paths", nargs="+", help="image files")
    ap.add_argument("-q", "--quality", type=int, default=80, help="WebP quality 1-100 (default 80)")
    args = ap.parse_args()

    for raw in args.paths:
        src = Path(raw)
        if not src.is_file():
            print(f"  not found: {src}")
            continue
        out_dir = src.parent / OUTPUT_DIR_NAME
        out_dir.mkdir(exist_ok=True)
        dest = out_dir / (src.stem + ".webp")
        optimize(src, dest, args.quality)
        print(f"  {src.name} -> {dest}")


if __name__ == "__main__":
    sys.exit(main())
