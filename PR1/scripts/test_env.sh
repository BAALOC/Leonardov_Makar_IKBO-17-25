#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo '== environment variables from the real OS'
EMU_DEMO=demo ./run.sh --script examples/scripts/env.emu
