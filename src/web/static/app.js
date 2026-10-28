let ramHistory = [];
let allProcesses = [];

async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    updateDashboard(data);
  } catch (err) {
    console.error('Error fetching status:', err);
  }
}

async function fetchProcesses() {
  try {
    const res = await fetch('/api/processes?limit=25');
    const data = await res.json();
    allProcesses = data.processes || [];
    filterProcesses();
  } catch (err) {
    console.error('Error fetching processes:', err);
  }
}

function updateDashboard(data) {
  const mem = data.memory;
  const isDaemon = data.daemon_running;

  // Daemon badge
  const daemonBadge = document.getElementById('daemon-badge');
  if (isDaemon) {
    daemonBadge.textContent = 'Daemon: Running (Active Guard)';
    daemonBadge.className = 'badge badge-active';
  } else {
    daemonBadge.textContent = 'Daemon: Standby';
    daemonBadge.className = 'badge badge-inactive';
  }

  // RAM Card
  const ram = mem.ram;
  document.getElementById('ram-summary').textContent = `${ram.used_gb} / ${ram.total_gb} GB`;
  document.getElementById('ram-used').textContent = `${ram.used_gb} GB`;
  document.getElementById('ram-avail').textContent = `${ram.available_gb} GB`;
  document.getElementById('ram-percent').textContent = `${ram.percent}%`;

  const ramBar = document.getElementById('ram-progress');
  ramBar.style.width = `${ram.percent}%`;
  ramBar.className = 'progress-bar ' + (
    ram.percent > 90 ? 'progress-red' :
    ram.percent > 80 ? 'progress-yellow' : 'progress-green'
  );

  // Add to history
  ramHistory.push(ram.percent);
  if (ramHistory.length > 30) {
    ramHistory.shift();
  }
  updateChart(ramHistory);

  // Swap Card
  const swap = mem.swap;
  document.getElementById('swap-summary').textContent = `${swap.used_gb} / ${swap.total_gb} GB`;
  document.getElementById('swap-used').textContent = `${swap.used_gb} GB`;
  document.getElementById('swap-free').textContent = `${swap.free_gb} GB`;
  document.getElementById('swap-percent').textContent = `${swap.percent}%`;
  document.getElementById('swap-progress').style.width = `${swap.percent}%`;

  // PSI
  const psi = mem.psi;
  document.getElementById('psi-10s').textContent = `${psi.some_avg10 || 0}%`;
  document.getElementById('psi-60s').textContent = `${psi.some_avg60 || 0}%`;
  document.getElementById('psi-300s').textContent = `${psi.some_avg300 || 0}%`;

  const psiPill = document.getElementById('psi-status-pill');
  if (psi.some_avg10 > 40) {
    psiPill.textContent = 'High Stall Risk';
    psiPill.className = 'pill pill-red';
  } else if (psi.some_avg10 > 15) {
    psiPill.textContent = 'Moderate Pressure';
    psiPill.className = 'pill pill-yellow';
  } else {
    psiPill.textContent = 'Low Pressure (Safe)';
    psiPill.className = 'pill pill-green';
  }

  // Status Banner
  const banner = document.getElementById('status-banner');
  const title = document.getElementById('status-title');
  const msg = document.getElementById('status-msg');

  title.textContent = `System Status: ${mem.status}`;
  msg.textContent = mem.status_message;

  if (mem.status === 'CRITICAL') {
    banner.className = 'status-banner status-critical';
  } else if (mem.status === 'HIGH_PRESSURE') {
    banner.className = 'status-banner status-high';
  } else if (mem.status === 'ELEVATED') {
    banner.className = 'status-banner status-elevated';
  } else {
    banner.className = 'status-banner status-healthy';
  }

  // Protected apps tags
  renderProtectedApps(data.config.protected_apps || []);
}

function updateChart(data) {
  if (data.length < 2) return;
  const width = 600;
  const height = 120;
  const step = width / (data.length - 1);

  let pathD = `M 0 ${height - (data[0] / 100) * height}`;
  for (let i = 1; i < data.length; i++) {
    const x = i * step;
    const y = height - (data[i] / 100) * height;
    pathD += ` L ${x} ${y}`;
  }

  const linePath = document.getElementById('chart-line');
  const areaPath = document.getElementById('chart-area');

  linePath.setAttribute('d', pathD);
  areaPath.setAttribute('d', `${pathD} L ${width} ${height} L 0 ${height} Z`);

  document.getElementById('chart-latest-val').textContent = `Current: ${data[data.length - 1]}%`;
}

function renderProtectedApps(apps) {
  const container = document.getElementById('protected-apps-list');
  container.innerHTML = '';
  apps.forEach(app => {
    const tag = document.createElement('div');
    tag.className = 'app-tag';
    tag.innerHTML = `
      <span>🛡️ ${escapeHtml(app)}</span>
      <span class="remove-btn" onclick="removeProtectedApp('${escapeHtml(app)}')" title="Remove protection">&times;</span>
    `;
    container.appendChild(tag);
  });
}

function filterProcesses() {
  const query = (document.getElementById('proc-search')?.value || '').toLowerCase();
  const filtered = allProcesses.filter(p =>
    p.name.toLowerCase().includes(query) ||
    String(p.pid).includes(query) ||
    (p.cmdline && p.cmdline.toLowerCase().includes(query))
  );
  renderProcessesTable(filtered);
}

function renderProcessesTable(procs) {
  const tbody = document.getElementById('processes-tbody');
  tbody.innerHTML = '';

  if (!procs || procs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;">No matching processes found</td></tr>';
    return;
  }

  procs.forEach(p => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${p.pid}</code></td>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>${p.memory_mb} MB</td>
      <td>${p.memory_percent}%</td>
      <td>${p.cpu_percent}%</td>
      <td>
        ${p.protected
          ? '<span class="protected-badge">🛡️ PROTECTED</span>'
          : '<span class="normal-badge">Normal</span>'}
      </td>
      <td>
        ${p.protected
          ? `<button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" onclick="removeProtectedApp('${escapeHtml(p.name)}')">Unprotect</button>`
          : `<button class="btn btn-primary" style="padding: 4px 8px; font-size: 0.75rem;" onclick="addProtectedAppDirect('${escapeHtml(p.name)}')">Protect</button>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function triggerOptimization() {
  const btn = document.getElementById('optimize-btn');
  btn.disabled = true;
  btn.textContent = 'Optimizing...';
  try {
    const res = await fetch('/api/optimize', { method: 'POST' });
    const data = await res.json();
    alert('Optimization Complete!\n' + (data.result.actions ? data.result.actions.join('\n') : 'Memory buffers synced.'));
    fetchStatus();
    fetchProcesses();
  } catch (err) {
    alert('Failed to optimize: ' + err);
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Optimize Memory Now';
  }
}

async function addCustomProtectedApp() {
  const input = document.getElementById('new-app-input');
  const val = input.value.trim();
  if (!val) return;
  await addProtectedAppDirect(val);
  input.value = '';
}

async function addProtectedAppDirect(app) {
  try {
    await fetch('/api/protect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app })
    });
    fetchStatus();
    fetchProcesses();
  } catch (err) {
    console.error(err);
  }
}

async function removeProtectedApp(app) {
  try {
    await fetch('/api/unprotect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app })
    });
    fetchStatus();
    fetchProcesses();
  } catch (err) {
    console.error(err);
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Initial fetch & loop
fetchStatus();
fetchProcesses();
setInterval(() => {
  fetchStatus();
  fetchProcesses();
}, 2500);
