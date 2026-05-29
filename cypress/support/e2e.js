// Cypress support file loaded before every E2E spec.
// Intentionally minimal: no custom commands are required for the current
// smoke test. Keeping this file lets us add shared setup later without
// touching individual specs.

// The web app uses the browser Clipboard API for subscription links.
// In headless CI the clipboard may be unavailable, so we stub it defensively
// in each spec rather than failing the run on an unrelated permission error.
