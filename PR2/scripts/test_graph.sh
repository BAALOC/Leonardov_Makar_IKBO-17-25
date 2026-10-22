#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh --test-mode "$@"
    echo "exit code: $?"
    echo
}

run --package A --repo examples/repos/chain.txt
run --package B --repo examples/repos/chain.txt
run --package A --repo examples/repos/tree.txt
run --package A --repo examples/repos/diamond.txt
run --package A --repo examples/repos/cycle.txt
run --package A --repo examples/repos/cycles.txt
run --package D --repo examples/repos/cycles.txt
run --package A --repo examples/repos/missing_dependency.txt
run --package A --repo examples/repos/components.txt
run --package C --repo examples/repos/components.txt
