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

  // ---- News Search ----
  searchNews(query, limit = 6, mode = "demo") {
    return this.post("/api/news/search", { query, limit, mode });
  },

  // ---- AI Digest ----
  generateDigest(query, mode = "demo") {
    return this.post("/api/digest/generate", { query, mode });
  },

  // ---- Chat ----
  sendChatMessage(message, session_id = null) {
    return this.post("/api/chat/message", { message, session_id });
  },
  getChatSessions() {
    return this.get("/api/chat/sessions");
  },
  getChatHistory(sessionId) {
    return this.get(`/api/chat/history/${sessionId}`);
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

