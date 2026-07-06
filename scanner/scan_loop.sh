#!/usr/bin/env bash
set -Eeuo pipefail

DATA_DIR="${DATA_DIR:-/data}"
CSV_DIR="${CSV_DIR:-$DATA_DIR/csv}"
STATION_NAME="${STATION_NAME:-SA8818}"
RTL_PREFIX="${RTL_PREFIX:-RTL1}"

setting() {
  local key="${RTL_PREFIX}_$1"
  local fallback="${2:-}"
  local value="${!key:-}"
  if [ -n "$value" ]; then
    printf '%s' "$value"
  else
    printf '%s' "$fallback"
  fi
}

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

RTL_NAME="$(setting NAME "$RTL_PREFIX")"
RTL_DEVICE_INDEX="$(setting DEVICE_INDEX "0")"
RTL_FREQUENCY_RANGE="$(setting FREQUENCY_RANGE "30M:1000M:10K")"
RTL_GAIN="$(setting GAIN "22.5")"
RTL_INTERVAL="$(setting INTERVAL "1")"
RTL_CROP="$(setting CROP "0.28")"
RTL_CAPTURE_DURATION="$(setting CAPTURE_DURATION "1m")"
RTL_SLEEP_SECONDS="$(setting SLEEP_SECONDS "1")"
RTL_EXTRA_ARGS="$(setting EXTRA_ARGS "")"

SOURCE_SLUG="$(slugify "$RTL_NAME")"
RANGE_SLUG="$(slugify "$RTL_FREQUENCY_RANGE")"
STATION_SLUG="$(slugify "$STATION_NAME")"

mkdir -p "$CSV_DIR"

echo "scanner: station=$STATION_NAME source=$RTL_NAME device=$RTL_DEVICE_INDEX range=$RTL_FREQUENCY_RANGE gain=$RTL_GAIN duration=$RTL_CAPTURE_DURATION"

while true; do
  start_time="$(date +%Y%m%d%H%M%S)"
  tmp_file="$CSV_DIR/.capture-${SOURCE_SLUG}-${start_time}.csv.tmp"

  set +e
  rtl_power \
    -d "$RTL_DEVICE_INDEX" \
    -f "$RTL_FREQUENCY_RANGE" \
    -g "$RTL_GAIN" \
    -i "$RTL_INTERVAL" \
    -c "$RTL_CROP" \
    -e "$RTL_CAPTURE_DURATION" \
    $RTL_EXTRA_ARGS \
    "$tmp_file"
  status=$?
  set -e

  stop_time="$(date +%Y%m%d%H%M%S)"
  final_file="$CSV_DIR/${STATION_SLUG}-${SOURCE_SLUG}-${RANGE_SLUG}-${start_time}-${stop_time}.csv"

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
