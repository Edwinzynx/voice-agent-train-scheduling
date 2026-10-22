"""Generate the demo's original, gentle instrumental loop (no samples or vocals)."""
from array import array
import math
from pathlib import Path
import wave

RATE = 22050
DURATION = 24
samples = [0.0] * (RATE * DURATION)


def note(midi, start, duration, volume, pad=False):
    frequency = 440 * 2 ** ((midi - 69) / 12)
    for i in range(int(duration * RATE)):
        t = i / RATE
        envelope = min(1, t / (.5 if pad else .025)) * min(1, (duration - t) / .65)
        if not pad:
            envelope *= math.exp(-t * 1.6)
        tone = math.sin(2 * math.pi * frequency * t)
        tone += .16 * math.sin(2 * math.pi * frequency * 2 * t)
        # Wrap note tails for a continuous loop.
        samples[(int(start * RATE) + i) % len(samples)] += tone * envelope * volume


for bar, chord in enumerate([(48, 55, 59, 64), (45, 52, 55, 60), (41, 48, 52, 57), (43, 50, 55, 59)]):
    for pitch in chord:
        note(pitch, bar * 6, 7, .032, pad=True)
    for beat, step in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
        note(chord[step] + 12, bar * 6 + beat * .75, 2.2, .075)

peak = max(abs(value) for value in samples)
output = Path(__file__).resolve().parents[1] / 'public' / 'demo-ambient.wav'
with wave.open(str(output), 'wb') as file:
    file.setnchannels(1)
    file.setsampwidth(2)
    file.setframerate(RATE)
    file.writeframes(array('h', (int(value / peak * 14000) for value in samples)).tobytes())
print(f'Created {output.name}: {DURATION}s original instrumental loop')
