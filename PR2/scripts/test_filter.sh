#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh --test-mode "$@"
    echo "exit code: $?"
    echo
}

run --package A --repo examples/repos/names.txt
run --package A --repo examples/repos/names.txt --filter BC
run --package A --repo examples/repos/names.txt --filter B
run --package A --repo examples/repos/names.txt --filter C
run --package A --repo examples/repos/tree.txt --filter B
run --package A --repo examples/repos/tree.txt --filter D
run --package A --repo examples/repos/cycles.txt --filter C
