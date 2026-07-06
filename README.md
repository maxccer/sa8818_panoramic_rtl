# SA8818 Panoramic RTL

Docker Compose stack for continuous RTL-SDR panorama capture:

- `scanner` runs `rtl_power` against one RTL-SDR dongle and writes CSV files.
- `heatmap` converts new CSV files to PNG images.
- `web` serves a local gallery with capture start/end timestamps.

The second RTL-SDR dongle is intentionally unused for now. The default config uses device index `0`.

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
docker compose down
```
