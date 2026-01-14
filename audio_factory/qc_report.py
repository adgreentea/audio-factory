from __future__ import annotations

from pathlib import Path
import json
import math
import hashlib
import soundfile as sf
import numpy as np
from PIL import Image


def stream_metrics(wav_path: Path, block_frames: int = 65536) -> tuple[float, float]:
    peak = 0.0
    sum_squares = 0.0
    count = 0
    with sf.SoundFile(str(wav_path), mode="r") as f:
        while True:
            block = f.read(block_frames, dtype="float32")
            if block.size == 0:
                break
            peak = max(peak, float(np.max(np.abs(block))))
            sum_squares += float(np.sum(np.square(block), dtype=np.float64))
            count += block.size
    if count == 0:
        return 0.0, float("-inf")
    rms = math.sqrt(sum_squares / count)
    rms_db = 20 * math.log10(rms + 1e-12)
    return peak, rms_db


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()



def main(
    release_dir: str,
    final_wav: str,
    cover: str,
    metadata: str,
    out_path: str,
    target_rms_db: float,
    preset_name: str,
    peak_ceiling_linear: float,
) -> None:
    release_path = Path(release_dir)
    wav_path = Path(final_wav)
    cover_path = Path(cover)
    meta_path = Path(metadata)
    info = sf.info(str(wav_path))
    with Image.open(cover_path) as img:
        cover_width, cover_height = img.size
    cover_file_size_mb = cover_path.stat().st_size / (1024 * 1024)

    peak_linear, rms_dbfs = stream_metrics(wav_path)
    peak_dbfs = 20 * math.log10(peak_linear + 1e-12)
    file_size_mb = wav_path.stat().st_size / (1024 * 1024)

    meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
    payload = {
        "timestamp": release_path.name,
        "artist": meta_payload.get("artist", ""),
        "title": meta_payload.get("title", ""),
        "album": meta_payload.get("album", ""),
        "genre": meta_payload.get("genre", ""),
        "preset_name": preset_name,
        "peak_ceiling_linear": peak_ceiling_linear,
        "cover_width_px": cover_width,
        "cover_height_px": cover_height,
        "cover_file_size_mb": cover_file_size_mb,
        "release_pack_sha256_file": "release_pack.sha256",
        "final_wav_sha256": sha256_file(wav_path),
        "duration_seconds": info.frames / info.samplerate,
        "sample_rate": info.samplerate,
        "file_size_mb": file_size_mb,
        "target_rms_db": target_rms_db,
        "rms_dbfs": rms_dbfs,
        "peak_linear": peak_linear,
        "peak_dbfs": peak_dbfs,
        "wav_filename": wav_path.name,
        "cover_filename": cover_path.name,
        "metadata_filename": meta_path.name,
    }
    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"QC report written: {out_path}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--release_dir", required=True)
    p.add_argument("--final_wav", required=True)
    p.add_argument("--cover", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--target_rms_db", type=float, required=True)
    p.add_argument("--preset_name", required=True)
    p.add_argument("--peak_ceiling_linear", type=float, required=True)
    args = p.parse_args()
    main(
        args.release_dir,
        args.final_wav,
        args.cover,
        args.metadata,
        args.out,
        args.target_rms_db,
        args.preset_name,
        args.peak_ceiling_linear,
    )
