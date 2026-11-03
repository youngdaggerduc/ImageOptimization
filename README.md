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

