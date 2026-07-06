# SA8818 Panoramic RTL

Docker Compose stack for continuous panorama capture from two RTL-SDR dongles:

- `scanner-rtl1` runs `rtl_power` with `RTL1_*` settings and writes CSV files.
- `scanner-rtl2` runs `rtl_power` with `RTL2_*` settings and writes CSV files.
- `heatmap` converts all queued CSV files into PNG images.
- `web` serves a local gallery with source, band, and capture start/end timestamps.

Both scanners write into the same `data/csv` queue. The heatmap worker does not care which dongle produced a CSV; the source and band are carried in the filename and shown in the gallery.

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

RTL-SDR devices are mounted from `/dev/bus/usb` into scanner containers. Some DVB kernel modules can claim RTL-SDR dongles. If `rtl_test` or `rtl_power` cannot open a device, blacklist the DVB drivers on the host.

## Configuration

Edit `.env`:

```dotenv
STATION_NAME=SA8818

RTL1_NAME=RTL1
RTL1_DEVICE_INDEX=0
RTL1_FREQUENCY_RANGE=30M:500M:10K
RTL1_GAIN=22.5
RTL1_CAPTURE_DURATION=60m

RTL2_NAME=RTL2
RTL2_DEVICE_INDEX=1
RTL2_FREQUENCY_RANGE=500M:1000M:10K
RTL2_GAIN=22.5
RTL2_CAPTURE_DURATION=60m
```

Useful scanner knobs:

- `RTL1_DEVICE_INDEX` / `RTL2_DEVICE_INDEX`: `0`, `1`, etc. as seen by `rtl_power`.
- `RTL*_NAME`: source label shown in filenames and gallery, for example `ANT-UHF` or `ANT-VHF`.
- `RTL*_FREQUENCY_RANGE`: passed directly to `rtl_power -f`.
- `RTL*_GAIN`: passed directly to `rtl_power -g`.
- `RTL*_INTERVAL`: passed to `rtl_power -i`.
- `RTL*_CROP`: passed to `rtl_power -c`.
- `RTL*_CAPTURE_DURATION`: passed to `rtl_power -e`, for example `1m`, `30m`, `1h`.
- `RTL*_EXTRA_ARGS`: optional extra `rtl_power` flags.

Useful heatmap knobs:

- `HEATMAP_COLORMAP`: matplotlib colormap, default `afmhot`.
- `HEATMAP_WIDTH_PX` / `HEATMAP_HEIGHT_PX`: rendered PNG size.
- `HEATMAP_FREQ_BINS`: horizontal frequency bins used before plotting. `4096` is a good default; try `8192` for more detail.
- `HEATMAP_XTICKS`: x-axis label spacing. Avoid `1MHz` for wide captures because it creates hundreds of labels; `50MHz` is the default.

Wide captures contain far more frequency bins than a normal PNG can display one-to-one. The renderer compresses frequency samples into `HEATMAP_FREQ_BINS` using max pooling, so narrow transmissions stay visible instead of being averaged away by image resizing.

## Data Layout

Runtime files are created under `./data`:

```text
data/
  csv/        active and queued captures
  processed/  CSV files after successful PNG rendering
  png/        gallery images and sidecar metadata
  failed/     CSV files that failed rendering
```

CSV filenames include station, source, band, start, and stop:

```text
sa8818-rtl1-30m-500m-10k-20260706153000-20260706163000.csv
sa8818-rtl2-500m-1000m-10k-20260706153000-20260706163000.csv
```

PNG files keep the same base name:

```text
sa8818-rtl1-30m-500m-10k-20260706153000-20260706163000.png
```

## Commands

```bash
docker compose logs -f scanner-rtl1
docker compose logs -f scanner-rtl2
docker compose logs -f heatmap
docker compose logs -f web
docker compose down
```
