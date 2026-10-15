#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo '== VFS file does not exist'
./run.sh --vfs examples/vfs/missing.csv
echo "exit code: $?"

echo '== VFS path is a directory'
./run.sh --vfs examples/vfs
echo "exit code: $?"

for file in examples/vfs/broken/*.csv; do
    echo "== invalid VFS: $file"
    ./run.sh --vfs "$file"
    echo "exit code: $?"
done
