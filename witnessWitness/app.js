const state = {
  hearings: [],
  witnessMap: new Map(),
  sortedWitnesses: [],
  filters: {
    witnessQuery: '',
    committee: 'all',
    tag: 'all',
    startDate: null,
    endDate: null,
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
  attachEventListeners();

  try {
    const text = await fetchCSV('Senate Committee Hearings.csv');
    const rows = parseCSV(text);

    if (!rows.length) {
      showTableMessage('No data rows were found in the CSV.');
      return;
    }

    const [headerRow, ...dataRows] = rows;
    const columns = headerRow.map((col) => col.trim());

    const hearings = dataRows
      .map((row) => rowToHearing(row, columns))
      .filter(Boolean);

    if (!hearings.length) {
      showTableMessage('No hearings could be parsed from the CSV.');
      return;
    }

    state.hearings = hearings;
    elements.totalHearings.textContent = hearings.length.toLocaleString();

    state.dateRange = computeDateRange(hearings);
    applyDateBounds();

    state.witnessMap = buildWitnessMap(hearings);
    state.sortedWitnesses = Array.from(state.witnessMap.values()).sort(sortWitnesses);
    elements.uniqueWitnesses.textContent = state.sortedWitnesses.length.toLocaleString();

    populateFilterOptions();
    renderWitnessList();
    applyFilters();
  } catch (error) {
    console.error('Failed to load hearings CSV', error);
    showTableMessage('Unable to load the CSV file. Ensure you are running a local server.');
  }
}

function attachEventListeners() {
  elements.witnessSearch.addEventListener('input', (event) => {
    state.filters.witnessQuery = event.target.value.trim();
    renderWitnessList();
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
    };
    state.selectedWitnessKey = null;

    elements.witnessSearch.value = '';
    elements.committeeFilter.value = 'all';
    elements.tagFilter.value = 'all';
    elements.startDate.value = '';
    elements.endDate.value = '';

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
}

async function fetchCSV(path) {
  const response = await fetch(path, {
    headers: { 'Cache-Control': 'no-cache' },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status} while fetching ${path}`);
  }

  return response.text();
}

function parseCSV(rawText) {
  if (!rawText) return [];

  let text = rawText;
  if (text.charCodeAt(0) === 0xfeff) {
    text = text.slice(1);
  }

  text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  const rows = [];
  let currentCell = '';
  let currentRow = [];
  let withinQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const nextChar = text[index + 1];

    if (char === '"') {
      if (withinQuotes && nextChar === '"') {
        currentCell += '"';
        index += 1;
      } else {
        withinQuotes = !withinQuotes;
      }
      continue;
    }

    if (char === ',' && !withinQuotes) {
      currentRow.push(currentCell);
      currentCell = '';
      continue;
    }

    if (char === '\n' && !withinQuotes) {
      currentRow.push(currentCell);
      rows.push(currentRow);
      currentRow = [];
      currentCell = '';
      continue;
    }

    currentCell += char;
  }

  // Push the last cell if there's any residue.
  if (currentCell.length > 0 || currentRow.length > 0) {
    currentRow.push(currentCell);
    rows.push(currentRow);
  }

  return rows;
}

function rowToHearing(row, columns) {
  if (!row || row.every((cell) => cell.trim() === '')) {
    return null;
  }

  const record = {};
  columns.forEach((column, index) => {
    record[column] = row[index] || '';
  });

  const dateString = record.Date ? record.Date.trim() : '';
  const parsedDate = parseDateString(dateString);

  const witnesses = normalizeWitnesses(record.Witnesses || '');
  const tags = Array.from(new Set(normalizeTags(record.Tags || '')));

  return {
    date: dateString,
    dateObj: parsedDate,
    title: (record.Title || '').trim(),
    committee: (record.Committee || '').trim(),
    pageUrl: (record.URL || '').trim(),
    videoUrl: (record['Video Url'] || '').trim(),
    tags,
    witnesses,
    witnessKeys: witnesses.map((name) => nameToKey(name)),
  };
}

function parseDateString(value) {
  if (!value) return null;
  const parts = value.split('/');
  if (parts.length < 3) return null;

  const month = Number(parts[0]);
  const day = Number(parts[1]);
  let year = parts[2];

  if (Number.isNaN(month) || Number.isNaN(day)) return null;

  if (year.length === 2) {
    const numeric = Number(year);
    year = numeric >= 70 ? 1900 + numeric : 2000 + numeric;
  } else {
    year = Number(year);
  }

  if (!year || Number.isNaN(year)) return null;

  return new Date(year, month - 1, day);
}

function normalizeWitnesses(raw) {
  if (!raw) return [];

  return raw
    .replace(/\u2022|\u25cf|\*/g, '\n')
    .replace(/\r/g, '')
    .split(/\n+/)
    .flatMap((entry) => entry.split(/\s*;\s*/))
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function normalizeTags(raw) {
  if (!raw) return [];
  const cleaned = raw.replace(/\r|\n/g, '').trim();
  if (!cleaned) return [];

  const candidate = cleaned.replace(/""/g, '"');

  try {
    const parsed = JSON.parse(candidate);
    if (Array.isArray(parsed)) {
      return parsed.map((tag) => String(tag).trim()).filter(Boolean);
    }
  } catch (error) {
    // Fall back to manual parsing when JSON.parse fails.
  }

  const fallback = candidate
    .replace(/^\[/, '')
    .replace(/\]$/, '')
    .replace(/[\"]/g, '');

  return fallback
    .split(/,\s*/)
    .map((tag) => tag.replace(/^'+|'+$/g, '').trim())
    .filter(Boolean);
}

function buildWitnessMap(hearings) {
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
      };

      if (!entry.name || entry.name.length < name.length) {
        entry.name = name;
      }

      entry.hearings.push(hearing);
      entry.count += 1;

      map.set(key, entry);
    });
  });

  return map;
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
  container.innerHTML = '';

  if (!state.sortedWitnesses.length) {
    container.textContent = 'No witnesses found.';
    return;
  }

  const query = state.filters.witnessQuery.toLowerCase();
  const matching = state.sortedWitnesses.filter((witness) =>
    !query || witness.name.toLowerCase().includes(query),
  );

  if (!matching.length) {
    container.textContent = 'No witnesses match that search.';
    return;
  }

  matching.forEach((witness) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'witness-item';
    if (state.selectedWitnessKey === witness.key) {
      button.classList.add('active');
    }

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

    container.append(button);
  });
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
    cell.colSpan = 5;
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

  if (!parts.length) {
    return '.';
  }

  return ` with ${parts.join(', ')}.`;
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
  cell.colSpan = 5;
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
