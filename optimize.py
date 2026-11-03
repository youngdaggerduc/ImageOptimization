"""
Image Optimizer - convert images to web-ready WebP.

Usage:
    python optimize.py <file-or-folder> [more files/folders...] [options]
    python optimize.py                 (asks you for a path)

Examples:
    python optimize.py photo.jpg
    python optimize.py ~/Pictures/site-images
    python optimize.py images/ -q 75 -w 1600
    python optimize.py hero.png --lossless
    python optimize.py images/ -r -o ./public/img

By default, output goes into an "optimized" folder next to each source image.
Missing dependencies (Pillow) are installed automatically into a private
.venv folder next to this script the first time you run it.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 8)
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / ".venv"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
REQUIREMENTS = ["Pillow>=9.0"]

OUTPUT_DIR_NAME = "optimized"
BASE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


# --------------------------------------------------------------------------- #
# Dependency checks
# --------------------------------------------------------------------------- #
def have_pillow() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def running_in_local_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == VENV_DIR.resolve()
    except OSError:
        return False


def rerun_with(python: Path):
    """Re-launch this script with another interpreter and exit with its code."""
    sys.stdout.flush()
    sys.exit(subprocess.call([str(python), str(Path(__file__).resolve()), *sys.argv[1:]]))


def confirm(question: str, assume_yes: bool) -> bool:
    if assume_yes or not sys.stdin.isatty():
        return True
    answer = input(f"{question} [Y/n] ").strip().lower()
    return answer in ("", "y", "yes")


def pip_install(python: Path | str, extra_args=()) -> bool:
    cmd = [str(python), "-m", "pip", "install", "--disable-pip-version-check", *extra_args, *REQUIREMENTS]
    print("  running:", " ".join(cmd))
    return subprocess.call(cmd) == 0


def manual_instructions():
    print("\nCould not install Pillow automatically. Install it yourself, then re-run:")
    if os.name == "nt":
        print("    py -m pip install Pillow")
    elif sys.platform == "darwin":
        print("    python3 -m pip install --user Pillow      (or: brew install pillow)")
    else:
        print("    python3 -m pip install --user Pillow")
        print("    or  sudo apt install python3-pil python3-venv   (Debian/Ubuntu)")
        print("    or  sudo dnf install python3-pillow             (Fedora)")
    sys.exit(1)


def ensure_dependencies(assume_yes: bool):
    if sys.version_info < MIN_PYTHON:
        sys.exit(f"Python {'.'.join(map(str, MIN_PYTHON))}+ is required "
                 f"(you have {sys.version.split()[0]}). Get it from https://www.python.org/downloads/")

    if have_pillow():
        return

    # A previous run already set up the private environment: use it.
    if VENV_PY.exists() and not running_in_local_venv():
        rerun_with(VENV_PY)

    print("Pillow (the image library this script needs) is not installed.")
    if not confirm(f"Install it now into {VENV_DIR.name}/ next to this script?", assume_yes):
        manual_instructions()

    # 1) Private virtual environment - works even on systems that block global pip installs.
    if not running_in_local_venv():
        print(f"\nCreating {VENV_DIR} ...")
        if subprocess.call([sys.executable, "-m", "venv", str(VENV_DIR)]) == 0 and VENV_PY.exists():
            if pip_install(VENV_PY):
                print("\nDependencies installed. Starting...\n")
                rerun_with(VENV_PY)
        print("  could not set up a virtual environment, trying a user install instead...")
    else:
        if pip_install(sys.executable):
            print("\nDependencies installed. Starting...\n")
            rerun_with(Path(sys.executable))

    # 2) Fall back to a per-user install for this Python.
    subprocess.call([sys.executable, "-m", "ensurepip", "--user"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if pip_install(sys.executable, ["--user"]):
        print("\nDependencies installed. Starting...\n")
        rerun_with(Path(sys.executable))

    manual_instructions()


# --------------------------------------------------------------------------- #
# Image processing
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def collect(paths, recursive, supported):
    """Turn the given files/folders into a list of image files."""
    files = []
    for raw in paths:
        p = Path(raw.strip().strip('"').strip("'")).expanduser()
        if p.is_file():
            if p.suffix.lower() in supported:
                files.append(p)
            else:
                print(f"  skip (unsupported type): {p.name}")
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(p.glob(pattern)):
                if (
                    f.is_file()
                    and f.suffix.lower() in supported
                    and OUTPUT_DIR_NAME not in f.relative_to(p).parts
                ):
                    files.append(f)
        else:
            print(f"  not found: {p}")
    return files


def resize(img, max_w, max_h):
    from PIL import Image

    if not max_w and not max_h:
        return img
    w, h = img.size
    scale = min((max_w / w) if max_w else 1, (max_h / h) if max_h else 1, 1)  # never upscale
    if scale >= 1:
        return img
    resample = getattr(Image, "Resampling", Image).LANCZOS
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), resample)


def normalise_mode(img):
    """WebP wants RGB or RGBA."""
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
    return img.convert("RGBA" if has_alpha else "RGB")


def optimize(src: Path, dest: Path, args) -> tuple[int, int]:
    from PIL import Image, ImageOps, ImageSequence

    with Image.open(src) as img:
        icc = img.info.get("icc_profile")  # keep colour profile so colours stay correct
        animated = getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1

        save_opts = dict(format="WEBP", quality=args.quality, method=6, lossless=args.lossless)
        if icc and not args.strip_icc:
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

    return src.stat().st_size, dest.stat().st_size


def dest_for(src: Path, args) -> Path:
    out_dir = Path(args.output).expanduser() if args.output else src.parent / OUTPUT_DIR_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / (src.stem + ".webp")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Convert images to optimized WebP for the web.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("paths", nargs="*", help="image files and/or folders")
    ap.add_argument("-q", "--quality", type=int, default=80, help="WebP quality 1-100 (default 80)")
    ap.add_argument("-w", "--max-width", type=int, default=1920, help="max width in px, 0 = no limit (default 1920)")
    ap.add_argument("-H", "--max-height", type=int, default=0, help="max height in px, 0 = no limit (default 0)")
    ap.add_argument("-o", "--output", help="put all output in this folder (default: 'optimized' next to each image)")
    ap.add_argument("-r", "--recursive", action="store_true", help="include images in subfolders")
    ap.add_argument("--lossless", action="store_true", help="lossless WebP (good for logos/graphics)")
    ap.add_argument("--overwrite", action="store_true", help="re-create .webp files that already exist")
    ap.add_argument("--strip-icc", action="store_true", help="also drop the colour profile (slightly smaller)")
    ap.add_argument("-y", "--yes", action="store_true", help="install missing dependencies without asking")
    args = ap.parse_args()

    if not 1 <= args.quality <= 100:
        ap.error("quality must be between 1 and 100")

    ensure_dependencies(args.yes)

    from PIL import features

    if not features.check("webp"):
        sys.exit("Your Pillow was built without WebP support. Fix with:\n"
                 f"    {Path(sys.executable).name} -m pip install --upgrade --force-reinstall Pillow")

    supported = set(BASE_FORMATS)
    heif = False
    try:  # optional iPhone HEIC support: pip install pillow-heif
        import pillow_heif  # type: ignore

        pillow_heif.register_heif_opener()
        supported |= {".heic", ".heif"}
        heif = True
    except ImportError:
        pass

    paths = args.paths
    if not paths:
        entered = input("Drag an image or folder here (or type its path) and press Enter:\n> ").strip()
        if not entered:
            sys.exit("Nothing given.")
        paths = [entered]

    files = collect(paths, args.recursive, supported)
    if not files:
        sys.exit("No supported images found." + ("" if heif else "  (For HEIC: pip install pillow-heif)"))

    mode = "lossless" if args.lossless else f"q{args.quality}"
    limits = (f", max {args.max_width}px wide" if args.max_width else "") + \
             (f", max {args.max_height}px tall" if args.max_height else "")
    print(f"\nOptimizing {len(files)} image(s)  ->  WebP {mode}{limits}\n")

    total_in = total_out = done = failed = skipped = 0
    for src in files:
        dest = dest_for(src, args)
        if dest.exists() and not args.overwrite:
            print(f"  skip (exists): {dest.name}   use --overwrite to redo")
            skipped += 1
            continue
        try:
            before, after = optimize(src, dest, args)
        except Exception as e:  # keep going on bad files
            print(f"  FAILED: {src.name}  ({e})")
            failed += 1
            continue
        total_in += before
        total_out += after
        done += 1
        saved = 100 * (1 - after / before) if before else 0
        change = f"{saved:.0f}% smaller" if saved >= 0 else f"{-saved:.0f}% LARGER"
        print(f"  {src.name:40} {human(before):>9} -> {human(after):>9}   ({change})")
        if after > before:
            print(f"    note: WebP came out larger than the original; consider keeping {src.name}")

    print("\n" + "-" * 60)
    if done:
        pct = 100 * (1 - total_out / total_in) if total_in else 0
        print(f"Done: {done} converted, {human(total_in)} -> {human(total_out)} ({pct:.0f}% smaller)")
    if skipped:
        print(f"Skipped: {skipped}")
    if failed:
        print(f"Failed: {failed}")
    if done:
        print(f"Output: {args.output or repr(OUTPUT_DIR_NAME) + ' folder next to the originals'}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
