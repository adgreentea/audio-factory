from __future__ import annotations
import math
import numpy as np
import soundfile as sf
from pathlib import Path


BASE_GAIN_6DB = 10 ** (-6 / 20)


def moving_average_block(x: np.ndarray, window: int, tail: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if window <= 1:
        return x, tail
    if tail.size < window - 1:
        pad = np.zeros(window - 1 - tail.size, dtype=np.float32)
        tail = np.concatenate([pad, tail])
    extended = np.concatenate([tail, x])
    cumsum = np.cumsum(extended, dtype=np.float64)
    cumsum = np.concatenate([np.array([0.0], dtype=np.float64), cumsum])
    y = (cumsum[window:] - cumsum[:-window]) / window
    new_tail = extended[-(window - 1):] if window > 1 else np.array([], dtype=np.float32)
    return y.astype(np.float32), new_tail.astype(np.float32)


def generate_block(preset: str, n: int, sr: int, rng: np.random.Generator, state: dict) -> tuple[np.ndarray, dict]:
    if preset == "brown_noise":
        white = rng.standard_normal(n).astype(np.float32)
        brown = np.cumsum(white) + state.get("brown_last", 0.0)
        brown = (brown * 0.02).astype(np.float32)
        brown -= float(np.mean(brown))
        state["brown_last"] = float(brown[-1])
        return (brown * BASE_GAIN_6DB).astype(np.float32), state

    if preset == "fan_noise":
        white = rng.standard_normal(n).astype(np.float32)
        brown = np.cumsum(white) + state.get("brown_last", 0.0)
        brown = (brown * 0.02).astype(np.float32)
        brown -= float(np.mean(brown))
        state["brown_last"] = float(brown[-1])
        mix = (0.7 * brown + 0.3 * white * 0.05).astype(np.float32)
        window = max(3, int(sr / 800))
        y, tail = moving_average_block(mix, window, state.get("lp_tail", np.array([], dtype=np.float32)))
        state["lp_tail"] = tail
        return (y * BASE_GAIN_6DB).astype(np.float32), state

    if preset == "rain_window":
        white = rng.standard_normal(n).astype(np.float32) * 0.05
        hp_window = max(3, int(sr / 200))
        lp_window = max(3, int(sr / 3500))
        low, tail_hp = moving_average_block(white, hp_window, state.get("hp_tail", np.array([], dtype=np.float32)))
        high = (white - low).astype(np.float32)
        band, tail_lp = moving_average_block(high, lp_window, state.get("lp_tail", np.array([], dtype=np.float32)))
        state["hp_tail"] = tail_hp
        state["lp_tail"] = tail_lp

        block_duration = n / sr
        rate = 1.0 / 120.0
        events = rng.poisson(rate * block_duration)
        for _ in range(int(events)):
            pos = int(rng.integers(0, n))
            length = int(min(n - pos, sr * 0.01))
            if length <= 0:
                continue
            env = np.exp(-np.arange(length, dtype=np.float32) / (sr * 0.003))
            band[pos:pos + length] += (rng.standard_normal(length).astype(np.float32) * env * 0.01)
        return band, state

    if preset == "ocean_waves":
        white = rng.standard_normal(n).astype(np.float32) * 0.04
        window = max(3, int(sr / 600))
        y, tail = moving_average_block(white, window, state.get("lp_tail", np.array([], dtype=np.float32)))
        state["lp_tail"] = tail

        phase = float(state.get("phase", 0.0))
        period = float(state.get("period", rng.uniform(8.0, 14.0)))
        omega = 2 * math.pi / period
        t = (np.arange(n, dtype=np.float32) / sr)
        mod = 0.4 + 0.6 * (0.5 + 0.5 * np.sin(phase + omega * t))
        phase = (phase + omega * (n / sr)) % (2 * math.pi)
        if rng.random() < 0.2:
            period = float(rng.uniform(8.0, 14.0))
        state["phase"] = phase
        state["period"] = period
        return (y * mod).astype(np.float32), state

    raise ValueError(f"Unknown preset: {preset}")


def generate_noise_to_file(out_path: str, duration_sec: float, sr: int, preset: str, seed: int | None) -> None:
    rng = np.random.default_rng(seed)
    total_frames = int(duration_sec * sr)
    block_frames = 65536
    state: dict = {}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with sf.SoundFile(out_path, mode="w", samplerate=sr, channels=1, subtype="PCM_16") as f:
        written = 0
        while written < total_frames:
            n = min(block_frames, total_frames - written)
            block, state = generate_block(preset, n, sr, rng, state)
            block = np.clip(block, -1.0, 1.0)
            f.write(block)
            written += n


def main(out_path: str, duration_hours: float, sr: int, preset: str) -> None:
    duration_sec = float(duration_hours) * 3600
    generate_noise_to_file(out_path=out_path, duration_sec=duration_sec, sr=sr, preset=preset, seed=None)
    print(f"Generated raw audio: {out_path}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--hours", type=float, default=8)
    p.add_argument("--sr", type=int, default=44100)
    p.add_argument("--preset", default="brown_noise")
    args = p.parse_args()
    main(args.out, args.hours, args.sr, args.preset)
