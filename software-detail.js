/** Project UPLINK — software details sourced entirely from software.json. */
import { loadSoftware, makeImage, setBackground, imageUrl, readable } from './data.js';

const $ = (selector) => document.querySelector(selector);

/** Add a statistic only if it has a meaningful value. */
function addStat(parent, label, value) {
  if (value == null || value === '' || (Array.isArray(value) && !value.length)) return;
  const dt = document.createElement('dt');
  const dd = document.createElement('dd');
  dt.textContent = label;
  dd.textContent = Array.isArray(value) ? value.join(', ') : String(value);
  parent.append(dt, dd);
}

function showSoftware(item) {
  document.title = `${item.title} — Project UPLINK`;
  setBackground($('#detailArt'), item.heroImage);
  const box = $('#detailBox');
  box.src = imageUrl(item.boxImage);
  box.alt = `${item.title} cover`;
  box.addEventListener('error', () => {
    if (!box.src.endsWith('/assets/placeholder.svg')) box.src = 'assets/placeholder.svg';
  });
  $('#detailCategory').textContent = (item.categories || []).join(' / ');
  $('#detailTitle').textContent = item.title;
  $('#detailShort').textContent = item.shortDescription || '';
  $('#detailDescription').textContent = item.description || item.shortDescription || 'Omschrijving volgt.';

  const download = $('#downloadButton');
  if (item.downloadUrl) {
    download.href = item.downloadUrl;
    download.textContent = '↓ DOWNLOAD SOFTWARE';
    if (/^https?:\/\//i.test(item.downloadUrl)) {
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
  for (let i = 0; i < 2; i++) {
    const figure = document.createElement('figure');
    figure.append(makeImage((item.screenshots || [])[i], `${item.title} screenshot ${i + 1}`));
    gallery.append(figure);
  }

  const stats = $('#stats');
  stats.replaceChildren();
  addStat(stats, 'Type', item.genre);
  addStat(stats, 'Versie', item.version);
  addStat(stats, 'Platformen', item.platforms);
  addStat(stats, 'Besturingssysteem', item.requirements?.os);
  addStat(stats, 'Processor', item.requirements?.cpu);
  addStat(stats, 'Werkgeheugen', item.requirements?.ram);
  addStat(stats, 'Schijfruimte', item.requirements?.storage);
  addStat(stats, 'Internetverbinding', item.requirements?.network);
  addStat(stats, 'Licentie', item.license);
  addStat(stats, 'Server', item.serverInfo);
  addStat(stats, 'Serveradres', item.serverAddress);
  $('#detail').hidden = false;
}

async function init() {
  try {
    const id = new URLSearchParams(location.search).get('id');
    const { software } = await loadSoftware();
    const item = software.find((entry) => entry.id === id);
    if (!item) throw new Error('Software niet gevonden');
    showSoftware(item);
  } catch (error) {
    $('#errorState').hidden = false;
    $('#errorState p').textContent = `${error.message}. Controleer software.json.`;
  }
}

init();
