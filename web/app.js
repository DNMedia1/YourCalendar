const state = {
  sample: true,
  categories: [],
  qualityLegend: [],
  sportsCoverage: { europeSports: [], globalCombatSports: [], championships: [] },
  sourcePlan: { total: 0, active: 0, needsWork: 0, items: [] },
  sourceMonitor: { total: 0, watching: 0, planned: 0, items: [] },
  sourceHealth: {
    status: "sample",
    label: "Sample",
    title: "Sample-Daten aktiv",
    detail: "Sample-Modus nutzt Testdaten.",
    hints: [],
  },
  selectedCoverageId: "football",
  selectedCategoryId: "sports",
  events: [],
  sourceCandidates: [],
  favorites: JSON.parse(localStorage.getItem("yourcalendar:favorites") || "[]"),
  theme: localStorage.getItem("yourcalendar:theme") || "system",
};

const $ = (id) => document.getElementById(id);

const elements = {
  liveMode: $("liveMode"),
  sampleMode: $("sampleMode"),
  refreshButton: $("refreshButton"),
  themeToggle: $("themeToggle"),
  appleButton: $("appleButton"),
  copyFeedButton: $("copyFeedButton"),
  downloadLink: $("downloadLink"),
  feedUrl: $("feedUrl"),
  catalogStatus: $("catalogStatus"),
  qualityLegend: $("qualityLegend"),
  sportsCoverage: $("sportsCoverage"),
  coverageDetail: $("coverageDetail"),
  sourcePlanStatus: $("sourcePlanStatus"),
  sourcePlan: $("sourcePlan"),
  sourceMonitorStatus: $("sourceMonitorStatus"),
  sourceMonitor: $("sourceMonitor"),
  categoryTabs: $("categoryTabs"),
  calendarCatalog: $("calendarCatalog"),
  teamSearch: $("teamSearch"),
  includePast: $("includePast"),
  eventList: $("eventList"),
  eventCount: $("eventCount"),
  favoriteCount: $("favoriteCount"),
  favorites: $("favorites"),
  sourceStatus: $("sourceStatus"),
  sourceNote: $("sourceNote"),
  modeBadge: $("modeBadge"),
  refreshMonitoring: $("refreshMonitoring"),
  monitoringList: $("monitoringList"),
  sourceCandidateFilter: $("sourceCandidateFilter"),
  includeRiskySources: $("includeRiskySources"),
  sourceCandidateCount: $("sourceCandidateCount"),
  sourceCandidateList: $("sourceCandidateList"),
};

const systemDark = window.matchMedia("(prefers-color-scheme: dark)");

function selectedLeagues() {
  return [...document.querySelectorAll(".league:checked")].map((input) => input.value);
}

function saveFavorites() {
  localStorage.setItem("yourcalendar:favorites", JSON.stringify(state.favorites));
  renderFavorites();
}

function setMode(sample) {
  state.sample = sample;
  elements.sampleMode.classList.toggle("active", sample);
  elements.liveMode.classList.toggle("active", !sample);
  elements.sampleMode.setAttribute("aria-pressed", String(sample));
  elements.liveMode.setAttribute("aria-pressed", String(!sample));
  loadEvents();
}

function effectiveTheme() {
  if (state.theme === "system") return systemDark.matches ? "dark" : "light";
  return state.theme;
}

function applyTheme(withTransition = false) {
  const theme = effectiveTheme();
  if (withTransition) {
    document.documentElement.classList.add("theme-transition");
    window.setTimeout(() => document.documentElement.classList.remove("theme-transition"), 260);
  }
  document.documentElement.dataset.theme = theme;
  const isDark = theme === "dark";
  elements.themeToggle.setAttribute("aria-pressed", String(isDark));
  elements.themeToggle.setAttribute("aria-label", isDark ? "Light Mode aktivieren" : "Dark Mode aktivieren");
  elements.themeToggle.querySelector(".theme-toggle-label").textContent = isDark ? "Light" : "Dark";
}

function toggleTheme() {
  state.theme = effectiveTheme() === "dark" ? "light" : "dark";
  localStorage.setItem("yourcalendar:theme", state.theme);
  applyTheme(true);
}

function params() {
  const query = new URLSearchParams();
  query.set("sample", String(state.sample));
  query.set("leagues", selectedLeagues().join(","));
  query.set("team", elements.teamSearch.value.trim());
  query.set("favorites", state.favorites.join(","));
  query.set("includePast", String(elements.includePast.checked));
  return query;
}

async function loadEvents() {
  setBusy(true);
  setEventListBusy(true);
  try {
    const response = await fetch(`/api/events?${params().toString()}`);
    const payload = await response.json();
    if (!payload.ok) {
      state.events = [];
      applySourceHealth(payload.sourceHealth, "Quelle gestört");
      updateFeedLinks();
      renderEvents();
      throw new Error(payload.error || payload.sourceNote || "Unbekannter Fehler");
    }
    state.events = payload.events;
    applySourceHealth(payload.sourceHealth, payload.mode === "sample" ? "Sample" : "OpenLigaDB");
    updateFeedLinks(payload);
    renderEvents();
  } catch (error) {
    if (!state.events.length && state.sourceHealth.status !== "error") {
      state.events = [];
      applySourceHealth({
        status: "error",
        label: "Quelle gestört",
        title: "Abruf fehlgeschlagen",
        detail: "Die Quelle konnte gerade nicht gelesen werden.",
        hints: ["Netzwerk und lokalen Server prüfen."],
      });
    }
    updateFeedLinks();
    renderEvents();
    toast(error.message, true);
  } finally {
    setEventListBusy(false);
    setBusy(false);
  }
}

async function loadMonitoring() {
  if (!elements.monitoringList) return;
  elements.refreshMonitoring.disabled = true;
  try {
    const response = await fetch("/api/import-status");
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Monitoring konnte nicht geladen werden.");
    renderMonitoring(payload.sources || []);
  } catch (error) {
    elements.monitoringList.innerHTML = `<div class="empty-small" role="status">Monitoring nicht verfügbar.</div>`;
    toast(error.message, true);
  } finally {
    elements.refreshMonitoring.disabled = false;
  }
}

async function loadCalendars() {
  if (!elements.calendarCatalog) return;
  elements.catalogStatus.textContent = "Lädt";
  elements.sourcePlanStatus.textContent = "Lädt";
  elements.sourceMonitorStatus.textContent = "Lädt";
  try {
    const response = await fetch("/api/calendars");
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Kalenderkatalog konnte nicht geladen werden.");

    state.categories = Array.isArray(payload.categories) ? payload.categories : [];
    state.qualityLegend = Array.isArray(payload.qualityLegend) ? payload.qualityLegend : [];
    state.sportsCoverage = payload.sportsCoverage || { europeSports: [], globalCombatSports: [], championships: [] };
    state.sourcePlan = payload.sourcePlan || { total: 0, active: 0, needsWork: 0, items: [] };
    state.sourceMonitor = payload.sourceMonitor || { total: 0, watching: 0, planned: 0, items: [] };

    if (!state.categories.some((category) => category.id === state.selectedCategoryId)) {
      state.selectedCategoryId = state.categories[0]?.id || "";
    }
    if (!coverageOptionById(state.selectedCoverageId)) {
      state.selectedCoverageId = allCoverageOptions()[0]?.id || "";
    }

    renderCalendarDiscovery();
    const calendarCount = state.categories.reduce((total, category) => total + (category.calendars || []).length, 0);
    elements.catalogStatus.textContent = `${calendarCount} Kalender`;
    elements.sourcePlanStatus.textContent = `${state.sourcePlan.active || 0} aktiv · ${state.sourcePlan.needsWork || 0} offen`;
    elements.sourceMonitorStatus.textContent = `${state.sourceMonitor.watching || 0} beobachtet · ${state.sourceMonitor.planned || 0} geplant`;
  } catch (error) {
    state.categories = [];
    renderCalendarDiscovery();
    elements.catalogStatus.textContent = "Fehler";
    elements.sourcePlanStatus.textContent = "Nicht verfügbar";
    elements.sourceMonitorStatus.textContent = "Nicht verfügbar";
    elements.calendarCatalog.innerHTML = `<div class="catalog-empty" role="status"><p>Kalenderkatalog nicht verfügbar.</p></div>`;
    toast(error.message, true);
  }
}

async function loadSourceCandidates() {
  if (!elements.sourceCandidateList) return;
  elements.sourceCandidateList.innerHTML = `<div class="empty-small">API-Kandidaten werden geladen.</div>`;
  try {
    const query = new URLSearchParams({
      includeRisky: String(elements.includeRiskySources.checked),
    });
    const response = await fetch(`/api/source-candidates?${query.toString()}`);
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "API-Kandidaten konnten nicht geladen werden.");
    state.sourceCandidates = payload.candidates || [];
    renderSourceCandidates();
  } catch (error) {
    state.sourceCandidates = [];
    elements.sourceCandidateCount.textContent = "0";
    elements.sourceCandidateList.innerHTML = `<div class="empty-state">API-Kandidaten nicht verfügbar.</div>`;
    toast(error.message, true);
  }
}

function setBusy(isBusy) {
  elements.refreshButton.disabled = isBusy;
  elements.appleButton.disabled = isBusy;
  elements.copyFeedButton.disabled = isBusy;
}

function setEventListBusy(isBusy) {
  elements.eventList.setAttribute("aria-busy", String(isBusy));
}

function updateFeedLinks(payload = null) {
  const fallback = `/feeds/current.ics?${params().toString()}`;
  const feedUrl = payload?.feedUrl || fallback;
  const subscribeUrl = payload?.subscribeUrl || new URL(feedUrl, window.location.origin).toString();
  elements.downloadLink.href = feedUrl;
  elements.feedUrl.value = subscribeUrl;
}

function applySourceHealth(sourceHealth = null, fallbackLabel = "Bereit") {
  const health = sourceHealth || {
    status: "unknown",
    label: fallbackLabel,
    title: fallbackLabel,
    detail: "Noch kein Quellenstatus verfügbar.",
    hints: [],
  };
  state.sourceHealth = health;
  elements.sourceStatus.textContent = health.label || fallbackLabel;
  elements.sourceStatus.dataset.status = health.status || "unknown";
  elements.sourceNote.textContent = health.detail || "";
  elements.modeBadge.textContent = health.label || fallbackLabel;
  elements.modeBadge.dataset.status = health.status || "unknown";
}

function renderCalendarDiscovery() {
  renderQualityLegend();
  renderSportsCoverage();
  renderCoverageDetail();
  renderSourcePlan();
  renderSourceMonitor();
  renderCategoryTabs();
  renderCalendarCatalog();
}

function renderQualityLegend() {
  if (!elements.qualityLegend) return;
  if (!state.qualityLegend.length) {
    elements.qualityLegend.innerHTML = `<div class="empty-small" role="status">Keine Qualitätsstufen geladen.</div>`;
    return;
  }

  elements.qualityLegend.innerHTML = state.qualityLegend.map((item) => `
    <div class="legend-item">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.description)}</span>
    </div>
  `).join("");
}

function coverageGroups() {
  return [
    ["Europäische Sportarten", state.sportsCoverage.europeSports || []],
    ["Kampfsport weltweit", state.sportsCoverage.globalCombatSports || []],
    ["WM & EM", state.sportsCoverage.championships || []],
  ];
}

function allCoverageOptions() {
  return coverageGroups().flatMap(([, options]) => options);
}

function coverageOptionById(id) {
  return allCoverageOptions().find((option) => option.id === id);
}

function renderSportsCoverage() {
  if (!elements.sportsCoverage) return;
  const groups = coverageGroups().filter(([, options]) => options.length);
  if (!groups.length) {
    elements.sportsCoverage.innerHTML = `<div class="empty-small" role="status">Keine Sportarten geladen.</div>`;
    return;
  }

  elements.sportsCoverage.innerHTML = groups.map(([label, options]) => `
    <div class="coverage-group">
      <strong>${escapeHtml(label)}</strong>
      <div class="coverage-options">
        ${options.map((option) => `
          <button class="coverage-chip${option.id === state.selectedCoverageId ? " active" : ""}" type="button" data-coverage-id="${escapeAttribute(option.id)}" aria-pressed="${option.id === state.selectedCoverageId}">
            ${escapeHtml(option.name)}
          </button>
        `).join("")}
      </div>
    </div>
  `).join("");

  document.querySelectorAll(".coverage-chip").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCoverageId = button.dataset.coverageId;
      renderSportsCoverage();
      renderCoverageDetail();
    });
  });
}

function renderCoverageDetail() {
  if (!elements.coverageDetail) return;
  const option = coverageOptionById(state.selectedCoverageId);
  if (!option) {
    elements.coverageDetail.innerHTML = `<p role="status">Keine Sportart ausgewählt.</p>`;
    return;
  }

  elements.coverageDetail.innerHTML = `
    <div>
      <span>${escapeHtml(option.scope)} · ${escapeHtml(option.group)}</span>
      <strong>${escapeHtml(option.name)}</strong>
    </div>
    <p>${escapeHtml(option.description)}</p>
    <em>${escapeHtml(option.statusLabel)} · ${escapeHtml(option.sourceNote)}</em>
  `;
}

function renderSourcePlan() {
  if (!elements.sourcePlan) return;
  const items = state.sourcePlan.items || [];
  if (!items.length) {
    elements.sourcePlan.innerHTML = `<div class="empty-small" role="status">Keine Provider-Pläne geladen.</div>`;
    return;
  }

  elements.sourcePlan.innerHTML = items.map((item) => `
    <article class="source-plan-card">
      <div class="source-plan-card-head">
        <div>
          <span>${escapeHtml(item.priority)} · ${escapeHtml(item.scope)}</span>
          <strong>${escapeHtml(item.title)}</strong>
        </div>
        <em class="${escapeAttribute(item.status)}">${escapeHtml(item.statusLabel)}</em>
      </div>
      <p>${escapeHtml(item.summary)}</p>
      <div class="source-plan-columns">
        <div>
          <span>Nächste Schritte</span>
          <ul>${renderListItems(item.nextSteps, "Noch nicht definiert.")}</ul>
        </div>
        <div>
          <span>Blocker</span>
          <ul>${renderListItems(item.blockers, "Keine Blocker erfasst.")}</ul>
        </div>
      </div>
    </article>
  `).join("");
}

function renderSourceMonitor() {
  if (!elements.sourceMonitor) return;
  const items = state.sourceMonitor.items || [];
  if (!items.length) {
    elements.sourceMonitor.innerHTML = `<div class="empty-small" role="status">Keine Quellenüberwachung geladen.</div>`;
    return;
  }

  elements.sourceMonitor.innerHTML = items.map((item) => {
    const lastRun = item.lastRun || {};
    return `
      <article class="source-monitor-card">
        <div class="source-monitor-card-head">
          <div>
            <span>${escapeHtml(item.scope)}</span>
            <strong>${escapeHtml(item.sourceLabel)}</strong>
          </div>
          <em class="${escapeAttribute(item.status)}">${escapeHtml(item.statusLabel)}</em>
        </div>
        <p>${escapeHtml(item.message)}</p>
        <dl>
          <div>
            <dt>Modus</dt>
            <dd>${escapeHtml(item.lastCheckedMode)}</dd>
          </div>
          <div>
            <dt>Events</dt>
            <dd>${escapeHtml(lastRun.eventCount ?? item.eventCountLabel)}</dd>
          </div>
        </dl>
        <small>${escapeHtml(lastRun.message || item.nextAction)}</small>
      </article>
    `;
  }).join("");
}

function renderListItems(items = [], emptyText) {
  const itemsToRender = items.slice(0, 3);
  if (!itemsToRender.length) return `<li>${escapeHtml(emptyText)}</li>`;
  return itemsToRender.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderCategoryTabs() {
  if (!elements.categoryTabs) return;
  if (!state.categories.length) {
    elements.categoryTabs.innerHTML = "";
    return;
  }

  elements.categoryTabs.innerHTML = state.categories.map((category) => `
    <button class="category-tab${category.id === state.selectedCategoryId ? " active" : ""}" type="button" role="tab" data-category-id="${escapeAttribute(category.id)}" aria-selected="${category.id === state.selectedCategoryId}">
      ${escapeHtml(category.name)} <strong>${category.calendarCount || 0}</strong>
    </button>
  `).join("");

  document.querySelectorAll(".category-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCategoryId = button.dataset.categoryId;
      renderCategoryTabs();
      renderCalendarCatalog();
    });
  });
}

function renderCalendarCatalog() {
  if (!elements.calendarCatalog) return;
  const category = state.categories.find((item) => item.id === state.selectedCategoryId);
  if (!category) {
    elements.calendarCatalog.innerHTML = `<div class="catalog-empty" role="status"><p>Keine Kalenderkategorie geladen.</p></div>`;
    return;
  }
  const calendars = category.calendars || [];
  if (!calendars.length) {
    elements.calendarCatalog.innerHTML = `
      <div class="catalog-empty" role="status">
        <span>${escapeHtml(category.name)}</span>
        <p>${escapeHtml(category.description)} Für diese Kategorie ist noch kein abonnierbarer Feed veröffentlicht.</p>
      </div>
    `;
    return;
  }

  elements.calendarCatalog.innerHTML = calendars.map((calendar) => `
    <article class="calendar-card">
      <div class="calendar-card-main">
        <div>
          <span class="calendar-category">${escapeHtml(category.name)}</span>
          <h4>${escapeHtml(calendar.name)}</h4>
        </div>
        <span class="status-pill ${escapeAttribute(calendar.quality?.level || calendar.status)}">${escapeHtml(calendar.statusLabel)}</span>
      </div>
      <p>${escapeHtml(calendar.description)}</p>
      <div class="source-row">
        <span>Quelle</span>
        <strong>${escapeHtml(calendar.sourceLabel)}</strong>
      </div>
      <div class="quality-grid">
        <div>
          <span>Qualität</span>
          <strong>${escapeHtml(calendar.quality?.label)}</strong>
          <small>${escapeHtml(calendar.quality?.reliabilityNote)}</small>
        </div>
        <div>
          <span>Aktualisierung</span>
          <strong>${escapeHtml(calendar.quality?.updatedLabel)}</strong>
          <small>${escapeHtml(calendar.quality?.updatePolicy)}</small>
        </div>
      </div>
      <ul class="quality-notes">${renderListItems(calendar.quality?.warnings, "Keine Warnhinweise erfasst.")}</ul>
      <div class="calendar-actions">
        ${calendar.hasFeed ? `
          <a class="button secondary" href="${escapeAttribute(calendar.feedUrl)}">ICS laden</a>
          <button class="button primary copy-calendar" type="button" data-subscribe-url="${escapeAttribute(calendar.subscribeUrl)}">Abo-Link kopieren</button>
        ` : `<span class="action-note">Noch kein abonnierbarer Feed.</span>`}
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".copy-calendar").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.subscribeUrl, "Abo-Link kopiert."));
  });
}

function renderSourceCandidates() {
  const searchTerm = elements.sourceCandidateFilter.value.trim().toLowerCase();
  const candidates = state.sourceCandidates.filter((candidate) => {
    if (!searchTerm) return true;
    return [
      candidate.name,
      candidate.coverage,
      candidate.endpointType,
      candidate.license,
      candidate.usageDecision,
      ...(candidate.sports || []),
    ].join(" ").toLowerCase().includes(searchTerm);
  });

  elements.sourceCandidateCount.textContent = String(candidates.length);
  if (!candidates.length) {
    elements.sourceCandidateList.innerHTML = `<div class="empty-state">Keine passenden API-Kandidaten.</div>`;
    return;
  }

  elements.sourceCandidateList.innerHTML = candidates.map((candidate) => {
    const sourceUrl = candidate.repoUrl || candidate.docsUrl || candidate.baseUrl || "";
    const links = [
      candidate.repoUrl ? `<a href="${escapeAttribute(candidate.repoUrl)}" target="_blank" rel="noopener noreferrer">Repo</a>` : "",
      candidate.docsUrl ? `<a href="${escapeAttribute(candidate.docsUrl)}" target="_blank" rel="noopener noreferrer">Docs</a>` : "",
      candidate.baseUrl ? `<a href="${escapeAttribute(candidate.baseUrl)}" target="_blank" rel="noopener noreferrer">API</a>` : "",
    ].filter(Boolean).join("");
    const sports = (candidate.sports || []).slice(0, 6).map((sport) => `
      <span class="source-sport">${escapeHtml(sport)}</span>
    `).join("");
    const extraSports = (candidate.sports || []).length > 6
      ? `<span class="source-sport">+${candidate.sports.length - 6}</span>`
      : "";

    return `
      <article class="source-candidate-card" data-risk="${escapeAttribute(candidate.riskLevel)}">
        <div class="source-candidate-main">
          <div>
            <strong>${escapeHtml(candidate.name)}</strong>
            <p>${escapeHtml(candidate.coverage)}</p>
          </div>
          <span class="risk-pill" data-risk="${escapeAttribute(candidate.riskLevel)}">${escapeHtml(riskLabel(candidate.riskLevel))}</span>
        </div>
        <div class="source-sports">${sports}${extraSports}</div>
        <div class="source-candidate-meta">
          <span>${escapeHtml(candidate.endpointType)}</span>
          <span>${candidate.supportsLiveEvents ? "Live-fähig" : "Dataset/Recherche"}</span>
          <span>${candidate.requiresApiKey ? "API-Key" : "Kein Key"}</span>
        </div>
        <p class="source-license">${escapeHtml(candidate.license)}</p>
        <div class="source-links" aria-label="${escapeAttribute(candidate.name)} Links">${links || `<span>${escapeHtml(sourceUrl)}</span>`}</div>
      </article>
    `;
  }).join("");
}

function riskLabel(risk) {
  const labels = {
    low: "niedrig",
    medium: "prüfen",
    high: "hoch",
  };
  return labels[risk] || "unklar";
}

function renderEvents() {
  elements.eventCount.textContent = String(state.events.length);

  if (!state.events.length) {
    elements.eventList.innerHTML = `<div class="empty-state" role="status">Keine Spiele für diese Filter.</div>`;
    return;
  }

  const visibleEvents = state.events.slice(0, 200);
  const limitNote = state.events.length > visibleEvents.length
    ? `<div class="list-note" role="status">Es werden 200 von ${state.events.length} Spielen angezeigt. Die ICS-Datei enthält alle gefilterten Spiele.</div>`
    : "";

  elements.eventList.innerHTML = visibleEvents.map((event) => {
    const homeFav = state.favorites.includes(event.homeTeam);
    const awayFav = state.favorites.includes(event.awayTeam);
    const leagueLabel = String(event.league || "sample").toUpperCase();
    return `
      <article class="event-card" tabindex="0" aria-label="${escapeAttribute(event.title)}">
        <div class="date-block">
          <strong>${escapeHtml(event.dateLabel)}</strong>
          <span>${escapeHtml(event.timeLabel)}</span>
        </div>
        <div class="event-main">
          <strong>${escapeHtml(event.title)}</strong>
          <div class="event-meta">${escapeHtml(event.leagueName)}${event.location ? ` · ${escapeHtml(event.location)}` : ""}</div>
        </div>
        <div class="event-actions">
          <button class="star-button${homeFav ? " is-active" : ""}" type="button" data-team="${escapeAttribute(event.homeTeam)}" aria-pressed="${homeFav}" aria-label="${homeFav ? "Heimteam aus Favoriten entfernen" : "Heimteam favorisieren"}">${homeFav ? "★" : "☆"}</button>
          <button class="star-button${awayFav ? " is-active" : ""}" type="button" data-team="${escapeAttribute(event.awayTeam)}" aria-pressed="${awayFav}" aria-label="${awayFav ? "Auswärtsteam aus Favoriten entfernen" : "Auswärtsteam favorisieren"}">${awayFav ? "★" : "☆"}</button>
          <span class="tag" data-league="${escapeAttribute(event.league)}">${escapeHtml(leagueLabel)}</span>
        </div>
      </article>
    `;
  }).join("") + limitNote;

  document.querySelectorAll(".star-button").forEach((button) => {
    button.addEventListener("click", () => toggleFavorite(button.dataset.team));
  });
}

function renderFavorites() {
  elements.favoriteCount.textContent = String(state.favorites.length);
  if (!state.favorites.length) {
    elements.favorites.innerHTML = `<span class="empty-small" role="status">Noch keine Favoriten</span>`;
    return;
  }
  elements.favorites.innerHTML = state.favorites.map((team) => `
    <button class="favorite-pill" type="button" data-team="${escapeAttribute(team)}" aria-label="${escapeAttribute(team)} aus Favoriten entfernen">${escapeHtml(team)} ×</button>
  `).join("");
  document.querySelectorAll(".favorite-pill").forEach((button) => {
    button.addEventListener("click", () => toggleFavorite(button.dataset.team));
  });
}

function renderMonitoring(sources) {
  if (!sources.length) {
    elements.monitoringList.innerHTML = `<div class="empty-small" role="status">Noch keine Importläufe.</div>`;
    return;
  }

  elements.monitoringList.innerHTML = sources.map((source) => {
    const status = String(source.status || "unknown");
    const label = statusLabel(status);
    const eventText = source.eventCount === null || source.eventCount === undefined
      ? "keine Events"
      : `${source.eventCount} Events`;
    const finished = source.finishedAt ? formatDateTime(source.finishedAt) : "noch nie";
    const detail = source.error || (source.warnings || []).join(" ") || eventText;
    return `
      <article class="monitoring-item" data-status="${escapeAttribute(status)}">
        <div>
          <strong>${escapeHtml(source.name || source.feedId)}</strong>
          <span>${escapeHtml(finished)} · ${escapeHtml(eventText)}</span>
        </div>
        <div class="status-pill" data-status="${escapeAttribute(status)}">${escapeHtml(label)}</div>
        <p>${escapeHtml(detail)}</p>
      </article>
    `;
  }).join("");
}

function statusLabel(status) {
  const labels = {
    success: "OK",
    warning: "Warnung",
    error: "Fehler",
    never_run: "Neu",
  };
  return labels[status] || "Unklar";
}

function formatDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function toggleFavorite(team) {
  if (!team) return;
  if (state.favorites.includes(team)) {
    state.favorites = state.favorites.filter((favorite) => favorite !== team);
  } else {
    state.favorites = [...state.favorites, team].sort();
  }
  saveFavorites();
  loadEvents();
}

function escapeAttribute(value) {
  return String(value || "").replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function openAppleCalendar() {
  try {
    const response = await fetch(`/api/open-apple?${params().toString()}`);
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Apple Kalender konnte nicht geöffnet werden.");
    toast("Apple Kalender wurde geöffnet.");
  } catch (error) {
    toast(error.message, true);
  }
}

async function copyFeedLink() {
  copyText(elements.feedUrl.value, "Feed-Link kopiert.");
}

async function copyText(value, successMessage) {
  try {
    await navigator.clipboard.writeText(value);
    toast(successMessage);
  } catch (error) {
    if (value === elements.feedUrl.value) {
      elements.feedUrl.select();
      toast("Link ist markiert und kann kopiert werden.");
      return;
    }
    toast("Link konnte nicht automatisch kopiert werden.", true);
  }
}

function toast(message, isError = false) {
  const node = document.createElement("div");
  node.className = `toast${isError ? " error" : ""}`;
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 3600);
}

elements.liveMode.addEventListener("click", () => setMode(false));
elements.sampleMode.addEventListener("click", () => setMode(true));
elements.refreshButton.addEventListener("click", loadEvents);
elements.refreshMonitoring.addEventListener("click", loadMonitoring);
elements.themeToggle.addEventListener("click", toggleTheme);
elements.appleButton.addEventListener("click", openAppleCalendar);
elements.copyFeedButton.addEventListener("click", copyFeedLink);
elements.sourceCandidateFilter.addEventListener("input", renderSourceCandidates);
elements.includeRiskySources.addEventListener("change", loadSourceCandidates);
elements.teamSearch.addEventListener("input", () => {
  window.clearTimeout(elements.teamSearch._timer);
  elements.teamSearch._timer = window.setTimeout(loadEvents, 250);
});
elements.includePast.addEventListener("change", loadEvents);
document.querySelectorAll(".league").forEach((input) => input.addEventListener("change", loadEvents));
$("clearFavorites").addEventListener("click", () => {
  state.favorites = [];
  saveFavorites();
  loadEvents();
});
systemDark.addEventListener("change", () => {
  if (state.theme === "system") applyTheme(true);
});

applyTheme();
renderFavorites();
updateFeedLinks();
loadCalendars();
loadEvents();
loadMonitoring();
loadSourceCandidates();
