# SA8818 Panoramic RTL

Docker Compose stack for continuous RTL-SDR panorama capture:

- `scanner` runs `rtl_power` against one RTL-SDR dongle and writes CSV files.
- `heatmap` converts new CSV files to PNG images.
- `web` serves a local gallery with capture start/end timestamps.
- `spyserver` optionally exposes the second RTL-SDR dongle to SDR# over TCP.

The default scanner config uses device index `0`. SpyServer is optional and is intended for the second dongle.

## Quick Start

```bash
git clone <your-repo-url> sa8818_panoramic_rtl
cd sa8818_panoramic_rtl
cp .env.example .env
docker compose up -d --build
```

Open:

```text
http://<mini-computer-ip>:8080
```

## Debian Host Notes

Install Docker and Compose plugin if needed:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker "$USER"
```

Log out and back in after adding the user to the `docker` group.

RTL-SDR devices are mounted from `/dev/bus/usb` into the scanner container. If a host service grabs the dongle, stop it:

```bash
sudo systemctl stop rtl-sdr.service 2>/dev/null || true
```

Some DVB kernel modules can also claim RTL-SDR dongles. If `rtl_test` or `rtl_power` cannot open the device, blacklist the DVB drivers on the host.

## Configuration

Edit `.env`:

```dotenv
RTL_DEVICE_INDEX=0
RTL_FREQUENCY_RANGE=30M:1000M:10K
RTL_GAIN=22.5
RTL_CAPTURE_DURATION=1m
WEB_PORT=8080
```

Useful knobs:

- `RTL_DEVICE_INDEX`: `0` for the first dongle, `1` for the second.
- `RTL_FREQUENCY_RANGE`: passed directly to `rtl_power -f`.
- `RTL_GAIN`: passed directly to `rtl_power -g`.
- `RTL_CAPTURE_DURATION`: passed to `rtl_power -e`, for example `1m`, `10m`, `1h`.
- `HEATMAP_COLORMAP`: matplotlib colormap, default `afmhot`.
- `HEATMAP_WIDTH_PX` / `HEATMAP_HEIGHT_PX`: rendered PNG size.
- `HEATMAP_FREQ_BINS`: horizontal frequency bins used before plotting. `4096` is a good default for a 30-1000 MHz one-hour capture; try `8192` for more detail.
- `HEATMAP_XTICKS`: x-axis label spacing. Avoid `1MHz` for wide captures because it creates hundreds of labels; `50MHz` is the default.

Wide one-hour captures contain far more frequency bins than a normal PNG can display one-to-one. The renderer compresses frequency samples into `HEATMAP_FREQ_BINS` using max pooling, so narrow transmissions stay visible instead of being averaged away by image resizing.

## SpyServer for SDR#

The `spyserver` service downloads the official Airspy Linux x86_64 SpyServer build during Docker image build. Airspy documents SpyServer as supporting RTL-SDR receivers, and the Linux x86_64 build requires a 64-bit Intel/AMD CPU with AVX2/FMA.

Start scanner, heatmap, web, and SpyServer:

```bash
docker compose up -d --build
```

Connect from SDR# to:

```text
spyserver://<mini-computer-ip>:5555
```

Config lives in `.env`:

```dotenv
SPYSERVER_PORT=5555
SPYSERVER_START_DELAY=5
SPYSERVER_DEVICE_TYPE=RTL-SDR
SPYSERVER_DEVICE_SERIAL=0
SPYSERVER_SAMPLE_RATE=2048000
SPYSERVER_MAXIMUM_CLIENTS=10
```

`SPYSERVER_DEVICE_SERIAL=0` means "first available device". This is also the setting used by the known-working baremetal SpyServer config. Because `scanner` starts first and holds device index `0`, SpyServer should normally take the other dongle.

For reliable long-term operation with two identical RTL-SDR sticks, give them unique serial numbers on the Debian host:

```bash
docker compose down
sudo apt install -y rtl-sdr
rtl_eeprom
rtl_eeprom -d 0 -s 00000001
rtl_eeprom -d 1 -s 00000002
```

Unplug/replug the dongles after changing EEPROM serials. Then set:

```dotenv
RTL_DEVICE_INDEX=0
SPYSERVER_DEVICE_SERIAL=0
```

Even after assigning unique EEPROM serials, keep SpyServer at `0` unless you have verified that its `device_serial` parser matches your RTL-SDR serial format.

If you expose SpyServer outside your LAN, firewall it carefully. SDR# control is enabled by default with `SPYSERVER_ALLOW_CONTROL=1`.

If SpyServer logs `usb_claim_interface error -6`, the device it tried to open is already busy. Check from inside the same container:

```bash
docker compose stop spyserver
docker compose run --rm --no-deps spyserver rtl_test -d 0 -t
docker compose run --rm --no-deps spyserver rtl_test -d 1 -t
```

With `scanner` running, `-d 0` should usually fail because scanner owns it, and `-d 1` should pass. If `-d 1` passes, set SpyServer to the second EEPROM serial in `.env`, for example:

```dotenv
SPYSERVER_DEVICE_SERIAL=22222222
```

Then recreate SpyServer:

```bash
docker compose up -d --force-recreate spyserver
```

## Data Layout

Runtime files are created under `./data`:

```text
data/
  csv/        active and queued captures
  processed/  CSV files after successful PNG rendering
  png/        gallery images and sidecar metadata
  failed/     CSV files that failed rendering
```

CSV filenames include start and stop timestamps:

```text
sa8818-202607061530-202607061531.csv
```

PNG files keep the same base name:

```text
sa8818-202607061530-202607061531.png
```

## Commands

```bash
docker compose logs -f scanner
docker compose logs -f heatmap
docker compose logs -f web
docker compose logs -f spyserver
docker compose down
```
