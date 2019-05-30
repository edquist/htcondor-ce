#!/bin/bash

# Create a temporary accounting file name
today=$(date -u --date='00:00:00 today' +%s)
yesterday=$(date -u --date='00:00:00 yesterday' +%s)

OUTPUT_DIR="$(condor_ce_config_val APEL_OUTPUT_DIR)"
OUTPUT_FILE="$OUTPUT_DIR/batch-$(date -u --date='yesterday' +%Y%m%d )-$(hostname -s)"

if [ ! -d $OUTPUT_DIR ] || [ ! -w $OUTPUT_DIR ]; then
    echo "Cannot write to $OUTPUT_DIR"
    exit 1
fi

# Build the filter for the history command
CONSTR="EnteredCurrentStatus >= $yesterday && EnteredCurrentStatus < $today && RemoteWallclockTime !=0"

HISTORY_SUFFIX='-format "\n" EMPTY'
SCALING_ATTR=$(condor_ce_config_val APEL_SCALING_ATTR)
[ $? -eq 0 ] && HISTORY_SUFFIX="-format \"%v|\" ${SCALING_ATTR} ${HISTORY_SUFFIX}"

TZ=GMT condor_history -constraint "$CONSTR" \
    -format "%s_$(condor_ce_config_val APEL_BATCH_HOST)|" ClusterId \
    -format "%s|" Owner \
    -format "%d|" RemoteWallClockTime \
    -format "%d|" RemoteUserCpu \
    -format "%d|" RemoteSysCpu \
    -format "%d|" JobStartDate \
    -format "%d|" EnteredCurrentStatus \
    -format "%d|" ResidentSetSize_RAW \
    -format "%d|" ImageSize_RAW \
    -format "%d|" RequestCpus \
    "${HISTORY_SUFFIX}" > $OUTPUT_FILE