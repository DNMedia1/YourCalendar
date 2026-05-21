export default {
  title: "YourCalendar/Components",
};

export const ButtonVariants = () => `
  <main style="padding: 32px; display: flex; gap: 12px; flex-wrap: wrap;">
    <button class="button primary" type="button">Apple Kalender oeffnen</button>
    <a class="button secondary" href="#">ICS laden</a>
    <button class="icon-button" type="button" aria-label="Aktualisieren">↻</button>
  </main>
`;

export const SegmentControl = () => `
  <main style="padding: 32px; max-width: 360px;">
    <div class="segmented" role="group" aria-label="Datenmodus">
      <button class="segment active" type="button" aria-pressed="true">Sample</button>
      <button class="segment" type="button" aria-pressed="false">Live</button>
    </div>
  </main>
`;

export const EventCard = () => `
  <main style="padding: 32px;">
    <article class="event-card">
      <div class="date-block">
        <strong>24.08.2026</strong>
        <span>20:30 CEST</span>
      </div>
      <div class="event-main">
        <strong>Karlsruher SC vs Hamburger SV</strong>
        <div class="event-meta">2. Bundesliga · BBBank Wildpark</div>
      </div>
      <div class="event-actions">
        <button class="star-button" type="button" aria-label="Heimteam favorisieren">☆</button>
        <button class="star-button is-active" type="button" aria-label="Auswaertsteam favorisiert">★</button>
        <span class="tag" data-league="bl2">BL2</span>
      </div>
    </article>
  </main>
`;

export const ThemeToggle = () => `
  <main style="padding: 32px;">
    <button class="theme-toggle" type="button" aria-pressed="false" aria-label="Dark Mode aktivieren">
      <span class="theme-toggle-track" aria-hidden="true">
        <span class="theme-toggle-thumb"></span>
      </span>
      <span>Dark Mode</span>
    </button>
  </main>
`;
