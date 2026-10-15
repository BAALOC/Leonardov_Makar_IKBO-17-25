#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo '== no parameters'
./run.sh

echo '== --vfs only'
./run.sh --vfs examples/vfs/minimal.csv

echo '== --script only'
./run.sh --script examples/scripts/basic.emu

echo '== --vfs and --script'
./run.sh --vfs examples/vfs/several.csv --script examples/scripts/basic.emu

echo '== --vfs=VALUE and --script=VALUE forms'
./run.sh --vfs=examples/vfs/deep.csv --script=examples/scripts/exit.emu
