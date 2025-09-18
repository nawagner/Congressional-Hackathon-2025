const COMBINED_DB_PATH = 'hearings_combined.db';
const EXCLUDED_LEGISLATORS_PATH = 'excluded_legislator_keys.json';
const MAX_HEARING_COUNT_PER_WITNESS = 55;
const SQL_JS_CDN_BASE = 'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/';

const NAME_TITLE_TOKENS = new Set([
  'the',
  'sen',
  'senator',
  'rep',
  'representative',
  'delegate',
  'commissioner',
  'chair',
  'chairman',
  'chairwoman',
  'ranking',
  'member',
  'hon',
  'honorable',
  'mr',
  'mrs',
  'ms',
  'miss',
  'dr',
  'prof',
  'reverend',
  'rev',
  'sir',
  'madam',
  'mayor',
  'governor',
]);

const NAME_SUFFIX_TOKENS = new Set(['jr', 'sr', 'ii', 'iii', 'iv', 'v']);

const LOCATION_KEYWORDS = new Set(['of', 'for', 'from']);

const LOCATION_TOKENS = new Set([
  'of',
  'the',
  'state',
  'commonwealth',
  'territory',
  'district',
  'columbia',
  'washington',
  'dc',
  'united',
  'states',
  'america',
  'at',
  'large',
  'puerto',
  'rico',
  'virgin',
  'islands',
  'northern',
  'mariana',
  'guam',
  'samoa',
  'american',
  'alabama',
  'alaska',
  'arizona',
  'arkansas',
  'california',
  'colorado',
  'connecticut',
  'delaware',
  'florida',
  'georgia',
  'hawaii',
  'idaho',
  'illinois',
  'indiana',
  'iowa',
  'kansas',
  'kentucky',
  'louisiana',
  'maine',
  'maryland',
  'massachusetts',
  'michigan',
  'minnesota',
  'mississippi',
  'missouri',
  'montana',
  'nebraska',
  'nevada',
  'new',
  'hampshire',
  'jersey',
  'mexico',
  'york',
  'north',
  'carolina',
  'dakota',
  'south',
  'ohio',
  'oklahoma',
  'oregon',
  'pennsylvania',
  'rhode',
  'island',
  'tennessee',
  'texas',
  'utah',
  'vermont',
  'virginia',
  'west',
  'wisconsin',
  'wyoming',
]);

const NON_NAME_TOKENS = new Set([
  'available',
  'briefing',
  'click',
  'closing',
  'committee',
  'document',
  'full',
  'hearing',
  'here',
  'link',
  'materials',
  'opening',
  'press',
  'release',
  'report',
  'statement',
  'submission',
  'submitted',
  'summary',
  'testimony',
  'transcript',
  'video',
  'webcast',
  'written',
]);

const PARTY_AFFILIATION_REGEX = /\b(?:R|D|I|ID|IND|DEM|REP|GOP)\b\s*[-–]?\s*\(?[A-Z]{2}\)?\b/;
const PARTY_WORD_REGEX = /\b(?:democrat|democratic|republican|independent|libertarian|green)\b/i;

let sqlJsInstancePromise;
let excludedLegislatorKeysPromise;

const state = {
  hearings: [],
  witnessMap: new Map(),
  sortedWitnesses: [],
  witnessElements: new Map(),
  witnessMessage: null,
  filters: {
    witnessQuery: '',
    committee: 'all',
    tag: 'all',
    startDate: null,
    endDate: null,
    dualChamberOnly: false,
  },
  selectedWitnessKey: null,
  filteredHearings: [],
  dateRange: { min: null, max: null },
  sort: {
    key: 'date',
    direction: 'desc',
  },
};

const elements = {
  witnessSearch: document.getElementById('witnessSearch'),
  committeeFilter: document.getElementById('committeeFilter'),
  tagFilter: document.getElementById('tagFilter'),
  startDate: document.getElementById('startDate'),
  endDate: document.getElementById('endDate'),
  clearFilters: document.getElementById('clearFilters'),
  dualChamberToggle: null,
  witnessList: document.getElementById('witnessList'),
  hearingsTableBody: document.querySelector('#hearingsTable tbody'),
  totalHearings: document.getElementById('totalHearings'),
  uniqueWitnesses: document.getElementById('uniqueWitnesses'),
  selectedWitnessCount: document.getElementById('selectedWitnessCount'),
  detailsTitle: document.getElementById('detailsTitle'),
  detailsSubtitle: document.getElementById('detailsSubtitle'),
  sortButtons: Array.from(document.querySelectorAll('.sort-button')),
};

document.addEventListener('DOMContentLoaded', initialise);

async function initialise() {
  showTableMessage('Loading hearings…');
  ensureDualChamberButton();
  attachEventListeners();

  try {
    const [SQL, excludedLegislatorKeys] = await Promise.all([
      loadSqlJsInstance(),
      loadExcludedLegislatorKeys(),
    ]);
    const databaseBytes = await fetchDatabase(COMBINED_DB_PATH);
    const db = new SQL.Database(databaseBytes);

    const hearings = buildHearingsFromDatabase(db);
    db.close();

    if (!hearings.length) {
      showTableMessage('No hearings could be loaded from the database.');
      return;
    }

    state.hearings = hearings;
    elements.totalHearings.textContent = hearings.length.toLocaleString();

    state.dateRange = computeDateRange(hearings);
    applyDateBounds();

    state.witnessMap = buildWitnessMap(hearings, { excludedLegislatorKeys });
    state.sortedWitnesses = Array.from(state.witnessMap.values()).sort(sortWitnesses);
    state.witnessElements = new Map();
    state.witnessMessage = null;
    elements.uniqueWitnesses.textContent = state.sortedWitnesses.length.toLocaleString();

    populateFilterOptions();
    renderWitnessList();
    applyFilters();
  } catch (error) {
    console.error('Failed to load hearings database', error);
    showTableMessage('Unable to load the combined hearings database. Ensure you are running a local server.');
  }
}

function attachEventListeners() {
  elements.witnessSearch.addEventListener('input', (event) => {
    state.filters.witnessQuery = event.target.value.trim();
    const selectionChanged = renderWitnessList();
    if (selectionChanged) {
      applyFilters();
    }
  });

  elements.committeeFilter.addEventListener('change', (event) => {
    state.filters.committee = event.target.value;
    applyFilters();
  });

  elements.tagFilter.addEventListener('change', (event) => {
    state.filters.tag = event.target.value;
    applyFilters();
  });

  elements.startDate.addEventListener('change', (event) => {
    state.filters.startDate = event.target.value ? new Date(event.target.value) : null;
    applyFilters();
  });

  elements.endDate.addEventListener('change', (event) => {
    state.filters.endDate = event.target.value ? new Date(event.target.value) : null;
    applyFilters();
  });

  elements.clearFilters.addEventListener('click', () => {
    state.filters = {
      witnessQuery: '',
      committee: 'all',
      tag: 'all',
      startDate: null,
      endDate: null,
      dualChamberOnly: false,
    };
    state.selectedWitnessKey = null;

    elements.witnessSearch.value = '';
    elements.committeeFilter.value = 'all';
    elements.tagFilter.value = 'all';
    elements.startDate.value = '';
    elements.endDate.value = '';

    updateDualChamberButton();
    renderWitnessList();
    applyFilters();
  });

  elements.sortButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const { sortKey } = button.dataset;
      if (!sortKey) return;
      updateSort(sortKey);
    });
  });

  if (elements.dualChamberToggle) {
    elements.dualChamberToggle.addEventListener('click', () => {
      const previousSelectedKey = state.selectedWitnessKey;
      state.filters.dualChamberOnly = !state.filters.dualChamberOnly;
      if (state.filters.dualChamberOnly && state.selectedWitnessKey) {
        const selected = state.witnessMap.get(state.selectedWitnessKey);
        if (!selected || selected.chambers.size < 2) {
          state.selectedWitnessKey = null;
        }
      }
      updateDualChamberButton();
      const selectionChanged = renderWitnessList();
      if (selectionChanged || previousSelectedKey !== state.selectedWitnessKey) {
        applyFilters();
      }
    });
  }
}

function ensureDualChamberButton() {
  if (elements.dualChamberToggle) return;
  if (!elements.clearFilters) return;

  const button = document.createElement('button');
  button.type = 'button';
  button.id = 'dualChamberToggle';
  button.className = 'button button--secondary';
  elements.clearFilters.insertAdjacentElement('afterend', button);

  elements.dualChamberToggle = button;
  updateDualChamberButton();
}

function updateDualChamberButton() {
  if (!elements.dualChamberToggle) return;
  const active = state.filters.dualChamberOnly;
  elements.dualChamberToggle.textContent = active
    ? 'Show all witnesses'
    : 'Show dual-chamber witnesses';
  elements.dualChamberToggle.setAttribute('aria-pressed', active ? 'true' : 'false');
}

// Lazy-load sql.js from CDN and return the initialised module.
function loadSqlJsInstance() {
  if (sqlJsInstancePromise) {
    return sqlJsInstancePromise;
  }

  sqlJsInstancePromise = new Promise((resolve, reject) => {
    function initialise() {
      if (typeof window.initSqlJs !== 'function') {
        reject(new Error('sql.js init function not available.'));
        return;
      }
      window
        .initSqlJs({ locateFile: (file) => `${SQL_JS_CDN_BASE}${file}` })
        .then(resolve)
        .catch(reject);
    }

    if (typeof window.initSqlJs === 'function') {
      initialise();
      return;
    }

    const script = document.createElement('script');
    script.src = `${SQL_JS_CDN_BASE}sql-wasm.js`;
    script.async = true;
    script.onload = initialise;
    script.onerror = () => reject(new Error('Failed to load sql.js library.'));
    document.head.appendChild(script);
  });

  return sqlJsInstancePromise;
}

function loadExcludedLegislatorKeys() {
  if (excludedLegislatorKeysPromise) {
    return excludedLegislatorKeysPromise;
  }

  excludedLegislatorKeysPromise = fetch(EXCLUDED_LEGISLATORS_PATH, { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} while fetching ${EXCLUDED_LEGISLATORS_PATH}`);
      }
      return response.json();
    })
    .then((payload) => {
      if (!Array.isArray(payload)) {
        console.warn('Excluded legislator list is not an array; ignoring it.');
        return new Set();
      }

      const keys = new Set();
      payload.forEach((item) => {
        if (typeof item !== 'string') return;
        const normalised = normaliseNameKey(item);
        if (!normalised) return;
        keys.add(normalised);
        if (normalised.includes('-')) {
          keys.add(normalised.replace(/-/g, ' '));
        }
        if (normalised.includes("'")) {
          keys.add(normalised.replace(/'/g, ''));
        }
      });
      return keys;
    })
    .catch((error) => {
      console.warn('Failed to load excluded legislator list; continuing without it.', error);
      return new Set();
    });

  return excludedLegislatorKeysPromise;
}

async function fetchDatabase(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} while fetching ${path}`);
  }
  const buffer = await response.arrayBuffer();
  return new Uint8Array(buffer);
}

// Pull hearings and witnesses into JS objects for the UI to consume.
function buildHearingsFromDatabase(db) {
  const hearingRows = selectAll(
    db,
    `
      SELECT id, chamber, source_hearing_id, event_id, url, title, date, time, datetime,
             location, committee, tags, scraped_at, witness_list_pdf
      FROM hearings
      ORDER BY date, id
    `,
  );

  const witnessRows = selectAll(
    db,
    `
      SELECT hearing_id, name, title, truth_in_testimony_pdf
      FROM witnesses
      ORDER BY hearing_id, id
    `,
  );

  const hearings = hearingRows.map((row) => ({
    id: Number(row.id),
    chamber: (row.chamber || '').trim(),
    sourceId: row.source_hearing_id ? String(row.source_hearing_id).trim() : null,
    eventId: row.event_id !== null && row.event_id !== undefined ? Number(row.event_id) : null,
    pageUrl: (row.url || '').trim(),
    videoUrl: '',
    title: (row.title || '').trim(),
    date: row.date || '',
    dateObj: parseIsoDate(row.date || ''),
    time: row.time || '',
    datetime: row.datetime || '',
    location: (row.location || '').trim(),
    committee: (row.committee || '').trim(),
    tags: parseTagColumn(row.tags),
    scrapedAt: row.scraped_at || '',
    witnessListPdf: row.witness_list_pdf || '',
    witnesses: [],
    witnessDetails: [],
    witnessKeys: [],
  }));

  attachWitnessesToHearings(hearings, witnessRows);
  return hearings;
}

function selectAll(db, query) {
  const stmt = db.prepare(query);
  const rows = [];
  while (stmt.step()) {
    rows.push(stmt.getAsObject());
  }
  stmt.free();
  return rows;
}

function attachWitnessesToHearings(hearings, witnessRows) {
  const hearingMap = new Map();
  hearings.forEach((hearing) => {
    hearingMap.set(hearing.id, hearing);
  });

  witnessRows.forEach((row) => {
    const hearing = hearingMap.get(Number(row.hearing_id));
    if (!hearing) return;

    const name = (row.name || '').trim();
    if (!name) return;

    hearing.witnesses.push(name);
    hearing.witnessDetails.push({
      name,
      title: (row.title || '').trim(),
      truthInTestimonyPdf: row.truth_in_testimony_pdf || '',
    });
  });

  hearings.forEach((hearing) => {
    const seen = new Set();
    const uniqueNames = [];
    const uniqueDetails = [];

    hearing.witnesses.forEach((name, index) => {
      const key = nameToKey(name);
      if (!key || seen.has(key)) {
        return;
      }
      seen.add(key);
      uniqueNames.push(name);
      uniqueDetails.push(hearing.witnessDetails[index]);
    });

    hearing.witnesses = uniqueNames;
    hearing.witnessDetails = uniqueDetails;
    hearing.witnessKeys = uniqueNames.map((name) => nameToKey(name));
  });
}

function parseTagColumn(raw) {
  if (!raw) return [];
  const text = String(raw).trim();
  if (!text) return [];

  const candidate = text.replace(/""/g, '"');
  try {
    const parsed = JSON.parse(candidate);
    if (Array.isArray(parsed)) {
      return parsed.map((tag) => String(tag).trim()).filter(Boolean);
    }
  } catch (error) {
    // Fall through to fallback parsing.
  }

  return candidate
    .replace(/^\[/, '')
    .replace(/\]$/, '')
    .split(/,\s*/)
    .map((tag) => tag.replace(/^['\"]+|['\"]+$/g, '').trim())
    .filter(Boolean);
}

function parseIsoDate(value) {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if ([year, month, day].some((part) => Number.isNaN(part))) {
    return null;
  }
  return new Date(year, month - 1, day);
}

function buildWitnessMap(hearings, options = {}) {
  const { excludedLegislatorKeys = new Set() } = options;
  const map = new Map();

  hearings.forEach((hearing) => {
    const seenDuringHearing = new Set();

    hearing.witnesses.forEach((name, index) => {
      const key = hearing.witnessKeys[index];
      if (!key || seenDuringHearing.has(key)) {
        return;
      }

      seenDuringHearing.add(key);

      const entry = map.get(key) || {
        key,
        name,
        hearings: [],
        count: 0,
        chambers: new Set(),
      };

      if (!entry.name || entry.name.length < name.length) {
        entry.name = name;
      }

      entry.hearings.push(hearing);
      entry.count += 1;
      if (hearing.chamber) {
        entry.chambers.add(hearing.chamber);
      }

      map.set(key, entry);
    });
  });

  map.forEach((entry) => {
    entry.isDualChamber = entry.chambers.size >= 2;
  });

  const filtered = new Map();
  map.forEach((entry) => {
    if (shouldIncludeWitness(entry, excludedLegislatorKeys)) {
      filtered.set(entry.key, entry);
    }
  });

  return filtered;
}

function shouldIncludeWitness(entry, excludedLegislatorKeys) {
  if (!entry) return false;
  if (entry.count > MAX_HEARING_COUNT_PER_WITNESS) {
    return false;
  }

  if (!hasFirstAndLastName(entry.name)) {
    return false;
  }

  if (containsPartyAffiliation(entry.name)) {
    return false;
  }

  const normalised = normaliseNameKey(entry.name);
  if (normalised && excludedLegislatorKeys.has(normalised)) {
    return false;
  }

  return true;
}

function hasFirstAndLastName(name) {
  const normalised = normaliseNameKey(name);
  if (!normalised) return false;
  const parts = normalised.split(' ').filter(Boolean);
  if (containsNonNameTokens(parts)) {
    return false;
  }
  if (parts.length < 2) {
    return false;
  }
  const first = parts[0];
  const last = parts[parts.length - 1];
  return first.length > 1 && last.length > 1;
}

function normaliseNameKey(rawName) {
  if (!rawName || typeof rawName !== 'string') {
    return '';
  }

  let text = rawName;
  text = text.replace(/\([^)]*\)/g, ' ');
  text = text.replace(/\b[RID]-[A-Z]{2}\b/g, ' ');
  const normalized = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const cleaned = normalized.replace(/[^A-Za-z\s'-]/g, ' ');
  let parts = cleaned
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .filter((token) => token.length > 1)
    .filter((token) => !NAME_TITLE_TOKENS.has(token) && !NAME_SUFFIX_TOKENS.has(token));
  parts = stripTrailingLocationTokens(parts);

  return parts.join(' ');
}

function stripTrailingLocationTokens(tokens) {
  if (!tokens.length) {
    return tokens;
  }

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!LOCATION_KEYWORDS.has(token)) {
      continue;
    }

    const tail = tokens.slice(index + 1);
    if (!tail.length) {
      continue;
    }

    if (tail.every((part) => LOCATION_TOKENS.has(part))) {
      return tokens.slice(0, index);
    }
  }

  return tokens;
}

function containsNonNameTokens(tokens) {
  return tokens.some((token) => NON_NAME_TOKENS.has(token));
}

function containsPartyAffiliation(text) {
  if (!text || typeof text !== 'string') {
    return false;
  }

  if (PARTY_AFFILIATION_REGEX.test(text.toUpperCase())) {
    return true;
  }

  if (PARTY_WORD_REGEX.test(text) && /\([A-Z]{2}\)/.test(text.toUpperCase())) {
    return true;
  }

  return false;
}

function sortWitnesses(a, b) {
  if (b.count !== a.count) {
    return b.count - a.count;
  }
  return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
}

function populateFilterOptions() {
  const committees = Array.from(
    new Set(state.hearings.map((hearing) => hearing.committee).filter(Boolean)),
  ).sort((a, b) => a.localeCompare(b));

  elements.committeeFilter.innerHTML = '';
  elements.committeeFilter.append(new Option('All committees', 'all'));
  committees.forEach((committee) => {
    elements.committeeFilter.append(new Option(committee, committee));
  });

  const tags = Array.from(
    new Set(
      state.hearings.flatMap((hearing) => hearing.tags).map((tag) => tag.trim()).filter(Boolean),
    ),
  ).sort((a, b) => a.localeCompare(b));

  elements.tagFilter.innerHTML = '';
  elements.tagFilter.append(new Option('All tags', 'all'));
  if (!tags.length) {
    elements.tagFilter.disabled = true;
  } else {
    elements.tagFilter.disabled = false;
    tags.forEach((tag) => {
      elements.tagFilter.append(new Option(tag, tag));
    });
  }
}

function renderWitnessList() {
  const container = elements.witnessList;
  if (!container) return false;

  let selectionChanged = false;

  if (!state.sortedWitnesses.length) {
    container.textContent = 'No witnesses found.';
    state.witnessElements = new Map();
    state.witnessMessage = null;
    if (state.selectedWitnessKey) {
      state.selectedWitnessKey = null;
      selectionChanged = true;
    }
    return selectionChanged;
  }

  if (state.witnessElements.size === 0) {
    container.innerHTML = '';
    const message = document.createElement('p');
    message.className = 'witness-list__message';
    message.hidden = true;
    container.append(message);
    state.witnessMessage = message;

    const fragment = document.createDocumentFragment();
    state.sortedWitnesses.forEach((witness) => {
      const button = createWitnessButton(witness);
      state.witnessElements.set(witness.key, button);
      fragment.append(button);
    });
    container.append(fragment);
  }

  const query = state.filters.witnessQuery.toLowerCase();
  const dualOnly = state.filters.dualChamberOnly;
  let matches = 0;
  let selectedVisible = false;

  state.sortedWitnesses.forEach((witness) => {
    const button = state.witnessElements.get(witness.key);
    if (!button) {
      return;
    }

    const match =
      (!dualOnly || witness.isDualChamber) &&
      (!query || witness.name.toLowerCase().includes(query));

    if (match) {
      matches += 1;
      button.hidden = false;
      button.setAttribute('aria-hidden', 'false');
      const isActive = state.selectedWitnessKey === witness.key;
      button.classList.toggle('active', isActive);
      if (isActive) {
        selectedVisible = true;
      }
    } else {
      button.hidden = true;
      button.setAttribute('aria-hidden', 'true');
      button.classList.remove('active');
    }
  });

  if (state.witnessMessage) {
    if (matches === 0) {
      const hasQuery = Boolean(state.filters.witnessQuery);
      const messageText = hasQuery
        ? 'No witnesses match that search.'
        : state.filters.dualChamberOnly
          ? 'No dual-chamber witnesses match the current filters.'
          : 'No witnesses match the current filters.';
      state.witnessMessage.textContent = messageText;
      state.witnessMessage.hidden = false;
    } else {
      state.witnessMessage.hidden = true;
    }
  }

  if (state.selectedWitnessKey && !selectedVisible) {
    state.selectedWitnessKey = null;
    selectionChanged = true;
  }

  return selectionChanged;
}

function createWitnessButton(witness) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'witness-item';
  button.dataset.witnessKey = witness.key;

  const nameSpan = document.createElement('span');
  nameSpan.className = 'witness-item__name';
  nameSpan.textContent = witness.name;

  const countSpan = document.createElement('span');
  countSpan.className = 'witness-item__count';
  countSpan.textContent = `${witness.count.toLocaleString()} hearings`;

  button.append(nameSpan, countSpan);

  button.addEventListener('click', () => {
    state.selectedWitnessKey = state.selectedWitnessKey === witness.key ? null : witness.key;
    renderWitnessList();
    applyFilters();
    scrollToTable();
  });

  return button;
}

function applyFilters() {
  const { hearings, filters, selectedWitnessKey } = state;

  let filtered = hearings.filter((hearing) => {
    if (filters.committee !== 'all' && hearing.committee !== filters.committee) {
      return false;
    }

    if (filters.tag !== 'all' && !hearing.tags.includes(filters.tag)) {
      return false;
    }

    if (filters.startDate && hearing.dateObj && hearing.dateObj < filters.startDate) {
      return false;
    }

    if (filters.endDate && hearing.dateObj && hearing.dateObj > filters.endDate) {
      return false;
    }

    return true;
  });

  if (selectedWitnessKey) {
    filtered = filtered.filter((hearing) => hearing.witnessKeys.includes(selectedWitnessKey));
  }

  const sortedHearings = sortHearings(filtered);
  state.filteredHearings = sortedHearings;
  renderHearingsTable(sortedHearings);
  updateSummary(sortedHearings);
  refreshSortIndicators();
}

function renderHearingsTable(hearings) {
  const tbody = elements.hearingsTableBody;
  tbody.innerHTML = '';

  if (!hearings.length) {
    const row = document.createElement('tr');
    const cell = document.createElement('td');
    cell.colSpan = 6;
    cell.className = 'empty-state';
    cell.textContent = 'No hearings match the current filters.';
    row.append(cell);
    tbody.append(row);
    return;
  }

  hearings.forEach((hearing) => {
    const row = document.createElement('tr');

    const dateCell = document.createElement('td');
    dateCell.textContent = hearing.dateObj ? formatDate(hearing.dateObj) : hearing.date;
    row.append(dateCell);

    const chamberCell = document.createElement('td');
    chamberCell.textContent = formatChamber(hearing.chamber) || '—';
    row.append(chamberCell);

    const titleCell = document.createElement('td');
    const titleLink = document.createElement('a');
    titleLink.className = 'hearing-title';
    titleLink.textContent = hearing.title || 'Untitled hearing';
    if (hearing.pageUrl) {
      titleLink.href = hearing.pageUrl;
      titleLink.target = '_blank';
      titleLink.rel = 'noopener noreferrer';
    } else {
      titleLink.href = '#';
      titleLink.addEventListener('click', (event) => event.preventDefault());
    }

    titleCell.append(titleLink);

    if (hearing.pageUrl || hearing.videoUrl) {
      const linkRow = document.createElement('div');
      linkRow.className = 'hearing-links';
      if (hearing.pageUrl) {
        const pageAnchor = document.createElement('a');
        pageAnchor.href = hearing.pageUrl;
        pageAnchor.target = '_blank';
        pageAnchor.rel = 'noopener noreferrer';
        pageAnchor.textContent = 'Hearing page';
        linkRow.append(pageAnchor);
      }
      if (hearing.videoUrl) {
        const videoAnchor = document.createElement('a');
        videoAnchor.href = hearing.videoUrl;
        videoAnchor.target = '_blank';
        videoAnchor.rel = 'noopener noreferrer';
        videoAnchor.textContent = 'Watch video';
        linkRow.append(videoAnchor);
      }
      titleCell.append(linkRow);
    }

    row.append(titleCell);

    const committeeCell = document.createElement('td');
    committeeCell.textContent = hearing.committee || '—';
    row.append(committeeCell);

    const witnessesCell = document.createElement('td');
    if (!hearing.witnesses.length) {
      witnessesCell.textContent = '—';
    } else {
      hearing.witnesses.forEach((name) => {
        const chip = document.createElement('span');
        chip.className = 'witness-chip';
        chip.textContent = name;
        if (state.selectedWitnessKey && nameToKey(name) === state.selectedWitnessKey) {
          chip.classList.add('witness-chip--active');
        }
        witnessesCell.append(chip);
      });
    }
    row.append(witnessesCell);

    const tagsCell = document.createElement('td');
    if (!hearing.tags.length) {
      tagsCell.textContent = '—';
    } else {
      hearing.tags.forEach((tag) => {
        const pill = document.createElement('span');
        pill.className = 'tag-pill';
        pill.textContent = tag;
        tagsCell.append(pill);
      });
    }
    row.append(tagsCell);

    tbody.append(row);
  });
}

function updateSummary(filteredHearings) {
  const selectedEntry = state.selectedWitnessKey
    ? state.witnessMap.get(state.selectedWitnessKey)
    : null;

  const baseCount = selectedEntry ? selectedEntry.count : 0;
  const filteredCount = selectedEntry ? filteredHearings.length : 0;

  elements.selectedWitnessCount.textContent = filteredCount.toLocaleString();

  if (selectedEntry) {
    elements.detailsTitle.textContent = `${selectedEntry.name} hearings`;
    if (filteredCount === baseCount) {
      elements.detailsSubtitle.textContent = `Showing all ${filteredCount.toLocaleString()} hearings for ${selectedEntry.name}.`;
    } else {
      elements.detailsSubtitle.textContent = `Showing ${filteredCount.toLocaleString()} of ${baseCount.toLocaleString()} hearings for ${selectedEntry.name} after filters.`;
    }
  } else {
    elements.detailsTitle.textContent = 'All hearings';
    const filterSummary = describeFilters();
    elements.detailsSubtitle.textContent = `Showing ${filteredHearings.length.toLocaleString()} hearings${filterSummary}.`;
    elements.selectedWitnessCount.textContent = '0';
  }
}

function describeFilters() {
  const { committee, tag, startDate, endDate } = state.filters;
  const parts = [];

  if (committee !== 'all') {
    parts.push(`committee: ${committee}`);
  }

  if (tag !== 'all') {
    parts.push(`tag: ${tag}`);
  }

  if (startDate) {
    parts.push(`from ${formatDate(startDate)}`);
  }

  if (endDate) {
    parts.push(`through ${formatDate(endDate)}`);
  }

  if (state.filters.dualChamberOnly) {
    parts.push('dual-chamber witnesses only');
  }

  if (!parts.length) {
    return '.';
  }

  return ` with ${parts.join(', ')}.`;
}

function formatChamber(chamber) {
  if (!chamber) return '';
  return chamber.charAt(0).toUpperCase() + chamber.slice(1);
}

function nameToKey(name) {
  return name ? name.toLowerCase().replace(/\s+/g, ' ').trim() : '';
}

function formatDate(date) {
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function updateSort(key) {
  if (!key) return;

  if (state.sort.key === key) {
    state.sort.direction = state.sort.direction === 'asc' ? 'desc' : 'asc';
  } else {
    state.sort.key = key;
    state.sort.direction = key === 'date' ? 'desc' : 'asc';
  }

  applyFilters();
}

function sortHearings(hearings) {
  const sorted = hearings.slice();
  const comparator = buildComparator(state.sort);
  sorted.sort(comparator);
  return sorted;
}

function buildComparator(sort) {
  const { key, direction } = sort;
  const multiplier = direction === 'asc' ? 1 : -1;

  return (a, b) => {
    const primary = compareByKey(key, a, b);
    if (primary !== 0) {
      return primary * multiplier;
    }

    // Break ties with date descending so recent hearings appear first.
    const fallback = compareByKey('date', a, b);
    return fallback * -1;
  };
}

function compareByKey(key, a, b) {
  switch (key) {
    case 'date':
      return compareDates(a.dateObj, b.dateObj);
    case 'title':
      return compareStrings(a.title, b.title);
    case 'chamber':
      return compareStrings(formatChamber(a.chamber), formatChamber(b.chamber));
    case 'committee':
      return compareStrings(a.committee, b.committee);
    case 'witnesses':
      return compareStrings(a.witnesses.join(' | '), b.witnesses.join(' | '));
    case 'tags':
      return compareStrings(a.tags.join(' | '), b.tags.join(' | '));
    default:
      return 0;
  }
}

function compareDates(dateA, dateB) {
  const hasA = dateA instanceof Date && !Number.isNaN(dateA.getTime());
  const hasB = dateB instanceof Date && !Number.isNaN(dateB.getTime());

  if (!hasA && !hasB) return 0;
  if (!hasA) return -1;
  if (!hasB) return 1;

  if (dateA.getTime() === dateB.getTime()) return 0;
  return dateA.getTime() < dateB.getTime() ? -1 : 1;
}

function compareStrings(a, b) {
  const left = (a || '').toString().toLowerCase();
  const right = (b || '').toString().toLowerCase();
  return left.localeCompare(right, undefined, { sensitivity: 'base' });
}

function refreshSortIndicators() {
  const { key, direction } = state.sort;
  if (!elements.sortButtons.length) return;

  elements.sortButtons.forEach((button) => {
    const buttonKey = button.dataset.sortKey;
    const header = button.closest('th');
    if (!buttonKey || !header) return;

    if (buttonKey === key) {
      button.dataset.sortDirection = direction;
      header.setAttribute('aria-sort', direction === 'asc' ? 'ascending' : 'descending');
    } else {
      delete button.dataset.sortDirection;
      header.setAttribute('aria-sort', 'none');
    }
  });
}

function computeDateRange(hearings) {
  const dates = hearings
    .map((hearing) => hearing.dateObj)
    .filter((date) => date instanceof Date && !Number.isNaN(date.getTime()));

  if (!dates.length) {
    return { min: null, max: null };
  }

  let min = dates[0];
  let max = dates[0];

  dates.forEach((date) => {
    if (date < min) min = date;
    if (date > max) max = date;
  });

  return { min, max };
}

function applyDateBounds() {
  const { min, max } = state.dateRange;
  if (!min || !max) return;

  const minIso = dateToInputValue(min);
  const maxIso = dateToInputValue(max);

  elements.startDate.min = minIso;
  elements.startDate.max = maxIso;
  elements.endDate.min = minIso;
  elements.endDate.max = maxIso;
}

function dateToInputValue(date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function showTableMessage(message) {
  const tbody = elements.hearingsTableBody;
  if (!tbody) return;
  tbody.innerHTML = '';
  const row = document.createElement('tr');
  const cell = document.createElement('td');
  cell.colSpan = 6;
  cell.className = 'empty-state';
  cell.textContent = message;
  row.append(cell);
  tbody.append(row);
}

function scrollToTable() {
  const table = document.getElementById('hearingsTable');
  if (!table) return;
  table.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
