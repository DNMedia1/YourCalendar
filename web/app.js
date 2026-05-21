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
  favorites: JSON.parse(localStorage.getItem("yourcalendar:favorites") || "[]"),
};

const $ = (id) => document.getElementById(id);

const elements = {
  liveMode: $("liveMode"),
  sampleMode: $("sampleMode"),
  refreshButton: $("refreshButton"),
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
};

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
  loadEvents();
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
    setBusy(false);
  }
}

function setBusy(isBusy) {
  elements.refreshButton.disabled = isBusy;
  elements.appleButton.disabled = isBusy;
  elements.copyFeedButton.disabled = isBusy;
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
  updateMonitorObservation(health.monitorObservation);
  elements.sourceStatus.textContent = health.label || fallbackLabel;
  elements.sourceStatus.dataset.status = health.status || "unknown";
  elements.sourceNote.textContent = health.detail || "";
  elements.modeBadge.textContent = health.label || fallbackLabel;
  elements.modeBadge.dataset.status = health.status || "unknown";
}

async function loadCalendars() {
  try {
    const response = await fetch("/api/calendars");
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Kalender konnten nicht geladen werden.");
    state.categories = payload.categories || [];
    state.qualityLegend = payload.qualityLegend || [];
    state.sportsCoverage = payload.sportsCoverage || { europeSports: [], globalCombatSports: [], championships: [] };
    state.sourcePlan = payload.sourcePlan || { total: 0, active: 0, needsWork: 0, items: [] };
    state.sourceMonitor = payload.sourceMonitor || { total: 0, watching: 0, planned: 0, items: [] };
    const selectedExists = state.categories.some((category) => category.id === state.selectedCategoryId);
    state.selectedCategoryId = selectedExists ? state.selectedCategoryId : state.categories[0]?.id || "";
    if (!findCoverageOption(state.selectedCoverageId)) {
      state.selectedCoverageId = allCoverageOptions()[0]?.id || "";
    }
    renderCatalog();
  } catch (error) {
    state.categories = [];
    elements.catalogStatus.textContent = "Fehler";
    elements.qualityLegend.innerHTML = "";
    elements.sportsCoverage.innerHTML = "";
    elements.coverageDetail.innerHTML = "";
    elements.sourcePlanStatus.textContent = "Fehler";
    elements.sourcePlan.innerHTML = "";
    elements.sourceMonitorStatus.textContent = "Fehler";
    elements.sourceMonitor.innerHTML = "";
    elements.categoryTabs.innerHTML = "";
    elements.calendarCatalog.innerHTML = `<div class="empty-state">Kalenderliste konnte nicht geladen werden.</div>`;
    toast(error.message, true);
  }
}

function renderCatalog() {
  const total = state.categories.reduce((sum, category) => sum + category.calendarCount, 0);
  elements.catalogStatus.textContent = `${total} Kalender`;
  renderQualityLegend();
  renderSportsCoverage();
  renderSourcePlan();
  renderSourceMonitor();
  renderCategoryTabs();
  renderCalendarCatalog();
}

function renderQualityLegend() {
  elements.qualityLegend.innerHTML = state.qualityLegend.map((item) => `
    <div class="legend-item">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.description)}</span>
    </div>
  `).join("");
}

function renderCategoryTabs() {
  elements.categoryTabs.innerHTML = state.categories.map((category) => {
    const selected = category.id === state.selectedCategoryId;
    return `
      <button class="category-tab${selected ? " active" : ""}" type="button" role="tab" aria-selected="${selected}" data-category="${escapeAttribute(category.id)}">
        <span>${escapeHtml(category.name)}</span>
        <strong>${category.calendarCount}</strong>
      </button>
    `;
  }).join("");
  document.querySelectorAll(".category-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCategoryId = button.dataset.category;
      renderCatalog();
    });
  });
}

function coverageGroups() {
  return [
    { title: "Europa Sportarten", items: state.sportsCoverage.europeSports || [] },
    { title: "Kampfsport weltweit", items: state.sportsCoverage.globalCombatSports || [] },
    { title: "WM & EM", items: state.sportsCoverage.championships || [] },
  ];
}

function allCoverageOptions() {
  return coverageGroups().flatMap((group) => group.items);
}

function findCoverageOption(id) {
  return allCoverageOptions().find((option) => option.id === id);
}

function renderSportsCoverage() {
  const groups = coverageGroups();
  elements.sportsCoverage.innerHTML = groups.map((group) => `
    <div class="coverage-group">
      <strong>${escapeHtml(group.title)}</strong>
      <div class="coverage-options">
        ${group.items.map((item) => `
          <button class="coverage-chip${item.id === state.selectedCoverageId ? " active" : ""}" type="button" data-coverage="${escapeAttribute(item.id)}">
            ${escapeHtml(item.name)}
          </button>
        `).join("")}
      </div>
    </div>
  `).join("");

  document.querySelectorAll(".coverage-chip").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedCoverageId = button.dataset.coverage;
      renderSportsCoverage();
    });
  });

  const selected = findCoverageOption(state.selectedCoverageId);
  if (!selected) {
    elements.coverageDetail.innerHTML = "";
    return;
  }
  elements.coverageDetail.innerHTML = `
    <div>
      <span>${escapeHtml(selected.scope)} · ${escapeHtml(selected.group)}</span>
      <strong>${escapeHtml(selected.name)}</strong>
    </div>
    <p>${escapeHtml(selected.description)}</p>
    <em>${escapeHtml(selected.statusLabel)} · ${escapeHtml(selected.sourceNote)}</em>
  `;
}

function renderSourcePlan() {
  const items = state.sourcePlan.items || [];
  elements.sourcePlanStatus.textContent = `${state.sourcePlan.needsWork || 0} offen · ${state.sourcePlan.active || 0} aktiv`;
  if (!items.length) {
    elements.sourcePlan.innerHTML = `<div class="empty-state">Noch keine Provider-Planung verfügbar.</div>`;
    return;
  }

  elements.sourcePlan.innerHTML = items.map((item) => `
    <article class="source-plan-card">
      <div class="source-plan-card-head">
        <div>
          <span>${escapeHtml(item.scope)} · ${escapeHtml(item.priority)}</span>
          <strong>${escapeHtml(item.title)}</strong>
        </div>
        <em class="${escapeAttribute(item.status)}">${escapeHtml(item.statusLabel)}</em>
      </div>
      <p>${escapeHtml(item.summary)}</p>
      <div class="source-plan-columns">
        <div>
          <span>Blocker</span>
          <ul>${item.blockers.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("")}</ul>
        </div>
        <div>
          <span>Nächste Schritte</span>
          <ul>${item.nextSteps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ul>
        </div>
      </div>
    </article>
  `).join("");
}

function updateMonitorObservation(observation = null) {
  if (!observation || !state.sourceMonitor.items?.length) return;
  state.sourceMonitor = {
    ...state.sourceMonitor,
    items: state.sourceMonitor.items.map((item) => {
      if (item.id !== observation.sourceId) return item;
      return {
        ...item,
        liveStatus: observation.status,
        lastObservationLabel: observation.checkedLabel,
        lastObservationCount: observation.eventCount,
        lastObservationMessage: observation.message,
      };
    }),
  };
  renderSourceMonitor();
}

function renderSourceMonitor() {
  const items = state.sourceMonitor.items || [];
  elements.sourceMonitorStatus.textContent = `${state.sourceMonitor.watching || 0} beobachtet · ${state.sourceMonitor.planned || 0} geplant`;
  if (!items.length) {
    elements.sourceMonitor.innerHTML = `<div class="empty-state">Noch keine Quellen im Monitoring.</div>`;
    return;
  }

  elements.sourceMonitor.innerHTML = items.map((item) => {
    const liveStatus = item.liveStatus || item.status;
    const eventCount = Number.isInteger(item.lastObservationCount)
      ? `${item.lastObservationCount} Events`
      : escapeHtml(item.eventCountLabel);
    const checkedLabel = item.lastObservationLabel || item.lastCheckedMode;
    const message = item.lastObservationMessage || item.message;
    return `
      <article class="source-monitor-card">
        <div class="source-monitor-card-head">
          <div>
            <span>${escapeHtml(item.scope)}</span>
            <strong>${escapeHtml(item.sourceLabel)}</strong>
          </div>
          <em class="${escapeAttribute(liveStatus)}">${escapeHtml(item.statusLabel)}</em>
        </div>
        <dl>
          <div>
            <dt>Letzte Prüfung</dt>
            <dd>${escapeHtml(checkedLabel)}</dd>
          </div>
          <div>
            <dt>Event-Anzahl</dt>
            <dd>${eventCount}</dd>
          </div>
        </dl>
        <p>${escapeHtml(message)}</p>
        <small>${escapeHtml(item.nextAction)}</small>
      </article>
    `;
  }).join("");
}

function renderCalendarCatalog() {
  const category = state.categories.find((item) => item.id === state.selectedCategoryId);
  if (!category) {
    elements.calendarCatalog.innerHTML = `<div class="empty-state">Noch keine Kategorien verfügbar.</div>`;
    return;
  }

  if (!category.calendars.length) {
    elements.calendarCatalog.innerHTML = `
      <article class="catalog-empty">
        <strong>${escapeHtml(category.name)} ist vorbereitet</strong>
        <p>${escapeHtml(category.description)}</p>
        <span>Kalender folgen, sobald eine verlässliche Quelle angebunden ist.</span>
      </article>
    `;
    return;
  }

  elements.calendarCatalog.innerHTML = category.calendars.map((calendar) => `
    <article class="calendar-card">
      <div class="calendar-card-main">
        <div>
          <span class="calendar-category">${escapeHtml(category.name)}</span>
          <h4>${escapeHtml(calendar.name)}</h4>
        </div>
        <span class="status-pill ${escapeAttribute(calendar.quality.level)}">${escapeHtml(calendar.quality.label)}</span>
      </div>
      <p>${escapeHtml(calendar.description)}</p>
      <div class="source-row">
        <span>Quelle</span>
        <strong>${escapeHtml(calendar.sourceLabel)}</strong>
      </div>
      <div class="quality-grid">
        <div>
          <span>Aktualisierung</span>
          <strong>${escapeHtml(calendar.quality.updatePolicy)}</strong>
          <small>${escapeHtml(calendar.quality.updatedLabel)}</small>
        </div>
        <div>
          <span>Einordnung</span>
          <strong>${escapeHtml(calendar.quality.sourceTypeLabel)}</strong>
          <small>${escapeHtml(calendar.quality.reliabilityNote)}</small>
        </div>
      </div>
      <ul class="quality-notes">
        ${calendar.quality.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}
      </ul>
      <div class="calendar-actions">
        ${calendar.hasFeed
          ? `<a class="button primary" href="${escapeAttribute(calendar.feedUrl)}">ICS abonnieren</a>
             <button class="button secondary calendar-copy" type="button" data-url="${escapeAttribute(calendar.subscribeUrl)}">Link kopieren</button>`
          : `<button class="button disabled" type="button" disabled>Provider nötig</button>
             <span class="action-note">Noch kein echter Event-Feed.</span>`
        }
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".calendar-copy").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.url, "Kalender-Link kopiert."));
  });
}

function renderEvents() {
  elements.eventCount.textContent = String(state.events.length);

  if (!state.events.length) {
    const health = state.sourceHealth || {};
    const hints = (health.hints || []).map((hint) => `<li>${escapeHtml(hint)}</li>`).join("");
    elements.eventList.innerHTML = `
      <div class="empty-state source-empty">
        <strong>${escapeHtml(health.title || "Keine Spiele für diese Filter.")}</strong>
        <p>${escapeHtml(health.detail || "Für diese Auswahl wurden keine Termine gefunden.")}</p>
        ${hints ? `<ul>${hints}</ul>` : ""}
      </div>
    `;
    return;
  }

  const visibleEvents = state.events.slice(0, 200);
  const limitNote = state.events.length > visibleEvents.length
    ? `<div class="list-note">Es werden 200 von ${state.events.length} Spielen angezeigt. Die ICS-Datei enthält alle gefilterten Spiele.</div>`
    : "";

  elements.eventList.innerHTML = visibleEvents.map((event) => {
    const homeFav = state.favorites.includes(event.homeTeam);
    const awayFav = state.favorites.includes(event.awayTeam);
    return `
      <article class="event-card">
        <div class="date-block">
          <strong>${event.dateLabel}</strong>
          <span>${event.timeLabel}</span>
        </div>
        <div class="event-main">
          <strong>${event.title}</strong>
          <div class="event-meta">${event.leagueName}${event.location ? ` · ${event.location}` : ""}</div>
        </div>
        <div class="event-actions">
          <button class="star-button" type="button" data-team="${escapeAttribute(event.homeTeam)}" title="${homeFav ? "Favorit entfernen" : "Heimteam favorisieren"}">${homeFav ? "★" : "☆"}</button>
          <button class="star-button" type="button" data-team="${escapeAttribute(event.awayTeam)}" title="${awayFav ? "Favorit entfernen" : "Auswärtsteam favorisieren"}">${awayFav ? "★" : "☆"}</button>
          <span class="tag">${event.league.toUpperCase()}</span>
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
    elements.favorites.innerHTML = `<span class="empty-small">Noch keine Favoriten</span>`;
    return;
  }
  elements.favorites.innerHTML = state.favorites.map((team) => `
    <button class="favorite-pill" type="button" data-team="${escapeAttribute(team)}">${team} ×</button>
  `).join("");
  document.querySelectorAll(".favorite-pill").forEach((button) => {
    button.addEventListener("click", () => toggleFavorite(button.dataset.team));
  });
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

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

elements.liveMode.addEventListener("click", () => setMode(false));
elements.sampleMode.addEventListener("click", () => setMode(true));
elements.refreshButton.addEventListener("click", loadEvents);
elements.appleButton.addEventListener("click", openAppleCalendar);
elements.copyFeedButton.addEventListener("click", copyFeedLink);
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

renderFavorites();
updateFeedLinks();
loadCalendars();
loadEvents();
