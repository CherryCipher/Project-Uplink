import { loadGames, makeImage, gameHref } from './data.js';

const daysElement = document.querySelector('#programDays');
const messageElement = document.querySelector('#programMessage');

function textElement(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = value || '';
  return element;
}

function eventCard(event, gamesById) {
  const game = typeof event.game === 'string' ? gamesById.get(event.game) : null;
  const item = document.createElement('article');
  item.className = 'program-event' + (game ? ' program-event-game' : '');

  const timing = textElement('div', 'program-time', `${event.start} – ${event.end}`);
  const body = document.createElement('div');
  body.className = 'program-event-body';

  if (game) {
    const link = document.createElement('a');
    link.className = 'program-event-link';
    link.href = gameHref(game);

    const cover = makeImage(game.boxImage, `${game.title} box art`);
    cover.className = 'program-cover';

    const content = document.createElement('div');
    content.className = 'program-event-copy';
    content.append(textElement('span', 'program-kind', 'GAME SESSION'));
    content.append(textElement('h3', '', event.title || game.title));
    // Show the name from games.json, even for a custom event title.
    if (event.title && event.title !== game.title) {
      content.append(textElement('span', 'program-game-name', game.title));
    }
    if (event.description) content.append(textElement('p', '', event.description));
    link.append(cover, content);
    body.append(link);
  } else {
    const content = document.createElement('div');
    content.className = 'program-event-copy';
    const type = event.type === 'break' ? 'BREAK / FOOD' : 'ACTIVITY';
    content.append(textElement('span', 'program-kind', type));
    content.append(textElement('h3', '', event.title || (event.game ? 'Unknown game' : 'Activity')));
    if (event.description) content.append(textElement('p', '', event.description));
    body.append(content);
    if (event.game) {
      body.append(textElement('p', 'program-missing-game', `Game ID '${event.game}' not found in games.json`));
    }
  }

  if (!game && typeof event.url === 'string' && /^(https?:\/\/|\.\/|\/|[\w-]+\.html(?:[?#].*)?$)/i.test(event.url)) {
    const link = document.createElement('a');
    link.className = 'program-extra-link';
    link.href = event.url;
    link.textContent = event.linkLabel || 'More information ↗';
    if (/^https?:\/\//i.test(event.url)) {
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    body.append(link);
  }

  item.append(timing, body);
  return item;
}

function render(data, games) {
  if (!data || !Array.isArray(data.days)) throw new Error('program.json needs a days array');
  if (data.title) document.querySelector('#programTitle').textContent = data.title;
  if (data.subtitle) document.querySelector('#programSubtitle').textContent = data.subtitle;

  const gamesById = new Map(games.map(game => [game.id, game]));
  const fragment = document.createDocumentFragment();

  for (const day of data.days) {
    if (!day || !Array.isArray(day.events)) continue;
    const section = document.createElement('section');
    section.className = 'program-day';

    const heading = textElement('h2', 'program-day-heading', day.label || day.date || 'Day');
    section.append(heading);

    const entries = document.createElement('div');
    entries.className = 'program-entries';
    // Display in chronological order, regardless of JSON insertion order.
    const sorted = [...day.events].filter(event => event && event.start && event.end)
      .sort((a, b) => a.start.localeCompare(b.start));

    for (const event of sorted) entries.append(eventCard(event, gamesById));
    if (!sorted.length) entries.append(textElement('p', 'empty', 'No activities planned yet.'));
    section.append(entries);
    fragment.append(section);
  }

  daysElement.replaceChildren(fragment);
  messageElement.hidden = true;
}

async function init() {
  try {
    const [response, gameData] = await Promise.all([
      fetch('./program.json', { cache: 'no-cache' }),
      loadGames()
    ]);
    if (!response.ok) throw new Error(`program.json could not be loaded (${response.status})`);
    render(await response.json(), gameData.games);
  } catch (error) {
    messageElement.hidden = false;
    messageElement.textContent = `Could not load the program: ${error.message}`;
  }
}

init();
