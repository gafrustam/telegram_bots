/**
 * recorder.js — Browser MediaRecorder wrapper with waveform visualisation.
 */

class AudioRecorder {
  constructor(canvasId) {
    this._canvas = canvasId ? document.getElementById(canvasId) : null;
    this._mediaRecorder = null;
    this._chunks = [];
    this._stream = null;
    this._analyser = null;
    this._animFrame = null;
    this._startTime = null;
    this._timerEl = null;
    this._timerInterval = null;
    this.blob = null;
  }

  /** Request microphone permission and set up stream. */
  async init() {
    if (this._stream) return;  // already initialised
    this._stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });
  }

  /**
   * Start recording.
   * @param {HTMLElement|null} timerEl - element to update with elapsed time
   */
  async start(timerEl = null) {
    await this.init();
    this.blob = null;
    this._chunks = [];
    this._timerEl = timerEl;

    // Pick best supported MIME type
    const mimeType = this._pickMimeType();

    this._mediaRecorder = new MediaRecorder(
      this._stream,
      mimeType ? { mimeType } : {}
    );

    this._mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) this._chunks.push(e.data);
    };

    this._mediaRecorder.start(100);  // collect chunks every 100ms
    this._startTime = Date.now();

    // Start waveform
    this._setupAnalyser();
    this._drawWaveform();

    // Start timer display
    if (timerEl) {
      timerEl.textContent = "0:00";
      this._timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - this._startTime) / 1000);
        const m = Math.floor(elapsed / 60);
        const s = elapsed % 60;
        timerEl.textContent = `${m}:${s.toString().padStart(2, "0")}`;
      }, 500);
    }
  }

  /**
   * Stop recording and return the audio blob.
   * @returns {Promise<Blob>}
   */
  stop() {
    return new Promise((resolve) => {
      if (!this._mediaRecorder || this._mediaRecorder.state === "inactive") {
        resolve(this.blob || new Blob(this._chunks));
        return;
      }
      this._mediaRecorder.onstop = () => {
        const mimeType = this._mediaRecorder.mimeType || "audio/webm";
        this.blob = new Blob(this._chunks, { type: mimeType });
        resolve(this.blob);
      };
      this._mediaRecorder.stop();
      this._stopAnimation();
      if (this._timerInterval) {
        clearInterval(this._timerInterval);
        this._timerInterval = null;
      }
    });
  }

  /** Release microphone. */
  release() {
    this._stopAnimation();
    if (this._stream) {
      this._stream.getTracks().forEach((t) => t.stop());
      this._stream = null;
    }
    if (this._timerInterval) {
      clearInterval(this._timerInterval);
      this._timerInterval = null;
    }
  }

  /** Elapsed recording seconds. */
  getElapsedSeconds() {
    if (!this._startTime) return 0;
    return (Date.now() - this._startTime) / 1000;
  }

  // ── Private helpers ──

  _pickMimeType() {
    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/ogg",
    ];
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return "";
  }

  _setupAnalyser() {
    if (!this._canvas || !this._stream) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const src = ctx.createMediaStreamSource(this._stream);
      this._analyser = ctx.createAnalyser();
      this._analyser.fftSize = 256;
      src.connect(this._analyser);
    } catch (_) {
      this._analyser = null;
    }
  }

  _drawWaveform() {
    if (!this._canvas || !this._analyser) return;
    const canvas = this._canvas;
    const ctx2d = canvas.getContext("2d");
    const bufLen = this._analyser.frequencyBinCount;
    const data = new Uint8Array(bufLen);

    const draw = () => {
      this._animFrame = requestAnimationFrame(draw);
      this._analyser.getByteTimeDomainData(data);

      const W = canvas.width, H = canvas.height;
      ctx2d.clearRect(0, 0, W, H);

      const style = getComputedStyle(document.documentElement);
      const barColor = style.getPropertyValue("--tg-theme-button-color").trim() || "#2678b6";
      ctx2d.fillStyle = barColor;

      const barW = 3, gap = 2;
      const total = barW + gap;
      const count = Math.floor(W / total);
      const step  = Math.floor(bufLen / count);

      for (let i = 0; i < count; i++) {
        const value = data[i * step] / 128.0;  // 0..2
        const height = Math.max(3, Math.abs(value - 1.0) * H);
        const x = i * total;
        const y = (H - height) / 2;
        ctx2d.fillRect(x, y, barW, height);
      }
    };
    draw();
  }

  _stopAnimation() {
    if (this._animFrame) {
      cancelAnimationFrame(this._animFrame);
      this._animFrame = null;
    }
    // Clear canvas
    if (this._canvas) {
      const ctx2d = this._canvas.getContext("2d");
      ctx2d.clearRect(0, 0, this._canvas.width, this._canvas.height);
    }
  }
}
