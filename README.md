# audio-factory

Fully automated pipeline to generate, post-process, quality-check, and package generic audio content  
(e.g. Sleep / Noise / Ambient) for distribution workflows.

## What it does
Given one or multiple presets, the pipeline:

1) Generates audio (e.g. brown noise, fan noise, rain, ocean)  
2) Post-processes (filters, fades, RMS normalization, peak ceiling)  
3) Computes QC metrics (duration, RMS, peak, sample rate, file size)  
4) Builds distributor-friendly metadata + cover art (3000×3000)  
5) Packages a release (ZIP + manifest + SHA256)

## Repository design
- `releases/` outputs are intentionally excluded via `.gitignore` (no large binaries in git)
- Repository contains code and configuration only

## Quickstart (Windows)
```bash
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m audio_factory.run_pipeline --config config.yaml
Configuration
All production parameters are defined in config.yaml, including:

batch presets

duration

RMS targets

peak ceilings

export settings

Output structure
Each pipeline run creates a release folder under releases/ (ignored by git):

diff
Code kopieren
releases/<release_id>/
- final.wav
- cover.jpg
- metadata.json
- qc_report.json
- manifest.txt
- release_pack.zip
- release_pack.sha256
Quality gates
A release is considered upload-ready only if:

RMS and peak values match preset targets

duration is within tolerance (±0.1%)

sample rate and bit depth match configuration

SHA256 checksum matches the packaged ZIP

Typical usage
Batch production of multiple presets in a single run

Short validation runs (e.g. 0.05h) before long renders

Deterministic, reproducible release generation via config-only changes

Scope
This project focuses on automated audio content production, quality control, and packaging.
Distributor uploads and store-side optimizations are handled externally.

Roadmap
CI dry-run pipeline (short renders)

QC schema validation

Preset catalog scaling

Distributor upload checklists

License
MIT<
