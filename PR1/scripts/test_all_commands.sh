#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo '== all commands of stages 1-3 with the deep VFS'
EMU_DEMO=demo ./run.sh --vfs examples/vfs/deep.csv \
    --script examples/scripts/all_commands.emu
