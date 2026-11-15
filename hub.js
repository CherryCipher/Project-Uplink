// De HUB wordt volledig gevuld vanuit hub.json; geen backend nodig.
const list = document.querySelector('#hubLinks');
const message = document.querySelector('#hubMessage');
const count = document.querySelector('#hubCount');

function safeUrl(value, allowRelative = false) {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value, window.location.href);
    if (!['http:', 'https:'].includes(url.protocol)) return null;
    if (!allowRelative && !/^https?:\/\//i.test(value)) return null;
    return url.href;
  } catch {
    return null;
  }
}

function card(item) {
  const url = safeUrl(item.url);
  if (!url || typeof item.title !== 'string' || !item.title.trim()) return null;

  const link = document.createElement('a');
  link.className = 'hub-card';
  link.href = url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.setAttribute('aria-label', item.title + ' (opent in nieuw tabblad)');

  const visual = document.createElement('div');
  visual.className = 'hub-card-image';
  const imageUrl = safeUrl(item.image, true);
  if (imageUrl) {
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = '';
    img.loading = 'lazy';
    img.addEventListener('error', () => {
      img.remove();
      visual.classList.add('hub-card-image-fallback');
    });
    visual.append(img);
  } else {
    visual.classList.add('hub-card-image-fallback');
  }

  const content = document.createElement('div');
  content.className = 'hub-card-content';
  const title = document.createElement('h3');
  title.textContent = item.title;
  const description = document.createElement('p');
  description.textContent = item.description || '';
  content.append(title, description);

  const arrow = document.createElement('span');
  arrow.className = 'hub-card-arrow';
  arrow.textContent = '↗';
  arrow.setAttribute('aria-hidden', 'true');

  link.append(visual, content, arrow);
  return link;
}

async function init() {
  try {
    const response = await fetch('hub.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    if (!Array.isArray(data.links)) throw new Error('hub.json moet een links-array bevatten');
    const cards = data.links.map(card).filter(Boolean);
    list.replaceChildren(...cards);
    count.textContent = '(' + cards.length + ')';
    message.hidden = cards.length > 0;
    if (!cards.length) message.textContent = 'Nog geen links toegevoegd aan hub.json.';
  } catch (error) {
    message.hidden = false;
    message.textContent = 'Kon de HUB-links niet laden: ' + error.message + '. Start de lokale webserver (zie README).';
  }
}
init();
