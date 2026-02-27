/**
 * app.js — IELTS Speaking Practice SPA state machine
 *
 * States: menu → topic_selection → [prep_timer] → recording → assessing → results
 *         menu → topic_selection → ... → (full mode) → full_results
 */

// ── Telegram Web App detection ───────────────────────────

const TgApp = window.Telegram?.WebApp || null;

if (TgApp) {
  TgApp.ready();
  TgApp.expand();
  const tp = TgApp.themeParams || {};
  const root = document.documentElement;
  const map = {
    "--tg-theme-bg-color":            tp.bg_color,
    "--tg-theme-text-color":          tp.text_color,
    "--tg-theme-hint-color":          tp.hint_color,
    "--tg-theme-link-color":          tp.link_color,
    "--tg-theme-button-color":        tp.button_color,
    "--tg-theme-button-text-color":   tp.button_text_color,
    "--tg-theme-secondary-bg-color":  tp.secondary_bg_color,
  };
  for (const [k, v] of Object.entries(map)) {
    if (v) root.style.setProperty(k, v);
  }
}

// ── Session token ────────────────────────────────────────

function getSessionToken() {
  let token = localStorage.getItem("ielts_session_token");
  if (!token) {
    token = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);
    localStorage.setItem("ielts_session_token", token);
  }
  return token;
}

const SESSION_TOKEN = getSessionToken();
const INIT_DATA = TgApp?.initData || null;

// ── State ────────────────────────────────────────────────

const state = {
  screen: "loading",
  part: null,          // 1 | 2 | 3
  topic: null,
  questions: [],
  cueCard: "",
  currentQ: 0,
  audioBlobs: [],
  result: null,
  prepTimer: null,
  prepSeconds: 60,
  prevScreen: null,    // screen to return to from topic_selection
  // Full Speaking mode
  fullMode: false,     // true when practicing all 3 parts in sequence
  fullResults: [],     // [part1Result, part2Result, part3Result]
};

const recorder = new AudioRecorder("waveform-canvas");

// ── Screen management ────────────────────────────────────

const SCREENS = {};

function registerScreen(id, htmlFn) {
  SCREENS[id] = htmlFn;
}

function showScreen(id) {
  const app = document.getElementById("app");
  app.querySelectorAll(".screen:not(#loading-screen)").forEach((el) => el.remove());

  state.screen = id;

  const htmlFn = SCREENS[id];
  if (!htmlFn) { console.error("Unknown screen:", id); return; }

  const wrapper = document.createElement("div");
  wrapper.className = "screen active";
  wrapper.id = `${id}-screen`;
  wrapper.innerHTML = htmlFn();
  app.appendChild(wrapper);

  document.getElementById("loading-screen").classList.remove("active");

  if (WIRE[id]) WIRE[id](wrapper);

  if (TgApp) {
    if (id === "menu") {
      TgApp.BackButton.hide();
    } else {
      TgApp.BackButton.show();
      TgApp.BackButton.onClick(() => navigateBack(id));
    }
  }
}

async function navigateBack(currentId) {
  if (currentId === "recording") {
    if (recorder._mediaRecorder?.state === "recording") {
      await recorder.stop().catch(() => {});
      recorder.release();
    }
    state.currentQ = 0;
    state.audioBlobs = [];
    showScreen("topic_selection");
    return;
  }
  if (currentId === "topic_selection") {
    const target = state.prevScreen || "menu";
    state.prevScreen = null;
    state.fullMode = false;
    state.fullResults = [];
    showScreen(target);
    return;
  }
  const backMap = {
    parts_menu: "menu",
    prep_timer: "topic_selection",
    results: "menu",
    full_results: "menu",

  };
  const target = backMap[currentId];
  if (target) {
    if (target === "menu") {
      state.fullMode = false;
      state.fullResults = [];
    }
    showScreen(target);
  }
}

// ── Toast notification ───────────────────────────────────

function showToast(msg, ms = 3000) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), ms);
}

// ── Part info ────────────────────────────────────────────

const PART_ICONS  = { 1: "🗣", 2: "🎙", 3: "💬" };
const PART_NAMES  = { 1: "Part 1 — Interview", 2: "Part 2 — Long Turn", 3: "Part 3 — Discussion" };
const PART_DESCS  = { 1: "4–5 everyday questions", 2: "2-min monologue", 3: "Abstract questions" };
const PART_HINTS  = {
  1: "Aim for <b>15–30 seconds</b> per answer.",
  2: "Speak for <b>up to 2 minutes</b>.",
  3: "Aim for <b>30–60 seconds</b> per answer.",
};

// Auto-stop limits (seconds) per part per question
const AUTO_STOP_SECS = { 1: 45, 2: 125, 3: 90 };

// ── Screen: menu ─────────────────────────────────────────

registerScreen("menu", () => `
  <div class="screen-header">
    <span class="screen-title">🎓 IELTS Speaking Practice</span>
  </div>

  <div class="menu-description">
    Выбери режим тренировки. IELTS Speaking — это все 3 части подряд, как на настоящем экзамене. Или можно потренировать конкретную часть отдельно.
  </div>

  <div class="spacer"></div>

  <button class="full-speaking-btn" id="full-speaking-btn">
    🎓 IELTS Speaking
    <span class="full-speaking-sub">Все 3 части подряд</span>
  </button>

  <button class="btn btn-secondary menu-parts-btn" id="parts-btn">
    📚 Отдельные части
  </button>

`);

// ── Screen: parts_menu ────────────────────────────────────

registerScreen("parts_menu", () => `
  <div class="screen-header">
    <button class="back-btn" id="back-btn">‹</button>
    <span class="screen-title">Части экзамена</span>
  </div>

  ${[1, 2, 3].map(p => `
  <button class="part-card" data-part="${p}">
    <span class="part-card-icon">${PART_ICONS[p]}</span>
    <div class="part-card-body">
      <div class="part-card-title">${PART_NAMES[p]}</div>
      <div class="part-card-desc">${PART_DESCS[p]}</div>
    </div>
    <span class="part-card-arrow">›</span>
  </button>`).join("")}
`);

// ── Screen: topic_selection ──────────────────────────────

registerScreen("topic_selection", () => `
  <div class="screen-header">
    <button class="back-btn" id="back-btn">‹</button>
    <span class="screen-title">${state.fullMode ? `Full · ${PART_NAMES[state.part]}` : PART_NAMES[state.part]}</span>
  </div>

  ${state.fullMode ? `
  <div class="full-progress-bar">
    ${[1, 2, 3].map(p => `
    <div class="full-progress-step ${p < state.part ? 'done' : p === state.part ? 'active' : ''}">
      <span>${PART_ICONS[p]}</span>
    </div>`).join("")}
  </div>` : ""}

  <div id="topic-area">
    <div class="loading-spinner" style="margin:40px auto"></div>
  </div>

  <div class="spacer"></div>
`);

// ── Screen: prep_timer (Part 2) ──────────────────────────

registerScreen("prep_timer", () => `
  <div class="screen-header">
    <button class="back-btn" id="back-btn">‹</button>
    <span class="screen-title">Part 2 — Preparation</span>
  </div>

  <div class="prep-timer-display" id="prep-countdown">1:00</div>
  <div class="prep-progress-bar">
    <div class="prep-progress-fill" id="prep-fill" style="width:100%"></div>
  </div>

  <div class="cue-card" id="prep-cue-card">${escapeHtml(state.cueCard)}</div>

  <div class="spacer"></div>

  <button class="btn btn-secondary" id="start-early-btn">🎤 Start Recording Early</button>
`);

// ── Screen: recording ────────────────────────────────────

registerScreen("recording", () => {
  const total = state.part === 2 ? 1 : state.questions.length;
  const idx   = state.currentQ;
  const dots  = state.part !== 2
    ? `<div class="progress-dots">${Array.from({length: total}, (_, i) => {
        const cls = i < idx ? "dot done" : i === idx ? "dot active" : "dot";
        return `<span class="${cls}"></span>`;
      }).join("")}</div>`
    : "";

  const questionHtml = state.part === 2
    ? `<div class="cue-card">${escapeHtml(state.cueCard)}</div>`
    : `<div class="question-bubble">${escapeHtml(state.questions[idx] || "")}</div>`;

  const maxSecs = AUTO_STOP_SECS[state.part] || 60;

  return `
  <div class="screen-header">
    <button class="back-btn" id="back-btn">‹</button>
    <span class="screen-title">Q ${idx + 1}${total > 1 ? ` / ${total}` : ""}</span>
  </div>

  ${dots}
  ${questionHtml}

  <canvas id="waveform-canvas" width="400" height="56"></canvas>

  <div class="record-area">
    <div class="record-btn-wrap">
      <div class="record-ring" id="record-ring"></div>
      <button class="record-btn" id="record-btn">🎤</button>
    </div>
    <div class="record-timer" id="record-timer">0:00</div>
    <div class="record-hint">${PART_HINTS[state.part]}</div>
    <div class="record-limit" id="record-limit" style="display:none">⏱ Max: ${formatTime(maxSecs)}</div>
  </div>

  <div class="spacer"></div>

  <button class="btn btn-primary" id="stop-btn" style="display:none">⏹ Stop &amp; Submit</button>
`;
});

// ── Screen: assessing ────────────────────────────────────

registerScreen("assessing", () => {
  const isBetweenParts = state.fullMode && state.part < 3;
  const icon      = isBetweenParts ? "✅" : "🎧";
  const headline  = isBetweenParts
    ? `Part ${state.part} complete`
    : `Analysing${state.fullMode ? ` Part ${state.part}` : ""}…`;
  const sub = isBetweenParts
    ? `Saving results · loading Part ${state.part + 1}…`
    : "Assessing your English…<br>15–45 seconds";
  return `
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;text-align:center">
    <div style="font-size:32px">${icon}</div>
    <div style="font-size:18px;font-weight:600">${headline}</div>
    <div class="assessing-dots">
      <div class="assessing-dot"></div>
      <div class="assessing-dot"></div>
      <div class="assessing-dot"></div>
    </div>
    <div class="text-hint">${sub}</div>
    ${!isBetweenParts ? `<div class="assessing-progress"><div class="assessing-progress-fill"></div></div>` : ""}
  </div>`;
});

// ── Screen: results ──────────────────────────────────────

registerScreen("results", () => {
  const r = state.result || {};
  const band = r.overall_band ?? "—";
  const criteria = [
    { key: "fluency_coherence",  label: "Fluency & Coherence" },
    { key: "lexical_resource",   label: "Lexical Resource" },
    { key: "grammatical_range",  label: "Grammar & Accuracy" },
    { key: "pronunciation",      label: "Pronunciation" },
  ];

  const criteriaHtml = criteria.map(({ key, label }) => {
    const score = r[key] ?? 0;
    const pct   = (score / 9) * 100;
    const feedback = r[key + "_feedback"] || r.feedback?.[key] || "";
    return `
    <div class="criterion">
      <div class="criterion-header">
        <span class="criterion-name">${label}</span>
        <span class="criterion-score">${score}</span>
      </div>
      <div class="criterion-bar">
        <div class="criterion-bar-fill" style="width:${pct}%"></div>
      </div>
    </div>
    <div class="feedback-item">
      <div class="feedback-header" data-feedback="${key}">
        <span>▼ ${label} feedback</span>
        <span class="chevron">▾</span>
      </div>
      <div class="feedback-body" id="fb-${key}">${escapeHtml(feedback)}</div>
    </div>`;
  }).join("");

  return `
  <div class="screen-header">
    <span class="screen-title">🏆 Results — ${PART_NAMES[state.part]}</span>
  </div>

  <div class="band-badge">
    <div class="band-number">Band ${band}</div>
    <div class="band-label">${bandLabel(band)}</div>
  </div>

  <div class="criteria-list">${criteriaHtml}</div>

  <div class="spacer"></div>

  <div class="btn-row mt-auto">
    <button class="btn btn-secondary" id="retry-btn">🔄 Try Again</button>
    <button class="btn btn-primary"   id="menu-btn">🏠 Menu</button>
  </div>
`;
});

// ── Screen: full_results ─────────────────────────────────

registerScreen("full_results", () => {
  const criteria = [
    { key: "fluency_coherence",  label: "Fluency" },
    { key: "lexical_resource",   label: "Lexical" },
    { key: "grammatical_range",  label: "Grammar" },
    { key: "pronunciation",      label: "Pronunciation" },
  ];

  const panels = [1, 2, 3].map(p => {
    const r = state.fullResults[p - 1] || {};
    const band = r.overall_band ?? "—";
    const barsHtml = criteria.map(({ key, label }) => {
      const score = r[key] ?? 0;
      const pct = (score / 9) * 100;
      return `
      <div class="criterion criterion-compact">
        <div class="criterion-header">
          <span class="criterion-name">${label}</span>
          <span class="criterion-score">${score}</span>
        </div>
        <div class="criterion-bar">
          <div class="criterion-bar-fill" style="width:${pct}%"></div>
        </div>
      </div>`;
    }).join("");

    return `
    <div class="full-result-panel">
      <div class="full-result-header">
        <span class="full-result-part">${PART_ICONS[p]} ${PART_NAMES[p]}</span>
        <span class="full-result-band">Band ${band}</span>
      </div>
      <div class="full-result-criteria">${barsHtml}</div>
    </div>`;
  }).join("");

  const bands = state.fullResults.map(r => r?.overall_band).filter(b => typeof b === "number");
  const avgBand = bands.length ? (bands.reduce((a, b) => a + b, 0) / bands.length).toFixed(1) : "—";

  return `
  <div class="screen-header">
    <span class="screen-title">🏆 Full Speaking Results</span>
  </div>

  <div class="band-badge">
    <div class="band-number">~${avgBand}</div>
    <div class="band-label">Average across all 3 parts</div>
  </div>

  ${panels}

  <div class="spacer"></div>

  <div class="btn-row mt-auto">
    <button class="btn btn-secondary" id="retry-full-btn">🔄 Practice Again</button>
    <button class="btn btn-primary"   id="menu-btn">🏠 Menu</button>
  </div>
`;
});


// ── Wire: event listeners per screen ────────────────────

const WIRE = {

  menu(el) {
    el.querySelector("#full-speaking-btn").addEventListener("click", () => {
      state.fullMode = true;
      state.fullResults = [];
      state.part = 1;
      state.currentQ = 0;
      state.audioBlobs = [];
      state.prevScreen = "menu";
      loadTopicScreen();
    });

    el.querySelector("#parts-btn").addEventListener("click", () => {
      showScreen("parts_menu");
    });

  },

  parts_menu(el) {
    el.querySelector("#back-btn").addEventListener("click", () => showScreen("menu"));
    el.querySelectorAll(".part-card").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.fullMode = false;
        state.fullResults = [];
        state.part = parseInt(btn.dataset.part);
        state.currentQ = 0;
        state.audioBlobs = [];
        state.prevScreen = "parts_menu";
        loadTopicScreen();
      });
    });
  },

  topic_selection(el) {
    el.querySelector("#back-btn").addEventListener("click", () => {
      const target = state.prevScreen || "menu";
      state.prevScreen = null;
      state.fullMode = false;
      state.fullResults = [];
      showScreen(target);
    });
    loadTopicData(el);
  },

  prep_timer(el) {
    el.querySelector("#back-btn").addEventListener("click", () => {
      clearInterval(state.prepTimer);
      showScreen("topic_selection");
    });
    el.querySelector("#start-early-btn").addEventListener("click", () => {
      clearInterval(state.prepTimer);
      state.currentQ = 0;
      showScreen("recording");
    });
    startPrepTimer(el);
  },

  recording(el) {
    const btn      = el.querySelector("#record-btn");
    const ring     = el.querySelector("#record-ring");
    const stopBtn  = el.querySelector("#stop-btn");
    const timerEl  = el.querySelector("#record-timer");
    const limitEl  = el.querySelector("#record-limit");
    const backBtn  = el.querySelector("#back-btn");
    let isRecording = false;
    let autoStopTimer = null;

    function clearAutoStop() {
      if (autoStopTimer) { clearTimeout(autoStopTimer); autoStopTimer = null; }
    }

    backBtn.addEventListener("click", async () => {
      clearAutoStop();
      if (isRecording) {
        isRecording = false;
        await recorder.stop().catch(() => {});
        recorder.release();
      }
      state.currentQ = 0;
      state.audioBlobs = [];
      showScreen("topic_selection");
    });

    btn.addEventListener("click", async () => {
      if (!isRecording) {
        try {
          await recorder.start(timerEl);
        } catch (err) {
          showToast("Microphone access denied: " + err.message);
          return;
        }
        isRecording = true;
        btn.classList.add("recording");
        btn.textContent = "⏹";
        ring.classList.add("pulsing");
        stopBtn.style.display = "flex";
        if (limitEl) limitEl.style.display = "block";

        // Auto-stop when time limit reached
        const maxSecs = AUTO_STOP_SECS[state.part] || 60;
        autoStopTimer = setTimeout(() => {
          if (isRecording) {
            showToast("⏱ Time limit reached — submitting…");
            doStopAndSubmit();
          }
        }, maxSecs * 1000);
      } else {
        clearAutoStop();
        await doStopAndSubmit();
      }
    });

    stopBtn.addEventListener("click", async () => {
      if (isRecording) {
        clearAutoStop();
        await doStopAndSubmit();
      }
    });

    async function doStopAndSubmit() {
      isRecording = false;
      btn.disabled = true;
      stopBtn.disabled = true;
      ring.classList.remove("pulsing");

      const blob = await recorder.stop();
      state.audioBlobs[state.currentQ] = blob;

      try {
        await submitAnswer(SESSION_TOKEN, state.currentQ, blob);
      } catch (err) {
        showToast("Upload error: " + err.message);
        btn.disabled = false;
        stopBtn.disabled = false;
        isRecording = true;
        return;
      }

      const total = state.part === 2 ? 1 : state.questions.length;
      if (state.part !== 2 && state.currentQ + 1 < total) {
        state.currentQ++;
        showScreen("recording");
      } else {
        showScreen("assessing");
        await runAssessment();
      }
    }
  },

  assessing() {},

  results(el) {
    el.querySelectorAll(".feedback-header").forEach((hdr) => {
      hdr.addEventListener("click", () => {
        const key = hdr.dataset.feedback;
        const body = document.getElementById(`fb-${key}`);
        body.classList.toggle("open");
        hdr.classList.toggle("open");
      });
    });

    el.querySelector("#retry-btn").addEventListener("click", () => {
      state.currentQ = 0;
      state.audioBlobs = [];
      if (state.part === 2) {
        state.prepSeconds = 60;
        showScreen("prep_timer");
      } else {
        showScreen("recording");
      }
    });

    el.querySelector("#menu-btn").addEventListener("click", () => {
      state.fullMode = false;
      state.fullResults = [];
      showScreen("menu");
    });
  },

  full_results(el) {
    el.querySelector("#retry-full-btn").addEventListener("click", () => {
      state.fullMode = true;
      state.fullResults = [];
      state.part = 1;
      state.currentQ = 0;
      state.audioBlobs = [];
      loadTopicScreen();
    });
    el.querySelector("#menu-btn").addEventListener("click", () => {
      state.fullMode = false;
      state.fullResults = [];
      showScreen("menu");
    });
  },

};

// ── Topic loading logic ──────────────────────────────────

function loadTopicScreen() {
  showScreen("topic_selection");
}

async function loadTopicData(screenEl) {
  const area = screenEl.querySelector("#topic-area");

  async function fetchTopic() {
    area.innerHTML = `<div class="loading-spinner" style="margin:40px auto"></div>`;
    try {
      const data = await generateTopic(state.part, SESSION_TOKEN);
      state.topic     = data.topic;
      state.questions = data.questions || [];
      state.cueCard   = data.cue_card  || "";
      renderTopicCard(area);
    } catch (err) {
      area.innerHTML = `<p class="text-hint" style="text-align:center;padding:20px">${err.message}</p>
        <button class="btn btn-secondary" id="retry-topic-btn">Try again</button>`;
      screenEl.querySelector("#retry-topic-btn")?.addEventListener("click", fetchTopic);
    }
  }

  const PART_DESCRIPTIONS = {
    1: "4–5 вопросов на повседневные темы. Отвечай развёрнуто — 15–30 секунд на каждый вопрос. Вопросы открываются по одному, когда начнёшь.",
    2: "1 минута подготовки, затем 2-минутный монолог по карточке с заданием. Карточка откроется, когда начнёшь.",
    3: "4–5 абстрактных вопросов, связанных с темой части 2. Развивай мысль — 30–60 секунд на ответ.",
  };

  function renderTopicCard(container) {
    // Cue card for Part 2 is shown only on the prep timer screen, not here.
    container.innerHTML = `
      <div class="topic-card">
        <div class="topic-label">${PART_NAMES[state.part]}</div>
        <div class="topic-name">${escapeHtml(state.topic)}</div>
        <div class="topic-part-desc">${PART_DESCRIPTIONS[state.part]}</div>
      </div>
      <div class="btn-row">
        <button class="btn btn-primary" id="start-btn">✅ Start</button>
        <button class="btn btn-secondary" id="another-btn">🔄 Another topic</button>
      </div>
    `;

    container.querySelector("#start-btn").addEventListener("click", () => {
      state.currentQ = 0;
      state.audioBlobs = [];
      if (state.part === 2) {
        state.prepSeconds = 60;
        showScreen("prep_timer");
      } else {
        showScreen("recording");
      }
    });

    container.querySelector("#another-btn").addEventListener("click", fetchTopic);
  }

  await fetchTopic();
}

// ── Part 2 prep timer ────────────────────────────────────

function startPrepTimer(screenEl) {
  const countdownEl = screenEl.querySelector("#prep-countdown");
  const fillEl      = screenEl.querySelector("#prep-fill");
  const TOTAL = 60;
  let remaining = TOTAL;

  function update() {
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    countdownEl.textContent = `${m}:${s.toString().padStart(2, "0")}`;
    fillEl.style.width = `${(remaining / TOTAL) * 100}%`;
  }

  update();

  state.prepTimer = setInterval(() => {
    remaining--;
    update();
    if (remaining <= 0) {
      clearInterval(state.prepTimer);
      state.currentQ = 0;
      showScreen("recording");
    }
  }, 1000);
}

// ── Assessment ───────────────────────────────────────────

async function runAssessment() {
  try {
    const result = await requestAssessment(SESSION_TOKEN, INIT_DATA);

    if (state.fullMode) {
      state.fullResults[state.part - 1] = result;
      if (state.part < 3) {
        const nextPart = state.part + 1;
        state.part = nextPart;
        state.currentQ = 0;
        state.audioBlobs = [];
        showToast(`✅ Part ${nextPart - 1} done! Now Part ${nextPart}…`, 2500);
        setTimeout(() => loadTopicScreen(), 1200);
      } else {
        showScreen("full_results");
      }
    } else {
      state.result = result;
      showScreen("results");
    }
  } catch (err) {
    if (state.fullMode) {
      state.fullResults[state.part - 1] = {};
      showToast("Assessment failed: " + err.message, 4000);
      if (state.part < 3) {
        const nextPart = state.part + 1;
        state.part = nextPart;
        state.currentQ = 0;
        state.audioBlobs = [];
        setTimeout(() => loadTopicScreen(), 1500);
      } else {
        showScreen("full_results");
      }
    } else {
      showToast("Assessment failed: " + err.message, 5000);
      state.result = {};
      showScreen("results");
    }
  }
}

// ── Helpers ──────────────────────────────────────────────

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function bandLabel(band) {
  if (typeof band !== "number") return "";
  if (band >= 8.5) return "C2 — Expert";
  if (band >= 7.5) return "C1 — Very Good";
  if (band >= 6.5) return "B2 — Good";
  if (band >= 5.5) return "B1 — Modest";
  if (band >= 4.5) return "A2 — Limited";
  return "A1 — Beginner";
}

function formatTime(secs) {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

// ── Boot ─────────────────────────────────────────────────

window.addEventListener("DOMContentLoaded", () => {
  showScreen("menu");
});
