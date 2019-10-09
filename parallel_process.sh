#!/usr/bin/env bash

# Associative arrays require Bash 4
if [ -z "${BASH_VERSINFO}" ] || [ -z "${BASH_VERSINFO[0]}" ] || [ ${BASH_VERSINFO[0]} -lt 4 ]; then echo "This script requires Bash version >= 4"; exit 1; fi

source logging_functions.sh

counter=1

dirs="$@"

declare -A dir_to_filecount_and_execution_time_map

files_to_process=()

shopt -s nullglob
for dir in $dirs
do
    debug "Will process all files in $dir"
    files=("$dir"/*)
    files_to_process=("${files_to_process[@]}" "${files[@]}")
done
shopt -u nullglob # Turn off nullglob to make sure it doesn't interfere with anything later

debug "Processing ${#files_to_process[@]} files..."

start_time=`date +%s`
parallel make process INPUT_FILE={} ::: ${files_to_process[@]}
end_time=`date +%s`

execution_time=$(expr $end_time - $start_time)

debug "Processed ${#files_to_process[@]} files in $execution_time seconds"
