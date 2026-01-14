from __future__ import annotations
import yaml
from pathlib import Path
import subprocess
from datetime import datetime
import sys

def run(cmd: list[str]) -> None:
    if cmd and cmd[0] == "python":
        cmd[0] = sys.executable
    print(" ".join(cmd))
    subprocess.check_call(cmd)

def main() -> None:
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    batch = cfg.get("batch") or []
    entries = batch if batch else [{
        "preset": "brown_noise",
        "title": cfg["track"]["title"],
        "filename_base": cfg["output"]["filename_base"],
    }]

    for entry in entries:
        preset = entry["preset"]
        title = entry["title"]
        base = entry["filename_base"]
        target_rms_db = entry.get("target_rms_db", cfg["audio"]["target_rms_db"])
        peak_ceiling_linear = entry.get("peak_ceiling_linear", 0.98)
        release_dir = Path(cfg["output"]["release_root"]) / f"{ts}_{preset}"
        release_dir.mkdir(parents=True, exist_ok=True)

        raw_wav = release_dir / f"{base}_raw.wav"
        final_wav = release_dir / f"{base}_final.wav"
        meta_json = release_dir / "metadata.json"
        cover_jpg = release_dir / "cover.jpg"
        qc_json = release_dir / "qc_report.json"
        manifest_txt = release_dir / "manifest.txt"
        release_zip = release_dir / "release_pack.zip"

        hours_val = cfg["audio"]["duration_hours"]
        hours_str = f"{hours_val:g}"
        description_tpl = cfg["track"]["description"]
        description = description_tpl.format(hours=hours_str, title=title, preset=preset)

        # 1) Generate
        run(["python", "generate_sleep_noise.py",
             "--out", str(raw_wav),
             "--hours", str(hours_val),
             "--sr", str(cfg["audio"]["sample_rate"]),
             "--preset", preset])

        # 2) Postprocess
        run(["python", "postprocess.py",
             "--in", str(raw_wav),
             "--out", str(final_wav),
             "--sr", str(cfg["audio"]["sample_rate"]),
             "--target_rms_db", str(target_rms_db),
             "--fade_seconds", str(cfg["audio"]["fade_seconds"]),
             "--highpass_hz", str(cfg["audio"]["highpass_hz"]),
             "--lowpass_hz", str(cfg["audio"]["lowpass_hz"]),
             "--peak_ceiling_linear", str(peak_ceiling_linear)])

        # 3) Metadata
        run(["python", "metadata_builder.py",
             "--out", str(meta_json),
             "--artist", cfg["project_name"],
             "--title", title,
             "--album", cfg["album_name"],
             "--genre", cfg["track"]["genre"],
             "--mood", *cfg["track"]["mood"],
             "--description", description])

        # 4) Cover
        run(["python", "cover_generator.py",
             "--out", str(cover_jpg),
             "--title", title,
             "--artist", cfg["project_name"]])

        # 5) QC report
        run(["python", "qc_report.py",
             "--release_dir", str(release_dir),
             "--final_wav", str(final_wav),
             "--cover", str(cover_jpg),
             "--metadata", str(meta_json),
             "--out", str(qc_json),
             "--target_rms_db", str(target_rms_db),
             "--preset_name", preset,
             "--peak_ceiling_linear", str(peak_ceiling_linear)])

        # 6) Pack release
        run(["python", "pack_release.py",
             "--release_dir", str(release_dir),
             "--qc_report", str(qc_json),
             "--manifest", str(manifest_txt),
             "--out_zip", str(release_zip)])

        print("\nREADY FOR UPLOAD:")
        print(final_wav)
        print(cover_jpg)
        print(meta_json)

if __name__ == "__main__":
    main()


