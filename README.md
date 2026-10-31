# 🎓 Classroom Lecture Speech-to-Text System

A simple, beginner-friendly web application that converts recorded classroom lecture audio into **editable text** and generates an **accuracy report** using Word Error Rate (WER).

---

## 📋 Features

| Feature | Description |
|---|---|
| **Audio Upload** | Drag-and-drop or browse for MP3, WAV, M4A, OGG, FLAC, WEBM |
| **Transcription** | OpenAI Whisper (base model) converts audio to text |
| **Timed Segments** | View transcript broken into timestamped segments |
| **Editable Transcript** | Edit the generated text directly in the browser |
| **Download** | Save the transcript as a `.txt` file |
| **WER Evaluation** | Paste a reference transcript to compute Word Error Rate |
| **Comparison Table** | Add multiple recordings and compare WER side-by-side |
| **CSV Export** | Export comparison results as a spreadsheet |

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Backend:** Python 3.9+ · Flask · Flask-CORS
- **Speech Recognition:** [OpenAI Whisper](https://github.com/openai/whisper) (pretrained `base` model)
- **Audio Processing:** [Librosa](https://librosa.org/)
- **WER Evaluation:** [JiWER](https://github.com/jitsi/jiwer)

---

## ⚙️ Installation

### 1. Clone or download the project

```bash
cd "Speech Recognition"
```

### 2. Create and activate a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Whisper requires [ffmpeg](https://ffmpeg.org/download.html) to process audio.
> - **Windows:** `winget install ffmpeg` or download from https://ffmpeg.org
> - **macOS:** `brew install ffmpeg`
> - **Linux:** `sudo apt install ffmpeg`

---

## 🚀 Running the Application

```bash
python run.py
```

Then open **http://localhost:5000** in your browser.

The Whisper `base` model (~140 MB) is downloaded automatically on first run.

---

## 🧪 Generating Test Audio Samples

Run the sample generator to create a few synthetic WAV files for testing:

```bash
pip install pyttsx3          # text-to-speech engine (optional)
python generate_samples.py
```

This saves WAV files + reference transcripts in the `samples/` folder.

**Alternatively**, record any 15–60 second audio clip yourself using:
- Windows Voice Recorder
- Audacity
- Your phone's voice memo app

---

## 📂 Project Structure

```
Speech Recognition/
├── app.py                  # Flask backend (API routes)
├── run.py                  # Single-command launcher
├── generate_samples.py     # Sample audio generator
├── requirements.txt        # Python dependencies
├── README.md
├── uploads/                # Temporary upload folder (auto-created)
├── samples/                # Test audio files (generated)
│   └── references/         # Ground-truth transcripts
└── static/
    ├── index.html          # Main UI
    ├── style.css           # Styles
    └── app.js              # Frontend logic
```

---

## 🖥️ Using the Application

### Step 1 — Upload Audio
- Drag a file into the drop zone, or click **Browse File**.
- An audio player appears so you can preview the recording.
- Click **▶ Transcribe**.

### Step 2 — Review & Edit Transcript
- The generated transcript appears in an editable text area.
- Click **▾ Show Timed Segments** to see timestamped lines.
- Click **⬇ Download .txt** to save the transcript.

### Step 3 — Evaluate Accuracy
- Paste the correct (reference) transcript in the box, or load a `.txt` file.
- Click **Calculate WER** to see:
  - Word Error Rate (WER %)
  - Accuracy (%)
  - Substitutions, Deletions, Insertions, Correct Words

### Step 4 — Multi-Recording Comparison
- Add rows for each recording (label + hypothesis + reference).
- Click **Run Comparison** to generate a comparison table.
- Click **⬇ Export Table as CSV** to save results.

---

## 📊 Understanding WER

$$\text{WER} = \frac{S + D + I}{N} \times 100\%$$

| Symbol | Meaning |
|---|---|
| S | Substitutions (wrong word) |
| D | Deletions (missing word) |
| I | Insertions (extra word) |
| N | Total words in reference |

**Typical WER benchmarks (Whisper base):**
| Condition | WER |
|---|---|
| Clean audio, native speaker | ~5–15% |
| Slight background noise | ~10–25% |
| Heavy accent / fast speech | ~20–40% |
| Very noisy audio | ~40%+ |

---

## 🔧 Configuration

To use a larger (more accurate) Whisper model, change line in `app.py`:

```python
MODEL = whisper.load_model("base")   # Options: tiny, base, small, medium, large
```

Larger models are more accurate but slower and require more RAM:

| Model | Parameters | ~VRAM | Relative Speed |
|---|---|---|---|
| tiny | 39 M | ~1 GB | ×32 |
| base | 74 M | ~1 GB | ×16 |
| small | 244 M | ~2 GB | ×6 |
| medium | 769 M | ~5 GB | ×2 |
| large | 1550 M | ~10 GB | ×1 |

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| `ffmpeg not found` | Install ffmpeg and add it to PATH |
| Transcription is very slow | Use `tiny` model; or run on a GPU machine |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Port 5000 already in use | Edit `run.py` to change `port=5000` to another value |
| Audio upload fails | Make sure the file is MP3/WAV/M4A/OGG/FLAC/WEBM |

---

## 📝 License

This project uses pre-trained models and libraries under their respective open-source licenses:
- Whisper: MIT License
- Librosa: ISC License  
- JiWER: Apache 2.0
- Flask: BSD License

