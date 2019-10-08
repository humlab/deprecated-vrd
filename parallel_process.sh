#!/usr/bin/env bash

# Associative arrays require Bash 4
if [ -z "${BASH_VERSINFO}" ] || [ -z "${BASH_VERSINFO[0]}" ] || [ ${BASH_VERSINFO[0]} -lt 4 ]; then echo "This script requires Bash version >= 4"; exit 1; fi

warn () {
    echo 1>&2 "$(tput setaf 3)[WARNING] $@$(tput sgr 0)"
}

panic () {
    echo 1>&2 "$(tput setaf 1)[ERROR] $@$(tput sgr 0)"
    kill -s TERM $PID
}

info () {
    echo 1>&2 "$(tput setaf 6)[INFO] $@$(tput sgr 0)"
}

debug () {
    info $1
}

counter=1

dirs="$@"

declare -A dir_to_filecount_and_execution_time_map

files_to_process=()

shopt -s nullglob
for dir in $dirs
do
    info "Appending all files in $dir to the list of files to process"
    files=("$dir"/*)
    files_to_process=("${files_to_process[@]}" "${files[@]}")
done
shopt -u nullglob # Turn off nullglob to make sure it doesn't interfere with anything later

start_time=`date +%s`
parallel make process INPUT_FILE={} ::: ${files_to_process[@]}
end_time=`date +%s`

execution_time=$(expr $end_time - $start_time)

info "Processed ${#files_to_process[@]} files in $execution_time seconds"
