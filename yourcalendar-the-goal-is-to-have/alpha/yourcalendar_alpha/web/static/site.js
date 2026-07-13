const dialog = document.getElementById('subscribeDialog');
const title = document.getElementById('dialogTitle');
const googleLink = document.getElementById('googleLink');
const outlookLink = document.getElementById('outlookLink');
const appleLink = document.getElementById('appleLink');
const icsLink = document.getElementById('icsLink');
const themeToggle = document.querySelector('[data-theme-toggle]');
const themeLabel = document.querySelector('.theme-label');

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('yc-theme', theme);
  if (themeLabel) {
    themeLabel.textContent = theme === 'dark' ? 'Lightmode' : 'Darkmode';
  }
  if (themeToggle) {
    themeToggle.setAttribute('aria-pressed', String(theme === 'dark'));
  }
}

const savedTheme = localStorage.getItem('yc-theme');
const preferredTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
setTheme(savedTheme || preferredTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  });
}

document.querySelectorAll('[data-subscribe]').forEach((button) => {
  button.addEventListener('click', () => {
    const payload = JSON.parse(button.dataset.subscribe);
    title.textContent = payload.name;
    googleLink.href = payload.google;
    outlookLink.href = payload.outlook;
    appleLink.href = payload.apple;
    icsLink.href = payload.ics;
    dialog.showModal();
  });
});

document.querySelectorAll('.group-panel').forEach((panel) => {
  panel.addEventListener('toggle', () => {
    const grid = panel.parentElement;
    if (!grid || !grid.classList.contains('tile-grid')) {
      return;
    }
    if (panel.open) {
      grid.querySelectorAll(':scope > .group-panel[open]').forEach((sibling) => {
        if (sibling !== panel) {
          closeGroupTree(sibling);
        }
      });
      grid.classList.add('has-open');
    } else if (!grid.querySelector(':scope > .group-panel[open]')) {
      closeDescendantGroups(panel);
      grid.classList.remove('has-open');
    }
  });
});

function closeGroupTree(panel) {
  closeDescendantGroups(panel);
  panel.open = false;
}

function closeDescendantGroups(panel) {
  panel.querySelectorAll('.group-panel[open]').forEach((child) => {
    child.open = false;
  });
  panel.querySelectorAll('.tile-grid.has-open').forEach((grid) => {
    grid.classList.remove('has-open');
  });
}
