import { loadSoftware, makeImage, setBackground, softwareHref, readable } from './data.js';

const grid = document.querySelector('#gamesGrid');
const filters = document.querySelector('#filters');
const search = document.querySelector('#search');
const emptyState = document.querySelector('#emptyState');
const gameCount = document.querySelector('#softwareCount');
let games = [];
let category = 'Alle software';

function card(game) {
  const a = document.createElement('a');
  a.className = 'game-card';
  a.href = softwareHref(game);
  const art = document.createElement('div');
  art.className = 'box-art';
  art.append(makeImage(game.boxImage, `${game.title} box art`));
  const overlay = document.createElement('span');
  overlay.className = 'box-overlay';
  overlay.textContent = 'BEKIJK SOFTWARE ↗';
  art.append(overlay);
  const name = document.createElement('strong');
  name.textContent = game.title;
  const meta = document.createElement('span');
  meta.className = 'card-meta';
  meta.textContent = `${readable(game.genre)} · ${readable(game.platforms?.join(', ') || game.platforms)}`;
  a.append(art, name, meta);
  return a;
}

function draw() {
  const q = search.value.trim().toLocaleLowerCase('nl');
  const visible = games.filter(g =>
    (category === 'Alle software' || (g.categories || []).includes(category)) &&
    [g.title, g.genre, g.shortDescription, ...(g.categories || [])].join(' ').toLocaleLowerCase('nl').includes(q)
  );
  grid.replaceChildren(...visible.map(card));
  emptyState.hidden = visible.length !== 0;
  gameCount.textContent = `(${visible.length})`;
}

function buildFilters() {
  const categories = ['Alle software', ...new Set(games.flatMap(g => g.categories || []))];
  filters.replaceChildren(...categories.map(label => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter' + (label === category ? ' active' : '');
    button.textContent = label;
    button.addEventListener('click', () => {
      category = label;
      filters.querySelectorAll('.filter').forEach(b => b.classList.toggle('active', b === button));
      draw();
    });
    return button;
  }));
}

function buildHero(game) {
  if (!game) return;
  setBackground(document.querySelector('#heroArt'), game.heroImage);
  document.querySelector('#heroTitle').textContent = game.title;
  document.querySelector('#heroTag').textContent = `${readable(game.genre).toUpperCase()} • ${(game.platforms || []).join(" / ").toUpperCase()}`;
  document.querySelector('#heroDescription').textContent = game.shortDescription || '';
  document.querySelector('#heroLink').href = softwareHref(game);
}

async function init() {
  try {
    const data = await loadSoftware();
    games = data.software;
    buildHero(games.find(g => g.featured) || games[0]);
    buildFilters();
    draw();
    search.addEventListener('input', draw);
  } catch (error) {
    emptyState.hidden = false;
    emptyState.textContent = `Kon de software niet laden: ${error.message}. Start een lokale webserver (zie README).`;
  }
}
init();
