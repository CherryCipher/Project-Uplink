import { loadGames, makeImage, setBackground, gameHref, readable } from './data.js';

const grid = document.querySelector('#gamesGrid');
const filters = document.querySelector('#filters');
const search = document.querySelector('#search');
const emptyState = document.querySelector('#emptyState');
const gameCount = document.querySelector('#gameCount');
let games = [];
let category = 'Alle games';

function card(game) {
  const a = document.createElement('a');
  a.className = 'game-card';
  a.href = gameHref(game);
  const art = document.createElement('div');
  art.className = 'box-art';
  art.append(makeImage(game.boxImage, `${game.title} box art`));

  // Independent metadata flags from games.json; neither implies a live ping.
  if (game.localServer === true) {
    const serverBadge = document.createElement('span');
    serverBadge.className = 'game-server-badge';
    serverBadge.setAttribute('aria-label', 'Lokale gameserver beschikbaar');
    serverBadge.title = 'Lokale gameserver beschikbaar';
    // A small inline SVG icon avoids external assets and icon-font dependencies.
    serverBadge.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="4" y="3" width="16" height="8" rx="2"/><rect x="4" y="13" width="16" height="8" rx="2"/><circle cx="8" cy="7" r="1"/><circle cx="8" cy="17" r="1"/><path d="M12 7h5M12 17h5"/></svg>';
    art.append(serverBadge);
  }
  if (game.liveScoring === true) {
    const liveBadge = document.createElement('span');
    liveBadge.className = 'game-live-scoring';
    liveBadge.textContent = 'LIVE SCORING';
    art.append(liveBadge);
  }
  const overlay = document.createElement('span');
  overlay.className = 'box-overlay';
  overlay.textContent = 'GO TO GAME ↗';
  art.append(overlay);
  const name = document.createElement('strong');
  name.textContent = game.title;
  const meta = document.createElement('span');
  meta.className = 'card-meta';
  meta.textContent = `${readable(game.genre)} · ${readable(game.players)} spelers`;
  a.append(art, name, meta);
  return a;
}

function draw() {
  const q = search.value.trim().toLocaleLowerCase('nl');
  const visible = games.filter(g =>
    (category === 'Alle games' || (g.categories || []).includes(category)) &&
    [g.title, g.genre, g.shortDescription, ...(g.categories || [])].join(' ').toLocaleLowerCase('nl').includes(q)
  );
  grid.replaceChildren(...visible.map(card));
  emptyState.hidden = visible.length !== 0;
  gameCount.textContent = `(${visible.length})`;
}

function buildFilters() {
  const categories = ['Alle games', ...new Set(games.flatMap(g => g.categories || []))];
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
  document.querySelector('#heroTag').textContent = `${readable(game.genre).toUpperCase()} • ${readable(game.players)} SPELERS`;
  document.querySelector('#heroDescription').textContent = game.shortDescription || '';
  document.querySelector('#heroLink').href = gameHref(game);
}

async function init() {
  try {
    const data = await loadGames();
    games = data.games;
    buildHero(games.find(g => g.featured) || games[0]);
    buildFilters();
    draw();
    search.addEventListener('input', draw);
  } catch (error) {
    emptyState.hidden = false;
    emptyState.textContent = `Kon de games niet laden: ${error.message}. Start een lokale webserver (zie README).`;
  }
}
init();
