#!/usr/bin/env bash

source logging_functions.sh

INPUT_FILE=$1
FILENAME_WITH_EXT=${INPUT_FILE##*/}
FILENAME=${FILENAME_WITH_EXT%.*}
SEGMENTS_TXT="${FILENAME}-segments.txt"
FRAMES_TXT="${FILENAME}-frames.txt"
KEYFRAMES_TXT="${FILENAME}-keyframes.txt"
AUDIO_TXT="${FILENAME}-audio.txt"
PROCESSED_DIR="processed"
SOURCES="${FILENAME}-sources.txt"
TARGETS="${FILENAME}-targets.txt"

info "Processing \"${FILENAME}\""

info "Producing segments from ${FILENAME}, output in ${SEGMENTS_TXT}"
make --no-print-directory segment INPUT_FILE="${INPUT_FILE}" > ${SEGMENTS_TXT}

info "Calling video_reuse_detector.downsample on each line in \"${SEGMENTS_TXT}\". Output can be read from \"${FRAMES_TXT}\""
cat ${SEGMENTS_TXT} | xargs pipenv run python -m video_reuse_detector.downsample > ${FRAMES_TXT}

info "Calling video_reuse_detector.keyframe on each group of five lines in \"${FRAMES_TXT}\". Output can be read from \"${KEYFRAMES_TXT}\""
cat ${FRAMES_TXT} | xargs -n 5 pipenv run python -m video_reuse_detector.keyframe > ${KEYFRAMES_TXT}

info "Calling video_reuse_detector.extract_audio on each line in \"${SEGMENTS_TXT}\". Output can be read from \"${AUDIO_TXT}\""
cat ${SEGMENTS_TXT} | xargs pipenv run python -m video_reuse_detector.extract_audio > ${AUDIO_TXT}

info "Creating the directory \"${PROCESSED_DIR}\" if it does not exist"
mkdir -p "${PROCESSED_DIR}"

info "Copying files listed in \"${KEYFRAMES_TXT}\" and \"${AUDIO_TXT}\" to \"${PROCESSED_DIR}\""
cat ${KEYFRAMES_TXT} ${AUDIO_TXT} > ${SOURCES}
sed "s/interim/${PROCESSED_DIR}/" ${SOURCES} > ${TARGETS}
./transfer_interim.sh "${SOURCES}" "${TARGETS}"