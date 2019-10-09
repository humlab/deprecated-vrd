#!/usr/bin/env bash

source logging_functions.sh

# Create target directories
while read p; do
    debug "Creating $(dirname $p)"
		mkdir -p $(dirname "$p")
done <"$2"

while IFS=$'\t' read -r f1 f2;
do
		debug "Copying \"$f1\" to \"$f2\""
		cp "$f1" "$f2"
done < <(paste "$1" "$2")
