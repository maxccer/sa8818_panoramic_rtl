import os
import json
import shutil
import subprocess
import time
from pathlib import Path


DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
CSV_DIR = Path(os.getenv("CSV_DIR", DATA_DIR / "csv"))
PNG_DIR = Path(os.getenv("PNG_DIR", DATA_DIR / "png"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", DATA_DIR / "processed"))
FAILED_DIR = Path(os.getenv("FAILED_DIR", DATA_DIR / "failed"))
POLL_SECONDS = float(os.getenv("HEATMAP_POLL_SECONDS", "5"))


def env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def build_heatmap_command(csv_path: Path, png_path: Path) -> list[str]:
    command = [
        "python",
        "/app/rtl_heatmap.py",
        "-i",
        str(csv_path),
        "-o",
        str(png_path),
        "-c",
        os.getenv("HEATMAP_COLORMAP", "afmhot"),
        "--xticks",
        os.getenv("HEATMAP_XTICKS", "50MHz"),
        "--yticks",
        os.getenv("HEATMAP_YTICKS", "10m"),
        "--width-px",
        os.getenv("HEATMAP_WIDTH_PX", "4096"),
        "--height-px",
        os.getenv("HEATMAP_HEIGHT_PX", "2300"),
        "--dpi",
        os.getenv("HEATMAP_DPI", "120"),
    ]

    freq_bins = os.getenv("HEATMAP_FREQ_BINS", "").strip()
    if freq_bins:
        command.extend(["--freq-bins", freq_bins])

    if env_flag("HEATMAP_COLORBAR", "1"):
        command.append("--colorbar")
    if env_flag("HEATMAP_XLINES", "1"):
        command.append("--xlines")
    if env_flag("HEATMAP_YLINES", "1"):
        command.append("--ylines")

    return command


def process_csv(csv_path: Path) -> None:
    png_path = PNG_DIR / f"{csv_path.stem}.png"
    meta_path = PNG_DIR / f"{csv_path.stem}.json"
    lock_path = CSV_DIR / f".{csv_path.name}.lock"

    try:
        csv_path.rename(lock_path)
    except FileNotFoundError:
        return

    try:
        subprocess.run(build_heatmap_command(lock_path, png_path), check=True)
        meta_path.write_text(
            json.dumps({"csv": csv_path.name, "png": png_path.name}) + "\n",
            encoding="utf-8",
        )
        shutil.move(str(lock_path), str(PROCESSED_DIR / csv_path.name))
        print(f"heatmap: rendered {png_path}", flush=True)
    except Exception as exc:
        print(f"heatmap: failed {csv_path.name}: {exc}", flush=True)
        shutil.move(str(lock_path), str(FAILED_DIR / csv_path.name))


def main() -> None:
    for path in (CSV_DIR, PNG_DIR, PROCESSED_DIR, FAILED_DIR):
        path.mkdir(parents=True, exist_ok=True)

    print(f"heatmap: watching {CSV_DIR}", flush=True)
    while True:
        for csv_path in sorted(CSV_DIR.glob("*.csv")):
            process_csv(csv_path)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
