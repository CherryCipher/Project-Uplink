/**
 * Project UPLINK — game detail page.
 * All game content comes from games.json.
 */
import { loadGames, makeImage, setBackground, imageUrl, readable } from './data.js';

const $ = (selector) => document.querySelector(selector);

/** Add one label/value pair to the game details panel. */
function addDetailRow(parent, label, value) {
  const term = document.createElement('dt');
  term.textContent = label;

  const description = document.createElement('dd');
  description.textContent = readable(value);

  parent.append(term, description);
}

/** Create a leaderboard cell without injecting untrusted HTML. */
function makeCell(className, value) {
  const cell = document.createElement('span');
  cell.className = className;
  cell.textContent = String(value ?? '');
  return cell;
}

/**
 * Render the leaderboard for a game.
 * `leaderboardLabel` controls the column heading (Kills, Wins, Points, etc.).
 * `score` remains the numeric value in each entry.
 */
function renderLeaderboard(game) {
  const container = $('#leaderboardContent');
  const status = $('#leaderboard .tag');
  const entries = Array.isArray(game.leaderboard) ? game.leaderboard : [];
  const label = game.leaderboardLabel || 'Score';

  container.replaceChildren();

  if (!entries.length) {
    status.textContent = 'COMING SOON';
    const empty = document.createElement('p');
    empty.className = 'leaderboard-empty';
    empty.textContent = 'Hier verschijnen binnenkort de topscores van deze game.';
    container.append(empty);
    return;
  }

  status.textContent = 'TOP PLAYERS';

  // Copy before sorting: never change the order stored in games.json.
  const sorted = [...entries].sort(
    (a, b) => (Number(b.score) || 0) - (Number(a.score) || 0)
  );

  const table = document.createElement('div');
  table.className = 'leaderboard-table';
  table.setAttribute('role', 'table');
  table.setAttribute('aria-label', `${game.title} leaderboard`);

  const header = document.createElement('div');
  header.className = 'leaderboard-row leaderboard-header';
  header.setAttribute('role', 'row');
  for (const heading of ['RANK', 'PLAYER', label.toUpperCase()]) {
    const cell = makeCell('', heading);
    cell.setAttribute('role', 'columnheader');
    header.append(cell);
  }
  table.append(header);

  sorted.forEach((player, index) => {
    const row = document.createElement('div');
    row.className = `leaderboard-row${index === 0 ? ' leaderboard-first' : ''}`;
    row.setAttribute('role', 'row');

    const rank = makeCell('leaderboard-rank', index === 0 ? '👑' : `#${index + 1}`);
    if (index === 0) rank.setAttribute('aria-label', 'Eerste plaats');
    const name = makeCell('leaderboard-player', player.name || 'Onbekend');
    const score = makeCell('leaderboard-score', Number(player.score) || 0);

    for (const cell of [rank, name, score]) cell.setAttribute('role', 'cell');
    row.append(rank, name, score);
    table.append(row);
  });

  container.append(table);
}

/** Populate the detail page with the selected game. */
function showGame(game) {
  document.title = `${game.title} — Project UPLINK`;

  setBackground($('#detailArt'), game.heroImage);

  const box = $('#detailBox');
  box.src = imageUrl(game.boxImage);
  box.alt = `${game.title} box art`;
  box.addEventListener('error', () => {
    if (!box.src.endsWith('/assets/placeholder.svg')) {
      box.src = 'assets/placeholder.svg';
    }
  });

  $('#detailCategory').textContent = (game.categories || []).join(' / ');
  $('#detailTitle').textContent = game.title;
  $('#detailShort').textContent = game.shortDescription || '';
  $('#detailDescription').textContent =
    game.description || game.shortDescription || 'Omschrijving volgt.';

  const download = $('#downloadButton');
  if (game.downloadUrl) {
    download.href = game.downloadUrl;
    download.textContent = '↓ DOWNLOAD GAME';
    if (/^https?:\/\//i.test(game.downloadUrl)) {
      download.target = '_blank';
      download.rel = 'noopener noreferrer';
    }
  } else {
    download.removeAttribute('href');
    download.classList.add('disabled');
    download.textContent = 'DOWNLOAD VOLGT';
    download.setAttribute('aria-disabled', 'true');
  }

  const gallery = $('#screenshots');
  gallery.replaceChildren();
  const screenshots = (game.screenshots || []).slice(0, 4);
  for (let index = 0; index < 4; index++) {
    const figure = document.createElement('figure');
    figure.append(makeImage(screenshots[index], `${game.title} screenshot ${index + 1}`));
    gallery.append(figure);
  }

  const stats = $('#stats');
  stats.replaceChildren();
  addDetailRow(stats, 'Genre', game.genre);
  addDetailRow(stats, 'Spelers', game.players);
  addDetailRow(stats, 'Modus', game.mode);
  addDetailRow(stats, 'Platform', Array.isArray(game.platforms) ? game.platforms.join(', ') : game.platforms);
  addDetailRow(stats, 'Licentie', game.license);
  addDetailRow(stats, 'Server', game.serverInfo);

  // Optional dedicated server address (IP or hostname + port).
  if (typeof game.serverAddress === 'string' && game.serverAddress.trim()) {
    addDetailRow(stats, 'Server IP', game.serverAddress.trim());
  }

  renderLeaderboard(game);
  $('#detail').hidden = false;
}

/** Find the game requested by `game.html?id=...`. */
async function init() {
  try {
    const id = new URLSearchParams(window.location.search).get('id');
    const { games } = await loadGames();
    const game = games.find((entry) => entry.id === id);
    if (!game) throw new Error('Game niet gevonden');
    showGame(game);
  } catch (error) {
    const errorState = $('#errorState');
    errorState.hidden = false;
    errorState.querySelector('p').textContent =
      `${error.message}. Controleer de game-id en games.json.`;
  }
}

init();
