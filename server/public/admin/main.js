const fmtTime = (ts) => {
  if (!ts) return '-';
  const d = new Date(Number(ts) * 1000);
  return d.toLocaleString();
};

const badge = (status) => {
  const s = status || 'unknown';
  return `<span class="badge ${s}">${s}</span>`;
};

let currentSort = { key: 'timestamp', dir: 'desc' };

const fetchMachines = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.os) params.set('os', filters.os);
  if (filters.hasIssues !== '') params.set('hasIssues', filters.hasIssues);
  if (filters.q) params.set('q', filters.q);
  const res = await fetch(`/admin/api/machines?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to load machines');
  const data = await res.json();
  return data.items || [];
};

const renderTable = (items) => {
  const tbody = document.querySelector('#machines-table tbody');
  tbody.innerHTML = items.map((x) => {
    const c = x.checks || {};
    return `<tr data-id="${x.machine_id}">
      <td>${x.hostname || ''}</td>
      <td>${x.machine_id}</td>
      <td>${x.os || ''}</td>
      <td><div class="timestamp">${fmtTime(x.timestamp)}</div></td>
      <td>${badge(c?.disk_encryption?.status)}</td>
      <td>${badge(c?.os_updates?.status)}</td>
      <td>${badge(c?.antivirus?.status)}</td>
      <td>${badge(c?.sleep_policy?.status)}</td>
    </tr>`;
  }).join('');

  // Row click to open details
  tbody.querySelectorAll('tr').forEach((tr) => {
    tr.addEventListener('click', async () => {
      const id = tr.getAttribute('data-id');
      const res = await fetch(`/admin/api/machines/${encodeURIComponent(id)}`);
      if (res.ok) {
        const data = await res.json();
        alert(JSON.stringify(data, null, 2));
      }
    });
  });
};

const sortItems = (items, key, dir) => {
  const mult = dir === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    const va = (a[key] ?? '').toString().toLowerCase();
    const vb = (b[key] ?? '').toString().toLowerCase();
    if (va < vb) return -1 * mult;
    if (va > vb) return 1 * mult;
    return 0;
  });
};

const updateStats = (items) => {
  const total = items.length;
  const issues = items.filter((x) => Object.values(x.checks || {}).some((c) => (c?.status || 'unknown') === 'issue')).length;
  document.getElementById('stats').textContent = `Machines: ${total} • With issues: ${issues}`;
};

const loadAndRender = async () => {
  const filters = {
    os: document.getElementById('filter-os').value,
    hasIssues: document.getElementById('filter-issues').value,
    q: document.getElementById('filter-q').value.trim()
  };
  const items = await fetchMachines(filters);
  const sorted = sortItems(items, currentSort.key, currentSort.dir);
  updateStats(sorted);
  renderTable(sorted);
};

const initSorting = () => {
  document.querySelectorAll('#machines-table th[data-sort]').forEach((th) => {
    th.addEventListener('click', () => {
      const key = th.getAttribute('data-sort');
      if (currentSort.key === key) {
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
      } else {
        currentSort.key = key;
        currentSort.dir = 'asc';
      }
      loadAndRender();
    });
  });
};

const initFilters = () => {
  document.getElementById('apply-filters').addEventListener('click', () => loadAndRender());
  document.getElementById('filter-q').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loadAndRender();
  });
};

window.addEventListener('DOMContentLoaded', async () => {
  initSorting();
  initFilters();
  await loadAndRender();
  setInterval(loadAndRender, 30000); // refresh every 30s
});
