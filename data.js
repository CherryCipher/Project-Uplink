/** Fetch the only data source. Serve through HTTP(S), not file://. */
export async function loadGames() {
  const response = await fetch('./games.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`games.json kon niet geladen worden (${response.status})`);
  const data = await response.json();
  if (!data || !Array.isArray(data.games)) throw new Error('games.json moet een "games" array bevatten.');
  return data;
}

export function imageUrl(path) { return (typeof path === 'string' && path.trim()) ? path : 'assets/placeholder.svg'; }

export function makeImage(src, alt, className = '') {
  const img = document.createElement('img');
  img.src = imageUrl(src);
  img.alt = alt;
  if (className) img.className = className;
  img.loading = 'lazy';
  img.addEventListener('error', () => { if (!img.src.endsWith('/assets/placeholder.svg')) img.src = 'assets/placeholder.svg'; });
  return img;
}

export function setBackground(node, path) {
  node.replaceChildren(makeImage(path, '', 'cover-art'));
}

export function gameHref(game) { return `game.html?id=${encodeURIComponent(game.id)}`; }
export function readable(value, fallback = 'Nog niet bekend') { return value === null || value === undefined || value === '' ? fallback : String(value); }


/** Load the independently maintained software catalog. */
export async function loadSoftware() {
  const response = await fetch('./software.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`software.json kon niet geladen worden (${response.status})`);
  const data = await response.json();
  if (!data || !Array.isArray(data.software)) throw new Error('software.json moet een "software" array bevatten.');
  return data;
}

export function softwareHref(item) {
  return `software-detail.html?id=${encodeURIComponent(item.id)}`;
}
