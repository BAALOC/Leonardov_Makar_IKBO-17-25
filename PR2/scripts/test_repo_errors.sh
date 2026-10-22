#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

run() {
    echo "\$ ./run.sh $*"
    ./run.sh --test-mode "$@"
    echo "exit code: $?"
    echo
}

run --package Z --repo examples/repos/tree.txt
for file in examples/repos/broken/*.txt; do
    run --package A --repo "$file"
done
