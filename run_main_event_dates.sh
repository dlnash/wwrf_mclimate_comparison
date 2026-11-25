#!/bin/bash

PYTHON=/home/dnash/miniconda3/envs/SEAK-impacts/bin/python

INIT_DATE_LST=(
    2021012200
    2021012300
    2021012400
    2021012500
    2021012600
    2021012700
    2021012800
)

for INIT_DATE in "${INIT_DATE_LST[@]}"; do

    echo "======================================"
    echo "Processing initialization: ${INIT_DATE}"
    echo "Start time: $(date)"
    echo "======================================"

    ${PYTHON} main.py \
        --init-date "${INIT_DATE}" \
        --source "archive"

    STATUS=$?

    if [ ${STATUS} -ne 0 ]; then
        echo "ERROR: Failed for ${INIT_DATE} (exit code ${STATUS})"
        exit ${STATUS}
    fi

    echo "Completed ${INIT_DATE}"
    echo "End time: $(date)"

done

echo "All initialization dates completed."