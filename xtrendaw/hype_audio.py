"""High-energy sound design & music generator for viral challenge videos (MrBeast style).
Creates dramatic impacts, whooshes, countdown ticking, emergency sirens, and energetic music.
"""
import numpy as np
import wave
from pathlib import Path

SR = 44100

def _sine(freq: float, dur: float) -> np.ndarray:
    t = np.linspace(0, dur, int(dur * SR), endpoint=False)
    return np.sin(2 * np.pi * freq * t)

def _noise(dur: float) -> np.ndarray:
    return np.random.uniform(-1, 1, int(dur * SR)).astype(np.float32)

def generate_whoosh(dur: float = 0.6) -> np.ndarray:
    n = _noise(dur)
    t = np.linspace(0, 1, len(n))
    env = np.sin(np.pi * t) ** 2
    return (n * env * 0.4).astype(np.float32)

def generate_boom(dur: float = 1.8) -> np.ndarray:
    t = np.linspace(0, dur, int(dur * SR), endpoint=False)
    # Pitch bend from 140Hz down to 40Hz
    freq = np.linspace(140, 40, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase)
    env = np.exp(-t * 2.8)
    # Add slight punch noise at the very start
    punch = _noise(0.08) * np.linspace(1, 0, int(0.08 * SR))
    out = np.zeros(len(t), dtype=np.float32)
    out[:len(punch)] += punch * 0.5
    out += sub * env * 0.8
    return out

def generate_ticks(dur: float = 6.0, bpm: int = 140) -> np.ndarray:
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    interval = int((60.0 / bpm) * SR)
    for pos in range(0, n, interval):
        tick_len = int(0.02 * SR)
        if pos + tick_len < n:
            tick = np.sin(2 * np.pi * 1800 * np.linspace(0, 0.02, tick_len))
            tick *= np.exp(-np.linspace(0, 15, tick_len))
            out[pos:pos+tick_len] += tick * 0.35
    return out

def generate_siren(dur: float = 3.5) -> np.ndarray:
    t = np.linspace(0, dur, int(dur * SR), endpoint=False)
    mod = np.sin(2 * np.pi * 2.0 * t) # 2 Hz modulation
    freq = 800 + mod * 250
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return (np.sin(phase) * 0.35).astype(np.float32)

def generate_chime(dur: float = 2.0) -> np.ndarray:
    t = np.linspace(0, dur, int(dur * SR), endpoint=False)
    env = np.exp(-t * 2.5)
    bell = (np.sin(2 * np.pi * 1046.5 * t) + 0.6 * np.sin(2 * np.pi * 2093.0 * t)) * env
    return (bell * 0.45).astype(np.float32)

def build_hype_soundtrack(total_dur: float, out_wav: Path) -> Path:
    n = int(total_dur * SR)
    sfx = np.zeros(n, dtype=np.float32)
    
    def paste(arr, start_sec):
        s = int(start_sec * SR)
        L = min(len(arr), n - s)
        if s < n and L > 0:
            sfx[s:s+L] += arr[:L]

    # 1. Opening Hook: Sub boom + whoosh
    paste(generate_whoosh(0.7), 0.0)
    paste(generate_boom(2.0), 0.2)

    # 2. Tension ticking
    paste(generate_ticks(7.0, 140), 2.5)

    # 3. Cash reveal whoosh
    paste(generate_whoosh(0.6), 10.0)
    paste(generate_boom(1.5), 10.3)

    # 4. Cold drop / riser
    paste(generate_whoosh(0.8), 21.0)

    # 5. Alarm siren & rapid ticking in climax
    paste(generate_ticks(6.0, 180), 28.0)
    paste(generate_siren(3.5), 31.0)

    # 6. Climax boom & victory chime
    paste(generate_boom(2.2), 36.5)
    paste(generate_chime(3.0), 37.0)

    # Add fast 135 BPM cinematic bass rhythm
    beat_samples = int((60.0 / 135.0) * SR)
    bass_track = np.zeros(n, dtype=np.float32)
    for pos in range(0, n, beat_samples):
        b_len = min(int(0.25 * SR), n - pos)
        if b_len > 0:
            t_b = np.linspace(0, b_len / SR, b_len)
            bass = np.sin(2 * np.pi * 65.0 * t_b) * np.exp(-t_b * 6.0)
            bass_track[pos:pos+b_len] += bass * 0.4

    full_mix = sfx * 0.75 + bass_track * 0.4
    peak = np.max(np.abs(full_mix)) or 1.0
    full_mix = (full_mix / peak) * 0.65

    # Write 16-bit stereo WAV
    pcm = (full_mix * 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())

    return out_wav
