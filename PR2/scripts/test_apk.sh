#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

URL=https://dl-cdn.alpinelinux.org/alpine/latest-stable/main/x86_64

run() {
    echo "\$ ./run.sh $*"
    ./run.sh "$@"
    echo "exit code: $?"
    echo
}

run --package busybox --repo "$URL"
run --package curl --repo "$URL"
run --package curl --repo "$URL" --filter musl
run --package python3 --repo "$URL"
run --package no-such-package --repo "$URL"
run --package curl --repo "$URL/missing"
run --package curl --repo https://localhost:1/main
