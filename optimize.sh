#!/usr/bin/env sh
# macOS / Linux launcher.
#   ./optimize.sh photo.jpg
#   ./optimize.sh ~/Pictures/site-images -q 75 -w 1600
DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(sys.version_info[0] < 3)'; then
    PY=python
else
    echo "Python 3 was not found on this computer."
    case "$(uname -s)" in
        Darwin) echo "Install it from https://www.python.org/downloads/  (or: brew install python)" ;;
        *)      echo "Install it with your package manager, e.g.: sudo apt install python3 python3-venv" ;;
    esac
    exit 1
fi

exec "$PY" "$DIR/optimize.py" "$@"
