from __future__ import annotations

from pathlib import Path
import json
import zipfile
import hashlib
from datetime import datetime


def write_manifest(qc: dict, out_path: Path) -> None:
    lines = [
        f"artist: {qc.get('artist', '')}",
        f"title: {qc.get('title', '')}",
        f"album: {qc.get('album', '')}",
        f"genre: {qc.get('genre', '')}",
        f"preset_name: {qc.get('preset_name', '')}",
        f"peak_ceiling_linear: {qc.get('peak_ceiling_linear', '')}",
        f"target_rms_db: {qc.get('target_rms_db', '')}",
        f"duration: {qc.get('duration_seconds', '')} sec",
        f"sample_rate: {qc.get('sample_rate', '')}",
        f"file_size_mb: {qc.get('file_size_mb', '')}",
        f"rms_dbfs: {qc.get('rms_dbfs', '')}",
        f"peak_dbfs: {qc.get('peak_dbfs', '')}",
        f"cover: {qc.get('cover_width_px', '')}x{qc.get('cover_height_px', '')} px, {qc.get('cover_file_size_mb', '')} MB",
        f"release_pack_sha256_file: {qc.get('release_pack_sha256_file', '')}",
        f"sha256_final_wav: {qc.get('final_wav_sha256', '')}",
        f"created_at: {datetime.now().isoformat(timespec='seconds')}",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_zip(release_dir: Path, zip_path: Path, qc: dict) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            qc.get("wav_filename", ""),
            qc.get("cover_filename", ""),
            qc.get("metadata_filename", ""),
            "qc_report.json",
            "manifest.txt",
        ]:
            file_path = release_dir / name
            if file_path.exists():
                zf.write(file_path, arcname=file_path.name)


def main(release_dir: str, qc_report: str, out_zip: str, manifest: str) -> None:
    release_path = Path(release_dir)
    qc_path = Path(qc_report)
    manifest_path = Path(manifest)
    qc = json.loads(qc_path.read_text(encoding="utf-8"))

    write_manifest(qc, manifest_path)
    make_zip(release_path, Path(out_zip), qc)
    sha_path = release_path / "release_pack.sha256"
    sha = sha256_file(Path(out_zip))
    sha_path.write_text(f"{sha}  release_pack.zip\n", encoding="utf-8")
    print(f"Manifest written: {manifest_path}")
    print(f"Release pack written: {out_zip}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--release_dir", required=True)
    p.add_argument("--qc_report", required=True)
    p.add_argument("--out_zip", required=True)
    p.add_argument("--manifest", required=True)
    args = p.parse_args()
    main(args.release_dir, args.qc_report, args.out_zip, args.manifest)
