"""
Image Optimizer - convert images to web-ready WebP.

Usage:
    python optimize.py <file-or-folder> [more files/folders...] [options]
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

OUTPUT_DIR_NAME = "optimized"
SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def collect(paths, recursive):
    """Turn the given files/folders into a list of image files."""
    files = []
    for raw in paths:
        p = Path(raw.strip().strip('"')).expanduser()
        if p.is_file():
            if p.suffix.lower() in SUPPORTED:
                files.append(p)
            else:
                print(f"  skip (unsupported type): {p.name}")
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(p.glob(pattern)):
                if (
                    f.is_file()
                    and f.suffix.lower() in SUPPORTED
                    and OUTPUT_DIR_NAME not in f.relative_to(p).parts
                ):
                    files.append(f)
        else:
            print(f"  not found: {p}")
    return files


def resize(img, max_w, max_h):
    if not max_w and not max_h:
        return img
    w, h = img.size
    scale = min((max_w / w) if max_w else 1, (max_h / h) if max_h else 1, 1)  # never upscale
    if scale >= 1:
        return img
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def optimize(src: Path, dest: Path, args):
    with Image.open(src) as img:
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img = resize(img, args.max_width, args.max_height)
        img.save(dest, format="WEBP", quality=args.quality, method=6)


def main():
    ap = argparse.ArgumentParser(description="Convert images to optimized WebP for the web.")
    ap.add_argument("paths", nargs="+", help="image files and/or folders")
    ap.add_argument("-q", "--quality", type=int, default=80, help="WebP quality 1-100 (default 80)")
    ap.add_argument("-w", "--max-width", type=int, default=1920, help="max width in px, 0 = no limit (default 1920)")
    ap.add_argument("-H", "--max-height", type=int, default=0, help="max height in px, 0 = no limit (default 0)")
    ap.add_argument("-r", "--recursive", action="store_true", help="include images in subfolders")
    args = ap.parse_args()

    files = collect(args.paths, args.recursive)
    if not files:
        sys.exit("No supported images found.")

    for src in files:
        out_dir = src.parent / OUTPUT_DIR_NAME
        out_dir.mkdir(exist_ok=True)
        dest = out_dir / (src.stem + ".webp")
        optimize(src, dest, args)
        print(f"  {src.name} -> {dest}")


if __name__ == "__main__":
    main()
