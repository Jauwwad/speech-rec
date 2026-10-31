"""
Classroom Lecture Speech-to-Text System
Backend using OpenAI Whisper API (cloud) for transcription — no local model loaded.
"""

import os
import gc
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from jiwer import process_words

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "ogg", "flac", "webm"}

MAX_FILE_BYTES = 24 * 1024 * 1024   # 24 MB (OpenAI limit is 25 MB)

# Build OpenAI client — key comes from OPENAI_API_KEY env var set in Render
_api_key = os.environ.get("OPENAI_API_KEY", "")
if not _api_key:
    print("⚠️  OPENAI_API_KEY not set — transcription will fail until the key is configured.")
client = OpenAI(api_key=_api_key)

print("✓ LectureScript backend ready (OpenAI Whisper API mode).")

# ─── Helpers ─────────────────────────────────────────────────────────────────


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_duration(filepath: str) -> float | None:
    """Cheaply get audio duration without loading full waveform."""
    try:
        import soundfile as sf
        info = sf.info(str(filepath))
        return round(info.duration, 2)
    except Exception:
        pass
    try:
        import librosa
        return round(librosa.get_duration(path=str(filepath)), 2)
    except Exception:
        return None


def transcribe_audio(filepath: str) -> dict:
    """Send audio to OpenAI Whisper API and return full transcript + segments."""
    with open(filepath, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",   # includes segments with timestamps
            timestamp_granularities=["segment"],
        )

    segments = []
    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            segments.append({
                "id":    seg.id,
                "start": round(seg.start, 2),
                "end":   round(seg.end,   2),
                "text":  seg.text.strip(),
            })

    return {
        "text":     (response.text or "").strip(),
        "language": getattr(response, "language", "unknown"),
        "segments": segments,
    }


def evaluate_wer(hypothesis: str, reference: str) -> dict:
    """Calculate WER and detailed error breakdown using JiWER."""
    hyp = " ".join(hypothesis.lower().split())
    ref = " ".join(reference.lower().split())

    if not ref:
        return {"error": "Reference transcript is empty."}

    out = process_words(ref, hyp)
    word_error_rate = out.wer
    accuracy = max(0.0, 1.0 - word_error_rate)

    return {
        "wer":           round(word_error_rate * 100, 2),
        "accuracy":      round(accuracy * 100, 2),
        "substitutions": out.substitutions,
        "deletions":     out.deletions,
        "insertions":    out.insertions,
        "hits":          out.hits,
        "ref_word_count": len(ref.split()),
        "hyp_word_count": len(hyp.split()),
    }


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/health")
def health():
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    return jsonify({"status": "ok", "api_key_configured": has_key})


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """Upload an audio file and return transcription from OpenAI Whisper API."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided."}), 400

    file = request.files["audio"]
    if not file.filename:
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    if not os.environ.get("OPENAI_API_KEY"):
        return jsonify({"error": "Server is not configured with an OpenAI API key. Please set the OPENAI_API_KEY environment variable in your Render dashboard."}), 503

    suffix = Path(file.filename).suffix.lower() or ".mp3"
    import tempfile
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, dir=str(UPLOAD_FOLDER)
    )
    tmp_path = Path(tmp.name)

    try:
        file.save(str(tmp_path))

        # Size guard
        size_bytes = tmp_path.stat().st_size
        if size_bytes > MAX_FILE_BYTES:
            return jsonify({
                "error": (
                    f"File is too large ({size_bytes // (1024*1024)} MB). "
                    "OpenAI Whisper API accepts files up to 24 MB. "
                    "Please compress or trim your audio."
                )
            }), 413

        # Metadata (cheap header read)
        duration = get_audio_duration(str(tmp_path))
        audio_info = {
            "duration_seconds": duration,
            "file_size_mb": round(size_bytes / (1024 * 1024), 2),
        }

        # Transcribe via API
        transcription = transcribe_audio(str(tmp_path))

        return jsonify({
            "success":    True,
            "transcript": transcription["text"],
            "language":   transcription["language"],
            "segments":   transcription["segments"],
            "audio_info": audio_info,
        })

    except Exception as e:
        traceback.print_exc()
        msg = str(e)
        # Surface readable OpenAI errors
        if "api_key" in msg.lower() or "authentication" in msg.lower():
            msg = "Invalid or missing OpenAI API key. Check OPENAI_API_KEY in your Render environment."
        elif "rate limit" in msg.lower():
            msg = "OpenAI rate limit hit. Please wait a moment and try again."
        return jsonify({"error": msg}), 500

    finally:
        tmp_path.unlink(missing_ok=True)
        gc.collect()


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Expected JSON body."}), 400

    hypothesis = data.get("hypothesis", "").strip()
    reference  = data.get("reference",  "").strip()

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
    data = request.get_json(silent=True)
    if not data or "entries" not in data:
        return jsonify({"error": "Expected JSON with 'entries' list."}), 400

    rows = []
    for entry in data["entries"]:
        label = entry.get("label", "—")
        hyp   = entry.get("hypothesis", "").strip()
        ref   = entry.get("reference",  "").strip()
        if hyp and ref:
            metrics = evaluate_wer(hyp, ref)
            rows.append({"label": label, **metrics})
        else:
            rows.append({"label": label, "error": "Missing hypothesis or reference."})

    return jsonify({"success": True, "rows": rows})


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🎓 LectureScript — open http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
