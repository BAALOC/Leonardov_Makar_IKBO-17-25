#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

for name in minimal several deep; do
    echo "== VFS: $name"
    ./run.sh --vfs "examples/vfs/$name.csv" \
        --script examples/scripts/show_tree.emu
done
