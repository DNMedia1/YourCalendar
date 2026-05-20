const state = {
  sample: true,
  events: [],
  favorites: JSON.parse(localStorage.getItem("yourcalendar:favorites") || "[]"),
};

const $ = (id) => document.getElementById(id);

const elements = {
  liveMode: $("liveMode"),
  sampleMode: $("sampleMode"),
  refreshButton: $("refreshButton"),
  appleButton: $("appleButton"),
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
    if (!payload.ok) throw new Error(payload.error || "Unbekannter Fehler");
    state.events = payload.events;
    elements.sourceStatus.textContent = payload.mode === "sample" ? "Sample" : "OpenLigaDB";
    elements.sourceNote.textContent = payload.sourceNote;
    elements.modeBadge.textContent = payload.mode === "sample" ? "Sample" : "Live";
    renderEvents();
  } catch (error) {
    state.events = [];
    elements.sourceStatus.textContent = "Fehler";
    elements.sourceNote.textContent = error.message;
    renderEvents();
    toast(error.message, true);
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  elements.refreshButton.disabled = isBusy;
  elements.appleButton.disabled = isBusy;
}

function renderEvents() {
  elements.eventCount.textContent = String(state.events.length);

  if (!state.events.length) {
    elements.eventList.innerHTML = `<div class="empty-state">Keine Spiele für diese Filter.</div>`;
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
    const response = await fetch("/api/open-apple");
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Apple Kalender konnte nicht geöffnet werden.");
    toast("Apple Kalender wurde geöffnet.");
  } catch (error) {
    toast(error.message, true);
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
elements.appleButton.addEventListener("click", openAppleCalendar);
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
loadEvents();
