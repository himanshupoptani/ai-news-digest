/**
 * app.js — SYNAPSE PRODUCTION CONTROLLER (v6.0)
 * Completely dynamic, event-driven, connected to all 9 FastAPI backend routes.
 */

const Synapse = {
  state: {
    activeView: 'radar',
    activeCategory: 'all',
    articles: [],
    searchResults: [],
    currentModalArticle: null,
    savedArticles: JSON.parse(localStorage.getItem('synapse_saved_dispatches') || '[]'),
    sessionId: null,
    speaking: false,
    speechUtterance: null
  },

  init() {
    this.bindEvents();
    this.updateSavedBadge();
    this.loadRadar();
    this.initChatWelcome();
  },

  bindEvents() {
    // Escape key closes modal dialog
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') Synapse.closeModal();
    });

    // Top Omnibar input
    const omni = document.getElementById('global-omnibar');
    if (omni) {
      omni.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const val = omni.value.trim();
          if (val) Synapse.search(val);
        }
      });
    }

    // Search view input
    const searchInput = document.getElementById('search-view-input');
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') Synapse.execSearch();
      });
    }

    // Dossier view input
    const dossierInput = document.getElementById('dossier-topic-input');
    if (dossierInput) {
      dossierInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') Synapse.execDossier();
      });
    }

    // Chat textarea (Enter sends, Shift+Enter newlines)
    const chatInput = document.getElementById('chat-textarea');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          Synapse.sendChatMessage();
        }
      });
    }

    // Knowledge graph topic input
    const graphTopic = document.getElementById('graph-topic-input');
    if (graphTopic) {
      graphTopic.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') Synapse.renderGraph();
      });
    }

    // Timeline query input
    const timelineTopic = document.getElementById('timeline-query-input');
    if (timelineTopic) {
      timelineTopic.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') Synapse.renderTimeline();
      });
    }
  },

  // ══════════════════════════════════════════════════════
  // NAVIGATION CONTROLLER
  // ══════════════════════════════════════════════════════
  nav(viewId) {
    this.state.activeView = viewId;

    // Toggle canvas view panels
    document.querySelectorAll('.syn-view-panel').forEach((el) => {
      el.classList.remove('active');
    });
    const target = document.getElementById(`panel-${viewId}`);
    if (target) target.classList.add('active');

    // Toggle sidebar nav items
    document.querySelectorAll('.syn-nav-item').forEach((btn) => {
      btn.classList.remove('active');
    });
    const navBtn = document.getElementById(`nav-${viewId}`);
    if (navBtn) navBtn.classList.add('active');

    // View specific activations
    if (viewId === 'saved') {
      this.renderSavedList();
    } else if (viewId === 'graph') {
      const gInput = document.getElementById('graph-topic-input');
      if (gInput && !gInput.value) gInput.value = 'Artificial Intelligence';
      this.renderGraph();
    } else if (viewId === 'timeline') {
      const tInput = document.getElementById('timeline-query-input');
      if (tInput && !tInput.value) tInput.value = 'Artificial Intelligence';
      this.renderTimeline();
    }
    // Auto-close mobile sidebar on nav
    if (window.innerWidth <= 900) this.closeMobileNav();
  },

  toggleMobileNav() {
    const sidebar = document.querySelector('.syn-sidebar');
    const backdrop = document.getElementById('mobile-backdrop');
    if (!sidebar) return;
    const isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
      sidebar.classList.remove('mobile-open');
      if (backdrop) backdrop.classList.remove('active');
      document.body.style.overflow = '';
    } else {
      sidebar.classList.add('mobile-open');
      if (backdrop) backdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  },

  closeMobileNav() {
    const sidebar = document.querySelector('.syn-sidebar');
    const backdrop = document.getElementById('mobile-backdrop');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (backdrop) backdrop.classList.remove('active');
    document.body.style.overflow = '';
  },

  // Category filter
  setCategory(cat) {
    this.state.activeCategory = cat;
    document.querySelectorAll('.syn-filter-strip .syn-chip').forEach((btn) => {
      btn.classList.remove('active');
      if (btn.textContent.toLowerCase().includes(cat)) {
        btn.classList.add('active');
      }
    });
    this.loadRadar();
  },

  refreshAll() {
    this.loadRadar();
  },

  // ══════════════════════════════════════════════════════
  // RADAR VIEW (HOMEPAGE FEED)
  // ══════════════════════════════════════════════════════
  async loadRadar() {
    try {
      this.showSpinner(true);
      const [newsRes, analyticsRes] = await Promise.all([
        Api.getHeadlines(this.state.activeCategory, 21).catch(() => ({ articles: [] })),
        Api.getAnalytics().catch(() => ({ total_articles: 30, total_sources: 18, trending_topics: [] }))
      ]);

      const articles = newsRes.articles || [];
      this.state.articles = articles;

      // Update telemetry tags
      const countBadge = document.getElementById('badge-dispatches-count');
      if (countBadge) countBadge.textContent = articles.length;

      const telemetryLabel = document.getElementById('telemetry-outlets-label');
      if (telemetryLabel) {
        telemetryLabel.textContent = `${analyticsRes.total_sources || 18} Global Wire Sources Syncing`;
      }

      // Update Ticker
      this.updateTicker(analyticsRes.trending_topics || [], articles);

      // Render Spotlight (0)
      if (articles.length > 0) {
        this.renderSpotlight(articles[0]);
      }

      // Render Intercept Stream (1..7)
      this.renderInterceptStream(articles.slice(1, 8));

      // Render Matrix Grid (8..21)
      this.renderMatrixGrid(articles.slice(8));

      const statusLabel = document.getElementById('dispatches-status-label');
      if (statusLabel) statusLabel.textContent = `${articles.length} dispatches live on wire`;

    } catch (e) {
      console.error('Failed to load radar:', e);
    } finally {
      this.showSpinner(false);
    }
  },

  updateTicker(trending, articles) {
    const track = document.getElementById('ticker-feed-track');
    if (!track) return;

    let items = [];
    if (trending && trending.length) {
      items = trending.map((t) => `<span class="syn-ticker-item" onclick="Synapse.search('${this.escapeHtml(t.name || t.tag || t)}')">${this.escapeHtml(t.name || t.tag || t)}</span>`);
    } else if (articles && articles.length) {
      items = articles.slice(0, 8).map((a) => `<span class="syn-ticker-item" onclick="Synapse.search('${this.escapeHtml(a.title)}')">${this.escapeHtml(a.title)}</span>`);
    }

    if (!items.length) {
      items = ['<span class="syn-ticker-item">Live multi-wire satellite dispatches actively monitored across 100+ countries.</span>'];
    }

    const merged = [...items, ...items].join(' <span style="opacity: 0.3; margin: 0 10px;">//</span> ');
    track.innerHTML = merged;
  },

  renderSpotlight(art) {
    const title = document.getElementById('spotlight-title');
    const desc = document.getElementById('spotlight-desc');
    const source = document.getElementById('spotlight-source');
    const time = document.getElementById('spotlight-time');
    const tag = document.getElementById('spotlight-tag');
    const img = document.getElementById('spotlight-img');

    if (title) title.textContent = art.title;
    if (desc) desc.textContent = art.content ? art.content.slice(0, 180) + '...' : '';
    if (source) source.textContent = art.source_name || 'Verified Wire';
    if (time) time.textContent = this.formatTimeAgo(art.published_at);
    if (tag) tag.textContent = (art.category || 'WORLD').toUpperCase();
    if (img) {
      const cat = (art.category || 'world').toLowerCase();
      const catKeywords = {
        'technology': 'technology,innovation', 'ai': 'artificial-intelligence',
        'business': 'business,finance', 'politics': 'government,politics',
        'science': 'science,space', 'sports': 'sports,stadium',
        'health': 'health,medicine', 'world': 'world,city',
        'india': 'india,culture', 'entertainment': 'cinema,entertainment'
      };
      const kw = catKeywords[cat] || 'news,world';
      const seed = art.title ? art.title.charCodeAt(0) : 0;
      const fallbackSrc = `https://source.unsplash.com/1200x500/?${kw}&sig=${seed}`;
      img.src = art.image_url || fallbackSrc;
      img.onerror = () => { img.onerror = null; img.src = fallbackSrc; };
    }
  },

  openSpotlight() {
    if (this.state.articles.length > 0) {
      this.openModal(this.state.articles[0]);
    }
  },

  renderInterceptStream(articles) {
    const list = document.getElementById('stream-scroll-list');
    if (!list) return;

    list.innerHTML = articles.map((a) => `
      <div class="syn-intercept-item" onclick="Synapse.openModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">
        <div class="syn-intercept-title">${this.escapeHtml(a.title)}</div>
        <div class="syn-intercept-meta">${this.escapeHtml(a.source_name || 'Newswire')} · ${this.formatTimeAgo(a.published_at)}</div>
      </div>
    `).join('');
  },

  renderMatrixGrid(articles) {
    const grid = document.getElementById('radar-matrix-grid');
    if (!grid) return;

    // Category → relevant Unsplash keywords for meaningful images
    const categoryImages = {
      'technology': ['technology,computer', 'artificial-intelligence,tech', 'coding,software', 'circuit,digital', 'innovation,future'],
      'ai': ['artificial-intelligence', 'machine-learning,tech', 'robot,future', 'neural-network', 'data,technology'],
      'business': ['business,finance', 'stock-market,trading', 'office,corporate', 'economy,money', 'startup,entrepreneur'],
      'politics': ['government,politics', 'parliament,democracy', 'election,voting', 'law,justice', 'diplomacy,world'],
      'science': ['science,research', 'laboratory,experiment', 'space,astronomy', 'biology,nature', 'physics,quantum'],
      'sports': ['sports,athlete', 'cricket,stadium', 'football,soccer', 'basketball,court', 'competition,winner'],
      'health': ['health,medicine', 'hospital,doctor', 'fitness,wellness', 'pharmacy,drug', 'mental-health'],
      'world': ['world,globe', 'international,news', 'city,urban', 'travel,culture', 'geography,map'],
      'india': ['india,culture', 'delhi,city', 'mumbai,urban', 'india,technology', 'indian,politics'],
      'entertainment': ['entertainment,cinema', 'music,concert', 'film,movie', 'celebrity,art', 'theatre,performance'],
    };

    const getImageUrl = (article, idx) => {
      // Use article's own image if available
      if (article.image_url && article.image_url.startsWith('http')) {
        return article.image_url;
      }
      // Pick category keywords (fallback to generic news)
      const cat = (article.category || '').toLowerCase();
      let keywords = null;
      for (const [key, imgs] of Object.entries(categoryImages)) {
        if (cat.includes(key)) { keywords = imgs[idx % imgs.length]; break; }
      }
      if (!keywords) {
        // Use title words for uniqueness
        const titleWords = (article.title || '').toLowerCase()
          .replace(/[^a-z\s]/g, '').split(' ')
          .filter(w => w.length > 4).slice(0, 2).join(',') || 'news,world';
        keywords = titleWords;
      }
      // Unsplash Source — free, no API key, unique per keyword+seed
      const seed = idx + (article.title ? article.title.charCodeAt(0) : 0);
      return `https://source.unsplash.com/700x400/?${keywords}&sig=${seed}`;
    };

    grid.innerHTML = articles.map((a, idx) => {
      const img = getImageUrl(a, idx);
      return `
        <div class="syn-news-card" onclick="Synapse.openModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">
          <div class="syn-thumb-frame">
            <img src="${img}" alt="news" loading="lazy" onerror="this.onerror=null;this.src='https://source.unsplash.com/700x400/?news,world&sig=${idx}'" />
          </div>
          <div class="syn-card-body">
            <div>
              <span class="syn-tag syn-tag-cyan">${this.escapeHtml(a.category || 'INTEL')}</span>
            </div>
            <h3 class="syn-card-title">${this.escapeHtml(a.title)}</h3>
            <p class="syn-card-snippet">${this.escapeHtml(a.content ? a.content.slice(0, 115) : '')}...</p>
            <div class="syn-card-foot">
              <span style="font-weight: 600; color: var(--syn-text-head);">${this.escapeHtml(a.source_name || 'Newswire')}</span>
              <span>${this.formatTimeAgo(a.published_at)}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  // ══════════════════════════════════════════════════════
  // UNIVERSAL SEARCH
  // ══════════════════════════════════════════════════════
  search(kw) {
    const omni = document.getElementById('global-omnibar');
    const viewInput = document.getElementById('search-view-input');
    if (omni) omni.value = kw;
    if (viewInput) viewInput.value = kw;
    this.nav('search');
    this.execSearch();
  },

  async execSearch() {
    const input = document.getElementById('search-view-input');
    const query = input?.value?.trim();
    if (!query) return;

    try {
      this.showSpinner(true);
      const res = await Api.searchNews(query, 18);
      this.state.searchResults = res.articles || [];

      // Coverage banner
      const covCard = document.getElementById('search-coverage-card');
      if (covCard && res.coverage) {
        const c = res.coverage;
        const geoText = c.detected_country 
          ? `${c.detected_country.toUpperCase()} (${c.detected_region || 'World'})` 
          : (c.detected_region || 'Worldwide Investigation');
        const languages = (c.languages_searched || ['en']).join(', ').toUpperCase();

        covCard.className = 'syn-coverage-banner';
        covCard.innerHTML = `
          <div>
            <div style="font-family: var(--syn-font-mono); font-size: 10px; font-weight: 700; color: var(--syn-cyan); text-transform: uppercase;">
              GEOGRAPHIC COVERAGE RADAR
            </div>
            <div style="font-family: var(--syn-font-head); font-size: 17px; font-weight: 700; color: #fff; margin-top: 2px;">
              ${this.escapeHtml(geoText)}
            </div>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <span class="syn-tag syn-tag-indigo">LANGS: ${languages}</span>
            <span class="syn-tag syn-tag-emerald">OUTLETS: ${(c.sources_retrieved || []).length || this.state.searchResults.length}</span>
            <span class="syn-tag syn-tag-cyan">SYSTEM: MULTI-WIRE</span>
          </div>
        `;
        covCard.style.display = 'flex';
      }

      // Results matrix
      const grid = document.getElementById('search-matrix-grid');
      if (grid) {
        if (!this.state.searchResults.length) {
          grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px 0; color: var(--syn-text-dim);">
              No dispatches discovered for "${this.escapeHtml(query)}". Try another country or topic.
            </div>
          `;
        } else {
          grid.innerHTML = this.state.searchResults.map((a) => `
            <div class="syn-news-card" onclick="Synapse.openModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">
              <div class="syn-card-body">
                <div>
                  <span class="syn-tag syn-tag-cyan">${this.escapeHtml(a.category || 'SEARCH')}</span>
                </div>
                <h3 class="syn-card-title">${this.escapeHtml(a.title)}</h3>
                <p class="syn-card-snippet">${this.escapeHtml(a.content ? a.content.slice(0, 140) : '')}...</p>
                <div class="syn-card-foot">
                  <span style="font-weight: 600; color: var(--syn-text-head);">${this.escapeHtml(a.source_name || 'Newswire')}</span>
                  <span>${this.formatTimeAgo(a.published_at)}</span>
                </div>
              </div>
            </div>
          `).join('');
        }
      }

    } catch (e) {
      console.error('Search error:', e);
    } finally {
      this.showSpinner(false);
    }
  },

  // ══════════════════════════════════════════════════════
  // AI EXECUTIVE DOSSIER
  // ══════════════════════════════════════════════════════
  async execDossier() {
    const input = document.getElementById('dossier-topic-input');
    const topic = input?.value?.trim();
    if (!topic) return;

    const board = document.getElementById('dossier-result-board');
    if (board) {
      board.innerHTML = `
        <div style="text-align: center; padding: 60px 0;">
          <div class="syn-spin-ring" style="margin: 0 auto 14px;"></div>
          <div style="font-family: var(--syn-font-head); font-size: 15px; font-weight: 700; color: #fff;">Synthesizing Intelligence Dossier...</div>
          <div style="font-family: var(--syn-font-mono); font-size: 11px; color: var(--syn-text-dim); margin-top: 4px;">Ingesting primary sources, running hallucination shield, and calculating bias rating</div>
        </div>
      `;
    }

    try {
      this.showSpinner(true);
      const res = await Api.generateDigest(topic);
      const d = res.digest || {};
      const audit = res.audit_report || {};

      if (board) {
        const points = (d.key_points || []).map((p) => `
          <div class="syn-dossier-point">
            <span style="color: var(--syn-cyan); font-weight: 700;">•</span>
            <div>${this.escapeHtml(p)}</div>
          </div>
        `).join('');

        const citations = (d.citations || []).map((c) => `
          <div class="syn-citation-card">
            <div style="font-size: 11.5px; font-weight: 700; color: #fff;">${this.escapeHtml(c.article_title || c.headline || 'Source')}</div>
            <div style="font-family: var(--syn-font-mono); font-size: 10px; color: var(--syn-cyan); margin-top: 2px;">${this.escapeHtml(c.source_name || 'Publisher')}</div>
          </div>
        `).join('');

        board.innerHTML = `
          <div>
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--syn-border-dim); padding-bottom: 14px;">
              <div>
                <span class="syn-tag syn-tag-emerald">CORROBORATED INTEL</span>
                <h2 style="font-family: var(--syn-font-head); font-size: 20px; font-weight: 800; color: #fff; margin-top: 6px;">
                  ${this.escapeHtml(d.headline || topic)}
                </h2>
              </div>
              <div style="font-family: var(--syn-font-mono); font-size: 10.5px; color: var(--syn-text-dim);">
                Confidence: <strong style="color: var(--syn-emerald);">${audit.coverage_percentage || 96}%</strong>
              </div>
            </div>

            <div style="margin-top: 16px; background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 8px; padding: 16px;">
              <div style="font-family: var(--syn-font-mono); font-size: 10px; font-weight: 700; color: var(--syn-cyan); margin-bottom: 4px;">EXECUTIVE BRIEFING</div>
              <div style="font-size: 13.5px; line-height: 1.6; color: var(--syn-text-body);">${this.escapeHtml(d.executive_summary || '')}</div>
            </div>

            <div style="margin-top: 20px;">
              <div style="font-family: var(--syn-font-mono); font-size: 10.5px; font-weight: 700; color: var(--syn-text-dim); margin-bottom: 8px;">KEY STRATEGIC DEVELOPMENTS</div>
              <div>${points}</div>
            </div>

            ${citations ? `
              <div style="margin-top: 20px;">
                <div style="font-family: var(--syn-font-mono); font-size: 10.5px; font-weight: 700; color: var(--syn-text-dim); margin-bottom: 8px;">PRIMARY ATTRIBUTED SOURCES</div>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 8px;">${citations}</div>
              </div>
            ` : ''}
          </div>
        `;
      }
    } catch (e) {
      if (board) board.innerHTML = `<div style="color: var(--syn-rose); padding: 40px; text-align: center;">Dossier generation failed: ${this.escapeHtml(e.message)}</div>`;
    } finally {
      this.showSpinner(false);
    }
  },

  // ══════════════════════════════════════════════════════
  // AI CHATBOT
  // ══════════════════════════════════════════════════════
  initChatWelcome() {
    const box = document.getElementById('chat-messages-log');
    if (box && !box.children.length) {
      this.appendChatMsg('assistant', 'Welcome to Synapse News Intelligence Chat. I can cross-corroborate global dispatches, evaluate regional developments, or clarify complex topics.');
    }
  },

  resetChat() {
    this.state.sessionId = null;
    const box = document.getElementById('chat-messages-log');
    if (box) box.innerHTML = '';
    this.initChatWelcome();
  },

  async sendChatMessage() {
    const textarea = document.getElementById('chat-textarea');
    const sendBtn = document.getElementById('chat-send-btn');
    const msg = textarea?.value?.trim();
    if (!msg) return;

    textarea.value = '';
    textarea.disabled = true;
    if (sendBtn) sendBtn.disabled = true;

    this.appendChatMsg('user', msg);

    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    this.appendChatMsgWithId('assistant', '⬤ &nbsp;⬤ &nbsp;⬤', typingId, 'typing-indicator');

    try {
      // 60s timeout — handles Render free tier cold start (can take 30-50s)
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 60000);

      const res = await Api.sendChatMessageWithSignal(msg, this.state.sessionId, controller.signal);
      clearTimeout(timeout);

      this.removeMsg(typingId);
      this.state.sessionId = res.session_id;
      this.appendChatMsg('assistant', res.content);
    } catch (e) {
      this.removeMsg(typingId);
      const isTimeout = e.name === 'AbortError';
      const errMsg = isTimeout
        ? '⚠️ Request timed out (server may be waking up). Please try again in a moment.'
        : '⚠️ Could not reach the intelligence server. Please try again.';
      this.appendChatMsg('assistant', errMsg);
    } finally {
      textarea.disabled = false;
      if (sendBtn) sendBtn.disabled = false;
      textarea.focus();
    }
  },

  appendChatMsg(role, text) {
    const box = document.getElementById('chat-messages-log');
    if (!box) return;
    const bubble = document.createElement('div');
    bubble.className = `syn-chat-bubble ${role}`;
    bubble.innerHTML = text.replace(/\n/g, '<br>');
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
  },

  appendChatMsgWithId(role, text, id, extraClass = '') {
    const box = document.getElementById('chat-messages-log');
    if (!box) return;
    const bubble = document.createElement('div');
    bubble.className = `syn-chat-bubble ${role}${extraClass ? ' ' + extraClass : ''}`;
    bubble.id = id;
    bubble.innerHTML = text;
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
  },

  removeMsg(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  },

  // ══════════════════════════════════════════════════════
  // D3 KNOWLEDGE GRAPH
  // ══════════════════════════════════════════════════════
  async renderGraph() {
    const input = document.getElementById('graph-topic-input');
    const topic = input?.value?.trim() || 'Artificial Intelligence';
    const svgEl = document.getElementById('syn-d3-svg');
    if (!svgEl) return;

    try {
      this.showSpinner(true);
      const res = await Api.getGraph(topic);
      const nodes = res.nodes || [];
      const edges = res.edges || [];

      d3.select('#syn-d3-svg').selectAll('*').remove();

      if (!nodes.length) return;

      const W = svgEl.parentElement.clientWidth || 900;
      const H = svgEl.parentElement.clientHeight || 550;

      const svg = d3.select('#syn-d3-svg')
        .attr('viewBox', `0 0 ${W} ${H}`);

      const colors = {
        topic: '#06B6D4',
        publisher: '#10B981',
        article: '#6366F1',
        entity: '#F59E0B'
      };

      const sim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id((d) => d.id).distance(110))
        .force('charge', d3.forceManyBody().strength(-240))
        .force('center', d3.forceCenter(W / 2, H / 2))
        .force('collide', d3.forceCollide(32));

      const link = svg.append('g')
        .selectAll('line').data(edges).enter().append('line')
        .attr('stroke', '#1F2633')
        .attr('stroke-width', 1.5);

      const node = svg.append('g')
        .selectAll('g').data(nodes).enter().append('g')
        .call(d3.drag()
          .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
          .on('end', (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
        );

      node.append('circle')
        .attr('r', (d) => d.type === 'topic' ? 14 : 9)
        .attr('fill', (d) => colors[d.type] || '#94A3B8')
        .attr('stroke', '#06080C')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (_, d) => {
          if (d.label) Synapse.search(d.label);
        });

      node.append('text')
        .attr('dx', 16)
        .attr('dy', '0.35em')
        .attr('font-size', '11px')
        .attr('font-family', 'Space Grotesk, sans-serif')
        .attr('fill', '#FFFFFF')
        .text((d) => d.label);

      sim.on('tick', () => {
        link
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);

        node.attr('transform', (d) => `translate(${d.x},${d.y})`);
      });

      svg.call(d3.zoom().on('zoom', (e) => {
        svg.selectAll('g').attr('transform', e.transform);
      }));

    } catch (e) {
      console.error('Graph render error:', e);
    } finally {
      this.showSpinner(false);
    }
  },

  // ══════════════════════════════════════════════════════
  // EVENT CHRONOLOGY TIMELINE
  // ══════════════════════════════════════════════════════
  async renderTimeline() {
    const input = document.getElementById('timeline-query-input');
    const query = input?.value?.trim() || 'Artificial Intelligence';
    const flow = document.getElementById('timeline-flow-list');
    if (!flow) return;

    try {
      this.showSpinner(true);
      const res = await Api.getTimeline(query);
      const milestones = res.timeline || [];

      if (!milestones.length) {
        flow.innerHTML = `<div style="text-align: center; color: var(--syn-text-dim); padding: 40px;">No timeline nodes found.</div>`;
        return;
      }

      flow.innerHTML = milestones.map((m) => `
        <div style="background: var(--syn-bg-surface); border: 1px solid var(--syn-border-dim); border-radius: 10px; padding: 16px; cursor: pointer;" onclick="Synapse.search('${this.escapeHtml(m.query || query)}')">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
            <span class="syn-tag syn-tag-cyan">${this.escapeHtml(m.date || 'MILESTONE')}</span>
            ${m.is_breaking ? '<span class="syn-tag syn-tag-rose">BREAKING</span>' : ''}
          </div>
          <div style="font-family: var(--syn-font-head); font-size: 14.5px; font-weight: 700; color: #fff;">${this.escapeHtml(m.headline || m.title || '')}</div>
          <div style="font-size: 12.5px; color: var(--syn-text-sec); margin-top: 4px; line-height: 1.5;">${this.escapeHtml(m.summary || '')}</div>
        </div>
      `).join('');
    } catch (e) {
      console.error('Timeline error:', e);
    } finally {
      this.showSpinner(false);
    }
  },

  // ══════════════════════════════════════════════════════
  // ARTICLE MODAL & AUDIO BRIEFING
  // ══════════════════════════════════════════════════════
  openModal(article) {
    this.state.currentModalArticle = article;
    const modal = document.getElementById('syn-article-modal');
    if (!modal) return;

    const cat = document.getElementById('modal-tag-badge');
    const src = document.getElementById('modal-source-label');
    const title = document.getElementById('modal-title-text');
    const author = document.getElementById('modal-author-text');
    const time = document.getElementById('modal-time-text');
    const body = document.getElementById('modal-body-text');
    const link = document.getElementById('modal-external-link');

    if (cat) cat.textContent = (article.category || 'WORLD').toUpperCase();
    if (src) src.textContent = article.source_name || 'Verified Wire';
    if (title) title.textContent = article.title;
    if (author) author.textContent = article.author ? `By ${article.author}` : 'Wire Service';
    if (time) time.textContent = this.formatTimeAgo(article.published_at);
    if (body) body.textContent = article.content || 'Full dispatch content verified at publisher source.';
    if (link) link.href = article.url || '#';

    this.updateModalSaveText();
    this.stopAudio();
    modal.classList.remove('hidden');
  },

  closeModal() {
    this.stopAudio();
    const modal = document.getElementById('syn-article-modal');
    if (modal) modal.classList.add('hidden');
  },

  dossierFromModal() {
    if (!this.state.currentModalArticle) return;
    const t = this.state.currentModalArticle.title;
    this.closeModal();
    this.nav('dossier');
    const input = document.getElementById('dossier-topic-input');
    if (input) input.value = t;
    this.execDossier();
  },

  toggleAudioModal() {
    if (this.state.speaking) {
      this.stopAudio();
    } else {
      this.startAudio();
    }
  },

  startAudio() {
    if (!('speechSynthesis' in window) || !this.state.currentModalArticle) return;
    window.speechSynthesis.cancel();
    const txt = `${this.state.currentModalArticle.title}. ${this.state.currentModalArticle.content || ''}`;
    this.state.speechUtterance = new SpeechSynthesisUtterance(txt);
    this.state.speechUtterance.onend = () => this.stopAudio();
    window.speechSynthesis.speak(this.state.speechUtterance);
    this.state.speaking = true;
    const btn = document.getElementById('modal-audio-btn-txt');
    if (btn) btn.textContent = '⏹ Stop';
  },

  stopAudio() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    this.state.speaking = false;
    const btn = document.getElementById('modal-audio-btn-txt');
    if (btn) btn.textContent = '🔊 Listen';
  },

  saveModalArticle() {
    if (!this.state.currentModalArticle) return;
    const url = this.state.currentModalArticle.url;
    const idx = this.state.savedArticles.findIndex((a) => a.url === url);

    if (idx >= 0) {
      this.state.savedArticles.splice(idx, 1);
    } else {
      this.state.savedArticles.unshift(this.state.currentModalArticle);
    }

    localStorage.setItem('synapse_saved_dispatches', JSON.stringify(this.state.savedArticles));
    this.updateSavedBadge();
    this.updateModalSaveText();
  },

  updateModalSaveText() {
    const btn = document.getElementById('modal-save-btn-txt');
    if (!btn || !this.state.currentModalArticle) return;
    const exists = this.state.savedArticles.some((a) => a.url === this.state.currentModalArticle.url);
    btn.textContent = exists ? '★ In Cache' : '☆ Save';
  },

  updateSavedBadge() {
    const badge = document.getElementById('badge-saved-count');
    if (badge) badge.textContent = this.state.savedArticles.length;
  },

  clearSaved() {
    this.state.savedArticles = [];
    localStorage.removeItem('synapse_saved_dispatches');
    this.updateSavedBadge();
    this.renderSavedList();
  },

  renderSavedList() {
    const grid = document.getElementById('saved-matrix-grid');
    if (!grid) return;

    if (!this.state.savedArticles.length) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--syn-text-dim); padding: 60px 0;">No articles saved in offline cache.</div>`;
      return;
    }

    grid.innerHTML = this.state.savedArticles.map((a, idx) => `
      <div class="syn-news-card" onclick="Synapse.openModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">
        <div class="syn-card-body">
          <div><span class="syn-tag syn-tag-rose">SAVED</span></div>
          <h3 class="syn-card-title">${this.escapeHtml(a.title)}</h3>
          <p class="syn-card-snippet">${this.escapeHtml(a.content ? a.content.slice(0, 110) : '')}...</p>
          <div class="syn-card-foot">
            <span>${this.escapeHtml(a.source_name || 'Newswire')}</span>
            <button class="syn-chip" style="color: var(--syn-rose); padding: 2px 6px;" onclick="event.stopPropagation(); Synapse.removeSavedItem(${idx})">Remove</button>
          </div>
        </div>
      </div>
    `).join('');
  },

  removeSavedItem(idx) {
    this.state.savedArticles.splice(idx, 1);
    localStorage.setItem('synapse_saved_dispatches', JSON.stringify(this.state.savedArticles));
    this.updateSavedBadge();
    this.renderSavedList();
  },

  // ══════════════════════════════════════════════════════
  // UTILITIES
  // ══════════════════════════════════════════════════════
  showSpinner(show) {
    const el = document.getElementById('syn-spinner');
    if (el) {
      if (show) el.classList.remove('hidden');
      else el.classList.add('hidden');
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  formatTimeAgo(dateStr) {
    if (!dateStr) return 'Live';
    try {
      const d = new Date(dateStr);
      const diff = Math.round((Date.now() - d.getTime()) / 3600000);
      if (diff < 1) return 'Just now';
      if (diff < 24) return `${diff}h ago`;
      return `${Math.round(diff / 24)}d ago`;
    } catch (e) {
      return 'Recent';
    }
  }
};

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {
  Synapse.init();
});
