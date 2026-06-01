const grid = document.getElementById("sportCalendarGrid");
const count = document.getElementById("sportCalendarCount");

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

function render(calendars) {
  count.textContent = `${calendars.length} Kalender`;
  if (!calendars.length) {
    grid.innerHTML = `
      <div class="catalog-empty" role="status">
        <span>Noch keine Teamkalender</span>
        <p>Der erste football-data.org Import hat noch kein Bundesliga-Teammanifest erzeugt. FOOTBALL_DATA_API_KEY muss als Secret gesetzt sein.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = calendars.map((calendar) => `
    <article class="calendar-card sport-team-card">
      <div class="calendar-card-main">
        <div>
          <span class="calendar-category">1. Bundesliga</span>
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
          <span>Aktualisierung</span>
          <strong>${escapeHtml(calendar.quality?.updatedLabel)}</strong>
          <small>${escapeHtml(calendar.quality?.updatePolicy)}</small>
        </div>
        <div>
          <span>Hinweis</span>
          <strong>${escapeHtml(calendar.quality?.label)}</strong>
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
    const calendars = (payload.calendars || []).filter((calendar) => String(calendar.id || "").startsWith("football-data-bl1-"));
    render(calendars);
  } catch (error) {
    count.textContent = "Fehler";
    grid.innerHTML = `<div class="catalog-empty" role="status"><p>Sportkalender konnten nicht geladen werden.</p></div>`;
    showToast(error.message, true);
  }
}

loadSportCalendars();
