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

args="$@"

declare -A dir_to_filecount_and_execution_time_map

for dir in $args
do
    shopt -s nullglob
    files_to_process=("$dir"/*)
    shopt -u nullglob # Turn off nullglob to make sure it doesn't interfere with anything later

    no_of_files=${#files_to_process[@]}
    info "Treating $dir as a directory. Processing ${no_of_files} files"

    start_time=`date +%s`
    parallel make process INPUT_FILE={} ::: ${files_to_process[@]}
    end_time=`date +%s`

    dir_to_filecount_and_execution_time_map["$dir", 0]=$no_of_files
    dir_to_filecount_and_execution_time_map["$dir", 1]=$(expr $end_time - $start_time)

    execution_time=${dir_to_filecount_and_execution_time_map[$dir, 1]}
    debug "Execution time was $execution_time seconds."
    debug "Processed $counter directories. $(($#-counter)) left to process"

    counter=$((counter+1))
done

total_number_of_files=0
total_execution_time=0
for dir in $args
do
    no_of_files=${dir_to_filecount_and_execution_time_map[$dir, 0]}
    execution_time=${dir_to_filecount_and_execution_time_map[$dir, 1]}
    average=$(expr $execution_time / $no_of_files)

    info "$dir: no_of_files=$no_of_files execution_time=$execution_time average time per file=$average"

    total_number_of_files=$((total_number_of_files+no_of_files))
    total_execution_time=$((total_execution_time+execution_time))
done

info "Processed $total_number_of_files files in $total_execution_time seconds"
