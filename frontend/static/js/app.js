/**
 * app.js — Frontend State Controller for AI News Intelligence Platform
 * Handles tab navigation, search, rendering, and chat interactions.
 */

// ============================================================
// STATE
// ============================================================
const State = {
  activeTab: "home",
  currentSessionId: null,
  isLoading: false,
};

// ============================================================
// UTILITIES
// ============================================================
function setLoading(show) {
  State.isLoading = show;
  const spinner = document.getElementById("global-spinner");
  if (spinner) spinner.classList.toggle("hidden", !show);
}

function showError(message) {
  const el = document.getElementById("error-toast");
  if (!el) return;
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 4000);
}

function switchTab(tabName) {
  State.activeTab = tabName;
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
  document.querySelectorAll(".nav-btn").forEach(b => {
    b.classList.remove("bg-blue-600", "text-white");
    b.classList.add("text-slate-400");
  });
  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.remove("hidden");
  const btn = document.getElementById(`nav-${tabName}`);
  if (btn) {
    btn.classList.add("bg-blue-600", "text-white");
    btn.classList.remove("text-slate-400");
  }
  // Auto-load content for intelligence tabs
  if (tabName === "graph") loadGraph();
  if (tabName === "timeline") loadTimeline();
  if (tabName === "analytics") loadAnalytics();
  if (tabName === "home") loadHome();
}

// ============================================================
// BADGE HELPERS
// ============================================================
function evidenceBadge(strength) {
  const map = {
    HIGH: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
    MEDIUM: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
    LOW: "bg-orange-500/20 text-orange-400 border-orange-500/40",
    INSUFFICIENT: "bg-red-500/20 text-red-400 border-red-500/40",
  };
  const cls = map[strength] || map["LOW"];
  return `<span class="text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}">${strength}</span>`;
}

function sourceBadge(name) {
  return `<span class="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 font-medium">${name}</span>`;
}

// ============================================================
// HOME / DISCOVER TAB
// ============================================================
async function loadHome() {
  try {
    setLoading(true);
    const [health, analytics] = await Promise.all([Api.getHealth(), Api.getAnalytics()]);
    renderHome(health, analytics);
  } catch (e) {
    showError("Failed to load home: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderHome(health, analytics) {
  const el = document.getElementById("home-content");
  if (!el) return;

  const trending = analytics.trending_topics || [];
  const trendingHtml = trending.slice(0, 5).map(t => `
    <button onclick="quickSearch('${t.name}')"
      class="flex items-center gap-2 px-3 py-1.5 rounded-full glass-card border border-slate-700 hover:border-blue-500 transition text-sm text-slate-300 hover:text-white">
      <span class="text-blue-400 font-bold">${t.tag}</span>
      <span>${t.name}</span>
      <span class="ml-auto text-xs text-slate-500">${t.trend_score}</span>
    </button>
  `).join("");

  const statHtml = `
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="glass-card rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-blue-400">${analytics.total_articles}</div>
        <div class="text-xs text-slate-400 mt-1">Articles Indexed</div>
      </div>
      <div class="glass-card rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-emerald-400">${analytics.total_sources}</div>
        <div class="text-xs text-slate-400 mt-1">Active Publishers</div>
      </div>
      <div class="glass-card rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-purple-400">${analytics.total_topics}</div>
        <div class="text-xs text-slate-400 mt-1">Topic Categories</div>
      </div>
    </div>
  `;

  el.innerHTML = `
    ${statHtml}
    <h2 class="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-3">Trending Right Now</h2>
    <div class="flex flex-wrap gap-2 mb-6">${trendingHtml}</div>
    <div class="glass-card rounded-xl p-4 flex items-center gap-3">
      <div class="w-2 h-2 rounded-full ${health.app_mode === 'live' ? 'bg-emerald-400' : 'bg-yellow-400'} animate-pulse"></div>
      <span class="text-sm text-slate-300">
        Platform Mode: <strong class="text-white">${health.app_mode.toUpperCase()}</strong> &nbsp;|&nbsp;
        Database: <strong class="text-emerald-400">${health.database}</strong>
      </span>
    </div>
  `;
}

// ============================================================
// NEWS SEARCH TAB
// ============================================================
function quickSearch(query) {
  switchTab("search");
  document.getElementById("search-input").value = query;
  executeSearch();
}

async function executeSearch() {
  const query = document.getElementById("search-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.searchNews(query, 6, "demo");
    renderSearchResults(res);
  } catch (e) {
    showError("Search failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderSearchResults(res) {
  const el = document.getElementById("search-results");
  if (!el) return;
  if (!res.articles || res.articles.length === 0) {
    el.innerHTML = `<p class="text-slate-500 text-center py-8">No articles found for this query.</p>`;
    return;
  }
  el.innerHTML = res.articles.map(a => `
    <div class="glass-card glass-card-hover rounded-xl p-4 transition cursor-pointer" onclick="window.open('${a.url}','_blank')">
      <div class="flex items-start justify-between gap-2 mb-2">
        <h3 class="font-semibold text-white text-sm leading-snug">${a.title}</h3>
        ${sourceBadge(a.source_name || "Unknown")}
      </div>
      <p class="text-xs text-slate-400 line-clamp-2">${a.content?.slice(0, 160) || ""}...</p>
      <div class="flex items-center gap-2 mt-2">
        <span class="text-xs text-slate-500">${a.published_at || ""}</span>
        ${a.category ? `<span class="text-xs text-blue-400"># ${a.category}</span>` : ""}
      </div>
    </div>
  `).join("");
}

// ============================================================
// AI DIGEST TAB
// ============================================================
async function generateDigest() {
  const query = document.getElementById("digest-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.generateDigest(query, "demo");
    renderDigest(res);
  } catch (e) {
    showError("Digest failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderDigest(res) {
  const el = document.getElementById("digest-result");
  if (!el) return;
  const d = res.digest;
  const audit = res.audit_report;
  const bias = res.bias_report;

  const keyPoints = (d.key_points || []).map((p, i) => `
    <li class="flex gap-2 text-sm text-slate-300">
      <span class="text-blue-400 font-bold mt-0.5">›</span>
      <span>${p}</span>
    </li>
  `).join("");

  const citations = (d.citations || []).map(c => `
    <div class="text-xs glass-card rounded-lg p-3">
      <span class="citation-badge">[${c.index}]</span>
      <span class="text-slate-300 ml-2">${c.headline}</span>
      ${c.url ? `<a href="${c.url}" target="_blank" class="text-blue-400 ml-2 hover:underline">↗</a>` : ""}
    </div>
  `).join("");

  el.innerHTML = `
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-bold text-white">${d.headline || "AI Intelligence Digest"}</h2>
        ${evidenceBadge(d.evidence_strength)}
      </div>
      <p class="text-sm text-slate-300 leading-relaxed">${d.executive_summary || ""}</p>
      <div>
        <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">Key Intelligence Points</h3>
        <ul class="space-y-1">${keyPoints}</ul>
      </div>
      ${citations ? `
        <div>
          <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">Source Citations</h3>
          <div class="space-y-2">${citations}</div>
        </div>
      ` : ""}
      <div class="grid grid-cols-2 gap-3 pt-2">
        <div class="glass-card rounded-lg p-3">
          <div class="text-xs text-slate-400 mb-1">Hallucination Shield</div>
          <div class="text-sm font-semibold text-white">${audit.evidence_strength || "—"}</div>
          <div class="text-xs text-slate-500">Evidence Score: ${(audit.evidence_score || 0).toFixed(2)}</div>
        </div>
        <div class="glass-card rounded-lg p-3">
          <div class="text-xs text-slate-400 mb-1">Bias Analysis (HHI)</div>
          <div class="text-sm font-semibold text-white">${bias.diversity_rating || "—"}</div>
          <div class="text-xs text-slate-500">Sources: ${bias.total_sources || 0}</div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================
// CHAT TAB
// ============================================================
async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input?.value?.trim();
  if (!message) return;
  input.value = "";
  appendChatBubble("user", message);
  try {
    setLoading(true);
    const res = await Api.sendChatMessage(message, State.currentSessionId);
    State.currentSessionId = res.session_id;
    appendChatBubble("assistant", res.content, res.evidence_strength);
  } catch (e) {
    showError("Chat error: " + e.message);
  } finally {
    setLoading(false);
  }
}

function appendChatBubble(role, content, strength = null) {
  const chatBox = document.getElementById("chat-messages");
  if (!chatBox) return;
  const isUser = role === "user";
  const div = document.createElement("div");
  div.className = `flex ${isUser ? "justify-end" : "justify-start"} mb-3`;
  div.innerHTML = `
    <div class="max-w-[80%] ${isUser
      ? "bg-blue-600 text-white rounded-2xl rounded-br-sm"
      : "glass-card text-slate-200 rounded-2xl rounded-bl-sm"
    } px-4 py-3 text-sm leading-relaxed">
      ${content}
      ${strength ? `<div class="mt-2">${evidenceBadge(strength)}</div>` : ""}
    </div>
  `;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ============================================================
// KNOWLEDGE GRAPH TAB
// ============================================================
async function loadGraph() {
  const topic = document.getElementById("graph-topic-input")?.value?.trim() || null;
  try {
    setLoading(true);
    const res = await Api.getGraph(topic);
    renderGraph(res);
  } catch (e) {
    showError("Graph failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderGraph(res) {
  const el = document.getElementById("graph-content");
  if (!el) return;
  const colorMap = { topic: "#3b82f6", source: "#10b981", article: "#8b5cf6", event: "#f59e0b" };

  const nodeRows = res.nodes.map(n =>
    `<div class="flex items-center gap-3 py-1.5 border-b border-slate-800">
      <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${colorMap[n.group] || '#64748b'}"></span>
      <span class="text-xs text-slate-300 flex-1">${n.label}</span>
      <span class="text-xs text-slate-500 capitalize">${n.group}</span>
    </div>`
  ).join("");

  const edgeRows = res.edges.map(e =>
    `<div class="flex items-center gap-2 py-1 text-xs text-slate-400 border-b border-slate-800">
      <span class="text-blue-400">${e.source}</span>
      <span class="text-slate-600">──${e.relation}──›</span>
      <span class="text-emerald-400">${e.target}</span>
    </div>`
  ).join("");

  el.innerHTML = `
    <div class="flex gap-4 mb-4 text-xs">
      ${Object.entries(colorMap).map(([g, c]) =>
        `<span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full" style="background:${c}"></span>${g}</span>`
      ).join("")}
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="glass-card rounded-xl p-4">
        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Nodes (${res.total_nodes})</h3>
        <div class="space-y-0.5 max-h-64 overflow-y-auto">${nodeRows}</div>
      </div>
      <div class="glass-card rounded-xl p-4">
        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Edges (${res.total_edges})</h3>
        <div class="space-y-0.5 max-h-64 overflow-y-auto">${edgeRows}</div>
      </div>
    </div>
  `;
}

// ============================================================
// TIMELINE TAB
// ============================================================
async function loadTimeline() {
  const query = document.getElementById("timeline-input")?.value?.trim() || "Artificial Intelligence";
  try {
    setLoading(true);
    const res = await Api.getTimeline(query);
    renderTimeline(res);
  } catch (e) {
    showError("Timeline failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderTimeline(res) {
  const el = document.getElementById("timeline-content");
  if (!el) return;
  if (!res.timeline || res.timeline.length === 0) {
    el.innerHTML = `<p class="text-slate-500 text-center py-8">No timeline data available.</p>`;
    return;
  }
  el.innerHTML = `
    <h2 class="text-base font-bold text-white mb-4">${res.event_topic} — ${res.total_milestones} Milestones</h2>
    <div class="relative pl-6 border-l-2 border-slate-700 space-y-6">
      ${res.timeline.map((m, i) => `
        <div class="relative">
          <div class="absolute -left-[1.6rem] top-1 w-4 h-4 rounded-full border-2 border-blue-500 bg-slate-900"></div>
          <div class="glass-card rounded-xl p-4 ml-2">
            <div class="text-xs text-blue-400 font-semibold mb-1">${m.display_time}</div>
            <h3 class="text-sm font-semibold text-white mb-1">${m.headline}</h3>
            <p class="text-xs text-slate-400">${m.summary}</p>
            <div class="flex items-center gap-2 mt-2">
              ${sourceBadge(m.source_name)}
              ${m.url ? `<a href="${m.url}" target="_blank" class="text-xs text-blue-400 hover:underline">View Source ↗</a>` : ""}
            </div>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

// ============================================================
// ANALYTICS TAB
// ============================================================
async function loadAnalytics() {
  try {
    setLoading(true);
    const res = await Api.getAnalytics();
    renderAnalytics(res);
  } catch (e) {
    showError("Analytics failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderAnalytics(res) {
  const el = document.getElementById("analytics-content");
  if (!el) return;

  const topicBars = Object.entries(res.topic_distribution || {}).map(([k, v]) => `
    <div class="flex items-center gap-3 text-sm">
      <span class="w-32 text-slate-400 truncate">${k}</span>
      <div class="flex-1 bg-slate-800 rounded-full h-2">
        <div class="bg-blue-500 h-2 rounded-full" style="width:${Math.min(100, v * 20)}%"></div>
      </div>
      <span class="text-slate-300 w-6 text-right">${v}</span>
    </div>
  `).join("");

  const trendCards = (res.trending_topics || []).map(t => `
    <div class="glass-card rounded-xl p-3 flex items-start gap-3">
      <div class="text-lg font-bold text-blue-400">${t.tag}</div>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium text-white truncate">${t.name}</div>
        <div class="text-xs text-slate-400">${t.article_count} articles · ${t.source_count} publishers</div>
      </div>
      <div class="text-right">
        <div class="text-sm font-bold text-emerald-400">${t.trend_score}</div>
        <div class="text-xs text-slate-500">score</div>
      </div>
    </div>
  `).join("");

  el.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="glass-card rounded-xl p-5">
        <h3 class="text-sm font-bold text-slate-300 mb-4">Topic Distribution</h3>
        <div class="space-y-3">${topicBars || '<p class="text-slate-500 text-sm">No distribution data.</p>'}</div>
      </div>
      <div class="glass-card rounded-xl p-5">
        <h3 class="text-sm font-bold text-slate-300 mb-4">Trending Topics</h3>
        <div class="space-y-3">${trendCards || '<p class="text-slate-500 text-sm">No trending data.</p>'}</div>
      </div>
    </div>
  `;
}

// ============================================================
// BOOT
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  switchTab("home");

  // Search enter key
  document.getElementById("search-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") executeSearch();
  });

  // Chat enter key
  document.getElementById("chat-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });
});

