"""
Classroom Lecture Speech-to-Text System
Flask backend using OpenAI Whisper for transcription and JiWER for WER evaluation.
"""

import os
import json
import tempfile
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import librosa
import numpy as np
from jiwer import wer, process_words

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "ogg", "flac", "webm"}

# Load the Whisper model once at startup (configurable via WHISPER_MODEL env var)
MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")
print(f"Loading Whisper model ({MODEL_NAME})... this may take a moment on first run.")
MODEL = whisper.load_model(MODEL_NAME)
print(f"Whisper model ({MODEL_NAME}) loaded ✓")

# ─── Helpers ─────────────────────────────────────────────────────────────────


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_info(filepath: str) -> dict:
    """Return basic audio metadata via librosa."""
    try:
        y, sr = librosa.load(filepath, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        rms = float(np.sqrt(np.mean(y ** 2)))
        return {
            "duration_seconds": round(duration, 2),
            "sample_rate": sr,
            "rms_energy": round(rms, 6),
            "estimated_snr_db": round(20 * np.log10(rms + 1e-9), 2),
        }
    except Exception:
        return {}


def transcribe_audio(filepath: str) -> dict:
    """Transcribe audio using Whisper and return transcript + segments.

    Audio is loaded via librosa first (no ffmpeg required) and passed as a
    float32 numpy array at Whisper's expected 16 kHz sample rate.
    """
    import whisper as _whisper

    # Load & resample to 16 kHz mono using librosa (no ffmpeg dependency)
    audio_np, _ = librosa.load(filepath, sr=_whisper.audio.SAMPLE_RATE, mono=True)

    result = MODEL.transcribe(audio_np, word_timestamps=False)
    segments = [
        {
            "id": seg["id"],
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        }
        for seg in result.get("segments", [])
    ]
    return {
        "text": result["text"].strip(),
        "language": result.get("language", "unknown"),
        "segments": segments,
    }


def evaluate_wer(hypothesis: str, reference: str) -> dict:
    """Calculate WER and detailed error breakdown using JiWER."""
    # Normalize whitespace
    hyp = " ".join(hypothesis.lower().split())
    ref = " ".join(reference.lower().split())

    if not ref:
        return {"error": "Reference transcript is empty."}

    out = process_words(ref, hyp)
    word_error_rate = out.wer
    accuracy = max(0.0, 1.0 - word_error_rate)

    return {
        "wer": round(word_error_rate * 100, 2),           # as percentage
        "accuracy": round(accuracy * 100, 2),              # as percentage
        "substitutions": out.substitutions,
        "deletions": out.deletions,
        "insertions": out.insertions,
        "hits": out.hits,
        "ref_word_count": len(ref.split()),
        "hyp_word_count": len(hyp.split()),
    }


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """Upload an audio file and return transcription results."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Save to uploads folder
    suffix = Path(file.filename).suffix
    tmp_path = UPLOAD_FOLDER / (next(tempfile._get_candidate_names()) + suffix)
    try:
        file.save(str(tmp_path))

        audio_info = get_audio_info(str(tmp_path))
        transcription = transcribe_audio(str(tmp_path))

        return jsonify({
            "success": True,
            "transcript": transcription["text"],
            "language": transcription["language"],
            "segments": transcription["segments"],
            "audio_info": audio_info,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up uploaded file
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    """Calculate WER between hypothesis and reference transcripts."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Expected JSON body."}), 400

    hypothesis = data.get("hypothesis", "").strip()
    reference = data.get("reference", "").strip()

    if not hypothesis:
        return jsonify({"error": "Hypothesis transcript is empty."}), 400
    if not reference:
        return jsonify({"error": "Reference transcript is empty."}), 400

    try:
        result = evaluate_wer(hypothesis, reference)
        return jsonify({"success": True, **result})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Compare multiple (label, hypothesis, reference) pairs and return a table."""
    data = request.get_json(silent=True)
    if not data or "entries" not in data:
        return jsonify({"error": "Expected JSON with 'entries' list."}), 400

    rows = []
    for entry in data["entries"]:
        label = entry.get("label", "—")
        hyp = entry.get("hypothesis", "").strip()
        ref = entry.get("reference", "").strip()
        if hyp and ref:
            metrics = evaluate_wer(hyp, ref)
            rows.append({"label": label, **metrics})
        else:
            rows.append({
                "label": label,
                "error": "Missing hypothesis or reference.",
            })

    return jsonify({"success": True, "rows": rows})


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n🎓 Classroom Lecture Speech-to-Text System")
    print(f"   Open http://localhost:{port} in your browser\n")
    app.run(host="0.0.0.0", port=port, debug=False)

