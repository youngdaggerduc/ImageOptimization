"""
Image Optimizer - convert images to web-ready WebP.

Usage:
    python optimize.py <file-or-folder> [more files/folders...] [options]
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence

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


def normalise_mode(img):
    """WebP wants RGB or RGBA."""
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
    return img.convert("RGBA" if has_alpha else "RGB")


def optimize(src: Path, dest: Path, args):
    with Image.open(src) as img:
        icc = img.info.get("icc_profile")  # keep colour profile so colours stay correct
        animated = getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1

        save_opts = dict(format="WEBP", quality=args.quality, method=6)
        if icc:
            save_opts["icc_profile"] = icc
        # EXIF/GPS metadata is intentionally NOT copied (privacy + smaller files)

        if animated:
            frames, durations = [], []
            for frame in ImageSequence.Iterator(img):
                frames.append(resize(frame.convert("RGBA"), args.max_width, args.max_height))
                durations.append(frame.info.get("duration", img.info.get("duration", 100)))
            frames[0].save(dest, save_all=True, append_images=frames[1:], duration=durations,
                           loop=img.info.get("loop", 0), **save_opts)
        else:
            out = ImageOps.exif_transpose(img)  # fix phone photos appearing sideways
            out = normalise_mode(out)
            out = resize(out, args.max_width, args.max_height)
            out.save(dest, **save_opts)


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
