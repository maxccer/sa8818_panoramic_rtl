#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_PATH="${SPYSERVER_CONFIG_PATH:-/opt/spyserver/spyserver.config}"
SPYSERVER_PORT="${SPYSERVER_PORT:-5555}"

write_optional_setting() {
  local key="$1"
  local value="$2"
  if [ -n "$value" ]; then
    printf '%s = %s\n' "$key" "$value" >> "$CONFIG_PATH"
  fi
}

cat > "$CONFIG_PATH" <<EOF
# Generated from container environment. Edit .env, not this file.

bind_host = 0.0.0.0
bind_port = ${SPYSERVER_PORT}

list_in_directory = ${SPYSERVER_LIST_IN_DIRECTORY:-0}
owner_name = ${SPYSERVER_OWNER_NAME:-}
owner_email = ${SPYSERVER_OWNER_EMAIL:-}
antenna_type = ${SPYSERVER_ANTENNA_TYPE:-}
antenna_location = ${SPYSERVER_ANTENNA_LOCATION:-}
general_description = ${SPYSERVER_DESCRIPTION:-SA8818 second RTL-SDR}

maximum_clients = ${SPYSERVER_MAXIMUM_CLIENTS:-1}
allow_control = ${SPYSERVER_ALLOW_CONTROL:-1}

device_type = ${SPYSERVER_DEVICE_TYPE:-RTL-SDR}
device_serial = ${SPYSERVER_DEVICE_SERIAL:-0}

fft_fps = ${SPYSERVER_FFT_FPS:-15}
fft_bin_bits = ${SPYSERVER_FFT_BIN_BITS:-15}

rtl_sampling_mode = ${SPYSERVER_RTL_SAMPLING_MODE:-0}

input_buffer_size_ms = ${SPYSERVER_INPUT_BUFFER_SIZE_MS:-10}
input_buffer_count = ${SPYSERVER_INPUT_BUFFER_COUNT:-4}
output_buffer_size_ms = ${SPYSERVER_OUTPUT_BUFFER_SIZE_MS:-50}
EOF

write_optional_setting "maximum_session_duration" "${SPYSERVER_MAXIMUM_SESSION_DURATION:-}"
write_optional_setting "device_sample_rate" "${SPYSERVER_SAMPLE_RATE:-}"
write_optional_setting "force_8bit" "${SPYSERVER_FORCE_8BIT:-}"
write_optional_setting "maximum_bandwidth" "${SPYSERVER_MAXIMUM_BANDWIDTH:-}"
write_optional_setting "initial_frequency" "${SPYSERVER_INITIAL_FREQUENCY:-}"
write_optional_setting "minimum_frequency" "${SPYSERVER_MINIMUM_FREQUENCY:-}"
write_optional_setting "maximum_frequency" "${SPYSERVER_MAXIMUM_FREQUENCY:-}"
write_optional_setting "frequency_correction_ppb" "${SPYSERVER_FREQUENCY_CORRECTION_PPB:-}"
write_optional_setting "initial_gain" "${SPYSERVER_INITIAL_GAIN:-}"
write_optional_setting "converter_offset" "${SPYSERVER_CONVERTER_OFFSET:-}"
write_optional_setting "enable_bias_tee" "${SPYSERVER_ENABLE_BIAS_TEE:-}"

echo "spyserver: port=${SPYSERVER_PORT} device_type=${SPYSERVER_DEVICE_TYPE:-RTL-SDR} device_serial=${SPYSERVER_DEVICE_SERIAL:-0}"
exec /opt/spyserver/spyserver "$CONFIG_PATH"
