import argparse
import csv
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render rtl_power CSV as a PNG heatmap.")
    parser.add_argument("-i", "--input", required=True, help="Input rtl_power CSV file")
    parser.add_argument("-o", "--output", required=True, help="Output PNG file")
    parser.add_argument("-c", "--colormap", default="afmhot", help="Matplotlib colormap")
    parser.add_argument("--colorbar", action="store_true", help="Show colorbar")
    parser.add_argument("--xticks", default="1MHz", help="Approximate x tick spacing, e.g. 1MHz")
    parser.add_argument("--yticks", default="10m", help="Approximate y tick spacing, e.g. 10m")
    parser.add_argument("--xlines", action="store_true", help="Show vertical grid lines")
    parser.add_argument("--ylines", action="store_true", help="Show horizontal grid lines")
    parser.add_argument("--width-px", type=int, default=4096, help="Output image width in pixels")
    parser.add_argument("--height-px", type=int, default=2300, help="Output image height in pixels")
    parser.add_argument("--dpi", type=int, default=120, help="Output image DPI")
    parser.add_argument(
        "--freq-bins",
        type=int,
        default=0,
        help="Horizontal frequency bins before plotting. 0 uses the output width.",
    )
    return parser.parse_args()


def parse_frequency(value: str) -> float:
    raw = value.strip().lower()
    multiplier = 1.0
    if raw.endswith("mhz"):
        multiplier = 1_000_000.0
        raw = raw[:-3]
    elif raw.endswith("khz"):
        multiplier = 1_000.0
        raw = raw[:-3]
    elif raw.endswith("m"):
        multiplier = 1_000_000.0
        raw = raw[:-1]
    elif raw.endswith("k"):
        multiplier = 1_000.0
        raw = raw[:-1]
    return float(raw) * multiplier


def parse_duration(value: str) -> int:
    raw = value.strip().lower()
    if raw.endswith("h"):
        return int(float(raw[:-1]) * 3600)
    if raw.endswith("m"):
        return int(float(raw[:-1]) * 60)
    if raw.endswith("s"):
        return int(float(raw[:-1]))
    return int(float(raw))


def iter_rtl_power_rows(path: Path):
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 7:
                continue
            timestamp = f"{row[0].strip()} {row[1].strip()}"
            try:
                start_hz = float(row[2])
                step_hz = float(row[4])
                values = np.array([float(value) for value in row[6:] if value.strip()], dtype=np.float32)
            except ValueError:
                continue

            if values.size == 0 or step_hz <= 0:
                continue

            yield timestamp, start_hz, step_hz, values


def scan_csv_bounds(path: Path) -> tuple[list[str], float, float]:
    seen_times: set[str] = set()
    times: list[str] = []
    min_freq = math.inf
    max_freq = -math.inf

    for timestamp, start_hz, step_hz, values in iter_rtl_power_rows(path):
        if timestamp not in seen_times:
            seen_times.add(timestamp)
            times.append(timestamp)
        min_freq = min(min_freq, start_hz)
        max_freq = max(max_freq, start_hz + (values.size - 1) * step_hz)

    if not times or not math.isfinite(min_freq) or not math.isfinite(max_freq):
        raise ValueError(f"No rtl_power samples found in {path}")

    return sorted(times), min_freq, max_freq


def load_rtl_power_csv(path: Path, freq_bins: int) -> tuple[np.ndarray, np.ndarray, list[datetime]]:
    times, min_freq, max_freq = scan_csv_bounds(path)
    time_index = {timestamp: index for index, timestamp in enumerate(times)}
    freq_bins = max(512, freq_bins)
    freq_span = max(max_freq - min_freq, 1.0)

    matrix = np.full((len(times), freq_bins), -np.inf, dtype=np.float32)
    for timestamp, start_hz, step_hz, values in iter_rtl_power_rows(path):
        freqs = start_hz + np.arange(values.size, dtype=np.float64) * step_hz
        bins = np.floor((freqs - min_freq) / freq_span * (freq_bins - 1)).astype(np.int32)
        bins = np.clip(bins, 0, freq_bins - 1)
        row = matrix[time_index[timestamp]]
        np.maximum.at(row, bins, values)

    matrix[matrix == -np.inf] = np.nan
    freqs = np.linspace(min_freq, max_freq, freq_bins)
    parsed_times = [datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") for timestamp in times]
    return matrix, freqs, parsed_times


def nice_stride(total: int, target: int) -> int:
    if total <= target:
        return 1
    return max(1, math.ceil(total / target))


def render_heatmap(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width_px = max(1200, args.width_px)
    height_px = max(800, args.height_px)
    dpi = max(72, args.dpi)
    freq_bins = args.freq_bins if args.freq_bins > 0 else width_px

    matrix, freqs, times = load_rtl_power_csv(input_path, freq_bins)
    masked = np.ma.masked_invalid(matrix)

    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)

    image = ax.imshow(masked, aspect="auto", interpolation="nearest", cmap=args.colormap, origin="lower")
    image.set_resample(False)
    start_mhz = freqs[0] / 1_000_000
    stop_mhz = freqs[-1] / 1_000_000
    ax.set_title(f"{input_path.stem}  |  {start_mhz:.3f}-{stop_mhz:.3f} MHz")
    ax.set_xlabel("Frequency, MHz")
    ax.set_ylabel("Time")

    try:
        x_spacing = parse_frequency(args.xticks)
        x_stride = max(1, round(x_spacing / max(freqs[1] - freqs[0], 1))) if len(freqs) > 1 else 1
    except Exception:
        x_stride = nice_stride(len(freqs), 12)

    x_positions = list(range(0, len(freqs), x_stride))
    if x_positions[-1] != len(freqs) - 1:
        x_positions.append(len(freqs) - 1)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f"{freqs[pos] / 1_000_000:.1f}" for pos in x_positions], rotation=45, ha="right")

    try:
        y_seconds = parse_duration(args.yticks)
        if len(times) > 1:
            seconds_per_row = max((times[-1] - times[0]).total_seconds() / (len(times) - 1), 1)
            y_stride = max(1, round(y_seconds / seconds_per_row))
        else:
            y_stride = 1
    except Exception:
        y_stride = nice_stride(len(times), 12)

    y_positions = list(range(0, len(times), y_stride))
    if y_positions[-1] != len(times) - 1:
        y_positions.append(len(times) - 1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([times[pos].strftime("%H:%M:%S") for pos in y_positions])

    if args.xlines:
        ax.grid(axis="x", color="white", alpha=0.18, linewidth=0.4)
    if args.ylines:
        ax.grid(axis="y", color="white", alpha=0.18, linewidth=0.4)
    if args.colorbar:
        cbar = fig.colorbar(image, ax=ax, pad=0.01)
        cbar.set_label("Power, dB")

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    render_heatmap(parse_args())


if __name__ == "__main__":
    main()
