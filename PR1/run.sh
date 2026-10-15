#!/bin/sh
root=$(cd "$(dirname "$0")" && pwd)
PYTHONPATH="$root/src" exec uv run --no-project --python 3.12 python -B -m emulator "$@"
