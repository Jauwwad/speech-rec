/* ═══════════════════════════════════════════
   LectureScript — app.js
   ═══════════════════════════════════════════ */
"use strict";

// ── DOM refs ─────────────────────────────────────────────────────────────────

const dropZone        = document.getElementById("drop-zone");
const audioInput      = document.getElementById("audio-input");
const fileSelected    = document.getElementById("file-selected");
const fileNameEl      = document.getElementById("file-name-text");
const fileSizeEl      = document.getElementById("file-size-text");
const clearFileBtn    = document.getElementById("clear-file-btn");
const audioPreview    = document.getElementById("audio-preview");
const transcribeBtn   = document.getElementById("transcribe-btn");

const progressWrap    = document.getElementById("progress-wrap");
const progressMsg     = document.getElementById("progress-msg");

const transcriptCard  = document.getElementById("transcript-card");
const metaChips       = document.getElementById("meta-chips");
const transcriptBox   = document.getElementById("transcript-box");
const wordCountEl     = document.getElementById("word-count");
const toggleSegBtn    = document.getElementById("toggle-segments-btn");
const segmentsPanel   = document.getElementById("segments-panel");
const copyBtn         = document.getElementById("copy-btn");
const downloadBtn     = document.getElementById("download-btn");
const clearTransBtn   = document.getElementById("clear-transcript-btn");

const accuracyCard    = document.getElementById("accuracy-card");
const referenceBox    = document.getElementById("reference-box");
const refFileInput    = document.getElementById("ref-file-input");
const evaluateBtn     = document.getElementById("evaluate-btn");
const werResults      = document.getElementById("wer-results");
const werQuality      = document.getElementById("wer-quality");

const compareRows     = document.getElementById("compare-rows");
const addRowBtn       = document.getElementById("add-row-btn");
const runCompareBtn   = document.getElementById("run-compare-btn");
const compareResults  = document.getElementById("compare-results");
const compareTbody    = document.getElementById("compare-tbody");
const exportCsvBtn    = document.getElementById("export-csv-btn");

const stepPills       = document.querySelectorAll(".step-pill");

// ── State ─────────────────────────────────────────────────────────────────────
let selectedFile = null;
let compareData  = [];
let rowCount     = 0;
let segVisible   = false;

// ── Toast ─────────────────────────────────────────────────────────────────────
const toast = document.getElementById("toast");
let toastTimer;
function showToast(msg, duration = 3000) {
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), duration);
}

// ── Step pills ────────────────────────────────────────────────────────────────
function setActiveStep(n) {
  stepPills.forEach(p => p.classList.toggle("active", +p.dataset.step === n));
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const show = el => el.classList.remove("hidden");
const hide = el => el.classList.add("hidden");

function fmtTime(s) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function fmtBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function countWords(text) {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}

function escHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ── File handling ─────────────────────────────────────────────────────────────
const ALLOWED = ["mp3","wav","m4a","ogg","flac","webm"];

function handleFile(file) {
  if (!file) return;
  const ext = file.name.split(".").pop().toLowerCase();
  if (!ALLOWED.includes(ext)) {
    showToast("⚠️ Unsupported file. Use MP3, WAV, M4A, OGG, FLAC or WEBM.", 4000);
    return;
  }
  selectedFile = file;
  fileNameEl.textContent = file.name;
  fileSizeEl.textContent = fmtBytes(file.size);
  audioPreview.src = URL.createObjectURL(file);
  show(fileSelected);
  transcribeBtn.disabled = false;
  setActiveStep(2);
  transcribeBtn.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearFile() {
  selectedFile = null;
  audioInput.value = "";
  audioPreview.src = "";
  fileNameEl.textContent = "—";
  fileSizeEl.textContent = "—";
  hide(fileSelected);
  transcribeBtn.disabled = true;
  setActiveStep(1);
}

// Drop zone
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("dragging"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("dragging");
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});
dropZone.addEventListener("click", () => audioInput.click());
dropZone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") audioInput.click(); });
audioInput.addEventListener("change", () => { if (audioInput.files[0]) handleFile(audioInput.files[0]); });
clearFileBtn.addEventListener("click", e => { e.stopPropagation(); clearFile(); });

// ── Transcription ─────────────────────────────────────────────────────────────
transcribeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  show(progressWrap);
  progressMsg.textContent = "Uploading to OpenAI Whisper API… please wait";
  transcribeBtn.disabled = true;
  setActiveStep(2);

  // Animated progress message cycle so user knows it's working
  const msgs = [
    "Uploading audio to OpenAI Whisper API…",
    "Transcribing your lecture… (this may take 10–30s)",
    "Processing longer audio… almost there…",
    "Finalising transcript…",
  ];
  let msgIdx = 0;
  const msgTimer = setInterval(() => {
    msgIdx = (msgIdx + 1) % msgs.length;
    progressMsg.textContent = msgs[msgIdx];
  }, 8000);

  const fd = new FormData();
  fd.append("audio", selectedFile);

  try {
    const res = await fetch("/api/transcribe", { method: "POST", body: fd });
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(`Server error (${res.status}). Check your Render logs.`);
    }
    if (!res.ok || data.error) throw new Error(data.error || "Transcription failed.");

    // Fill transcript
    transcriptBox.value = data.transcript;
    updateWordCount();

    // Build chips
    metaChips.innerHTML = "";
    const info = data.audio_info || {};
    const chips = [
      data.language ? ["🌐", "Language", data.language.toUpperCase()] : null,
      info.duration_seconds ? ["⏱", "Duration", `${info.duration_seconds}s`] : null,
      info.sample_rate ? ["📊", "Sample Rate", `${(info.sample_rate/1000).toFixed(1)} kHz`] : null,
      data.segments?.length ? ["💬", "Segments", data.segments.length] : null,
    ].filter(Boolean);
    chips.forEach(([icon, label, val]) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.innerHTML = `${icon} ${label}: <strong>${escHtml(String(val))}</strong>`;
      metaChips.appendChild(chip);
    });

    // Build segments
    segmentsPanel.innerHTML = "";
    (data.segments || []).forEach(seg => {
      const row = document.createElement("div");
      row.className = "seg-row";
      row.innerHTML = `<span class="seg-ts">${fmtTime(seg.start)} → ${fmtTime(seg.end)}</span>
                       <span class="seg-txt">${escHtml(seg.text)}</span>`;
      segmentsPanel.appendChild(row);
    });

    show(transcriptCard);
    show(accuracyCard);
    setActiveStep(3);
    transcriptCard.scrollIntoView({ behavior: "smooth" });
    showToast("✅ Transcription complete!");

  } catch (err) {
    showToast(`❌ ${err.message}`, 7000);
  } finally {
    clearInterval(msgTimer);
    hide(progressWrap);
    transcribeBtn.disabled = false;
  }
});

// ── Word count ────────────────────────────────────────────────────────────────
function updateWordCount() {
  const n = countWords(transcriptBox.value);
  wordCountEl.textContent = `${n.toLocaleString()} word${n !== 1 ? "s" : ""}`;
}
transcriptBox.addEventListener("input", updateWordCount);

// ── Segments toggle ───────────────────────────────────────────────────────────
toggleSegBtn.addEventListener("click", () => {
  segVisible = !segVisible;
  segmentsPanel.classList.toggle("hidden", !segVisible);
  toggleSegBtn.textContent = segVisible ? "▴ Hide timed segments" : "▾ Show timed segments";
});

// ── Copy ──────────────────────────────────────────────────────────────────────
copyBtn.addEventListener("click", async () => {
  const text = transcriptBox.value.trim();
  if (!text) return showToast("Nothing to copy.");
  try {
    await navigator.clipboard.writeText(text);
    showToast("📋 Copied to clipboard!");
  } catch {
    showToast("⚠️ Copy failed — select & copy manually.");
  }
});

// ── Download transcript ───────────────────────────────────────────────────────
downloadBtn.addEventListener("click", () => {
  const text = transcriptBox.value.trim();
  if (!text) return showToast("Nothing to download.");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  a.download = "transcript.txt";
  a.click();
  showToast("⬇ Downloading transcript.txt");
});

clearTransBtn.addEventListener("click", () => {
  transcriptBox.value = "";
  updateWordCount();
  showToast("Transcript cleared.");
});

// ── Load reference file ───────────────────────────────────────────────────────
refFileInput.addEventListener("change", () => {
  const file = refFileInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    referenceBox.value = e.target.result;
    showToast("📂 Reference file loaded.");
  };
  reader.readAsText(file);
});

// ── WER Evaluation ────────────────────────────────────────────────────────────
evaluateBtn.addEventListener("click", async () => {
  const hyp = transcriptBox.value.trim();
  const ref = referenceBox.value.trim();
  if (!hyp) return showToast("⚠️ Transcript is empty.");
  if (!ref)  return showToast("⚠️ Reference transcript is empty.");

  evaluateBtn.disabled = true;
  evaluateBtn.innerHTML = `<span>Calculating…</span>`;

  try {
    const res  = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hypothesis: hyp, reference: ref }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Evaluation failed.");

    document.getElementById("stat-wer").textContent = `${data.wer}%`;
    document.getElementById("stat-acc").textContent = `${data.accuracy}%`;
    document.getElementById("stat-sub").textContent = data.substitutions;
    document.getElementById("stat-del").textContent = data.deletions;
    document.getElementById("stat-ins").textContent = data.insertions;
    document.getElementById("stat-hit").textContent = data.hits;

    // Progress bar fills
    document.getElementById("wer-bar").style.width = `${Math.min(data.wer, 100)}%`;
    document.getElementById("acc-bar").style.width = `${data.accuracy}%`;

    // Quality badge
    let qClass, qText;
    if (data.wer <= 10) { qClass = "q-excellent"; qText = "🏆 Excellent — near-perfect transcription!"; }
    else if (data.wer <= 25) { qClass = "q-good";  qText = "👍 Good — minor errors, easy to correct."; }
    else if (data.wer <= 45) { qClass = "q-fair";  qText = "⚠️ Fair — moderate errors, review recommended."; }
    else                     { qClass = "q-poor";  qText = "❌ Poor — heavy errors, likely noisy audio."; }

    werQuality.className = `wer-quality ${qClass}`;
    werQuality.textContent = qText;
    show(werQuality);

    show(werResults);
    setActiveStep(4);
    werResults.scrollIntoView({ behavior: "smooth", block: "nearest" });
    showToast("✅ WER calculated!");

  } catch (err) {
    showToast(`❌ ${err.message}`, 5000);
  } finally {
    evaluateBtn.disabled = false;
    evaluateBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> Calculate WER`;
  }
});

// ── Compare rows ──────────────────────────────────────────────────────────────
function addCompareRow(label = "", hyp = "", ref = "") {
  rowCount++;
  const row = document.createElement("div");
  row.className = "compare-row";
  row.dataset.id = rowCount;
  row.innerHTML = `
    <div class="compare-field-wrap">
      <span class="compare-field-label">Label</span>
      <input type="text" class="ce-label" placeholder="e.g. Speaker A" value="${escHtml(label)}" />
    </div>
    <div class="compare-field-wrap">
      <span class="compare-field-label">Hypothesis (ASR output)</span>
      <textarea class="ce-hyp" rows="3" placeholder="Paste ASR output…">${escHtml(hyp)}</textarea>
    </div>
    <div class="compare-field-wrap">
      <span class="compare-field-label">Reference (ground truth)</span>
      <textarea class="ce-ref" rows="3" placeholder="Paste reference…">${escHtml(ref)}</textarea>
    </div>
    <button class="icon-btn danger remove-row" title="Remove row" aria-label="Remove row">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>`;
  row.querySelector(".remove-row").addEventListener("click", () => row.remove());
  compareRows.appendChild(row);
}

// Seed 2 rows
addCompareRow("Recording 1");
addCompareRow("Recording 2");

addRowBtn.addEventListener("click", () => addCompareRow());

runCompareBtn.addEventListener("click", async () => {
  const rows = [...compareRows.querySelectorAll(".compare-row")];
  const entries = rows.map(r => ({
    label:      r.querySelector(".ce-label")?.value.trim() || "—",
    hypothesis: r.querySelector(".ce-hyp")?.value.trim()  || "",
    reference:  r.querySelector(".ce-ref")?.value.trim()  || "",
  })).filter(e => e.hypothesis && e.reference);

  if (!entries.length) {
    showToast("⚠️ Fill in at least one complete row.", 4000);
    return;
  }

  runCompareBtn.disabled = true;
  runCompareBtn.innerHTML = `<span>Running…</span>`;

  try {
    const res  = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Comparison failed.");

    compareData = data.rows;
    renderTable(data.rows);
    show(compareResults);
    compareResults.scrollIntoView({ behavior: "smooth" });
    showToast("✅ Comparison done!");
  } catch (err) {
    showToast(`❌ ${err.message}`, 5000);
  } finally {
    runCompareBtn.disabled = false;
    runCompareBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Comparison`;
  }
});

function renderTable(rows) {
  compareTbody.innerHTML = "";
  rows.forEach(row => {
    const tr = document.createElement("tr");
    if (row.error) {
      tr.innerHTML = `<td class="td-label">${escHtml(row.label)}</td>
                      <td colspan="6" class="td-err">${escHtml(row.error)}</td>`;
    } else {
      // Color-code WER cell
      const werClass = row.wer <= 15 ? "style='color:var(--green-600)'" :
                       row.wer <= 35 ? "style='color:var(--amber-600)'" :
                                       "style='color:var(--red-600)'";
      tr.innerHTML = `
        <td class="td-label">${escHtml(row.label)}</td>
        <td class="td-wer" ${werClass}>${row.wer}%</td>
        <td class="td-acc">${row.accuracy}%</td>
        <td>${row.substitutions}</td>
        <td>${row.deletions}</td>
        <td>${row.insertions}</td>
        <td>${row.ref_word_count}</td>`;
    }
    compareTbody.appendChild(tr);
  });
}

// ── Export CSV ────────────────────────────────────────────────────────────────
exportCsvBtn.addEventListener("click", () => {
  if (!compareData.length) return;
  const headers = ["Label","WER (%)","Accuracy (%)","Substitutions","Deletions","Insertions","Ref Words"];
  const lines = [headers.join(",")];
  compareData.forEach(r => {
    if (r.error) lines.push(`"${r.label}","Error","—","—","—","—","—"`);
    else lines.push([r.label,r.wer,r.accuracy,r.substitutions,r.deletions,r.insertions,r.ref_word_count].join(","));
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
  a.download = "wer_comparison.csv";
  a.click();
  showToast("⬇ Downloading wer_comparison.csv");
});
