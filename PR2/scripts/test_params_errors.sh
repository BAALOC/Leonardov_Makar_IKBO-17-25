#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

URL=https://dl-cdn.alpinelinux.org/alpine/latest-stable/main/x86_64
REPO=examples/repos/tree.txt

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

echo '== package'
run --repo "$URL"
run --package '' --repo "$URL"
run --package 'bad name' --repo "$URL"
run --package curl --repo "$URL" --test-mode

echo '== repo'
run --package curl
run --package curl --repo alpine-main
run --package curl --repo ftp://example.com/main
run --package curl --repo http://
run --package A --repo examples/repos/missing.txt --test-mode
run --package A --repo examples/repos --test-mode

echo '== test mode'
run --package A --repo "$URL" --test-mode

echo '== output'
run --package A --repo "$REPO" --test-mode --output graph.svg
run --package A --repo "$REPO" --test-mode --output no/such/dir/graph.png

echo '== filter'
run --package A --repo "$REPO" --test-mode --filter 'a b'
run --package A --repo "$REPO" --test-mode --filter A

echo '== unknown parameter'
run --package A --repo "$REPO" --test-mode --color
