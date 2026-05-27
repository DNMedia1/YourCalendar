const state = {
  sample: true,
  events: [],
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
    if (!payload.ok) throw new Error(payload.error || "Unbekannter Fehler");
    state.events = payload.events;
    updateFeedLinks(payload);
    elements.sourceStatus.textContent = payload.mode === "sample" ? "Sample" : "OpenLigaDB";
    elements.sourceNote.textContent = payload.sourceNote;
    elements.modeBadge.textContent = payload.mode === "sample" ? "Sample" : "Live";
    renderEvents();
  } catch (error) {
    state.events = [];
    updateFeedLinks();
    elements.sourceStatus.textContent = "Fehler";
    elements.sourceNote.textContent = error.message;
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
  try {
    await navigator.clipboard.writeText(elements.feedUrl.value);
    toast("Feed-Link kopiert.");
  } catch (error) {
    elements.feedUrl.select();
    toast("Link ist markiert und kann kopiert werden.");
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
loadEvents();
loadMonitoring();
