#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo '== missing script file'
./run.sh --script examples/scripts/missing.emu
echo "exit code: $?"

echo '== script path is a directory'
./run.sh --script examples/scripts
echo "exit code: $?"

echo '== unknown parameter'
./run.sh --unknown
echo "exit code: $?"

echo '== parameter without a value'
./run.sh --script
echo "exit code: $?"

echo '== errors inside the script are shown in the window'
./run.sh --vfs examples/vfs/minimal.csv --script examples/scripts/errors.emu
