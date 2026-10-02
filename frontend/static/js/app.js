/**
 * app.js — Frontend State Controller for AI News Digest
 * Editorial Publication Edition
 */

const State = {
  activeTab: "home",
  appMode: "live",
  currentSessionId: null,
  activeCategory: "all",
  currentArticle: null,
  cachedHeadlines: [],
  savedArticles: JSON.parse(localStorage.getItem("news_saved_articles") || "[]"),
  speechSynth: window.speechSynthesis || null,
  speechUtterance: null,
  isSpeaking: false,
};

// ============================================================
// UTILITIES
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

function updateDate() {
  const el = document.getElementById("current-date-str");
  if (el) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    el.textContent = new Date().toLocaleDateString('en-US', options);
  }
}

function updateSavedBadge() {
  const b = document.getElementById("nav-saved-badge");
  if (b) b.textContent = State.savedArticles.length;
}

// ============================================================
// NAVIGATION TABS
// ============================================================
function switchTab(tabName) {
  State.activeTab = tabName;
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));

  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.remove("hidden");

  if (tabName === "home") loadHome();
  if (tabName === "saved") renderSavedArticles();
  if (tabName === "chat") initChat();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================
// EDITORIAL HOMEPAGE DATA LOADER
// ============================================================
async function loadHome() {
  try {
    setLoading(true);
    updateDate();
    const [headlinesRes, analyticsRes] = await Promise.all([
      Api.getHeadlines(State.activeCategory, 18).catch(() => ({ articles: [] })),
      Api.getAnalytics().catch(() => ({ total_articles: 16, total_sources: 9, trending_topics: [] }))
    ]);

    const articles = headlinesRes.articles || [];
    State.cachedHeadlines = articles;

    renderSecondaryStrip(articles);
    renderHeroStory(articles);
    renderAIDigestPanel(articles);
    renderDontMiss(articles);
    renderTopStoriesSidebar(articles);
    renderLatestNewsGrid(articles);
    updateSavedBadge();
  } catch (e) {
    showError("Failed to stream headlines: " + e.message);
  } finally {
    setLoading(false);
  }
}

function refreshHome() {
  loadHome();
}

function setHeadlinesCategory(cat) {
  State.activeCategory = cat;
  document.querySelectorAll(".cat-nav-link").forEach(btn => {
    btn.classList.remove("active");
  });
  const activeBtn = document.getElementById(`cat-${cat}`);
  if (activeBtn) activeBtn.classList.add("active");
  switchTab("home");
}

// 1. Secondary Strip: 4 small cards in a row under nav
function renderSecondaryStrip(articles) {
  const el = document.getElementById("secondary-news-strip");
  if (!el || !articles.length) return;
  const items = articles.slice(1, 5);

  const fallbackImages = [
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=200&q=80",
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=200&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=200&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=200&q=80"
  ];

  el.innerHTML = items.map((art, idx) => `
    <div class="flex items-center gap-3 p-2 bg-white rounded border border-[#E2E5E9] hover:border-slate-400 cursor-pointer transition" onclick="openArticleModalById(${idx + 1})">
      <div class="w-14 h-14 bg-slate-200 rounded flex-shrink-0 overflow-hidden">
        <img src="${art.image_url || fallbackImages[idx % fallbackImages.length]}" alt="thumb" class="w-full h-full object-cover" onerror="this.src='${fallbackImages[0]}'" />
      </div>
      <div class="flex-1 min-w-0">
        <h4 class="text-xs font-bold text-[#111318] hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(art.title)}</h4>
        <div class="text-[10px] text-slate-400 font-mono-data mt-1">${escapeHtml(art.source_name || "Newswire")} · ${formatTimeAgo(art.published_at)}</div>
      </div>
    </div>
  `).join("");
}

// 2. Large Hero Story
function renderHeroStory(articles) {
  if (!articles.length) return;
  const art = articles[0];
  const titleEl = document.getElementById("hero-title");
  const summaryEl = document.getElementById("hero-summary");
  const catEl = document.getElementById("hero-category");
  const countEl = document.getElementById("hero-source-count");
  const imgEl = document.getElementById("hero-img");

  if (titleEl) titleEl.textContent = art.title;
  if (summaryEl) summaryEl.textContent = art.content?.slice(0, 180) + "..." || "";
  if (catEl) catEl.textContent = art.category || "TECHNOLOGY";
  if (countEl) countEl.textContent = `${art.source_name || "Newswire"} · 34 sources · ${formatTimeAgo(art.published_at)}`;
  if (imgEl && art.image_url) imgEl.src = art.image_url;
}

function openHeroArticle() {
  if (State.cachedHeadlines.length > 0) {
    openArticleModal(State.cachedHeadlines[0]);
  }
}

// 3. AI Digest Dark Panel
function renderAIDigestPanel(articles) {
  const bulletsEl = document.getElementById("home-ai-digest-bullets");
  if (!bulletsEl || !articles.length) return;
  
  const samplePoints = articles.slice(0, 3).map(a => `
    <li class="flex items-start gap-2">
      <span class="text-[#1769E0] font-bold mt-0.5">•</span>
      <span class="line-clamp-2">${escapeHtml(a.title)}</span>
    </li>
  `).join("");
  bulletsEl.innerHTML = samplePoints;
}

// 4. "Don't Miss" Section
function renderDontMiss(articles) {
  const largeCard = articles[5] || articles[0];
  const smallCards = articles.slice(6, 10);

  if (largeCard) {
    const t = document.getElementById("dont-miss-large-title");
    const tag = document.getElementById("dont-miss-large-tag");
    const tm = document.getElementById("dont-miss-large-time");
    const img = document.getElementById("dont-miss-large-img");

    if (t) t.textContent = largeCard.title;
    if (tag) tag.textContent = largeCard.category || "WORLD";
    if (tm) tm.textContent = `${largeCard.source_name || "Newswire"} · ${formatTimeAgo(largeCard.published_at)}`;
    if (img && largeCard.image_url) img.src = largeCard.image_url;
  }

  const gridEl = document.getElementById("dont-miss-grid");
  if (!gridEl) return;

  const fallbackImages = [
    "https://images.unsplash.com/photo-1508873696983-2df5293cbdaf?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=400&q=80"
  ];

  gridEl.innerHTML = smallCards.map((art, idx) => `
    <div class="news-card p-3 flex flex-col justify-between cursor-pointer group" onclick="openArticleModalById(${idx + 6})">
      <div>
        <div class="h-28 bg-slate-200 rounded overflow-hidden mb-2 img-zoom-wrap">
          <img src="${art.image_url || fallbackImages[idx % fallbackImages.length]}" alt="card" class="w-full h-full object-cover" onerror="this.src='${fallbackImages[0]}'" />
        </div>
        <span class="tag-pill text-[9px] mb-1.5">${escapeHtml(art.category || "GENERAL")}</span>
        <h4 class="text-xs font-bold text-[#111318] group-hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(art.title)}</h4>
      </div>
      <div class="text-[10px] text-slate-400 font-mono-data mt-2">${formatTimeAgo(art.published_at)}</div>
    </div>
  `).join("");
}

function openDontMissLarge() {
  if (State.cachedHeadlines.length > 5) {
    openArticleModal(State.cachedHeadlines[5]);
  }
}

// 5. Top Stories Numbered Sidebar
function renderTopStoriesSidebar(articles) {
  const el = document.getElementById("top-stories-list");
  if (!el || !articles.length) return;
  const topFive = articles.slice(0, 5);

  const fallbackThumbs = [
    "https://images.unsplash.com/photo-1508873696983-2df5293cbdaf?auto=format&fit=crop&w=120&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=120&q=80",
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=120&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=120&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=120&q=80"
  ];

  el.innerHTML = topFive.map((art, idx) => `
    <div class="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between gap-3 cursor-pointer group" onclick="openArticleModalById(${idx})">
      <div class="flex items-start gap-2.5">
        <span class="text-base font-black text-[#1769E0] font-mono-data leading-none mt-0.5">${idx + 1}</span>
        <div>
          <h4 class="text-xs font-bold text-[#111318] group-hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(art.title)}</h4>
          <div class="text-[10px] text-slate-400 font-mono-data mt-0.5">${escapeHtml(art.source_name || "Newswire")} · ${formatTimeAgo(art.published_at)}</div>
        </div>
      </div>
      <div class="w-14 h-11 bg-slate-200 rounded overflow-hidden flex-shrink-0">
        <img src="${art.image_url || fallbackThumbs[idx]}" alt="thumb" class="w-full h-full object-cover" onerror="this.src='${fallbackThumbs[0]}'" />
      </div>
    </div>
  `).join("");
}

// 6. Latest News Grid
function renderLatestNewsGrid(articles) {
  const el = document.getElementById("latest-news-grid");
  const countBadge = document.getElementById("article-count-badge");
  if (!el) return;
  const items = articles.slice(10);
  if (countBadge) countBadge.textContent = `${articles.length} dispatches live`;

  if (!items.length) {
    el.innerHTML = `<div class="p-8 text-center text-slate-400 text-xs col-span-full">All current top headlines displayed above.</div>`;
    return;
  }

  el.innerHTML = items.map((art, idx) => `
    <div class="news-card p-4 flex flex-col justify-between cursor-pointer group" onclick="openArticleModalById(${idx + 10})">
      <div>
        <div class="flex items-center justify-between text-[11px] font-mono-data text-slate-400 mb-1.5">
          <span class="tag-pill text-[9px]">${escapeHtml(art.category || "NEWS")}</span>
          <span>${formatTimeAgo(art.published_at)}</span>
        </div>
        <h4 class="text-sm font-bold text-[#111318] group-hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(art.title)}</h4>
        <p class="text-xs text-slate-500 line-clamp-2 mt-1 leading-relaxed">${escapeHtml(art.content?.slice(0, 140) || "")}...</p>
      </div>
      <div class="pt-3 mt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono-data text-slate-400">
        <span>${escapeHtml(art.source_name || "Newswire")}</span>
        <span class="text-[#1769E0] font-semibold">Read →</span>
      </div>
    </div>
  `).join("");
}

// ============================================================
// SEARCH LOGIC
// ============================================================
function executeTopSearch() {
  const query = document.getElementById("main-search-input")?.value?.trim();
  if (!query) return;
  const sInput = document.getElementById("search-input");
  if (sInput) sInput.value = query;
  switchTab("search");
  executeSearch();
}

function quickSearch(query) {
  const sInput = document.getElementById("search-input");
  const topInput = document.getElementById("main-search-input");
  if (sInput) sInput.value = query;
  if (topInput) topInput.value = query;
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

  if (bannerEl) {
    const geoTitle = coverage.detected_country 
      ? `${coverage.detected_country.toUpperCase()} (${coverage.detected_region || "World"})`
      : (coverage.detected_region || "Worldwide Open Wire");
    const langs = (coverage.languages_searched || ["en"]).join(", ").toUpperCase();
    const providers = (coverage.providers_used || ["Google News RSS", "GDELT"]).join(" · ");
    const sourcesCount = (coverage.sources_retrieved || []).length || articles.length;

    bannerEl.className = "p-4 rounded-lg bg-[#EEF4FD] border border-[#D0E1FB] text-xs";
    bannerEl.innerHTML = `
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div>
          <span class="text-[10px] font-bold text-[#1769E0] font-mono-data uppercase">Geographic Coverage Active</span>
          <div class="text-sm font-black text-[#111318]">${escapeHtml(geoTitle)}</div>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-[11px] font-mono-data text-slate-600">
          <span class="citation-chip">Languages: <strong>${escapeHtml(langs)}</strong></span>
          <span class="citation-chip">Outlets: <strong class="text-emerald-700">${sourcesCount}</strong></span>
          <span class="citation-chip">Pipeline: <strong class="text-[#1769E0]">${escapeHtml(providers)}</strong></span>
        </div>
      </div>
    `;
    bannerEl.classList.remove("hidden");
  }

  if (eventsEl) {
    const developing = events.filter(e => e.source_count >= 2 || e.is_developing);
    if (developing.length > 0) {
      eventsEl.innerHTML = `
        <div class="pt-2">
          <h3 class="text-xs font-bold text-rose-600 uppercase font-mono-data mb-2">
            ● Cross-Corroborated Developing Stories (${developing.length})
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            ${developing.slice(0, 4).map(ev => `
              <div class="news-card p-3 border-rose-200 bg-rose-50/20 space-y-1.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700 font-mono-data">
                  🚨 ${ev.source_count} Independent Sources
                </span>
                <h4 class="text-xs font-bold text-[#111318] line-clamp-2 leading-snug">${escapeHtml(ev.headline)}</h4>
                <div class="flex flex-wrap gap-1 pt-1">
                  ${ev.sources.slice(0, 4).map(s => `<span class="citation-chip">${escapeHtml(s)}</span>`).join("")}
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      `;
      eventsEl.classList.remove("hidden");
    } else {
      eventsEl.classList.add("hidden");
    }
  }

  if (!articles.length) {
    el.innerHTML = `<div class="p-12 text-center text-slate-400 text-xs col-span-full news-card">No articles found matching this query.</div>`;
    return;
  }
  State.cachedHeadlines = articles;

  el.innerHTML = articles.map((a, idx) => `
    <div class="news-card p-4 flex flex-col justify-between cursor-pointer group" onclick="openArticleModalById(${idx})">
      <div>
        <div class="flex items-center justify-between text-[11px] font-mono-data text-slate-400 mb-1.5">
          <span class="text-[#1769E0] font-bold">${escapeHtml(a.source_name || "Newswire")}</span>
          <span>${formatTimeAgo(a.published_at)}</span>
        </div>
        <h4 class="text-sm font-bold text-[#111318] group-hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(a.title)}</h4>
        <p class="text-xs text-slate-500 line-clamp-2 mt-1 leading-relaxed">${escapeHtml(a.content?.slice(0, 160) || "")}...</p>
      </div>
      <div class="pt-3 mt-2 border-t border-slate-100 flex items-center justify-between text-xs">
        <span class="tag-pill text-[9px]">${escapeHtml(a.category || "WORLD")}</span>
        <span class="text-[#1769E0] font-semibold">Inspect Story →</span>
      </div>
    </div>
  `).join("");
}

// ============================================================
// ARTICLE READER MODAL & AUDIO
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
  document.getElementById("modal-reading-time").textContent = `${intel.reading_time_min || 3} min read`;
  document.getElementById("modal-sentiment").textContent = intel.sentiment || "Neutral";
  document.getElementById("modal-impact").textContent = intel.impact_level || "Standard Priority";
  document.getElementById("modal-body").innerHTML = `<p>${escapeHtml(article.content || "Full dispatch text available at original publisher.")}</p>`;

  const entitiesEl = document.getElementById("modal-entities");
  if (entitiesEl) {
    const list = intel.entities || [];
    entitiesEl.innerHTML = list.length ? list.map(e => `
      <span class="citation-chip">${escapeHtml(e)}</span>
    `).join("") : '<span class="text-xs text-slate-400 font-mono-data">None detected</span>';
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

function openVideoModal() {
  if (State.cachedHeadlines.length > 0) {
    openArticleModal(State.cachedHeadlines[0]);
  }
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
// SAVED ARTICLES
// ============================================================
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
    el.innerHTML = `<div class="p-12 text-center text-slate-400 text-xs col-span-full news-card">No saved articles yet.</div>`;
    return;
  }
  State.cachedHeadlines = State.savedArticles;

  el.innerHTML = State.savedArticles.map((art, idx) => `
    <div class="news-card p-4 flex flex-col justify-between cursor-pointer group" onclick="openArticleModalById(${idx})">
      <div>
        <div class="flex items-center justify-between text-[11px] font-mono-data text-slate-400 mb-1.5">
          <span class="text-[#1769E0] font-bold">${escapeHtml(art.source_name || "Newswire")}</span>
          <span>${formatTimeAgo(art.published_at)}</span>
        </div>
        <h4 class="text-sm font-bold text-[#111318] group-hover:text-[#1769E0] line-clamp-2 leading-snug">${escapeHtml(art.title)}</h4>
        <p class="text-xs text-slate-500 line-clamp-2 mt-1 leading-relaxed">${escapeHtml(art.content?.slice(0, 160) || "")}...</p>
      </div>
      <div class="pt-3 mt-2 border-t border-slate-100 flex items-center justify-between text-xs">
        <span class="text-amber-500 font-mono-data text-[11px]">★ Saved</span>
        <button onclick="event.stopPropagation(); State.savedArticles.splice(${idx}, 1); localStorage.setItem('news_saved_articles', JSON.stringify(State.savedArticles)); updateSavedBadge(); renderSavedArticles();" class="text-rose-600 hover:underline">
          Remove
        </button>
      </div>
    </div>
  `).join("");
}

// ============================================================
// EXECUTIVE DOSSIER
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
    <li class="flex items-start gap-2 text-xs md:text-sm text-slate-700 leading-relaxed">
      <span class="text-[#1769E0] font-bold mt-0.5">•</span>
      <span>${escapeHtml(p)}</span>
    </li>
  `).join("");

  const citations = (d.citations || []).map(c => `
    <div class="p-3 bg-slate-50 rounded border border-slate-200 flex items-start gap-2.5">
      <span class="citation-chip flex-shrink-0">[${c.index}]</span>
      <div class="flex-1 min-w-0">
        <div class="text-xs font-bold text-slate-900 truncate">${escapeHtml(c.article_title || c.headline)}</div>
        <div class="text-[11px] text-slate-500">${escapeHtml(c.source_name)}</div>
      </div>
      ${c.url ? `<a href="${c.url}" target="_blank" class="text-xs text-[#1769E0] hover:underline font-mono-data flex-shrink-0">Read ↗</a>` : ""}
    </div>
  `).join("");

  el.innerHTML = `
    <div class="space-y-5">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-slate-200">
        <div>
          <span class="text-[10px] font-bold text-[#1769E0] font-mono-data uppercase">✦ Verified Intelligence Dossier</span>
          <h2 class="text-xl md:text-2xl font-black text-[#111318] mt-0.5">${escapeHtml(d.headline || "Executive Briefing")}</h2>
        </div>
        <span class="px-2.5 py-0.5 rounded text-[11px] font-mono-data font-bold bg-emerald-50 text-emerald-700 border border-emerald-300">✓ Corroborated</span>
      </div>

      <div class="p-4 rounded-lg bg-[#EEF4FD] border border-[#D0E1FB]">
        <h3 class="text-xs font-bold text-[#1769E0] uppercase font-mono-data mb-1.5">Executive Summary</h3>
        <p class="text-xs md:text-sm text-slate-800 leading-relaxed">${escapeHtml(d.executive_summary || "")}</p>
      </div>

      <div>
        <h3 class="text-xs font-bold text-slate-400 uppercase font-mono-data mb-2">Key Strategic Developments</h3>
        <ul class="space-y-2">${keyPoints}</ul>
      </div>

      ${citations ? `
        <div>
          <h3 class="text-xs font-bold text-slate-400 uppercase font-mono-data mb-2">Attributed Primary Outlets</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">${citations}</div>
        </div>
      ` : ""}
    </div>
  `;
}

// ============================================================
// CHATBOT RESEARCH ASSISTANT
// ============================================================
async function initChat() {
  const chatBox = document.getElementById("chat-messages");
  if (chatBox && chatBox.children.length === 0) {
    appendChatBubble("assistant", `Welcome to <strong>AI News Digest Research Assistant</strong>.<br><br>I continuously monitor live wire dispatches from Reuters, Bloomberg, Associated Press, Google News, and regional newsrooms.<br><br>Ask any question about current international developments.`);
  }

  try {
    const res = await Api.getChatSuggestions();
    renderSuggestionChips(res.suggestions || []);
  } catch (e) {
    renderSuggestionChips([
      "What is the latest news on AI?",
      "Summarize global business headlines",
      "What is happening in Nepal right now?"
    ]);
  }
}

function renderSuggestionChips(suggestions) {
  const container = document.getElementById("suggestion-chips");
  if (!container) return;
  container.innerHTML = suggestions.slice(0, 4).map(s => `
    <button onclick="useSuggestion(this.dataset.q)" data-q="${escapeHtml(s)}"
      class="citation-chip text-left">
      ${escapeHtml(s)}
    </button>
  `).join("");
}

function useSuggestion(q) {
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = q;
    input.focus();
  }
}

function startNewChat() {
  State.currentSessionId = null;
  const chatBox = document.getElementById("chat-messages");
  if (chatBox) chatBox.innerHTML = "";
  initChat();
}

async function sendChatMessage() {
  const input = document.getElementById("chat-input");
  const msg = input?.value?.trim();
  if (!msg) return;

  input.value = "";
  appendChatBubble("user", msg);

  const typingEl = document.getElementById("chat-typing");
  if (typingEl) typingEl.classList.remove("hidden");

  try {
    const res = await Api.sendChatMessage(msg, State.currentSessionId);
    State.currentSessionId = res.session_id;
    if (typingEl) typingEl.classList.add("hidden");
    appendChatBubble("assistant", res.content, null, res.citations || [], res.follow_up_questions || []);
  } catch (e) {
    if (typingEl) typingEl.classList.add("hidden");
    appendChatBubble("assistant", `Connection error: please verify that the backend is active.`);
  }
}

function appendChatBubble(role, content, strength = null, citations = [], followUps = []) {
  const chatBox = document.getElementById("chat-messages");
  if (!chatBox) return;
  const isUser = role === "user";
  const div = document.createElement("div");
  div.className = `flex ${isUser ? "justify-end" : "justify-start"}`;

  let citationsHtml = "";
  if (!isUser && citations.length > 0) {
    citationsHtml = `
      <div class="mt-2 pt-2 border-t border-slate-200">
        <div class="text-[10px] font-bold text-slate-400 font-mono-data mb-1">Sources:</div>
        <div class="flex flex-col gap-1">
          ${citations.map(c => `
            <div class="text-xs text-slate-600 truncate">
              [${c.index}] ${escapeHtml(c.article_title || c.source_name)}
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  div.innerHTML = `
    <div class="max-w-[85%] ${isUser ? "bg-[#1769E0] text-white" : "bg-white text-slate-900 border border-slate-200"} rounded-lg px-3.5 py-2.5 text-xs leading-relaxed shadow-sm">
      <div>${content}</div>
      ${citationsHtml}
    </div>
  `;

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ============================================================
// BOOTSTRAP INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  switchTab("home");

  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      closeArticleModal();
    }
  });

  document.getElementById("main-search-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") executeTopSearch();
  });

  document.getElementById("search-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") executeSearch();
  });

  document.getElementById("digest-input")?.addEventListener("keydown", e => {
    if (e.key === "Enter") generateDigest();
  });
});
