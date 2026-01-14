from __future__ import annotations
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt
from pathlib import Path
import math

def butter_filter(x: np.ndarray, sr: int, lowpass_hz: float | None, highpass_hz: float | None) -> np.ndarray:
    y = x
    if highpass_hz and highpass_hz > 0:
        b, a = butter(2, highpass_hz / (sr / 2), btype="highpass")
        y = filtfilt(b, a, y).astype(np.float32)
    if lowpass_hz and lowpass_hz > 0:
        b, a = butter(2, lowpass_hz / (sr / 2), btype="lowpass")
        y = filtfilt(b, a, y).astype(np.float32)
    return y

def apply_fade(x: np.ndarray, sr: int, fade_seconds: int) -> np.ndarray:
    fade_len = int(fade_seconds * sr)
    if fade_len <= 0 or fade_len * 2 > len(x):
        return x
    fade_in = np.linspace(0, 1, fade_len, dtype=np.float32)
    fade_out = np.linspace(1, 0, fade_len, dtype=np.float32)
    x[:fade_len] *= fade_in
    x[-fade_len:] *= fade_out
    return x

def rms_db(x: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(x), dtype=np.float64)) + 1e-12)
    return 20 * math.log10(rms)

def normalize_to_rms_db(x: np.ndarray, target_db: float, peak_ceiling_linear: float = 0.98) -> np.ndarray:
    current_db = rms_db(x)
    gain_db = target_db - current_db
    gain = 10 ** (gain_db / 20)
    y = (x * gain).astype(np.float32)

    # Hard safety: prevent clipping
    peak = np.max(np.abs(y)) + 1e-12
    if peak > peak_ceiling_linear:
        y = (y / peak * peak_ceiling_linear).astype(np.float32)
    return y

def main(
    inp: str,
    out: str,
    sr: int,
    target_rms_db: float,
    fade_seconds: int,
    hp: float,
    lp: float,
    peak_ceiling_linear: float,
) -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    x, file_sr = sf.read(inp, dtype="float32")
    if file_sr != sr:
        raise ValueError(f"Sample rate mismatch: file={file_sr}, expected={sr}")

    y = butter_filter(x, sr=sr, lowpass_hz=lp, highpass_hz=hp)
    y = apply_fade(y, sr=sr, fade_seconds=fade_seconds)
    y = normalize_to_rms_db(y, target_db=target_rms_db, peak_ceiling_linear=peak_ceiling_linear)

    sf.write(out, y, sr, subtype="PCM_16")
    peak = float(np.max(np.abs(y))) + 1e-12
    peak_db = 20 * math.log10(peak)
    print(f"Processed audio: {out}")
    print(f"RMS dB (approx): {rms_db(y):.2f} dBFS")
    print(f"Peak (linear): {peak:.6f}")
    print(f"Peak (dBFS): {peak_db:.2f} dBFS")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--sr", type=int, default=44100)
    p.add_argument("--target_rms_db", type=float, default=-20.0)
    p.add_argument("--fade_seconds", type=int, default=15)
    p.add_argument("--highpass_hz", type=float, default=18.0)
    p.add_argument("--lowpass_hz", type=float, default=1200.0)
    p.add_argument("--peak_ceiling_linear", type=float, default=0.98)
    args = p.parse_args()
    main(
        args.inp,
        args.out,
        args.sr,
        args.target_rms_db,
        args.fade_seconds,
        args.highpass_hz,
        args.lowpass_hz,
        args.peak_ceiling_linear,
    )
