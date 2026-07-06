#!/usr/bin/env bash
set -Eeuo pipefail

DATA_DIR="${DATA_DIR:-/data}"
CSV_DIR="${CSV_DIR:-$DATA_DIR/csv}"
STATION_NAME="${STATION_NAME:-SA8818}"
RTL_DEVICE_INDEX="${RTL_DEVICE_INDEX:-0}"
RTL_FREQUENCY_RANGE="${RTL_FREQUENCY_RANGE:-30M:1000M:10K}"
RTL_GAIN="${RTL_GAIN:-22.5}"
RTL_INTERVAL="${RTL_INTERVAL:-1}"
RTL_CROP="${RTL_CROP:-0.28}"
RTL_CAPTURE_DURATION="${RTL_CAPTURE_DURATION:-1m}"
RTL_SLEEP_SECONDS="${RTL_SLEEP_SECONDS:-1}"

mkdir -p "$CSV_DIR"

echo "scanner: station=$STATION_NAME device=$RTL_DEVICE_INDEX range=$RTL_FREQUENCY_RANGE gain=$RTL_GAIN duration=$RTL_CAPTURE_DURATION"

while true; do
  start_time="$(date +%Y%m%d%H%M%S)"
  tmp_file="$CSV_DIR/.capture-${start_time}.csv.tmp"

  set +e
  rtl_power \
    -d "$RTL_DEVICE_INDEX" \
    -f "$RTL_FREQUENCY_RANGE" \
    -g "$RTL_GAIN" \
    -i "$RTL_INTERVAL" \
    -c "$RTL_CROP" \
    -e "$RTL_CAPTURE_DURATION" \
    "$tmp_file"
  status=$?
  set -e

  stop_time="$(date +%Y%m%d%H%M%S)"
  final_file="$CSV_DIR/${STATION_NAME,,}-${start_time}-${stop_time}.csv"

  if [ "$status" -eq 0 ] && [ -s "$tmp_file" ]; then
    mv "$tmp_file" "$final_file"
    echo "scanner: wrote $final_file"
  else
    rm -f "$tmp_file"
    echo "scanner: rtl_power failed with exit code $status" >&2
    sleep 10
  fi

  sleep "$RTL_SLEEP_SECONDS"
done
