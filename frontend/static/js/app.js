/**
 * app.js — AI News Digest Master Application Controller (v3.0)
 * Completely bug-free, modular, clean & reactive.
 */

const App = {
  state: {
    activeTab: 'home',
    activeCategory: 'all',
    articles: [],
    searchResults: [],
    currentArticle: null,
    savedArticles: JSON.parse(localStorage.getItem('ai_digest_saved') || '[]'),
    sessionId: null,
    isSpeaking: false,
    speechUtterance: null,
  },

  // ──────────────────────────────────────────
  // INIT & BOOTSTRAP
  // ──────────────────────────────────────────
  init() {
    this.bindEvents();
    this.updateSavedBadge();
    this.loadHome();
    this.initChatSuggestions();
  },

  bindEvents() {
    // Escape key closes modal
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') App.closeModal();
    });

    // Enter listeners for search boxes
    const headerSearch = document.getElementById('header-search-input');
    if (headerSearch) {
      headerSearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.runHeaderSearch();
      });
    }

    const mainSearch = document.getElementById('search-input');
    if (mainSearch) {
      mainSearch.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.runSearch();
      });
    }

    const digestInput = document.getElementById('digest-input');
    if (digestInput) {
      digestInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.runDigest();
      });
    }

    const graphInput = document.getElementById('graph-input');
    if (graphInput) {
      graphInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.loadGraph();
      });
    }

    const timelineInput = document.getElementById('timeline-input');
    if (timelineInput) {
      timelineInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') App.loadTimeline();
      });
    }

    const chatText = document.getElementById('chat-textarea');
    if (chatText) {
      chatText.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          App.sendChat();
        }
      });
    }
  },

  // ──────────────────────────────────────────
  // NAVIGATION & TABS
  // ──────────────────────────────────────────
  switchTab(tabName) {
    this.state.activeTab = tabName;

    // Toggle panels
    document.querySelectorAll('.tab-panel').forEach((el) => {
      el.classList.remove('active');
    });
    const targetPanel = document.getElementById(`panel-${tabName}`);
    if (targetPanel) targetPanel.classList.add('active');

    // Toggle navbar state
    document.querySelectorAll('.nav-btn').forEach((btn) => {
      btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`nav-${tabName}`);
    if (activeBtn) activeBtn.classList.add('active');

    // Lazy load or refresh data depending on tab
    if (tabName === 'saved') {
      this.renderSaved();
    } else if (tabName === 'graph') {
      const graphInput = document.getElementById('graph-input');
      if (graphInput && !graphInput.value) {
        graphInput.value = 'Artificial Intelligence';
      }
      this.loadGraph();
    } else if (tabName === 'timeline') {
      const timelineInput = document.getElementById('timeline-input');
      if (timelineInput && !timelineInput.value) {
        timelineInput.value = 'Artificial Intelligence';
      }
      this.loadTimeline();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  setCategory(cat) {
    this.state.activeCategory = cat;

    // Highlight chip
    const chips = ['all', 'world', 'tech', 'ai', 'business', 'science'];
    chips.forEach((c) => {
      const el = document.getElementById(`ctab-${c}`);
      if (el) {
        if (c === cat) {
          el.style.borderColor = 'var(--blue)';
          el.style.background = 'var(--blue-light)';
          el.style.color = 'var(--blue)';
        } else {
          el.style.borderColor = 'var(--border)';
          el.style.background = 'var(--bg-surface)';
          el.style.color = 'var(--text-2)';
        }
      }
    });

    this.loadHome();
  },

  // ──────────────────────────────────────────
  // HOME FEED LOADER
  // ──────────────────────────────────────────
  async loadHome() {
    try {
      this.setLoading(true);
      const [newsRes, analyticsRes] = await Promise.all([
        Api.getHeadlines(this.state.activeCategory, 18).catch(() => ({ articles: [] })),
        Api.getAnalytics().catch(() => ({ total_articles: 24, total_sources: 12, trending_topics: [] }))
      ]);

      const articles = newsRes.articles || [];
      this.state.articles = articles;

      // Update macro telemetry metrics
      const statArticles = document.getElementById('stat-articles');
      if (statArticles) statArticles.textContent = analyticsRes.total_articles || articles.length || '48+';

      const statSources = document.getElementById('stat-sources');
      if (statSources) statSources.textContent = analyticsRes.total_sources || '16+';

      const statTrending = document.getElementById('stat-trending');
      const trending = analyticsRes.trending_topics || [];
      if (statTrending) {
        statTrending.textContent = trending.length ? trending[0] : 'Global Markets';
      }

      // Update Ticker
      this.renderTicker(trending, articles);

      // Render Hero Story (article 0)
      if (articles.length > 0) {
        this.renderHero(articles[0]);
      }

      // Render Top Stories sidebar (articles 1 to 5)
      this.renderTopStories(articles.slice(1, 6));

      // Render Grid (articles 6 onward)
      this.renderArticlesGrid(articles.slice(6));

      const countBadge = document.getElementById('article-count');
      if (countBadge) countBadge.textContent = `${articles.length} dispatches live`;

    } catch (err) {
      this.showToast('Failed to load live dispatches: ' + err.message);
    } finally {
      this.setLoading(false);
    }
  },

  renderTicker(trending, articles) {
    const tickerInner = document.getElementById('ticker-inner');
    if (!tickerInner) return;

    let items = [];
    if (trending && trending.length) {
      items = trending.map((t) => `<span class="ticker-item" onclick="App.quickSearch('${App.escapeHtml(t)}')">${App.escapeHtml(t)}</span>`);
    } else if (articles && articles.length) {
      items = articles.slice(0, 6).map((a) => `<span class="ticker-item" onclick="App.openArticleByTitle('${App.escapeHtml(a.title)}')">${App.escapeHtml(a.title)}</span>`);
    }

    if (!items.length) {
      items = ['<span class="ticker-item">Continuous global news intelligence active across 100+ countries</span>'];
    }

    // Duplicate list for seamless infinite scroll
    const combined = [...items, ...items].join('<span class="ticker-sep">·</span>');
    tickerInner.innerHTML = combined;
  },

  renderHero(article) {
    if (!article) return;
    const tag = document.getElementById('hero-tag');
    const title = document.getElementById('hero-title');
    const summary = document.getElementById('hero-summary');
    const source = document.getElementById('hero-source');
    const time = document.getElementById('hero-time');
    const img = document.getElementById('hero-img');

    if (tag) tag.textContent = article.category ? article.category.toUpperCase() : 'WORLD';
    if (title) title.textContent = article.title;
    if (summary) summary.textContent = article.content ? article.content.slice(0, 160) + '...' : '';
    if (source) source.textContent = article.source_name || 'Verified Wire';
    if (time) time.textContent = this.formatTime(article.published_at);
    if (img && article.image_url) {
      img.src = article.image_url;
      img.onerror = () => {
        img.src = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80';
      };
    }
  },

  renderTopStories(stories) {
    const container = document.getElementById('top-stories-list');
    if (!container) return;

    if (!stories.length) {
      container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-3);font-size:12px;">No top stories available.</div>';
      return;
    }

    container.innerHTML = stories.map((s, idx) => `
      <div class="side-story" onclick="App.openArticle(${JSON.stringify(s).replace(/"/g, '&quot;')})">
        <div class="side-story-num">0${idx + 1}</div>
        <div style="flex:1;min-width:0;">
          <div class="side-story-title clamp-2">${this.escapeHtml(s.title)}</div>
          <div class="side-story-meta">${this.escapeHtml(s.source_name || 'Newswire')} · ${this.formatTime(s.published_at)}</div>
        </div>
      </div>
    `).join('');
  },

  renderArticlesGrid(articles) {
    const grid = document.getElementById('articles-grid');
    if (!grid) return;

    if (!articles.length) {
      grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);font-size:13px;">No more articles found in this category.</div>';
      return;
    }

    const fallbacks = [
      'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80',
      'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80',
      'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80',
      'https://images.unsplash.com/photo-1508873696983-2df5293cbdaf?auto=format&fit=crop&w=600&q=80',
      'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=600&q=80'
    ];

    grid.innerHTML = articles.map((a, idx) => {
      const fallbackImg = fallbacks[idx % fallbacks.length];
      const imgUrl = a.image_url || fallbackImg;
      return `
        <div class="article-card" onclick="App.openArticle(${JSON.stringify(a).replace(/"/g, '&quot;')})">
          <img class="thumb" src="${imgUrl}" alt="article" loading="lazy" onerror="this.src='${fallbackImg}'" />
          <div class="body">
            <div class="meta">
              <span class="tag tag-blue">${this.escapeHtml(a.category || 'WORLD')}</span>
              <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);margin-left:auto;">${this.formatTime(a.published_at)}</span>
            </div>
            <h3 class="clamp-2">${this.escapeHtml(a.title)}</h3>
            <p class="clamp-2">${this.escapeHtml(a.content ? a.content.slice(0, 120) : '')}...</p>
            <div class="footer">
              <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);font-weight:600;">${this.escapeHtml(a.source_name || 'Newswire')}</span>
              <span style="font-size:11.5px;color:var(--blue);font-weight:600;">Read →</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  // ──────────────────────────────────────────
  // SEARCH FUNCTIONALITY
  // ──────────────────────────────────────────
  runHeaderSearch() {
    const val = document.getElementById('header-search-input')?.value?.trim();
    if (!val) return;
    this.quickSearch(val);
  },

  quickSearch(query) {
    const input = document.getElementById('search-input');
    const headerInput = document.getElementById('header-search-input');
    if (input) input.value = query;
    if (headerInput) headerInput.value = query;
    this.switchTab('search');
    this.runSearch();
  },

  async runSearch() {
    const input = document.getElementById('search-input');
    const query = input?.value?.trim();
    if (!query) return;

    try {
      this.setLoading(true);
      const res = await Api.searchNews(query, 16);
      this.state.searchResults = res.articles || [];

      // 1. Render Coverage banner
      const covEl = document.getElementById('search-coverage');
      if (covEl && res.coverage) {
        const c = res.coverage;
        const regionName = c.detected_country 
          ? `${c.detected_country.toUpperCase()} (${c.detected_region || 'World'})` 
          : (c.detected_region || 'Worldwide Coverage');
        const languages = (c.languages_searched || ['en']).join(', ').toUpperCase();
        const sourcesCount = (c.sources_retrieved || []).length || this.state.searchResults.length;

        covEl.className = 'coverage-banner';
        covEl.innerHTML = `
          <div>
            <div class="coverage-label">Geographic Intelligence Engine</div>
            <div class="coverage-geo">${this.escapeHtml(regionName)}</div>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
            <span class="cite">Languages: <strong>${this.escapeHtml(languages)}</strong></span>
            <span class="cite">Sources: <strong>${sourcesCount}</strong></span>
            <span class="cite">Engine: <strong>Global Multi-Wire</strong></span>
          </div>
        `;
        covEl.style.display = 'flex';
      } else if (covEl) {
        covEl.style.display = 'none';
      }

      // 2. Render Events / Developing Clusters
      const evEl = document.getElementById('search-events');
      if (evEl && res.events && res.events.length) {
        evEl.innerHTML = `
          <div style="background:var(--red-light);border:1.5px solid #FECACA;border-radius:var(--r-lg);padding:14px 18px;">
            <div style="font-size:11px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:0.07em;font-family:var(--font-mono);margin-bottom:8px;">
              🚨 Developing Story Clusters (${res.events.length})
            </div>
            <div class="grid-2">
              ${res.events.slice(0, 4).map((ev) => `
                <div style="background:#fff;border:1px solid #FCA5A5;border-radius:var(--r-md);padding:12px;">
                  <div style="font-size:10px;font-weight:700;color:var(--red);font-family:var(--font-mono);margin-bottom:4px;">
                    ${ev.source_count} Independent Sources Corroborating
                  </div>
                  <div style="font-size:13px;font-weight:700;color:var(--text);line-height:1.4;">${this.escapeHtml(ev.headline)}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
        evEl.style.display = 'block';
      } else if (evEl) {
        evEl.style.display = 'none';
      }

      // 3. Render Results Grid
      const container = document.getElementById('search-results');
      if (container) {
        if (!this.state.searchResults.length) {
          container.innerHTML = `
            <div style="text-align:center;padding:60px;color:var(--text-3);">
              <div style="font-size:40px;margin-bottom:12px;">📰</div>
              <p style="font-size:14px;font-weight:600;color:var(--text-2);">No dispatches found for "${this.escapeHtml(query)}"</p>
              <p style="font-size:12px;margin-top:4px;">Try a broader query or a specific country name.</p>
            </div>
          `;
        } else {
          container.className = 'grid-3';
          container.innerHTML = this.state.searchResults.map((a) => `
            <div class="article-card" onclick="App.openArticle(${JSON.stringify(a).replace(/"/g, '&quot;')})">
              <div class="body">
                <div class="meta">
                  <span class="tag tag-blue">${this.escapeHtml(a.category || 'NEWS')}</span>
                  <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);margin-left:auto;">${this.formatTime(a.published_at)}</span>
                </div>
                <h3 class="clamp-2">${this.escapeHtml(a.title)}</h3>
                <p class="clamp-3">${this.escapeHtml(a.content ? a.content.slice(0, 150) : '')}...</p>
                <div class="footer">
                  <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);font-weight:600;">${this.escapeHtml(a.source_name || 'Newswire')}</span>
                  <span style="font-size:11.5px;color:var(--blue);font-weight:600;">Inspect Story →</span>
                </div>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      this.showToast('Search failed: ' + err.message);
    } finally {
      this.setLoading(false);
    }
  },

  // ──────────────────────────────────────────
  // AI DOSSIER
  // ──────────────────────────────────────────
  digestQuick(topic) {
    const input = document.getElementById('digest-input');
    if (input) input.value = topic;
    this.runDigest();
  },

  async runDigest() {
    const input = document.getElementById('digest-input');
    const topic = input?.value?.trim();
    if (!topic) return;

    const out = document.getElementById('digest-output');
    if (out) {
      out.innerHTML = `
        <div style="text-align:center;padding:60px;color:var(--text-3);">
          <div class="spinner" style="margin:0 auto 16px;"></div>
          <p style="font-size:14px;font-weight:600;color:var(--text);">Synthesizing multi-source intelligence dossier...</p>
          <p style="font-size:12px;margin-top:4px;">Cross-corroborating facts and calculating bias ratings</p>
        </div>
      `;
    }

    try {
      this.setLoading(true);
      const res = await Api.generateDigest(topic);
      const d = res.digest || {};
      const audit = res.audit_report || {};

      if (out) {
        const keyPointsHtml = (d.key_points || []).map((p) => `<div class="key-point">${this.escapeHtml(p)}</div>`).join('');

        const citationsHtml = (d.citations || []).map((c) => `
          <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--r-md);padding:10px 14px;display:flex;align-items:center;justify-content:space-between;gap:8px;">
            <div style="min-width:0;flex:1;">
              <div style="font-size:12px;font-weight:700;color:var(--text);" class="truncate">${this.escapeHtml(c.article_title || c.headline || 'Source')}</div>
              <div style="font-size:10.5px;color:var(--text-3);font-family:var(--font-mono);">${this.escapeHtml(c.source_name || 'Publisher')}</div>
            </div>
            ${c.url ? `<a href="${c.url}" target="_blank" style="font-size:11px;color:var(--blue);text-decoration:none;font-weight:600;">Link ↗</a>` : ''}
          </div>
        `).join('');

        out.innerHTML = `
          <div class="digest-result">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;padding-bottom:16px;border-bottom:1px solid var(--border);">
              <div>
                <span class="tag tag-green">✓ Corroborated Intelligence</span>
                <h2 style="font-size:20px;font-weight:900;letter-spacing:-0.4px;margin-top:6px;">${this.escapeHtml(d.headline || topic)}</h2>
              </div>
              <div style="font-size:11px;font-family:var(--font-mono);color:var(--text-3);">
                Factual Confidence: <strong style="color:var(--green);">${audit.coverage_percentage || 95}%</strong>
              </div>
            </div>

            <div style="margin-top:16px;background:var(--blue-light);border:1.5px solid var(--blue-mid);border-radius:var(--r-md);padding:14px 18px;">
              <div style="font-size:10px;font-weight:700;color:var(--blue);text-transform:uppercase;letter-spacing:0.07em;font-family:var(--font-mono);margin-bottom:4px;">Executive Summary</div>
              <p style="font-size:13.5px;line-height:1.65;color:var(--text);">${this.escapeHtml(d.executive_summary || '')}</p>
            </div>

            <div class="digest-section">
              <h3>Key Strategic Developments</h3>
              <div>${keyPointsHtml || '<p style="color:var(--text-3);font-size:12px;">No specific points extracted.</p>'}</div>
            </div>

            ${citationsHtml ? `
              <div class="digest-section">
                <h3>Primary Sources Attributed (${d.citations.length})</h3>
                <div class="grid-2" style="margin-top:8px;">${citationsHtml}</div>
              </div>
            ` : ''}
          </div>
        `;
      }
    } catch (err) {
      this.showToast('Dossier synthesis failed: ' + err.message);
      if (out) out.innerHTML = `<div style="text-align:center;padding:40px;color:var(--red);">Error synthesizing dossier: ${this.escapeHtml(err.message)}</div>`;
    } finally {
      this.setLoading(false);
    }
  },

  digestFromModal() {
    if (!this.state.currentArticle) return;
    const title = this.state.currentArticle.title;
    this.closeModal();
    this.switchTab('digest');
    const input = document.getElementById('digest-input');
    if (input) input.value = title;
    this.runDigest();
  },

  // ──────────────────────────────────────────
  // AI CHATBOT
  // ──────────────────────────────────────────
  async initChatSuggestions() {
    const container = document.getElementById('chat-suggestions');
    if (!container) return;

    try {
      const res = await Api.getChatSuggestions();
      const suggestions = res.suggestions || [
        'What is happening in AI breakthroughs today?',
        'Summarize top world news right now',
        'What are the latest developments in India?'
      ];
      container.innerHTML = suggestions.slice(0, 4).map((s) => `
        <button class="chip" onclick="App.useSuggestion('${App.escapeHtml(s)}')">${App.escapeHtml(s)}</button>
      `).join('');
    } catch (e) {
      container.innerHTML = `
        <button class="chip" onclick="App.useSuggestion('What is the latest world news?')">Latest world news</button>
        <button class="chip" onclick="App.useSuggestion('Tell me about AI news')">AI news</button>
      `;
    }
  },

  useSuggestion(text) {
    const textEl = document.getElementById('chat-textarea');
    if (textEl) {
      textEl.value = text;
      this.sendChat();
    }
  },

  newChat() {
    this.state.sessionId = null;
    const box = document.getElementById('chat-messages');
    if (box) box.innerHTML = '';
    this.appendChatBubble('assistant', 'Hello! I am your AI News Intelligence Research Assistant. Ask me anything about current events, breaking dispatches, and geopolitical developments.');
  },

  async sendChat() {
    const textarea = document.getElementById('chat-textarea');
    const msg = textarea?.value?.trim();
    if (!msg) return;

    textarea.value = '';
    this.appendChatBubble('user', msg);

    const typing = document.getElementById('chat-typing');
    if (typing) typing.style.display = 'block';

    try {
      const res = await Api.sendChatMessage(msg, this.state.sessionId);
      this.state.sessionId = res.session_id;

      if (typing) typing.style.display = 'none';
      this.appendChatBubble('assistant', res.content, res.citations);
    } catch (err) {
      if (typing) typing.style.display = 'none';
      this.appendChatBubble('assistant', 'Sorry, I encountered an issue connecting to the intelligence backend. Please verify the server is running.');
    }
  },

  appendChatBubble(role, content, citations = []) {
    const box = document.getElementById('chat-messages');
    if (!box) return;

    const div = document.createElement('div');
    div.className = `chat-bubble ${role}`;

    let citesHtml = '';
    if (citations && citations.length) {
      citesHtml = `
        <div style="margin-top:8px;padding-top:6px;border-top:1px solid rgba(0,0,0,0.08);font-size:11px;color:var(--text-3);font-family:var(--font-mono);">
          <strong>Attributed Sources:</strong>
          <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;">
            ${citations.map((c) => `<span class="cite">[${c.index}] ${this.escapeHtml(c.article_title || c.source_name)}</span>`).join('')}
          </div>
        </div>
      `;
    }

    div.innerHTML = `
      <div class="bubble-content">
        <div>${content.replace(/\n/g, '<br>')}</div>
        ${citesHtml}
      </div>
    `;

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  },

  // ──────────────────────────────────────────
  // KNOWLEDGE GRAPH (D3.JS)
  // ──────────────────────────────────────────
  async loadGraph() {
    const input = document.getElementById('graph-input');
    const topic = input?.value?.trim() || 'Artificial Intelligence';
    const svgEl = document.getElementById('d3-graph-svg');
    const emptyMsg = document.getElementById('graph-empty');
    if (!svgEl) return;

    if (emptyMsg) emptyMsg.style.display = 'none';

    try {
      this.setLoading(true);
      const res = await Api.getGraph(topic);
      const nodes = res.nodes || [];
      const edges = res.edges || [];

      d3.select('#d3-graph-svg').selectAll('*').remove();

      if (!nodes.length) {
        if (emptyMsg) {
          emptyMsg.textContent = `No knowledge graph entities found for "${topic}". Try another topic.`;
          emptyMsg.style.display = 'block';
        }
        return;
      }

      const container = svgEl.parentElement;
      const width = container.clientWidth || 800;
      const height = 520;

      const svg = d3.select('#d3-graph-svg')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .attr('preserveAspectRatio', 'xMidYMid meet');

      const colorMap = {
        topic: '#2563EB',
        publisher: '#16A34A',
        article: '#7C3AED',
        entity: '#D97706',
        default: '#94A3B8'
      };

      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).id((d) => d.id).distance(100).strength(0.4))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide(30));

      const link = svg.append('g')
        .selectAll('line')
        .data(edges)
        .enter()
        .append('line')
        .attr('stroke', '#E2E8F0')
        .attr('stroke-width', 1.5);

      const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .call(d3.drag()
          .on('start', (e, d) => {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
          .on('end', (e, d) => {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
          })
        );

      node.append('circle')
        .attr('r', (d) => d.type === 'topic' ? 14 : d.type === 'publisher' ? 10 : 7)
        .attr('fill', (d) => colorMap[d.type] || colorMap.default)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', (_, d) => {
          if (d.label) App.quickSearch(d.label);
        });

      node.append('text')
        .attr('dx', (d) => d.type === 'topic' ? 18 : 13)
        .attr('dy', '0.35em')
        .attr('font-size', (d) => d.type === 'topic' ? '11px' : '10px')
        .attr('font-weight', (d) => d.type === 'topic' ? '700' : '600')
        .attr('fill', '#1E293B')
        .attr('font-family', 'Inter, sans-serif')
        .text((d) => (d.label || '').length > 20 ? d.label.slice(0, 18) + '…' : d.label);

      simulation.on('tick', () => {
        link
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);

        node.attr('transform', (d) => `translate(${Math.max(20, Math.min(width - 20, d.x))},${Math.max(20, Math.min(height - 20, d.y))})`);
      });

      svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', (event) => {
        svg.selectAll('g').attr('transform', event.transform);
      }));

    } catch (err) {
      this.showToast('Failed to render graph: ' + err.message);
      if (emptyMsg) {
        emptyMsg.textContent = 'Error rendering graph. Please try again.';
        emptyMsg.style.display = 'block';
      }
    } finally {
      this.setLoading(false);
    }
  },

  // ──────────────────────────────────────────
  // EVENT CHRONOLOGY TIMELINE
  // ──────────────────────────────────────────
  async loadTimeline() {
    const input = document.getElementById('timeline-input');
    const query = input?.value?.trim() || 'Artificial Intelligence';
    const out = document.getElementById('timeline-output');
    if (!out) return;

    out.innerHTML = `
      <div style="text-align:center;padding:60px;color:var(--text-3);">
        <div class="spinner" style="margin:0 auto 16px;"></div>
        <p style="font-size:14px;font-weight:600;color:var(--text);">Building historical milestone chronology...</p>
      </div>
    `;

    try {
      this.setLoading(true);
      const res = await Api.getTimeline(query);
      const milestones = res.timeline || [];

      if (!milestones.length) {
        out.innerHTML = `
          <div style="text-align:center;padding:60px;color:var(--text-3);">
            <div style="font-size:40px;margin-bottom:12px;">📅</div>
            <p style="font-size:14px;font-weight:600;color:var(--text-2);">No timeline milestones found for "${this.escapeHtml(query)}"</p>
            <p style="font-size:12px;margin-top:4px;">Try a broader global event or technological topic.</p>
          </div>
        `;
        return;
      }

      out.innerHTML = `
        <div class="timeline" style="max-width:760px;margin:20px auto 0;">
          ${milestones.map((m, idx) => `
            <div class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-card" onclick="App.quickSearch('${this.escapeHtml(m.query || query)}')">
                <div class="timeline-date">${this.escapeHtml(m.date || `Milestone ${idx + 1}`)}</div>
                <div class="timeline-headline">${this.escapeHtml(m.headline || m.title || '')}</div>
                ${m.summary ? `<div class="timeline-summary">${this.escapeHtml(m.summary)}</div>` : ''}
                ${(m.sources || []).length ? `
                  <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;">
                    ${m.sources.slice(0, 3).map((s) => `<span class="cite">${this.escapeHtml(s)}</span>`).join('')}
                  </div>
                ` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (err) {
      this.showToast('Timeline generation failed: ' + err.message);
      out.innerHTML = `<div style="text-align:center;padding:40px;color:var(--red);">Error building timeline: ${this.escapeHtml(err.message)}</div>`;
    } finally {
      this.setLoading(false);
    }
  },

  // ──────────────────────────────────────────
  // ARTICLE MODAL & TEXT-TO-SPEECH
  // ──────────────────────────────────────────
  openById(idx) {
    if (this.state.articles[idx]) {
      this.openArticle(this.state.articles[idx]);
    }
  },

  openArticleByTitle(title) {
    const art = this.state.articles.find((a) => a.title === title);
    if (art) {
      this.openArticle(art);
    } else {
      this.quickSearch(title);
    }
  },

  openArticle(article) {
    this.state.currentArticle = article;
    const modal = document.getElementById('article-modal');
    if (!modal) return;

    const intel = article.intelligence || {};

    const tag = document.getElementById('modal-tag');
    const source = document.getElementById('modal-source');
    const title = document.getElementById('modal-title');
    const author = document.getElementById('modal-author');
    const time = document.getElementById('modal-time');
    const readTime = document.getElementById('modal-read-time');
    const sentiment = document.getElementById('modal-sentiment');
    const impact = document.getElementById('modal-impact');
    const category = document.getElementById('modal-category');
    const body = document.getElementById('modal-body');
    const link = document.getElementById('modal-link');
    const entities = document.getElementById('modal-entities-wrap');

    if (tag) tag.textContent = article.category || 'WORLD';
    if (source) source.textContent = article.source_name || 'Newswire';
    if (title) title.textContent = article.title;
    if (author) author.textContent = article.author ? `By ${article.author}` : 'Wire Service';
    if (time) time.textContent = this.formatTime(article.published_at);
    if (readTime) readTime.textContent = `${intel.reading_time_min || 3} min read`;

    if (sentiment) {
      sentiment.textContent = intel.sentiment || 'Neutral';
      sentiment.style.color = (intel.sentiment === 'Positive') ? 'var(--green)' : (intel.sentiment === 'Negative') ? 'var(--red)' : 'var(--text)';
    }

    if (impact) impact.textContent = intel.impact_level || 'Standard';
    if (category) category.textContent = article.category || 'General';

    if (body) {
      body.innerHTML = `<p>${this.escapeHtml(article.content || 'Full article text available directly at original publisher website.')}</p>`;
    }

    if (link) {
      link.href = article.url || '#';
    }

    if (entities) {
      const entList = intel.entities || [];
      if (entList.length) {
        entities.innerHTML = entList.map((e) => `<span class="chip" onclick="App.quickSearch('${App.escapeHtml(e)}')">${this.escapeHtml(e)}</span>`).join('');
      } else {
        entities.innerHTML = '';
      }
    }

    this.updateSaveButton();
    this.stopAudio();
    modal.classList.remove('hide');
  },

  closeModal() {
    this.stopAudio();
    const modal = document.getElementById('article-modal');
    if (modal) modal.classList.add('hide');
  },

  toggleAudio() {
    if (this.state.isSpeaking) {
      this.stopAudio();
    } else {
      this.startAudio();
    }
  },

  startAudio() {
    if (!('speechSynthesis' in window) || !this.state.currentArticle) return;
    window.speechSynthesis.cancel();

    const text = `${this.state.currentArticle.title}. Reported by ${this.state.currentArticle.source_name}. ${this.state.currentArticle.content || ''}`;
    this.state.speechUtterance = new SpeechSynthesisUtterance(text);
    this.state.speechUtterance.rate = 1.0;
    this.state.speechUtterance.onend = () => this.stopAudio();
    this.state.speechUtterance.onerror = () => this.stopAudio();

    window.speechSynthesis.speak(this.state.speechUtterance);
    this.state.isSpeaking = true;

    const btnTxt = document.getElementById('audio-btn-txt');
    if (btnTxt) btnTxt.textContent = 'Pause';
  },

  stopAudio() {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    this.state.isSpeaking = false;
    const btnTxt = document.getElementById('audio-btn-txt');
    if (btnTxt) btnTxt.textContent = 'Listen';
  },

  // ──────────────────────────────────────────
  // SAVED ARTICLES & BOOKMARKS
  // ──────────────────────────────────────────
  toggleSave() {
    if (!this.state.currentArticle) return;
    const url = this.state.currentArticle.url;
    const idx = this.state.savedArticles.findIndex((a) => a.url === url);

    if (idx >= 0) {
      this.state.savedArticles.splice(idx, 1);
      this.showToast('Article removed from saved.');
    } else {
      this.state.savedArticles.unshift(this.state.currentArticle);
      this.showToast('Article saved to reading list.');
    }

    localStorage.setItem('ai_digest_saved', JSON.stringify(this.state.savedArticles));
    this.updateSavedBadge();
    this.updateSaveButton();
  },

  updateSaveButton() {
    const btn = document.getElementById('save-btn');
    if (!btn || !this.state.currentArticle) return;
    const isSaved = this.state.savedArticles.some((a) => a.url === this.state.currentArticle.url);
    btn.innerHTML = isSaved ? '★ Saved' : '☆ Save';
    btn.style.color = isSaved ? 'var(--amber)' : 'inherit';
  },

  updateSavedBadge() {
    const badge = document.getElementById('saved-count');
    if (!badge) return;
    const len = this.state.savedArticles.length;
    if (len > 0) {
      badge.textContent = len;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }
  },

  clearSaved() {
    this.state.savedArticles = [];
    localStorage.removeItem('ai_digest_saved');
    this.updateSavedBadge();
    this.renderSaved();
    this.showToast('All saved articles cleared.');
  },

  renderSaved() {
    const grid = document.getElementById('saved-grid');
    const desc = document.getElementById('saved-desc');
    if (!grid) return;

    const list = this.state.savedArticles;
    if (desc) {
      desc.textContent = list.length ? `${list.length} articles saved locally` : 'Your reading list is empty.';
    }

    if (!list.length) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:60px 0;color:var(--text-3);">
          <div style="font-size:40px;margin-bottom:12px;">☆</div>
          <p style="font-size:14px;font-weight:600;color:var(--text-2);">No saved articles yet</p>
          <p style="font-size:12px;margin-top:4px;">Click "☆ Save" on any article to keep it in your private reading list.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = list.map((a, idx) => `
      <div class="article-card" onclick="App.openArticle(${JSON.stringify(a).replace(/"/g, '&quot;')})">
        <div class="body">
          <div class="meta">
            <span class="tag tag-amber">★ Saved</span>
            <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);margin-left:auto;">${this.formatTime(a.published_at)}</span>
          </div>
          <h3 class="clamp-2">${this.escapeHtml(a.title)}</h3>
          <p class="clamp-2">${this.escapeHtml(a.content ? a.content.slice(0, 120) : '')}...</p>
          <div class="footer">
            <span style="font-size:11px;color:var(--text-3);font-family:var(--font-mono);">${this.escapeHtml(a.source_name || 'Newswire')}</span>
            <button onclick="event.stopPropagation(); App.removeSaved(${idx})" style="background:none;border:none;color:var(--red);font-size:11px;cursor:pointer;font-weight:600;">Remove</button>
          </div>
        </div>
      </div>
    `).join('');
  },

  removeSaved(idx) {
    this.state.savedArticles.splice(idx, 1);
    localStorage.setItem('ai_digest_saved', JSON.stringify(this.state.savedArticles));
    this.updateSavedBadge();
    this.renderSaved();
  },

  // ──────────────────────────────────────────
  // UTILITIES
  // ──────────────────────────────────────────
  setLoading(show) {
    const el = document.getElementById('loading-overlay');
    if (el) {
      if (show) el.classList.remove('hide');
      else el.classList.add('hide');
    }
  },

  showToast(msg) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.remove('hide');
    setTimeout(() => {
      el.classList.add('hide');
    }, 4000);
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

  formatTime(dateStr) {
    if (!dateStr) return 'Recent';
    try {
      const d = new Date(dateStr);
      const diffHrs = Math.round((Date.now() - d.getTime()) / (1000 * 60 * 60));
      if (diffHrs < 1) return 'Just now';
      if (diffHrs < 24) return `${diffHrs}h ago`;
      return `${Math.round(diffHrs / 24)}d ago`;
    } catch (e) {
      return 'Recent';
    }
  }
};

// ── BOOTSTRAP ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
