#!/usr/bin/env bash

. logging_functions.sh

SOURCE_DIRECTORY=$(realpath $1)
TARGET_DIRECTORY=$(realpath $2)

for f in "${SOURCE_DIRECTORY}"/*; do 
    NAME=$(basename $f)
    info "$f: extracting ten seconds, starting at 00:00:30 to ${TARGET_DIRECTORY}/$NAME"
    ffmpeg -i "$f" -ss 00:00:30 -to 00:00:40 -c copy -y "${TARGET_DIRECTORY}/$NAME"
done
