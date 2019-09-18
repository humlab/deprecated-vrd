#!/usr/bin/env bash

# Create target directories
while read p; do
    echo "Creating $(dirname $p)"
		mkdir -p $(dirname "$p")
done <"$2"

while IFS=$'\t' read -r f1 f2;
do
		echo "Copying \"$f1\" to \"$f2\""
		cp "$f1" "$f2"
done < <(paste "$1" "$2")
