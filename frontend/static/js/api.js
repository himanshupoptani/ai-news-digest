/**
 * api.js — Unified HTTP Client for AI News Intelligence Platform
 * Communicates with all FastAPI REST endpoints.
 */

const BASE_URL = "";  // Same origin — FastAPI serves both frontend and API

const Api = {

  async get(path) {
    const res = await fetch(`${BASE_URL}${path}`);
    if (!res.ok) throw new Error(`API Error [${res.status}]: ${await res.text()}`);
    return res.json();
  },

  async post(path, body) {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API Error [${res.status}]: ${await res.text()}`);
    return res.json();
  },

  // ---- Headlines Feed ----
  getHeadlines(category = "all", limit = 12) {
    return this.get(`/api/news/headlines?category=${encodeURIComponent(category)}&limit=${limit}`);
  },

  // ---- News Search ----
  searchNews(query, limit = 8, mode = null) {
    const payload = { query, limit };
    if (mode) payload.mode = mode;
    return this.post("/api/news/search", payload);
  },

  // ---- AI Digest ----
  generateDigest(query, mode = null) {
    const payload = { query };
    if (mode) payload.mode = mode;
    return this.post("/api/digest/generate", payload);
  },

  // ---- Chat ----
  sendChatMessage(message, session_id = null) {
    return this.post("/api/chat/message", { message, session_id });
  },
  sendChatMessageWithSignal(message, session_id = null, signal = null) {
    const body = JSON.stringify({ message, session_id });
    return fetch(`${BASE_URL}/api/chat/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal,
    }).then(async (res) => {
      if (!res.ok) throw new Error(`API Error [${res.status}]: ${await res.text()}`);
      return res.json();
    });
  },
  getChatSessions() {
    return this.get("/api/chat/sessions");
  },
  getChatHistory(sessionId) {
    return this.get(`/api/chat/history/${sessionId}`);
  },
  getChatSuggestions(topic = null) {
    const url = topic ? `/api/chat/suggest?topic=${encodeURIComponent(topic)}` : "/api/chat/suggest";
    return this.get(url).catch(() => ({ suggestions: [
      "What is the latest AI news today?",
      "Summarize global market headlines",
      "What's happening in South Asia?",
      "Latest technology breakthroughs"
    ]}));
  },

  // ---- Intelligence ----
  getGraph(topic = null) {
    const url = topic ? `/api/intelligence/graph?topic=${encodeURIComponent(topic)}` : "/api/intelligence/graph";
    return this.get(url);
  },
  getTimeline(query = "Artificial Intelligence") {
    return this.get(`/api/intelligence/timeline?query=${encodeURIComponent(query)}`);
  },
  getAnalytics() {
    return this.get("/api/intelligence/analytics");
  },

  // ---- Health ----
  getHealth() {
    return this.get("/api/health");
  }
};
