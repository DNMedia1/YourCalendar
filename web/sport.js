const grid = document.getElementById("sportCalendarGrid");
const count = document.getElementById("sportCalendarCount");
const taxonomyNode = document.getElementById("sportTaxonomy");
const subgroupNode = document.getElementById("sportSubgroups");

let state = {
  calendars: [],
  taxonomy: { groups: [], providers: [] },
  selectedGroup: new URLSearchParams(window.location.search).get("group") || "team-sports",
  selectedSubgroup: new URLSearchParams(window.location.search).get("subgroup") || "",
};

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return String(value || "").replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

function pageUrl(groupId, subgroupId = "") {
  const params = new URLSearchParams({ group: groupId });
  if (subgroupId) params.set("subgroup", subgroupId);
  return `/sport.html?${params.toString()}`;
}

async function copyText(value) {
  try {
    await navigator.clipboard.writeText(value);
    showToast("Abo-Link kopiert.");
  } catch {
    showToast("Link konnte nicht automatisch kopiert werden.", true);
  }
}

function showToast(message, isError = false) {
  const node = document.createElement("div");
  node.className = `toast${isError ? " error" : ""}`;
  node.textContent = message;
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 3200);
}

function selectedGroup() {
  return state.taxonomy.groups.find((group) => group.id === state.selectedGroup) || state.taxonomy.groups[0];
}

function selectedSubgroups() {
  const group = selectedGroup();
  return group?.subgroups || [];
}

function matchingCalendars() {
  return state.calendars.filter((calendar) => {
    if (!calendar.groupId && !calendar.subgroupId) return false;
    if (state.selectedGroup && calendar.groupId !== state.selectedGroup) return false;
    if (state.selectedSubgroup && calendar.subgroupId !== state.selectedSubgroup) return false;
    return true;
  });
}

function plannedProviders() {
  return (state.taxonomy.providers || []).filter((provider) => {
    if (provider.groupId !== state.selectedGroup) return false;
    if (state.selectedSubgroup && provider.subgroupId !== state.selectedSubgroup) return false;
    return true;
  });
}

function renderTaxonomy() {
  taxonomyNode.innerHTML = (state.taxonomy.groups || []).map((group) => `
    <a class="sport-nav-chip${group.id === state.selectedGroup ? " active" : ""}" href="${escapeAttribute(pageUrl(group.id))}">
      <strong>${escapeHtml(group.name)}</strong>
      <span>${escapeHtml(group.description)}</span>
    </a>
  `).join("");

  subgroupNode.innerHTML = selectedSubgroups().map((subgroup) => `
    <a class="sport-subgroup-chip${subgroup.id === state.selectedSubgroup ? " active" : ""}" href="${escapeAttribute(pageUrl(state.selectedGroup, subgroup.id))}">
      ${escapeHtml(subgroup.name)}
    </a>
  `).join("");
}

function render() {
  renderTaxonomy();
  const calendars = matchingCalendars();
  const providers = plannedProviders();
  count.textContent = `${calendars.length} Kalender`;

  if (!calendars.length) {
    const providerList = providers.map((provider) => `
      <li>${escapeHtml(provider.sportName)} · ${escapeHtml(provider.leagueName)} · ${escapeHtml(provider.provider)}${provider.enabled ? "" : " · noch nicht automatisch aktiviert"}</li>
    `).join("");
    grid.innerHTML = `
      <div class="catalog-empty" role="status">
        <span>Noch keine erzeugten Kalender</span>
        <p>Der Import hat fuer diese Auswahl noch keine Feed-Kacheln erzeugt. Sichtbare Provider-Pfade:</p>
        <ul>${providerList || "<li>Keine Provider-Konfiguration fuer diese Untergruppe.</li>"}</ul>
      </div>
    `;
    return;
  }

  grid.innerHTML = calendars.map((calendar) => `
    <article class="calendar-card sport-team-card">
      <div class="calendar-card-main">
        <div>
          <span class="calendar-category">${escapeHtml(calendar.leagueName || calendar.sportId)}</span>
          <h2>${escapeHtml(calendar.name)}</h2>
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
          <span>Typ</span>
          <strong>${escapeHtml(calendar.calendarMode === "team" ? "Teamkalender" : "Competition")}</strong>
          <small>${escapeHtml(calendar.providerKey)}</small>
        </div>
        <div>
          <span>Aktualisierung</span>
          <strong>${escapeHtml(calendar.quality?.updatedLabel)}</strong>
          <small>${escapeHtml(calendar.quality?.reliabilityNote)}</small>
        </div>
      </div>
      <div class="calendar-actions">
        <a class="button secondary" href="${escapeAttribute(calendar.feedUrl)}">ICS laden</a>
        <button class="button primary copy-team-calendar" type="button" data-subscribe-url="${escapeAttribute(calendar.subscribeUrl)}">Abo-Link kopieren</button>
      </div>
    </article>
  `).join("");

  document.querySelectorAll(".copy-team-calendar").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.subscribeUrl));
  });
}

async function loadSportCalendars() {
  try {
    const response = await fetch("/api/calendars");
    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Kalender konnten nicht geladen werden.");
    state.calendars = payload.calendars || [];
    state.taxonomy = payload.sportTaxonomy || { groups: [], providers: [] };
    if (!selectedGroup()) {
      state.selectedGroup = state.taxonomy.groups?.[0]?.id || "";
    }
    render();
  } catch (error) {
    count.textContent = "Fehler";
    grid.innerHTML = `<div class="catalog-empty" role="status"><p>Sportkalender konnten nicht geladen werden.</p></div>`;
    showToast(error.message, true);
  }
}

loadSportCalendars();
