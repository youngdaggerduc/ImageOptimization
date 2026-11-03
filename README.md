# Image Optimizer

Converts images (JPG, PNG, GIF, BMP, TIFF, WebP, and optionally HEIC) to small, web-ready **WebP** files.

- Resizes anything wider than 1920px (never upscales)
- Strips EXIF/GPS metadata, keeps the colour profile
- Fixes sideways phone photos
- Keeps transparency and GIF animation
- Never touches your originals: output goes to an `optimized/` folder next to them

## Requirements

Only **Python 3.8+**. The first time you run it, the script checks for its one dependency
([Pillow](https://pypi.org/project/Pillow/)) and offers to install it into a private `.venv/`
folder next to the script. Nothing is installed system-wide.

- Windows: https://www.python.org/downloads/ (tick **"Add python.exe to PATH"**)
- macOS: https://www.python.org/downloads/ or `brew install python`
- Linux: `sudo apt install python3 python3-venv` (or your distro's equivalent)

## Usage

**Windows:** drag images or folders onto `optimize.bat`, or double-click it and paste a path.

**macOS / Linux:**

```sh
chmod +x optimize.sh        # once
./optimize.sh photo.jpg
./optimize.sh ~/Pictures/site-images
```

**Any OS:**

```sh
python optimize.py <files-or-folders> [options]
```

### Options

| Option | Default | Description |
|---|---|---|
| `-q`, `--quality` | 80 | WebP quality, 1–100 |
| `-w`, `--max-width` | 1920 | Max width in px (`0` = no limit) |
| `-H`, `--max-height` | 0 | Max height in px (`0` = no limit) |
| `-o`, `--output` | `optimized/` next to source | Write everything to one folder |
| `-r`, `--recursive` | off | Include subfolders |
| `--lossless` | off | Lossless WebP: best for logos and graphics, not photos |
| `--overwrite` | off | Re-create existing `.webp` files |
| `--strip-icc` | off | Also remove the colour profile |
| `-y`, `--yes` | off | Install missing dependencies without asking |

### Examples

```sh
python optimize.py hero.jpg -q 75
python optimize.py ./photos -r -w 1600 -o ./public/img
python optimize.py logo.png --lossless
```

For iPhone `.heic` photos, also install `pillow-heif` (`pip install pillow-heif`).
