'use strict';

/* ── Utilities ───────────────────────────────────────── */
function uuid() {
  return crypto.randomUUID ? crypto.randomUUID()
       : 'xxxx-xxxx-xxxx-xxxx'.replace(/x/g, () => (Math.random()*16|0).toString(16));
}
function fmt(sec) {
  const m = Math.floor(sec / 60), s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}
function el(id) { return document.getElementById(id); }
function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  el(id).classList.add('active');
}
function scoreColor(v) {
  if (v >= 8) return '#22c55e';
  if (v >= 6) return '#3b82f6';
  if (v >= 4) return '#f59e0b';
  return '#ef4444';
}
function verdict(v) {
  if (v >= 9)   return 'Outstanding!';
  if (v >= 7.5) return 'Excellent!';
  if (v >= 6)   return 'Very Good';
  if (v >= 4.5) return 'Good Effort';
  if (v >= 3)   return 'Keep Practicing';
  return 'Just Getting Started';
}

/* ── State ───────────────────────────────────────────── */
const state = {
  sessionId: localStorage.getItem('shadowing_session') || (() => {
    const id = uuid(); localStorage.setItem('shadowing_session', id); return id;
  })(),
  level: 'C1',
  duration: 60,
  passage: null,
  audioUrl: null,
  listenCount: 0,
  recordingBlob: null,
  recordingUrl: null,
  lastResult: null,
};

/* ── Level descriptions ──────────────────────────────── */
const LEVEL_DESCS = {
  A1: 'Basic vocabulary and simple present tense. Perfect for true beginners.',
  A2: 'Everyday vocabulary and simple past tense. Short, clear sentences.',
  B1: 'Standard vocabulary with various tenses. Intermediate complexity.',
  B2: 'Wide vocabulary, complex sentences, idiomatic expressions.',
  C1: 'Sophisticated vocabulary and complex structures. Near-advanced level.',
  C2: 'Near-native complexity with nuanced vocabulary and subtle expressions.',
};

/* ── Audio elements ──────────────────────────────────── */
let origAudio = null;   // HTMLAudioElement
let userAudio = null;   // HTMLAudioElement

/* ── Recording ───────────────────────────────────────── */
let mediaRecorder = null;
let recordChunks  = [];
let recordTimer   = null;
let recordStart   = null;
let audioCtx      = null;
let analyser      = null;
let waveAnimFrame = null;
let micStream     = null;

/* ── Init ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Pill groups
  setupPillGroup('level-group', (v) => {
    state.level = v;
    el('level-desc').textContent = LEVEL_DESCS[v] || '';
  });
  setupPillGroup('duration-group', (v) => { state.duration = parseInt(v); });

  // Set initial level desc
  el('level-desc').textContent = LEVEL_DESCS[state.level];

  // Player click-to-seek
  el('orig-bar').addEventListener('click', (e) => seekAudio(origAudio, e, 'orig'));
  el('user-bar').addEventListener('click', (e) => seekAudio(userAudio, e, 'user'));
});

function setupPillGroup(groupId, onChange) {
  el(groupId).querySelectorAll('.pill').forEach(p => {
    p.addEventListener('click', () => {
      el(groupId).querySelectorAll('.pill').forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      onChange(p.dataset.value);
    });
  });
}

/* ── App object ──────────────────────────────────────── */
const app = {

  async generate() {
    el('btn-generate').disabled = true;
    el('loading-text').textContent = 'Generating passage…';
    showSection('sec-loading');

    try {
      const res = await fetch('api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: state.sessionId,
          level: state.level,
          duration: state.duration,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      state.passage  = data.text;
      state.audioUrl = data.audio_url;
      state.listenCount = 0;
      state.recordingBlob = null;
      state.recordingUrl  = null;

      el('loading-text').textContent = 'Synthesizing voice…';
      await _setupPractice();

    } catch (err) {
      alert('Error: ' + err.message);
      showSection('sec-config');
    } finally {
      el('btn-generate').disabled = false;
    }
  },

  toggleText() {
    const p = el('passage-text');
    const btn = el('btn-toggle-text');
    const blurred = p.classList.toggle('blurred');
    btn.textContent = blurred ? 'Show Text' : 'Hide Text';
  },

  toggleOriginal() {
    if (!origAudio) return;
    if (origAudio.paused) {
      if (userAudio && !userAudio.paused) userAudio.pause();
      origAudio.play();
    } else {
      origAudio.pause();
    }
  },

  toggleUser() {
    if (!userAudio) return;
    if (userAudio.paused) {
      if (origAudio && !origAudio.paused) origAudio.pause();
      userAudio.play();
    } else {
      userAudio.pause();
    }
  },

  async toggleRecord() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      _stopRecording();
    } else {
      await _startRecording();
    }
  },

  reRecord() {
    el('user-playback').classList.add('hidden');
    el('btn-submit').classList.add('hidden');
    el('record-hint').textContent = 'Press the button and repeat the passage out loud';
    if (userAudio) { userAudio.pause(); userAudio = null; }
    state.recordingBlob = null;
    state.recordingUrl  = null;
  },

  async submit() {
    if (!state.recordingBlob) return;
    el('btn-submit').disabled = true;
    el('loading-text').textContent = 'Analyzing your pronunciation…';
    showSection('sec-loading');

    try {
      const form = new FormData();
      form.append('session_id', state.sessionId);
      form.append('audio', state.recordingBlob, 'recording.webm');

      const res = await fetch('api/assess', { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }
      state.lastResult = await res.json();
      _showResults(state.lastResult);

    } catch (err) {
      alert('Error: ' + err.message);
      showSection('sec-practice');
    } finally {
      el('btn-submit').disabled = false;
    }
  },

  tryAgain() {
    // Keep same passage, reset recording
    this.reRecord();
    showSection('sec-practice');
  },

  reset() {
    // Cleanup audio
    if (origAudio) { origAudio.pause(); origAudio = null; }
    if (userAudio)  { userAudio.pause(); userAudio = null; }
    _stopRecording(true);
    state.passage = null;
    state.audioUrl = null;
    state.recordingBlob = null;
    state.recordingUrl  = null;
    state.listenCount = 0;
    // Regenerate session id so old audio won't be served
    const id = uuid();
    localStorage.setItem('shadowing_session', id);
    state.sessionId = id;
    showSection('sec-config');
  },
};

/* ── Internal helpers ────────────────────────────────── */
async function _setupPractice() {
  el('passage-badge').textContent = state.level;
  el('passage-text').textContent  = state.passage;
  el('passage-text').classList.remove('blurred');
  el('btn-toggle-text').textContent = 'Hide Text';

  // Original audio
  if (origAudio) origAudio.pause();
  origAudio = new Audio(state.audioUrl);
  origAudio.preload = 'auto';

  origAudio.addEventListener('loadedmetadata', () => {
    el('orig-dur').textContent = fmt(origAudio.duration);
  });
  origAudio.addEventListener('timeupdate', () => {
    const pct = origAudio.currentTime / (origAudio.duration || 1) * 100;
    el('orig-fill').style.width = pct + '%';
    el('orig-cur').textContent  = fmt(origAudio.currentTime);
  });
  origAudio.addEventListener('play', () => {
    el('orig-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M6 19h4V5H6zm8-14v14h4V5z"/></svg>';
  });
  origAudio.addEventListener('pause', () => {
    el('orig-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M8 5v14l11-7z"/></svg>';
  });
  origAudio.addEventListener('ended', () => {
    state.listenCount++;
    el('listen-badge').textContent = state.listenCount + '×';
    el('orig-play-btn').innerHTML  = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M8 5v14l11-7z"/></svg>';
  });

  // Reset record UI
  el('user-playback').classList.add('hidden');
  el('btn-submit').classList.add('hidden');
  el('waveform').classList.add('hidden');
  el('record-timer').textContent = '';
  el('record-btn').classList.remove('recording');
  el('record-icon').textContent = '●';
  el('record-hint').textContent = 'Press the button and repeat the passage out loud';
  el('listen-badge').textContent = '0×';
  el('orig-fill').style.width = '0%';
  el('orig-cur').textContent = '0:00';

  showSection('sec-practice');
  origAudio.play().catch(() => {});
}

function seekAudio(audio, e, prefix) {
  if (!audio) return;
  const bar = el(prefix + '-bar');
  const rect = bar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  audio.currentTime = pct * audio.duration;
}

/* ── Recording logic ─────────────────────────────────── */
async function _startRecording() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    alert('Microphone access denied. Please allow microphone access and try again.');
    return;
  }

  // Web Audio for waveform
  audioCtx  = new AudioContext();
  analyser  = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  audioCtx.createMediaStreamSource(micStream).connect(analyser);

  recordChunks = [];
  mediaRecorder = new MediaRecorder(micStream, { mimeType: _bestMime() });
  mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordChunks.push(e.data); };
  mediaRecorder.onstop = _onRecordStop;
  mediaRecorder.start(100);

  recordStart = Date.now();
  recordTimer = setInterval(_updateTimer, 100);

  el('record-btn').classList.add('recording');
  el('record-icon').textContent = '■';
  el('record-hint').textContent = 'Recording… press again to stop';
  el('waveform').classList.remove('hidden');
  el('user-playback').classList.add('hidden');
  el('btn-submit').classList.add('hidden');
  _drawWaveform();
}

function _stopRecording(silent = false) {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  if (recordTimer) { clearInterval(recordTimer); recordTimer = null; }
  if (waveAnimFrame) { cancelAnimationFrame(waveAnimFrame); waveAnimFrame = null; }
  if (audioCtx) { audioCtx.close().catch(() => {}); audioCtx = null; analyser = null; }

  el('record-btn').classList.remove('recording');
  el('record-icon').textContent = '●';
  el('waveform').classList.add('hidden');
  if (!silent) el('record-timer').textContent = '';
}

function _onRecordStop() {
  if (recordChunks.length === 0) return;
  const blob = new Blob(recordChunks, { type: recordChunks[0].type || 'audio/webm' });
  state.recordingBlob = blob;

  if (state.recordingUrl) URL.revokeObjectURL(state.recordingUrl);
  state.recordingUrl = URL.createObjectURL(blob);

  // Setup user audio player
  if (userAudio) userAudio.pause();
  userAudio = new Audio(state.recordingUrl);
  userAudio.addEventListener('loadedmetadata', () => {
    el('user-dur').textContent = fmt(userAudio.duration);
  });
  userAudio.addEventListener('timeupdate', () => {
    const pct = userAudio.currentTime / (userAudio.duration || 1) * 100;
    el('user-fill').style.width = pct + '%';
    el('user-cur').textContent  = fmt(userAudio.currentTime);
  });
  userAudio.addEventListener('play', () => {
    el('user-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M6 19h4V5H6zm8-14v14h4V5z"/></svg>';
  });
  userAudio.addEventListener('pause', () => {
    el('user-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M8 5v14l11-7z"/></svg>';
  });
  userAudio.addEventListener('ended', () => {
    el('user-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M8 5v14l11-7z"/></svg>';
  });

  el('user-cur').textContent = '0:00';
  el('user-fill').style.width = '0%';
  el('user-play-btn').innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20"><path d="M8 5v14l11-7z"/></svg>';

  el('record-hint').textContent = 'Great! Listen to your recording or submit for assessment.';
  el('user-playback').classList.remove('hidden');
  el('btn-submit').classList.remove('hidden');
}

function _updateTimer() {
  const sec = (Date.now() - recordStart) / 1000;
  el('record-timer').textContent = fmt(sec);
}

function _drawWaveform() {
  const canvas = el('waveform');
  const ctx    = canvas.getContext('2d');
  const W = canvas.width  = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight;
  const buf = new Uint8Array(analyser ? analyser.frequencyBinCount : 64);

  function draw() {
    if (!analyser) return;
    analyser.getByteTimeDomainData(buf);
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--card2').trim() || '#243047';
    ctx.fillRect(0, 0, W, H);

    ctx.lineWidth   = 2;
    ctx.strokeStyle = '#3b82f6';
    ctx.shadowBlur  = 6;
    ctx.shadowColor = '#3b82f680';
    ctx.beginPath();

    const sliceW = W / buf.length;
    let x = 0;
    for (let i = 0; i < buf.length; i++) {
      const v = buf[i] / 128.0;
      const y = (v * H) / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      x += sliceW;
    }
    ctx.lineTo(W, H / 2);
    ctx.stroke();

    waveAnimFrame = requestAnimationFrame(draw);
  }
  draw();
}

function _bestMime() {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
    'audio/mp4',
  ];
  return types.find(t => MediaRecorder.isTypeSupported(t)) || '';
}

/* ── Results rendering ───────────────────────────────── */
function _showResults(r) {
  const overall = r.overall || 0;

  // Overall gauge (circumference of r=52: 2π*52 ≈ 327)
  const arc = el('overall-arc');
  const fill = overall / 10 * 327;
  arc.setAttribute('stroke-dasharray', `${fill} 327`);
  arc.setAttribute('stroke', scoreColor(overall));

  el('overall-score').textContent = overall.toFixed(1);
  el('overall-verdict').textContent = verdict(overall);

  // Text coverage
  const cov = r.text_coverage || 0;
  el('coverage-fill').style.width  = cov + '%';
  el('coverage-pct').textContent   = cov + '%';

  // Criteria (circumference of r=32: 2π*32 ≈ 201)
  const crits = { pronunciation: r.pronunciation, rhythm: r.rhythm, intonation: r.intonation, fluency: r.fluency };
  document.querySelectorAll('.crit-arc').forEach(arc => {
    const key  = arc.dataset.crit;
    const val  = crits[key] || 0;
    const fill = val / 10 * 201;
    arc.setAttribute('stroke-dasharray', `${fill} 201`);
    arc.setAttribute('stroke', scoreColor(val));
    el('score-' + key).textContent = val.toFixed(1);
  });

  // Strengths
  const sl = el('strengths-list');
  sl.innerHTML = '';
  (r.strengths || []).forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    sl.appendChild(li);
  });

  // Improvements
  const il = el('improvements-list');
  il.innerHTML = '';
  (r.improvements || []).forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    il.appendChild(li);
  });

  // Comment
  el('comment-text').textContent = r.comment || '';

  showSection('sec-results');
}
