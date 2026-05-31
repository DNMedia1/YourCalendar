// Smoke test for the public YourCalendar website.
// Covers the three core visitor flows required by issue #48:
//   1. The public calendar catalog renders without login.
//   2. A visitor can select a calendar category.
//   3. A visitor can trigger a subscription-link (Abo-Link) action.
//
// The web app is served separately on the Cypress baseUrl
// (http://127.0.0.1:8765). This spec only drives the browser.

describe("YourCalendar public calendar catalog", () => {
  beforeEach(() => {
    cy.visit("/", {
      onBeforeLoad(win) {
        // Clipboard access is unreliable in headless browsers. Stub it so the
        // success path is exercised deterministically; the app also has a
        // visible fallback, so the assertions below hold either way.
        try {
          if (!win.navigator.clipboard) {
            Object.defineProperty(win.navigator, "clipboard", {
              value: {},
              configurable: true,
            });
          }
          cy.stub(win.navigator.clipboard, "writeText").resolves();
        } catch (err) {
          // Ignore: a non-configurable clipboard just routes through the
          // app's visible fallback toast, which the tests still assert on.
        }
      },
    });

    // Wait until the catalog has finished loading (status leaves "Lädt").
    cy.get("#catalogStatus", { timeout: 20000 }).should("not.have.text", "Lädt");
  });

  it("renders the public catalog without requiring a login", () => {
    cy.get("#discoverTitle").should("contain.text", "Kalenderkatalog");
    cy.get(".catalog-intro").should("contain.text", "ohne Login");
    cy.get("#categoryOverview .category-summary").should("have.length.greaterThan", 0);
    cy.get("#calendarCatalog").should("exist");
  });

  it("lets a visitor select a calendar category", () => {
    cy.get("#categoryOverview .category-summary").should("have.length.greaterThan", 0);

    cy.get("#categoryOverview .category-summary").then(($cards) => {
      // Prefer a non-active category so the selection visibly changes; fall
      // back to the first category when only one exists.
      const index = $cards.length > 1 ? 1 : 0;
      const categoryId = $cards.eq(index).attr("data-category-id");

      // Selecting from the overview updates both the overview and the tabs.
      cy.wrap($cards.eq(index)).click();

      cy.get(`#categoryOverview .category-summary[data-category-id="${categoryId}"]`)
        .should("have.attr", "aria-pressed", "true");
      cy.get(`#categoryTabs .category-tab[data-category-id="${categoryId}"]`)
        .should("have.attr", "aria-selected", "true");
    });
  });

  it("copies a calendar subscription link from the catalog", () => {
    // At least one calendar in the catalog must expose an Abo-Link action.
    cy.get("#calendarCatalog .copy-calendar", { timeout: 20000 })
      .should("have.length.greaterThan", 0)
      .first()
      .should("have.attr", "data-subscribe-url")
      .and("match", /\.ics/);

    cy.get("#calendarCatalog .copy-calendar").first().click();
    cy.get(".toast").should("be.visible");
  });

  it("copies the current feed subscription link", () => {
    // The feed URL input is populated once events finish loading.
    cy.get("#feedUrl", { timeout: 20000 }).invoke("val").should("match", /\.ics/);
    // The copy button is disabled while loading; wait until it is ready.
    cy.get("#copyFeedButton").should("not.be.disabled").click();
    cy.get(".toast").should("be.visible");
  });
});
