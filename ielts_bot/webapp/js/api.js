/**
 * api.js — HTTP client for IELTS server API
 */

// Relative base so the app works under any subpath (e.g. /ielts/)
const API_BASE = ".";

/**
 * Generate a topic for the given part.
 * @param {number} part - 1, 2, or 3
 * @param {string} sessionToken
 * @returns {Promise<{topic: string, questions: string[], cue_card: string}>}
 */
async function generateTopic(part, sessionToken) {
  const resp = await fetch(`${API_BASE}/api/topic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ part, session_token: sessionToken }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Topic generation failed (${resp.status})`);
  }
  return resp.json();
}

/**
 * Submit an audio answer blob.
 * @param {string} sessionToken
 * @param {number} questionIndex
 * @param {Blob} audioBlob
 * @returns {Promise<{status: string, question_index: number}>}
 */
async function submitAnswer(sessionToken, questionIndex, audioBlob) {
  const fd = new FormData();
  fd.append("session_token", sessionToken);
  fd.append("question_index", String(questionIndex));
  fd.append("file", audioBlob, "answer.webm");

  const resp = await fetch(`${API_BASE}/api/answer`, {
    method: "POST",
    body: fd,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${resp.status})`);
  }
  return resp.json();
}

/**
 * Trigger AI assessment for the session.
 * @param {string} sessionToken
 * @param {string|null} initData - Telegram initData string (optional)
 * @returns {Promise<object>} assessment result JSON
 */
async function requestAssessment(sessionToken, initData = null) {
  const headers = { "Content-Type": "application/json" };
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  }
  const resp = await fetch(`${API_BASE}/api/assess`, {
    method: "POST",
    headers,
    body: JSON.stringify({ session_token: sessionToken }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Assessment failed (${resp.status})`);
  }
  return resp.json();
}

/**
 * Fetch user stats.
 * @param {string|null} initData - Telegram initData (optional)
 * @param {string|null} sessionToken
 * @returns {Promise<object>}
 */
async function getStats(initData = null, sessionToken = null) {
  const headers = {};
  if (initData)     headers["X-Telegram-Init-Data"] = initData;
  if (sessionToken) headers["X-Session-Token"] = sessionToken;

  const resp = await fetch(`${API_BASE}/api/stats`, { headers });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Stats failed (${resp.status})`);
  }
  return resp.json();
}
