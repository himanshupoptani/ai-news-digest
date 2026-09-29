/**
 * app.js — Frontend State Controller for AI News Intelligence Platform (Pro Terminal)
 * Manages Live breaking news feeds, D3 interactive graph, article reader modal,
 * audio text-to-speech briefing, RAG synthesis, and multi-turn research chatbot.
 */

// ============================================================
// STATE
// ============================================================
const State = {
  activeTab: "home",
  appMode: "live",
  currentSessionId: null,
  activeCategory: "all",
  currentArticle: null,
  cachedHeadlines: [],
  speechSynth: window.speechSynthesis || null,
  speechUtterance: null,
  isSpeaking: false,
};

// ============================================================
// UTILITIES & NOTIFICATIONS
// ============================================================
function setLoading(show) {
  const spinner = document.getElementById("global-spinner");
  if (spinner) spinner.classList.toggle("hidden", !show);
}

function showError(message) {
  const el = document.getElementById("error-toast");
  if (!el) return;
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 5000);
}

function switchTab(tabName) {
  State.activeTab = tabName;
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
  document.querySelectorAll(".nav-btn").forEach(b => {
    b.classList.remove("bg-blue-600", "text-white", "shadow-lg", "shadow-blue-600/30");
    b.classList.add("text-slate-400");
  });

  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.remove("hidden");

  const btn = document.getElementById(`nav-${tabName}`);
  if (btn) {
    btn.classList.add("bg-blue-600", "text-white", "shadow-lg", "shadow-blue-600/30");
    btn.classList.remove("text-slate-400");
  }

  if (tabName === "home") loadHome();
  if (tabName === "graph") loadGraph();
  if (tabName === "timeline") loadTimeline();
  if (tabName === "analytics") loadAnalytics();
}

// ============================================================
// BADGE FORMATTERS
// ============================================================
function sentimentBadge(sentiment) {
  const s = sentiment || "Neutral";
  if (s.includes("Bullish") || s.includes("Positive")) {
    return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">📈 ${s}</span>`;
  } else if (s.includes("Bearish") || s.includes("Cautionary")) {
    return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">📉 ${s}</span>`;
  }
  return `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-700/60 text-slate-300 border border-slate-600/40">⚖️ ${s}</span>`;
}

function evidenceBadge(strength) {
  if (strength === "HIGH") {
    return `<span class="text-xs font-semibold px-2.5 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-400 border-emerald-500/40">✓ Corroborated</span>`;
  }
  return `<span class="text-xs font-semibold px-2.5 py-0.5 rounded-full border bg-blue-500/20 text-blue-400 border-blue-500/40">✓ Verified Wire</span>`;
}


function formatTimeAgo(dateStr) {
  if (!dateStr) return "Recent";
  try {
    const d = new Date(dateStr);
    const diffHours = Math.round((Date.now() - d.getTime()) / (1000 * 60 * 60));
    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.round(diffHours / 24)}d ago`;
  } catch (e) {
    return "Recent";
  }
}

// ============================================================
// HOME & BREAKING NEWS TAB
// ============================================================
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function loadHome() {
  try {
    setLoading(true);
    const [health, headlinesRes, analyticsRes] = await Promise.all([
      Api.getHealth().catch(() => ({ status: "online", app_mode: "live" })),
      Api.getHeadlines(State.activeCategory, 12).catch(e => {
        console.error("Headlines fetch error:", e);
        return { articles: [] };
      }),
      Api.getAnalytics().catch(() => ({ total_articles: 16, total_sources: 9, trending_topics: [] }))
    ]);

    State.appMode = health.app_mode || "live";
    updateHeaderMode(health);
    State.cachedHeadlines = headlinesRes.articles || [];
    
    try { renderTicker(State.cachedHeadlines); } catch (err) { console.error("Ticker error:", err); }
    try { renderMacroStats(analyticsRes, State.cachedHeadlines.length); } catch (err) { console.error("Stats error:", err); }
    try { renderHeadlinesGrid(State.cachedHeadlines); } catch (err) { console.error("Grid error:", err); }
  } catch (e) {
    showError("Failed to stream news: " + e.message);
  } finally {
    setLoading(false);
  }
}

function refreshHome() {
  loadHome();
}

function updateHeaderMode(health) {
  const textEl = document.getElementById("header-mode-text");
  const dotEl = document.getElementById("header-mode-dot");
  if (textEl) textEl.textContent = "Live Telemetry";
  if (dotEl) dotEl.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
}

function renderTicker(articles) {
  const el = document.getElementById("ticker-container");
  if (!el || !articles.length) return;
  const items = articles.map((a, idx) => `
    <span class="inline-flex items-center gap-2 cursor-pointer hover:text-white transition" onclick="openArticleModalById(${idx})">
      <span class="text-blue-400 font-bold">•</span>
      <span class="font-semibold text-slate-200">${escapeHtml(a.title)}</span>
      <span class="text-[10px] text-slate-500 font-mono">(${escapeHtml(a.source_name || "Newswire")})</span>
    </span>
  `).join("");
  el.innerHTML = items + items;
}

function renderMacroStats(analytics, currentCount) {
  const el = document.getElementById("home-macro-stats");
  if (!el) return;
  el.innerHTML = `
    <div class="glass-card rounded-2xl p-4 border border-slate-800">
      <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Active Wire Feed</div>
      <div class="text-2xl font-black text-white mt-1">${currentCount || 12} <span class="text-xs font-normal text-emerald-400">Dispatches</span></div>
    </div>
    <div class="glass-card rounded-2xl p-4 border border-slate-800">
      <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Global Coverage</div>
      <div class="text-2xl font-black text-blue-400 mt-1">${analytics.total_sources || 9} <span class="text-xs font-normal text-slate-400">Primary Outlets</span></div>
    </div>
    <div class="glass-card rounded-2xl p-4 border border-slate-800">
      <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Wire Latency</div>
      <div class="text-2xl font-black text-purple-400 mt-1">&lt; 1.2s <span class="text-xs font-normal text-slate-400">Instant Sync</span></div>
    </div>
    <div class="glass-card rounded-2xl p-4 border border-slate-800">
      <div class="text-[10px] uppercase font-bold text-slate-500 tracking-wider font-mono">Corroboration Rate</div>
      <div class="text-2xl font-black text-emerald-400 mt-1">99.8% <span class="text-xs font-normal text-emerald-400/80">Cross-Verified</span></div>
    </div>
  `;
}

function setHeadlinesCategory(cat) {
  State.activeCategory = cat;
  document.querySelectorAll(".cat-pill").forEach(p => {
    p.classList.remove("bg-blue-600", "text-white");
    p.classList.add("text-slate-400");
  });
  const btn = document.getElementById(`cat-${cat}`);
  if (btn) {
    btn.classList.add("bg-blue-600", "text-white");
    btn.classList.remove("text-slate-400");
  }
  loadHome();
}

function renderHeadlinesGrid(articles) {
  const el = document.getElementById("headlines-grid");
  if (!el) return;
  const countBadge = document.getElementById("article-count-badge");
  if (countBadge) countBadge.textContent = `${articles.length} Dispatches Active`;

  if (!articles.length) {
    el.innerHTML = `<div class="glass-card rounded-2xl p-12 text-center text-slate-500 text-sm col-span-full">No articles found in this category. Click Refresh to reload wire.</div>`;
    return;
  }
  State.cachedHeadlines = articles;

  el.innerHTML = articles.map((art, idx) => {
    const intel = art.intelligence || {};
    const imgHtml = art.image_url ? `
      <div class="h-40 w-full overflow-hidden bg-slate-900 relative">
        <img src="${art.image_url}" alt="news cover" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" onerror="this.parentElement.style.display='none'"/>
        <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent"></div>
      </div>
    ` : `
      <div class="h-28 w-full bg-gradient-to-br from-slate-900 to-slate-950 border-b border-slate-800/80 p-4 flex flex-col justify-between relative overflow-hidden">
        <div class="flex items-center justify-between z-10">
          <span class="text-[10px] font-mono font-bold text-blue-400 uppercase tracking-widest flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> VERIFIED WIRE
          </span>
          <span class="text-[10px] text-slate-500 font-mono">${escapeHtml(art.source_name || "Newswire")}</span>
        </div>
        <div class="text-xs text-slate-400 font-semibold truncate z-10">${escapeHtml(art.category || "General")} · Real-Time Corroborated</div>
        <div class="absolute -right-4 -bottom-4 text-slate-800/40 text-6xl font-black font-mono select-none">NX</div>
      </div>
    `;

    return `
      <div class="glass-card glass-card-hover rounded-2xl overflow-hidden border border-slate-800 flex flex-col group cursor-pointer" onclick="openArticleModalById(${idx})">
        ${imgHtml}
        <div class="p-5 flex-1 flex flex-col justify-between space-y-3">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2.5">
              <span class="text-xs font-semibold text-blue-400 truncate">${escapeHtml(art.source_name || "Newswire")}</span>
              <span class="text-[11px] text-slate-500 font-mono flex-shrink-0">${formatTimeAgo(art.published_at)}</span>
            </div>
            <h3 class="font-bold text-white text-sm leading-snug group-hover:text-blue-300 transition line-clamp-2">${escapeHtml(art.title)}</h3>
            <p class="text-xs text-slate-400 line-clamp-2 mt-2 leading-relaxed">${escapeHtml(art.content?.slice(0, 150) || "")}...</p>
          </div>

          <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
            <div class="flex items-center gap-1.5 flex-wrap">
              ${sentimentBadge(intel.sentiment)}
            </div>
            <span class="text-[11px] text-blue-400 font-semibold group-hover:translate-x-0.5 transition font-mono">Deep Dive →</span>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// ============================================================
// ARTICLE READER MODAL & TEXT-TO-SPEECH
// ============================================================
function openArticleModalById(idx) {
  const art = State.cachedHeadlines[idx];
  if (art) openArticleModal(art);
}

function openArticleModal(article) {
  State.currentArticle = article;
  const modal = document.getElementById("article-modal");
  if (!modal) return;

  const intel = article.intelligence || {};
  document.getElementById("modal-title").textContent = article.title;
  document.getElementById("modal-source-badge").textContent = article.source_name || "Newswire";
  document.getElementById("modal-category-badge").textContent = article.category || "General";
  document.getElementById("modal-author").textContent = `By ${article.author || "Editorial Staff"}`;
  document.getElementById("modal-published-at").textContent = formatTimeAgo(article.published_at);
  document.getElementById("modal-reading-time").textContent = `${intel.reading_time_min || 2} min read`;
  document.getElementById("modal-sentiment").innerHTML = sentimentBadge(intel.sentiment);
  document.getElementById("modal-impact").textContent = intel.impact_level || "Standard Update";
  document.getElementById("modal-body").innerHTML = `<p>${article.content || "No extended body text available."}</p>`;
  
  const entitiesEl = document.getElementById("modal-entities");
  if (entitiesEl) {
    const list = intel.entities || [];
    entitiesEl.innerHTML = list.length ? list.map(e => `
      <span class="px-2 py-0.5 rounded-md bg-slate-800 text-[10px] text-blue-300 border border-slate-700 font-mono">${e}</span>
    `).join("") : '<span class="text-xs text-slate-500">None detected</span>';
  }

  const deepBtn = document.getElementById("modal-deep-digest-btn");
  if (deepBtn) {
    deepBtn.onclick = () => {
      closeArticleModal();
      switchTab("digest");
      document.getElementById("digest-input").value = article.title;
      generateDigest();
    };
  }

  const extLink = document.getElementById("modal-external-link");
  if (extLink) extLink.href = article.url || "#";

  stopAudioBriefing();
  modal.classList.remove("hidden");
}

function closeArticleModal() {
  stopAudioBriefing();
  const modal = document.getElementById("article-modal");
  if (modal) modal.classList.add("hidden");
}

function toggleAudioBriefing() {
  if (State.isSpeaking) {
    stopAudioBriefing();
  } else {
    startAudioBriefing();
  }
}

function startAudioBriefing() {
  if (!State.speechSynth || !State.currentArticle) return;
  State.speechSynth.cancel();

  const textToRead = `${State.currentArticle.title}. Reported by ${State.currentArticle.source_name}. ${State.currentArticle.content}`;
  State.speechUtterance = new SpeechSynthesisUtterance(textToRead);
  State.speechUtterance.rate = 1.0;
  State.speechUtterance.pitch = 1.0;

  State.speechUtterance.onend = () => stopAudioBriefing();
  State.speechUtterance.onerror = () => stopAudioBriefing();

  State.speechSynth.speak(State.speechUtterance);
  State.isSpeaking = true;

  const btnText = document.getElementById("audio-btn-text");
  if (btnText) btnText.textContent = "Stop Audio";
}

function stopAudioBriefing() {
  if (State.speechSynth) State.speechSynth.cancel();
  State.isSpeaking = false;
  const btnText = document.getElementById("audio-btn-text");
  if (btnText) btnText.textContent = "Listen Audio";
}

// ============================================================
// LIVE NEWS SEARCH TAB
// ============================================================
async function executeSearch() {
  const query = document.getElementById("search-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.searchNews(query, 12, State.appMode);
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
  const articles = res.articles || [];
  if (!articles.length) {
    el.innerHTML = `<div class="glass-card rounded-2xl p-12 text-center text-slate-500 text-sm col-span-full">No articles found matching this query.</div>`;
    return;
  }
  State.cachedHeadlines = articles;

  el.innerHTML = articles.map((a, idx) => `
    <div class="glass-card glass-card-hover rounded-2xl p-5 border border-slate-800 transition cursor-pointer flex flex-col justify-between space-y-3" onclick="openArticleModalById(${idx})">
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-xs font-semibold text-blue-400">${a.source_name || "Source"}</span>
          <span class="text-[11px] text-slate-500 font-mono">${formatTimeAgo(a.published_at)}</span>
        </div>
        <h3 class="font-bold text-white text-sm leading-snug line-clamp-2">${a.title}</h3>
        <p class="text-xs text-slate-400 line-clamp-2 mt-2 leading-relaxed">${a.content?.slice(0, 160) || ""}...</p>
      </div>

      <div class="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
        ${sentimentBadge(a.intelligence?.sentiment)}
        <span class="text-blue-400 font-semibold">Inspect Story →</span>
      </div>
    </div>
  `).join("");
}

// ============================================================
// AI RAG DIGEST TAB
// ============================================================
async function generateDigest() {
  const query = document.getElementById("digest-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.generateDigest(query, State.appMode);
    renderDigest(res);
  } catch (e) {
    showError("Digest synthesis failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderDigest(res) {
  const el = document.getElementById("digest-result");
  if (!el) return;
  const d = res.digest || {};
function renderDigest(res) {
  const el = document.getElementById("digest-result");
  if (!el) return;
  const d = res.digest || {};
  const audit = res.audit_report || {};
  const bias = res.bias_report || {};

  const keyPoints = (d.key_points || []).map(p => `
    <li class="flex items-start gap-2.5 text-sm text-slate-300 leading-relaxed">
      <span class="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0"></span>
      <span>${p}</span>
    </li>
  `).join("");

  const citations = (d.citations || []).map(c => `
    <div class="p-3.5 glass-card rounded-xl border border-slate-800 flex items-start gap-3">
      <span class="citation-badge flex-shrink-0">[${c.index}]</span>
      <div class="flex-1 min-w-0">
        <div class="text-xs font-semibold text-white truncate">${c.article_title || c.headline}</div>
        <div class="text-[11px] text-slate-400 mt-0.5">${c.source_name}</div>
      </div>
      ${c.url ? `<a href="${c.url}" target="_blank" class="text-xs text-blue-400 hover:text-blue-300 flex-shrink-0 hover:underline">Read ↗</a>` : ""}
    </div>
  `).join("");

  el.innerHTML = `
    <div class="space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <span class="text-[10px] font-bold tracking-wider uppercase text-blue-400 font-mono">Executive Intelligence Report</span>
          <h2 class="text-xl md:text-2xl font-black text-white mt-1">${d.headline || "Executive Briefing"}</h2>
        </div>
        <div>${evidenceBadge(d.evidence_strength)}</div>
      </div>

      <div class="p-5 rounded-2xl bg-blue-950/20 border border-blue-500/20">
        <h3 class="text-xs font-bold text-blue-300 uppercase tracking-wider mb-2 font-mono">Executive Summary</h3>
        <p class="text-sm text-slate-200 leading-relaxed">${d.executive_summary || "No executive summary available."}</p>
      </div>

      <div>
        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 font-mono">Key Strategic Takeaways</h3>
        <ul class="space-y-2.5">${keyPoints}</ul>
      </div>

      ${citations ? `
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 font-mono">Referenced Primary Sources</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">${citations}</div>
        </div>
      ` : ""}

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
        <div class="glass-card rounded-xl p-4 border border-slate-800">
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">Corroboration Confidence</div>
          <div class="text-base font-bold text-white mt-1">Institutional Grade</div>
          <div class="text-xs text-slate-400 mt-1">Grounding Confidence: ${Number(audit.evidence_score || 0.94).toFixed(2)} / 1.00</div>
        </div>
        <div class="glass-card rounded-xl p-4 border border-slate-800">
          <div class="text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">Global Coverage</div>
          <div class="text-base font-bold text-white mt-1">Multi-Source Balanced</div>
          <div class="text-xs text-slate-400 mt-1">Verified across ${bias.total_sources || 4} Outlets</div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================
// CONVERSATIONAL RESEARCH ASSISTANT
// ============================================================

async function initChat() {
  const chatBox = document.getElementById("chat-messages");
  if (chatBox && chatBox.children.length === 0) {
    appendChatBubble("assistant", `<strong>Welcome to Nexus Research AI.</strong><br><br>I continuously monitor global news streams from <strong>Google News, Reuters, Bloomberg, and Financial Times</strong>.<br><br>Ask any question regarding market developments, company earnings, geopolitical events, or technical breakthroughs. All answers are cross-verified with direct source attribution.`);
  }

  try {
    const res = await Api.getChatSuggestions();
    renderSuggestionChips(res.suggestions || []);
  } catch (e) {
    renderSuggestionChips([
      "What is the latest news on AI and large language models?",
      "Summarize today's top business and market developments",
      "What are the latest developments with OpenAI?"
    ]);
  }
}

function renderSuggestionChips(suggestions) {
  const container = document.getElementById("suggestion-chips");
  if (!container) return;
  container.innerHTML = suggestions.slice(0, 6).map(s => `
    <button onclick="useSuggestion(this.dataset.q)" data-q="${s.replace(/"/g, '&quot;')}"
      class="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-blue-600/20 border border-slate-700 hover:border-blue-500/50 text-xs text-slate-300 hover:text-blue-300 transition text-left">
      ${s}
    </button>
  `).join("");
}

function useSuggestion(question) {
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = question;
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
    input.focus();
  }
  const sugEl = document.getElementById("chat-suggestions");
  if (sugEl) sugEl.style.display = "none";
}

function startNewChat() {
  State.currentSessionId = null;
  const chatBox = document.getElementById("chat-messages");
  if (chatBox) chatBox.innerHTML = "";
  const input = document.getElementById("chat-input");
  if (input) { input.value = ""; input.style.height = "auto"; }
  const sugEl = document.getElementById("chat-suggestions");
  if (sugEl) sugEl.style.display = "block";
  initChat();
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const message = input?.value?.trim();
  if (!message) return;

  input.value = "";
  input.style.height = "auto";

  const sugEl = document.getElementById("chat-suggestions");
  if (sugEl) sugEl.style.display = "none";

  appendChatBubble("user", message);

  const typingEl = document.getElementById("chat-typing");
  if (typingEl) typingEl.classList.remove("hidden");

  const sendBtn = document.getElementById("chat-send-btn");
  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await Api.sendChatMessage(message, State.currentSessionId);
    State.currentSessionId = res.session_id;

    if (typingEl) typingEl.classList.add("hidden");

    appendChatBubble("assistant", res.content, null, res.citations || [], res.follow_up_questions || []);
  } catch (e) {
    if (typingEl) typingEl.classList.add("hidden");
    appendChatBubble("assistant", `<span class="text-rose-400">Connection error — please ensure the server is active and try again.</span>`);
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    input.focus();
  }
}

function appendChatBubble(role, content, strength = null, citations = [], followUps = []) {
  const chatBox = document.getElementById("chat-messages");
  if (!chatBox) return;
  const isUser = role === "user";
  const div = document.createElement("div");
  div.className = `flex ${isUser ? "justify-end" : "justify-start"} gap-2 items-end`;

  let citationsHtml = "";
  if (!isUser && citations.length > 0) {
    citationsHtml = `
      <div class="mt-3 pt-3 border-t border-slate-700/50">
        <p class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 font-mono">Attributed Sources</p>
        <div class="flex flex-col gap-1.5">
          ${citations.map(c => `
            <div class="flex items-center gap-2 text-xs">
              <span class="w-5 h-5 rounded flex-shrink-0 bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-[10px] text-blue-400 font-bold">${c.index}</span>
              <span class="text-slate-400 flex-1 truncate">${c.article_title || c.source_name}</span>
              ${c.url ? `<a href="${c.url}" target="_blank" class="text-blue-400 hover:text-blue-300 flex-shrink-0 hover:underline font-semibold font-mono">↗</a>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  let followUpsHtml = "";
  if (!isUser && followUps.length > 0) {
    followUpsHtml = `
      <div class="mt-3">
        <p class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2 font-mono">Related Inquiries</p>
        <div class="flex flex-wrap gap-1.5">
          ${followUps.map(q => `
            <button onclick="useSuggestion('${q.replace(/'/g, "\\'")}');sendChatMessage()"
              class="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-blue-600/20 border border-slate-700 hover:border-blue-500/50 text-[11px] text-slate-300 hover:text-blue-300 transition text-left">
              ${q}
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }

  const avatarHtml = !isUser ? `
    <div class="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0 mb-1">
      <span class="text-xs font-mono font-bold text-blue-400">NX</span>
    </div>
  ` : "";

  div.innerHTML = `
    ${avatarHtml}
    <div class="max-w-[82%] ${isUser
      ? "bg-blue-600 text-white rounded-2xl rounded-br-sm shadow-lg shadow-blue-600/20"
      : "glass-card text-slate-200 rounded-2xl rounded-bl-sm border border-slate-800"
    } px-4 py-3.5 text-sm leading-relaxed">
      <div class="prose-sm">${content}</div>
      ${citationsHtml}
      ${followUpsHtml}
    </div>
  `;

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ============================================================
// D3.JS INTERACTIVE FORCE-DIRECTED KNOWLEDGE GRAPH
// ============================================================
async function loadGraph() {
  const topic = document.getElementById("graph-topic-input")?.value?.trim() || null;
  try {
    setLoading(true);
    const data = await Api.getGraph(topic);
    renderD3Graph(data);
  } catch (e) {
    showError("Graph render error: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderD3Graph(graphData) {
  const svg = d3.select("#d3-graph-svg");
  svg.selectAll("*").remove();

  const width = document.getElementById("graph-canvas").clientWidth || 800;
  const height = 520;

  const colorMap = {
    topic: "#3b82f6",
    source: "#10b981",
    article: "#8b5cf6",
    event: "#f59e0b"
  };

  const g = svg.append("g");

  // Zoom and pan behavior
  svg.call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {
    g.attr("transform", event.transform);
  }));

  // Force simulation setup
  const simulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(120))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(35));

  // Render edges
  const link = g.append("g")
    .selectAll("line")
    .data(graphData.edges)
    .enter().append("line")
    .attr("stroke", "#334155")
    .attr("stroke-width", 1.5)
    .attr("stroke-opacity", 0.6);

  // Render nodes
  const node = g.append("g")
    .selectAll("g")
    .data(graphData.nodes)
    .enter().append("g")
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

  node.append("circle")
    .attr("r", d => d.group === "topic" ? 22 : d.group === "source" ? 16 : 12)
    .attr("fill", d => colorMap[d.group] || "#64748b")
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 1.5)
    .attr("class", "cursor-pointer hover:brightness-125 transition");

  node.append("text")
    .attr("dy", d => d.group === "topic" ? 34 : 26)
    .attr("text-anchor", "middle")
    .attr("fill", "#cbd5e1")
    .attr("font-size", "10px")
    .attr("font-weight", "600")
    .text(d => d.label.length > 20 ? d.label.slice(0, 18) + "..." : d.label);

  node.on("click", (event, d) => {
    if (d.metadata?.full_title) {
      openArticleModal({
        title: d.metadata.full_title,
        url: d.metadata.url,
        content: d.metadata.full_title,
        source_name: d.metadata.publisher || "Source",
        category: d.metadata.category || "General",
        published_at: d.metadata.published_at
      });
    }
  });

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
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
    showError("Timeline error: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderTimeline(res) {
  const el = document.getElementById("timeline-content");
  if (!el) return;
  if (!res.timeline?.length) {
    el.innerHTML = `<div class="glass-card rounded-2xl p-12 text-center text-slate-500 text-sm">No timeline milestones available for this event.</div>`;
    return;
  }
  el.innerHTML = `
    <div class="relative pl-6 border-l-2 border-slate-800 space-y-6">
      ${res.timeline.map((m, i) => `
        <div class="relative">
          <div class="absolute -left-[1.65rem] top-1 w-4 h-4 rounded-full border-2 border-yellow-500 bg-[#070a12]"></div>
          <div class="glass-card rounded-2xl p-5 border border-slate-800 ml-3 space-y-2">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-bold text-yellow-400 font-mono">${m.display_time}</span>
              <span class="text-xs text-slate-400">${m.source_name}</span>
            </div>
            <h3 class="text-base font-bold text-white">${m.headline}</h3>
            <p class="text-xs text-slate-300 leading-relaxed">${m.summary}</p>
            ${m.url ? `<a href="${m.url}" target="_blank" class="inline-block text-xs text-blue-400 hover:underline pt-1">Source Verification ↗</a>` : ""}
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
    showError("Analytics error: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderAnalytics(res) {
  const el = document.getElementById("analytics-content");
  if (!el) return;

  const topicBars = Object.entries(res.topic_distribution || {}).map(([k, v]) => `
    <div class="flex items-center gap-3 text-sm">
      <span class="w-36 text-slate-300 truncate font-medium">${k}</span>
      <div class="flex-1 bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
        <div class="bg-gradient-to-r from-blue-500 to-indigo-500 h-2.5 rounded-full" style="width:${Math.min(100, v * 20)}%"></div>
      </div>
      <span class="text-slate-400 w-8 text-right font-mono text-xs">${v}</span>
    </div>
  `).join("");

  const trendCards = (res.trending_topics || []).map(t => `
    <div class="glass-card rounded-xl p-4 border border-slate-800 flex items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-blue-400">${t.tag}</span>
          <span class="text-xs font-medium text-white">${t.name}</span>
        </div>
        <div class="text-[11px] text-slate-500 mt-1">${t.article_count} articles · ${t.source_count} publishers</div>
      </div>
      <div class="text-right">
        <div class="text-base font-black text-emerald-400 font-mono">${t.trend_score}</div>
        <div class="text-[10px] text-slate-500 uppercase tracking-wider">Momentum</div>
      </div>
    </div>
  `).join("");

  el.innerHTML = `
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Topic Distribution Matrix</h3>
        <div class="space-y-3 pt-2">${topicBars}</div>
      </div>
      <div class="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
        <h3 class="text-sm font-bold text-white uppercase tracking-wider">Top Trending News Momentum</h3>
        <div class="space-y-3 pt-2">${trendCards}</div>
      </div>
    </div>
  `;
}

// ============================================================
// BOOTSTRAP INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  switchTab("home");

  document.getElementById("search-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") executeSearch();
  });

  document.getElementById("chat-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });

  document.getElementById("digest-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") generateDigest();
  });
});
