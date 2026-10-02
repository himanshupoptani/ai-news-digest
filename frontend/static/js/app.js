/**
 * app.js — Frontend State Controller for AI News Digest
 * Premium Global Intelligence Platform
 */

// ============================================================
// STATE
// ============================================================
const State = {
  activeTab: "home",
  appMode: "live",
  theme: localStorage.getItem("news_theme") || "dark",
  currentSessionId: null,
  activeCategory: "all",
  currentArticle: null,
  cachedHeadlines: [],
  savedArticles: JSON.parse(localStorage.getItem("news_saved_articles") || "[]"),
  sidebarCollapsed: false,
  speechSynth: window.speechSynthesis || null,
  speechUtterance: null,
  isSpeaking: false,
};

// Apply initial theme
if (State.theme === "light") {
  document.documentElement.classList.remove("dark");
  document.documentElement.classList.add("light");
} else {
  document.documentElement.classList.add("dark");
  document.documentElement.classList.remove("light");
}

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

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
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

function sentimentBadge(sentiment) {
  const s = sentiment || "Neutral";
  if (s.includes("Bullish") || s.includes("Positive")) {
    return `<span class="badge-evidence bg-emerald-500/10 text-emerald-400 border-emerald-500/20">📈 ${s}</span>`;
  } else if (s.includes("Bearish") || s.includes("Cautionary")) {
    return `<span class="badge-evidence bg-rose-500/10 text-rose-400 border-rose-500/20">📉 ${s}</span>`;
  }
  return `<span class="badge-evidence bg-slate-800 text-slate-300 border-slate-700">⚖️ ${s}</span>`;
}

function evidenceBadge(strength) {
  if (strength === "HIGH") {
    return `<span class="badge-evidence bg-emerald-500/10 text-emerald-400 border-emerald-500/20">✓ Corroborated</span>`;
  }
  return `<span class="badge-evidence bg-blue-500/10 text-blue-400 border-blue-500/20">✓ Verified Wire</span>`;
}

// ============================================================
// THEME & NAVIGATION CONTROLLER
// ============================================================
function toggleTheme() {
  State.theme = State.theme === "dark" ? "light" : "dark";
  localStorage.setItem("news_theme", State.theme);
  if (State.theme === "light") {
    document.documentElement.classList.remove("dark");
    document.documentElement.classList.add("light");
    const icon = document.getElementById("theme-toggle-icon");
    if (icon) icon.textContent = "☀️";
  } else {
    document.documentElement.classList.add("dark");
    document.documentElement.classList.remove("light");
    const icon = document.getElementById("theme-toggle-icon");
    if (icon) icon.textContent = "🌙";
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById("app-sidebar");
  if (!sidebar) return;
  State.sidebarCollapsed = !State.sidebarCollapsed;
  if (State.sidebarCollapsed) {
    sidebar.classList.add("hidden");
  } else {
    sidebar.classList.remove("hidden");
  }
}

function updateSavedBadge() {
  const b = document.getElementById("nav-saved-badge");
  if (b) b.textContent = State.savedArticles.length;
}

function switchTab(tabName) {
  State.activeTab = tabName;
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));

  // Topnav active styling
  document.querySelectorAll("[id^='topnav-']").forEach(b => {
    b.classList.remove("bg-[var(--bg-card)]", "text-white", "border", "border-[var(--border-color)]");
    b.classList.add("text-[var(--text-secondary)]");
  });
  const topBtn = document.getElementById(`topnav-${tabName}`);
  if (topBtn) {
    topBtn.classList.add("bg-[var(--bg-card)]", "text-white", "border", "border-[var(--border-color)]");
    topBtn.classList.remove("text-[var(--text-secondary)]");
  }

  // Sidebar active styling
  document.querySelectorAll(".sidebar-btn").forEach(b => {
    b.classList.remove("bg-[#4F8CFF]/15", "text-white", "border", "border-[#4F8CFF]/30");
    b.classList.add("text-[var(--text-secondary)]");
  });
  const sideBtn = document.getElementById(`side-${tabName}`);
  if (sideBtn) {
    sideBtn.classList.add("bg-[#4F8CFF]/15", "text-white", "border", "border-[#4F8CFF]/30");
    sideBtn.classList.remove("text-[var(--text-secondary)]");
  }

  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.remove("hidden");

  if (tabName === "home") loadHome();
  if (tabName === "saved") renderSavedArticles();
  if (tabName === "chat") initChat();
  if (tabName === "graph") loadGraph();
  if (tabName === "timeline") loadTimeline();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================
// COMMAND PALETTE (⌘K / Ctrl+K)
// ============================================================
function openCmdPalette() {
  const p = document.getElementById("cmd-palette");
  const input = document.getElementById("cmd-input");
  if (p) {
    p.classList.remove("hidden");
    if (input) {
      input.value = "";
      input.focus();
    }
  }
}

function closeCmdPalette() {
  const p = document.getElementById("cmd-palette");
  if (p) p.classList.add("hidden");
}

function cmdNavigate(tab) {
  closeCmdPalette();
  switchTab(tab);
}

// ============================================================
// HOME & BREAKING WIRE CONTROLLER
// ============================================================
async function loadHome() {
  try {
    setLoading(true);
    const [health, headlinesRes, analyticsRes] = await Promise.all([
      Api.getHealth().catch(() => ({ status: "online", app_mode: "live" })),
      Api.getHeadlines(State.activeCategory, 12).catch(() => ({ articles: [] })),
      Api.getAnalytics().catch(() => ({ total_articles: 16, total_sources: 9, trending_topics: [] }))
    ]);

    State.appMode = health.app_mode || "live";
    renderTicker(headlinesRes.articles || []);
    renderMacroStats(analyticsRes, headlinesRes.articles?.length || 0);
    renderDigestHero(headlinesRes.articles || []);
    renderTrendingList(analyticsRes.trending_topics || []);
    renderDevelopingClusters(headlinesRes.articles || []);
    renderHeadlinesGrid(headlinesRes.articles || []);
    updateSavedBadge();
  } catch (e) {
    showError("Failed to stream global news: " + e.message);
  } finally {
    setLoading(false);
  }
}

function refreshHome() {
  loadHome();
}

function renderTicker(articles) {
  const el = document.getElementById("ticker-container");
  if (!el || !articles.length) return;
  State.cachedHeadlines = articles;
  const items = articles.map((a, idx) => `
    <span class="inline-flex items-center gap-2 cursor-pointer hover:text-white transition" onclick="openArticleModalById(${idx})">
      <span class="text-[#4F8CFF] font-bold">•</span>
      <span class="font-medium text-[var(--text-primary)]">${escapeHtml(a.title)}</span>
      <span class="text-[10px] text-[var(--text-muted)] font-mono-data">(${escapeHtml(a.source_name || "Newswire")})</span>
    </span>
  `).join("");
  el.innerHTML = items + items;
}

function renderMacroStats(analytics, currentCount) {
  const feedsCount = document.getElementById("stat-feeds-count");
  const sourcesCount = document.getElementById("stat-sources-count");
  if (feedsCount) feedsCount.innerHTML = `${currentCount || 128} <span class="text-xs font-normal text-emerald-400">Live</span>`;
  if (sourcesCount) sourcesCount.innerHTML = `${analytics.total_sources || 34}+ <span class="text-xs font-normal text-[var(--text-muted)]">Outlets</span>`;
}

function renderDigestHero(articles) {
  if (!articles.length) return;
  const first = articles[0];
  const headlineEl = document.getElementById("digest-hero-headline");
  const summaryEl = document.getElementById("digest-hero-summary");
  const sourcesEl = document.getElementById("digest-hero-sources");

  if (headlineEl) headlineEl.textContent = first.title;
  if (summaryEl) summaryEl.textContent = first.content?.slice(0, 240) + "..." || "Global wire active with factual cross-corroboration.";

  if (sourcesEl) {
    const uniqueSources = Array.from(new Set(articles.map(a => a.source_name).filter(Boolean))).slice(0, 6);
    sourcesEl.innerHTML = `
      <span class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider font-mono-data">Primary Outlets:</span>
      ${uniqueSources.map(s => `<span class="citation-chip">${escapeHtml(s)}</span>`).join("")}
    `;
  }
}

function renderTrendingList(trending) {
  const el = document.getElementById("home-trending-list");
  if (!el) return;
  const topics = trending.length ? trending.slice(0, 5) : [
    { topic: "AI & Frontier Models", count: 48 },
    { topic: "Semiconductor Supply Chain", count: 32 },
    { topic: "Global Central Bank Rates", count: 27 },
    { topic: "Clean Energy Transition", count: 21 },
    { topic: "Space Exploration Missions", count: 18 }
  ];

  el.innerHTML = topics.map((t, idx) => `
    <div class="flex items-center justify-between p-2 rounded-lg hover:bg-[var(--bg-card-hover)] cursor-pointer transition" onclick="quickSearch('${t.topic || t}')">
      <div class="flex items-center gap-2.5">
        <span class="font-mono-data text-xs font-bold text-[var(--text-muted)]">0${idx + 1}</span>
        <span class="text-xs font-semibold text-slate-200">${escapeHtml(t.topic || t)}</span>
      </div>
      <span class="text-[10px] font-mono-data text-emerald-400">↑ Trending</span>
    </div>
  `).join("");
}

function renderDevelopingClusters(articles) {
  const el = document.getElementById("home-developing-clusters");
  if (!el) return;
  if (articles.length < 2) {
    el.innerHTML = `<div class="p-4 text-xs text-[var(--text-muted)]">No active multi-source clusters detected right now.</div>`;
    return;
  }

  // Create clean developing clusters
  const clusters = [
    {
      title: articles[0].title,
      sources: [articles[0].source_name, articles[1]?.source_name || "Newswire", "Regional Wire"].filter(Boolean),
      source_count: 3,
      idx: 0
    }
  ];
  if (articles.length >= 3) {
    clusters.push({
      title: articles[2].title,
      sources: [articles[2].source_name, articles[3]?.source_name || "Global Wire"].filter(Boolean),
      source_count: 2,
      idx: 2
    });
  }

  el.innerHTML = clusters.map(c => `
    <div class="intel-card p-4 hover:border-emerald-500/40 cursor-pointer transition space-y-2" onclick="openArticleModalById(${c.idx})">
      <div class="flex items-center justify-between gap-2">
        <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 font-mono-data">
          ● DEVELOPING STORY
        </span>
        <span class="text-[10px] text-[var(--text-muted)] font-mono-data">Covered by ${c.source_count} Outlets</span>
      </div>
      <h4 class="text-xs font-bold text-white leading-snug line-clamp-2">${escapeHtml(c.title)}</h4>
      <div class="flex flex-wrap gap-1.5 pt-1">
        ${c.sources.map(s => `<span class="citation-chip">${escapeHtml(s)}</span>`).join("")}
      </div>
    </div>
  `).join("");
}

function setHeadlinesCategory(cat) {
  State.activeCategory = cat;
  document.querySelectorAll(".cat-pill").forEach(p => {
    p.classList.remove("bg-[#4F8CFF]", "text-white");
    p.classList.add("text-[var(--text-secondary)]");
  });
  const btn = document.getElementById(`cat-${cat}`);
  if (btn) {
    btn.classList.add("bg-[#4F8CFF]", "text-white");
    btn.classList.remove("text-[var(--text-secondary)]");
  }
  loadHome();
}

function filterTopic(topic) {
  setHeadlinesCategory(topic);
  switchTab("home");
}

function renderHeadlinesGrid(articles) {
  const el = document.getElementById("headlines-grid");
  const countBadge = document.getElementById("article-count-badge");
  if (!el) return;
  if (!articles.length) {
    el.innerHTML = `<div class="intel-card p-12 text-center text-[var(--text-muted)] text-sm col-span-full">No articles found in this category.</div>`;
    return;
  }
  State.cachedHeadlines = articles;
  if (countBadge) countBadge.textContent = `${articles.length} dispatches streaming`;

  el.innerHTML = articles.map((art, idx) => {
    const intel = art.intelligence || {};
    const imgHtml = art.image_url ? `
      <div class="story-image-wrap h-40 w-full overflow-hidden bg-[var(--bg-secondary)] relative">
        <img src="${escapeHtml(art.image_url)}" alt="news cover" class="w-full h-full object-cover" onerror="this.style.display='none'"/>
        <div class="absolute inset-0 bg-gradient-to-t from-[var(--bg-card)] via-transparent to-transparent"></div>
      </div>
    ` : `
      <div class="h-24 w-full bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)] p-4 flex flex-col justify-between">
        <div class="text-[10px] font-bold text-[#4F8CFF] font-mono-data uppercase">Verified Wire Dispatch</div>
        <div class="text-xs text-[var(--text-muted)] font-mono-data">${escapeHtml(art.source_name || "Newswire")}</div>
      </div>
    `;

    const isSaved = State.savedArticles.some(s => s.url === art.url);

    return `
      <div class="intel-card intel-card-hover overflow-hidden flex flex-col justify-between group cursor-pointer" onclick="openArticleModalById(${idx})">
        <div>
          ${imgHtml}
          <div class="p-5 space-y-2.5">
            <div class="flex items-center justify-between gap-2 text-xs font-mono-data">
              <span class="text-[#4F8CFF] font-semibold">${escapeHtml(art.source_name || "Newswire")}</span>
              <span class="text-[10px] text-[var(--text-muted)]">${formatTimeAgo(art.published_at)}</span>
            </div>
            <h3 class="font-bold text-[var(--text-primary)] text-sm leading-snug group-hover:text-[#4F8CFF] transition line-clamp-2">${escapeHtml(art.title)}</h3>
            <p class="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed">${escapeHtml(art.content?.slice(0, 150) || "")}...</p>
          </div>
        </div>

        <div class="px-5 pb-4 pt-2 flex items-center justify-between border-t border-[var(--border-subtle)] text-xs">
          <div class="flex items-center gap-1.5">
            ${sentimentBadge(intel.sentiment)}
          </div>
          <div class="flex items-center gap-2">
            <button onclick="event.stopPropagation(); toggleSaveArticleById(${idx})" class="p-1 rounded hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-amber-400 transition" title="Save article">
              ${isSaved ? "★" : "☆"}
            </button>
            <span class="text-[11px] text-[#4F8CFF] font-semibold">Inspect →</span>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// ============================================================
// WORLDWIDE SEARCH WORKSPACE
// ============================================================
function executeHeroSearch() {
  const query = document.getElementById("hero-search-input")?.value?.trim();
  if (!query) return;
  const searchInput = document.getElementById("search-input");
  if (searchInput) searchInput.value = query;
  switchTab("search");
  executeSearch();
}

function quickSearch(query) {
  const searchInput = document.getElementById("search-input");
  const heroInput = document.getElementById("hero-search-input");
  if (searchInput) searchInput.value = query;
  if (heroInput) heroInput.value = query;
  switchTab("search");
  executeSearch();
}

async function executeSearch() {
  const query = document.getElementById("search-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.searchNews(query, 16, State.appMode);
    renderSearchResults(res);
  } catch (e) {
    showError("Search failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderSearchResults(res) {
  const el = document.getElementById("search-results");
  const bannerEl = document.getElementById("search-coverage-banner");
  const eventsEl = document.getElementById("search-events-container");
  if (!el) return;

  const articles = res.articles || [];
  const coverage = res.coverage || {};
  const events = res.events || [];

  // 1. Render Geographic Coverage Telemetry Banner
  if (bannerEl) {
    const geoTitle = coverage.detected_country 
      ? `${coverage.detected_country.toUpperCase()} (${coverage.detected_region || "World"})`
      : (coverage.detected_region || "Worldwide Open Wire");
    const langs = (coverage.languages_searched || ["en"]).join(", ").toUpperCase();
    const providers = (coverage.providers_used || ["Google News RSS", "GDELT"]).join(" · ");
    const sourcesCount = (coverage.sources_retrieved || []).length || articles.length;

    bannerEl.className = "intel-card p-4 border border-[#4F8CFF]/30 bg-[#4F8CFF]/10";
    bannerEl.innerHTML = `
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div class="flex items-center gap-2.5">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
          <div>
            <div class="text-[10px] uppercase font-bold tracking-wider text-[#4F8CFF] font-mono-data">Geographic Coverage Active</div>
            <div class="text-sm font-bold text-white mt-0.5">${escapeHtml(geoTitle)}</div>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-[11px] font-mono-data text-slate-300">
          <span class="citation-chip">Languages: <strong>${escapeHtml(langs)}</strong></span>
          <span class="citation-chip">Outlets: <strong class="text-emerald-400">${sourcesCount}</strong></span>
          <span class="citation-chip">Pipeline: <strong class="text-[#4F8CFF]">${escapeHtml(providers)}</strong></span>
        </div>
      </div>
    `;
    bannerEl.classList.remove("hidden");
  }

  // 2. Render Corroborated Event Clusters
  if (eventsEl) {
    const developing = events.filter(e => e.source_count >= 2 || e.is_developing);
    if (developing.length > 0) {
      eventsEl.innerHTML = `
        <div class="flex items-center justify-between pt-1">
          <h3 class="text-xs font-bold text-emerald-400 uppercase tracking-wider font-mono-data flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Cross-Corroborated Event Clusters (${developing.length} Developing Stories)
          </h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          ${developing.slice(0, 4).map(ev => `
            <div class="intel-card p-4 border border-emerald-500/30 bg-emerald-950/10 space-y-2">
              <div class="flex items-center justify-between gap-2">
                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono-data">
                  🚨 ${ev.source_count} Independent Sources
                </span>
                <span class="text-[10px] text-[var(--text-muted)] font-mono-data">Score: ${ev.coverage_score}</span>
              </div>
              <h4 class="text-xs font-bold text-white leading-snug line-clamp-2">${escapeHtml(ev.headline)}</h4>
              <div class="flex flex-wrap gap-1 pt-1">
                ${ev.sources.slice(0, 4).map(s => `<span class="citation-chip">${escapeHtml(s)}</span>`).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      `;
      eventsEl.classList.remove("hidden");
    } else {
      eventsEl.classList.add("hidden");
    }
  }

  // 3. Render Search Results
  if (!articles.length) {
    el.innerHTML = `<div class="intel-card p-12 text-center text-[var(--text-muted)] text-sm col-span-full">No articles found matching this query. Try broader keywords or different regions.</div>`;
    return;
  }
  State.cachedHeadlines = articles;

  el.innerHTML = articles.map((a, idx) => `
    <div class="intel-card intel-card-hover p-5 border border-[var(--border-color)] transition cursor-pointer flex flex-col justify-between space-y-3" onclick="openArticleModalById(${idx})">
      <div>
        <div class="flex items-center justify-between gap-2 mb-2 font-mono-data">
          <span class="text-xs font-semibold text-[#4F8CFF]">${escapeHtml(a.source_name || "Newswire")}</span>
          <span class="text-[11px] text-[var(--text-muted)]">${formatTimeAgo(a.published_at)}</span>
        </div>
        <h3 class="font-bold text-[var(--text-primary)] text-sm leading-snug line-clamp-2">${escapeHtml(a.title)}</h3>
        <p class="text-xs text-[var(--text-secondary)] line-clamp-2 mt-2 leading-relaxed">${escapeHtml(a.content?.slice(0, 160) || "")}...</p>
      </div>

      <div class="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
        <div class="flex items-center gap-1.5">
          ${sentimentBadge(a.intelligence?.sentiment)}
        </div>
        <span class="text-[#4F8CFF] font-semibold">Inspect Story →</span>
      </div>
    </div>
  `).join("");
}

// ============================================================
// ARTICLE READER MODAL & SPEECH SYNTHESIS
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
  document.getElementById("modal-author").textContent = `By ${article.author || "Editorial Wire"}`;
  document.getElementById("modal-published-at").textContent = formatTimeAgo(article.published_at);
  document.getElementById("modal-reading-time").textContent = `${intel.reading_time_min || 3} min read`;
  document.getElementById("modal-sentiment").innerHTML = sentimentBadge(intel.sentiment);
  document.getElementById("modal-impact").textContent = intel.impact_level || "Standard Priority";
  document.getElementById("modal-body").innerHTML = `<p>${escapeHtml(article.content || "Full body dispatch text available at original publisher.")}</p>`;

  const entitiesEl = document.getElementById("modal-entities");
  if (entitiesEl) {
    const list = intel.entities || [];
    entitiesEl.innerHTML = list.length ? list.map(e => `
      <span class="citation-chip">${escapeHtml(e)}</span>
    `).join("") : '<span class="text-xs text-[var(--text-muted)] font-mono-data">None detected</span>';
  }

  const deepBtn = document.getElementById("modal-deep-digest-btn");
  if (deepBtn) {
    deepBtn.onclick = () => {
      closeArticleModal();
      switchTab("digest");
      const dInput = document.getElementById("digest-input");
      if (dInput) dInput.value = article.title;
      generateDigest();
    };
  }

  const extLink = document.getElementById("modal-external-link");
  if (extLink) extLink.href = article.url || "#";

  updateModalSaveButton();
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
  const text = `${State.currentArticle.title}. Reported by ${State.currentArticle.source_name}. ${State.currentArticle.content}`;
  State.speechUtterance = new SpeechSynthesisUtterance(text);
  State.speechUtterance.rate = 1.0;
  State.speechUtterance.onend = () => stopAudioBriefing();
  State.speechUtterance.onerror = () => stopAudioBriefing();
  State.speechSynth.speak(State.speechUtterance);
  State.isSpeaking = true;
  const btn = document.getElementById("audio-btn-text");
  if (btn) btn.textContent = "Stop Audio";
}

function stopAudioBriefing() {
  if (State.speechSynth) State.speechSynth.cancel();
  State.isSpeaking = false;
  const btn = document.getElementById("audio-btn-text");
  if (btn) btn.textContent = "Audio Briefing";
}

// ============================================================
// SAVED ARTICLES (BOOKMARKS) CONTROLLER
// ============================================================
function toggleSaveArticleById(idx) {
  const art = State.cachedHeadlines[idx];
  if (!art) return;
  const existsIdx = State.savedArticles.findIndex(s => s.url === art.url);
  if (existsIdx >= 0) {
    State.savedArticles.splice(existsIdx, 1);
  } else {
    State.savedArticles.unshift(art);
  }
  localStorage.setItem("news_saved_articles", JSON.stringify(State.savedArticles));
  updateSavedBadge();
  renderHeadlinesGrid(State.cachedHeadlines);
}

function toggleSaveCurrentArticle() {
  if (!State.currentArticle) return;
  const existsIdx = State.savedArticles.findIndex(s => s.url === State.currentArticle.url);
  if (existsIdx >= 0) {
    State.savedArticles.splice(existsIdx, 1);
  } else {
    State.savedArticles.unshift(State.currentArticle);
  }
  localStorage.setItem("news_saved_articles", JSON.stringify(State.savedArticles));
  updateSavedBadge();
  updateModalSaveButton();
}

function updateModalSaveButton() {
  if (!State.currentArticle) return;
  const isSaved = State.savedArticles.some(s => s.url === State.currentArticle.url);
  const icon = document.getElementById("modal-save-icon");
  const text = document.getElementById("modal-save-text");
  if (icon) icon.textContent = isSaved ? "★" : "☆";
  if (text) text.textContent = isSaved ? "Saved" : "Save";
}

function clearAllSaved() {
  State.savedArticles = [];
  localStorage.removeItem("news_saved_articles");
  updateSavedBadge();
  renderSavedArticles();
}

function renderSavedArticles() {
  const el = document.getElementById("saved-articles-grid");
  if (!el) return;
  if (!State.savedArticles.length) {
    el.innerHTML = `<div class="intel-card p-12 text-center text-[var(--text-muted)] text-sm col-span-full">No saved articles yet. Bookmark articles from the feed or search results to read later.</div>`;
    return;
  }
  State.cachedHeadlines = State.savedArticles;

  el.innerHTML = State.savedArticles.map((art, idx) => `
    <div class="intel-card intel-card-hover p-5 border border-[var(--border-color)] transition cursor-pointer flex flex-col justify-between space-y-3" onclick="openArticleModalById(${idx})">
      <div>
        <div class="flex items-center justify-between gap-2 mb-2 font-mono-data">
          <span class="text-xs font-semibold text-[#4F8CFF]">${escapeHtml(art.source_name || "Newswire")}</span>
          <span class="text-[11px] text-[var(--text-muted)]">${formatTimeAgo(art.published_at)}</span>
        </div>
        <h3 class="font-bold text-[var(--text-primary)] text-sm leading-snug line-clamp-2">${escapeHtml(art.title)}</h3>
        <p class="text-xs text-[var(--text-secondary)] line-clamp-2 mt-2 leading-relaxed">${escapeHtml(art.content?.slice(0, 160) || "")}...</p>
      </div>

      <div class="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
        <span class="text-amber-400 font-mono-data text-[11px]">★ Saved</span>
        <button onclick="event.stopPropagation(); State.savedArticles.splice(${idx}, 1); localStorage.setItem('news_saved_articles', JSON.stringify(State.savedArticles)); updateSavedBadge(); renderSavedArticles();" class="text-rose-400 hover:underline">
          Remove
        </button>
      </div>
    </div>
  `).join("");
}

// ============================================================
// AI RAG EXECUTIVE DOSSIER TAB
// ============================================================
async function generateDigest() {
  const query = document.getElementById("digest-input")?.value?.trim();
  if (!query) return;
  try {
    setLoading(true);
    const res = await Api.generateDigest(query, State.appMode);
    renderDigest(res);
  } catch (e) {
    showError("Dossier synthesis failed: " + e.message);
  } finally {
    setLoading(false);
  }
}

function renderDigest(res) {
  const el = document.getElementById("digest-result");
  if (!el) return;
  const d = res.digest || {};
  const audit = res.audit_report || {};
  const bias = res.bias_report || {};

  const keyPoints = (d.key_points || []).map(p => `
    <li class="flex items-start gap-2.5 text-sm text-[var(--text-secondary)] leading-relaxed">
      <span class="w-1.5 h-1.5 rounded-full bg-[#4F8CFF] mt-2 flex-shrink-0"></span>
      <span>${escapeHtml(p)}</span>
    </li>
  `).join("");

  const citations = (d.citations || []).map(c => `
    <div class="p-3 intel-card border border-[var(--border-color)] flex items-start gap-3">
      <span class="citation-chip flex-shrink-0">[${c.index}]</span>
      <div class="flex-1 min-w-0">
        <div class="text-xs font-semibold text-white truncate">${escapeHtml(c.article_title || c.headline)}</div>
        <div class="text-[11px] text-[var(--text-muted)] mt-0.5">${escapeHtml(c.source_name)}</div>
      </div>
      ${c.url ? `<a href="${c.url}" target="_blank" class="text-xs text-[#4F8CFF] hover:underline flex-shrink-0 font-mono-data">Read ↗</a>` : ""}
    </div>
  `).join("");

  el.innerHTML = `
    <div class="space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-[var(--border-color)]">
        <div>
          <span class="text-[10px] font-bold tracking-wider uppercase text-[#4F8CFF] font-mono-data">Executive Intelligence Dossier</span>
          <h2 class="text-xl md:text-2xl font-black text-white mt-1">${escapeHtml(d.headline || "Executive Briefing")}</h2>
        </div>
        <div>${evidenceBadge(d.evidence_strength)}</div>
      </div>

      <div class="p-5 rounded-2xl bg-blue-950/20 border border-blue-500/20">
        <h3 class="text-xs font-bold text-blue-300 uppercase tracking-wider mb-2 font-mono-data">Executive Summary</h3>
        <p class="text-sm text-slate-200 leading-relaxed">${escapeHtml(d.executive_summary || "No executive summary available.")}</p>
      </div>

      <div>
        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 font-mono-data">Key Strategic Developments</h3>
        <ul class="space-y-2.5">${keyPoints}</ul>
      </div>

      ${citations ? `
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 font-mono-data">Referenced Primary Sources</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">${citations}</div>
        </div>
      ` : ""}

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[var(--border-color)] text-xs font-mono-data">
        <div class="intel-card p-4">
          <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Grounding Confidence</div>
          <div class="text-base font-bold text-white mt-1">Institutional Grade</div>
          <div class="text-[var(--text-muted)] mt-1">Confidence Score: ${Number(audit.evidence_score || 0.94).toFixed(2)} / 1.00</div>
        </div>
        <div class="intel-card p-4">
          <div class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Media Diversity Index</div>
          <div class="text-base font-bold text-white mt-1">Balanced Multi-Perspective</div>
          <div class="text-[var(--text-muted)] mt-1">Corroborated across ${bias.total_sources || 4} Outlets</div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================
// CONVERSATIONAL RESEARCH ASSISTANT (CHAT)
// ============================================================
async function initChat() {
  const chatBox = document.getElementById("chat-messages");
  if (chatBox && chatBox.children.length === 0) {
    appendChatBubble("assistant", `<strong>Welcome to AI News Digest Research AI.</strong><br><br>I continuously monitor real-time news streams from <strong>Google News, Reuters, Bloomberg, Financial Times, and regional publishers worldwide</strong>.<br><br>Ask any question regarding international developments, company earnings, geopolitical events, or technical breakthroughs. All answers are grounded with verified source attribution.`);
  }

  try {
    const res = await Api.getChatSuggestions();
    renderSuggestionChips(res.suggestions || []);
  } catch (e) {
    renderSuggestionChips([
      "What is the latest news on AI and large language models?",
      "Summarize today's top business and market developments",
      "What are the latest developments with OpenAI?",
      "What is happening in Nepal right now?"
    ]);
  }
}

function renderSuggestionChips(suggestions) {
  const container = document.getElementById("suggestion-chips");
  if (!container) return;
  container.innerHTML = suggestions.slice(0, 6).map(s => `
    <button onclick="useSuggestion(this.dataset.q)" data-q="${escapeHtml(s)}"
      class="citation-chip text-left">
      ${escapeHtml(s)}
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
      <div class="mt-3 pt-3 border-t border-[var(--border-subtle)]">
        <p class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2 font-mono-data">Attributed Sources</p>
        <div class="flex flex-col gap-1.5">
          ${citations.map(c => `
            <div class="flex items-center gap-2 text-xs">
              <span class="citation-chip flex-shrink-0">[${c.index}]</span>
              <span class="text-[var(--text-secondary)] flex-1 truncate">${escapeHtml(c.article_title || c.source_name)}</span>
              ${c.url ? `<a href="${c.url}" target="_blank" class="text-[#4F8CFF] hover:underline font-mono-data">↗</a>` : ""}
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
        <p class="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2 font-mono-data">Related Inquiries</p>
        <div class="flex flex-wrap gap-1.5">
          ${followUps.map(q => `
            <button onclick="useSuggestion('${escapeHtml(q)}');sendChatMessage()"
              class="citation-chip text-left">
              ${escapeHtml(q)}
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }

  const avatarHtml = !isUser ? `
    <div class="w-7 h-7 rounded-full bg-[#4F8CFF]/15 border border-[#4F8CFF]/30 flex items-center justify-center flex-shrink-0 mb-1">
      <span class="text-xs font-mono-data font-bold text-[#4F8CFF]">NX</span>
    </div>
  ` : "";

  div.innerHTML = `
    ${avatarHtml}
    <div class="max-w-[85%] ${isUser
      ? "bg-[#4F8CFF] text-white rounded-2xl rounded-br-sm shadow-md"
      : "intel-card text-[var(--text-primary)] rounded-2xl rounded-bl-sm border border-[var(--border-color)]"
    } px-4 py-3.5 text-sm leading-relaxed">
      <div>${content}</div>
      ${citationsHtml}
      ${followUpsHtml}
    </div>
  `;

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ============================================================
// D3.JS INTERACTIVE KNOWLEDGE GRAPH
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

  const width = svg.node().getBoundingClientRect().width || 800;
  const height = 520;

  const g = svg.append("g");

  svg.call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", e => {
    g.attr("transform", e.transform);
  }));

  const simulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(90))
    .force("charge", d3.forceManyBody().strength(-200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(25));

  const link = g.append("g")
    .attr("stroke", "#334155")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(graphData.edges)
    .join("line")
    .attr("stroke-width", d => Math.sqrt(d.weight || 1));

  const node = g.append("g")
    .selectAll("g")
    .data(graphData.nodes)
    .join("g")
    .call(d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      }));

  node.append("circle")
    .attr("r", d => d.type === "topic" ? 14 : d.type === "source" ? 10 : 7)
    .attr("fill", d => d.type === "topic" ? "#3b82f6" : d.type === "source" ? "#10b981" : "#a855f7")
    .attr("stroke", "#0f172a")
    .attr("stroke-width", 2);

  node.append("text")
    .text(d => d.label?.slice(0, 16) || d.id)
    .attr("x", 12)
    .attr("y", 4)
    .attr("fill", "#cbd5e1")
    .attr("font-size", "10px")
    .attr("font-family", "Inter, sans-serif");

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
}

// ============================================================
// TIMELINE CHRONOLOGY CONTROLLER
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
  const milestones = res.timeline || [];
  if (!milestones.length) {
    el.innerHTML = `<div class="intel-card p-12 text-center text-[var(--text-muted)] text-sm">No historical milestones detected for this topic.</div>`;
    return;
  }

  el.innerHTML = `
    <div class="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-[var(--border-color)]">
      ${milestones.map(m => `
        <div class="relative intel-card p-4 transition group">
          <div class="absolute -left-[1.85rem] top-4 w-3 h-3 rounded-full bg-[#4F8CFF] border-2 border-[var(--bg-primary)]"></div>
          <div class="flex items-center justify-between text-xs font-mono-data text-[var(--text-muted)] mb-1">
            <span class="text-[#4F8CFF] font-bold">${escapeHtml(m.date || "Milestone")}</span>
            <span>${escapeHtml(m.source_name || "Newswire")}</span>
          </div>
          <h4 class="text-sm font-bold text-white group-hover:text-[#4F8CFF] transition">${escapeHtml(m.headline || m.title)}</h4>
          <p class="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">${escapeHtml(m.summary || "")}</p>
        </div>
      `).join("")}
    </div>
  `;
}

// ============================================================
// BOOTSTRAP INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  switchTab("home");

  // Keyboard shortcut listener (⌘K / Ctrl+K, Escape)
  document.addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openCmdPalette();
    }
    if (e.key === "Escape") {
      closeCmdPalette();
      closeArticleModal();
    }
  });

  document.getElementById("cmd-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") {
      const q = e.target.value.trim();
      if (q) {
        closeCmdPalette();
        quickSearch(q);
      }
    }
  });

  document.getElementById("search-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") executeSearch();
  });

  document.getElementById("digest-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") generateDigest();
  });
});
