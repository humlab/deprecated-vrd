#!/usr/bin/env bash

start_time=`date +%s`
parallel make process INPUT_FILE={} ::: $1
end_time=`date +%s`

echo "Execution time was $(expr $end_time - $start_time) seconds."
