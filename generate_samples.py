"""
Script to generate short synthetic test audio files using text-to-speech (pyttsx3)
or to download permitted public-domain recordings for testing.

Run:  python generate_samples.py
This creates a `samples/` folder with a few WAV files ready to upload.
"""

import os
import sys
from pathlib import Path

SAMPLES_DIR = Path("samples")
SAMPLES_DIR.mkdir(exist_ok=True)

SAMPLE_TEXTS = {
    "sample_01_slow_clear.wav": (
        "Welcome to today's lecture on machine learning. "
        "We will begin by discussing supervised learning algorithms. "
        "These algorithms learn from labeled training data."
    ),
    "sample_02_medium_pace.wav": (
        "The human brain contains approximately eighty six billion neurons. "
        "Each neuron can form thousands of connections with other neurons. "
        "This complex network enables thinking, memory, and perception."
    ),
    "sample_03_fast_pace.wav": (
        "Photosynthesis is the process used by plants to convert light energy "
        "into chemical energy stored in glucose. Chlorophyll absorbs sunlight "
        "and drives the reaction between carbon dioxide and water."
    ),
    "sample_04_technical.wav": (
        "A neural network consists of an input layer, one or more hidden layers, "
        "and an output layer. Each connection has a weight that is updated during "
        "backpropagation using gradient descent optimization."
    ),
}

def generate_with_pyttsx3():
    try:
        import pyttsx3
    except ImportError:
        print("pyttsx3 not installed. Run:  pip install pyttsx3")
        return False

    engine = pyttsx3.init()
    voices = engine.getProperty("voices")

    for i, (filename, text) in enumerate(SAMPLE_TEXTS.items()):
        out_path = str(SAMPLES_DIR / filename)
        # Alternate between voices if available for variety
        if voices and len(voices) > 1:
            engine.setProperty("voice", voices[i % len(voices)].id)

        # Vary speaking rate for different samples
        rates = [130, 165, 200, 150]
        engine.setProperty("rate", rates[i % len(rates)])

        engine.save_to_file(text, out_path)
        engine.runAndWait()
        print(f"  ✓ Created {out_path}")

    return True


if __name__ == "__main__":
    print("Generating sample audio files …\n")

    if generate_with_pyttsx3():
        print(f"\n✅ {len(SAMPLE_TEXTS)} sample WAV files saved to: {SAMPLES_DIR.resolve()}")
        print("\nReference transcripts are stored alongside in samples/references/")

        # Write reference transcripts
        ref_dir = SAMPLES_DIR / "references"
        ref_dir.mkdir(exist_ok=True)
        for wav_name, text in SAMPLE_TEXTS.items():
            ref_path = ref_dir / wav_name.replace(".wav", "_reference.txt")
            ref_path.write_text(text, encoding="utf-8")
            print(f"  ✓ Reference → {ref_path}")
    else:
        print("\n⚠️  Could not generate samples automatically.")
        print("    You can record your own WAV/MP3 files and place them in the `samples/` folder.")
        print("    Any short lecture recording (10–60 seconds) works great for testing.")

