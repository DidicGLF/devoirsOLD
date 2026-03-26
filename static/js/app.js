/* ═══════════════════════════════════════════════════════════════════════════
   app.js — Core: API helper, Router, Toast, Modal, State
   ═══════════════════════════════════════════════════════════════════════════ */

// ── State global ─────────────────────────────────────────────────────────────
const State = {
  classes: [],
  devoirs: [],
  config: {},
  sortMode: 'manuel',
};

// ── API helper ────────────────────────────────────────────────────────────────
async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = `Erreur HTTP ${res.status}`;
    try { const e = await res.json(); msg = e.error || msg; } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

// ── Couleur helper ────────────────────────────────────────────────────────────
function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  const r = parseInt(clean.substring(0, 2), 16);
  const g = parseInt(clean.substring(2, 4), 16);
  const b = parseInt(clean.substring(4, 6), 16);
  return { r, g, b };
}

function colorStyle(hex, alpha = 0.15) {
  const { r, g, b } = hexToRgb(hex);
  return `background: rgba(${r},${g},${b},${alpha}); border-color: rgba(${r},${g},${b},0.35);`;
}

function tagStyle(hex) {
  const { r, g, b } = hexToRgb(hex);
  return `background: rgba(${r},${g},${b},0.2); color: rgb(${Math.max(0,r-40)},${Math.max(0,g-40)},${Math.max(0,b-40)});`;
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.animation = 'none';
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    el.style.transition = 'opacity .2s, transform .2s';
    setTimeout(() => el.remove(), 220);
  }, duration);
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(html) {
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

function confirmer({ titre, message, labelOk = 'Confirmer', danger = false }) {
  return new Promise((resolve) => {
    openModal(`
      <div class="modal-title">${titre}</div>
      <p style="color:var(--text-secondary);font-size:14px">${message}</p>
      <div class="modal-actions">
        <button class="btn btn-secondary" id="modal-non">Annuler</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="modal-oui">${labelOk}</button>
      </div>
    `);
    document.getElementById('modal-oui').addEventListener('click', () => { closeModal(); resolve(true); });
    document.getElementById('modal-non').addEventListener('click', () => { closeModal(); resolve(false); });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modal-overlay')) closeModal();
  });
});

// ── Icône Projection ──────────────────────────────────────────────────────────
function iconProjection(size = 18) {
  return `<span style="font-size:${size}px;line-height:1;vertical-align:middle">🖥️</span>`;
}

// ── Tri des classes par niveau (6° > 5° > 4° > 3°, sans niveau en dernier) ───
function sortClasses(classes) {
  return [...classes].sort((a, b) => {
    const nA = parseInt(a.nom.match(/\d+/)?.[0] ?? 'NaN');
    const nB = parseInt(b.nom.match(/\d+/)?.[0] ?? 'NaN');
    const hasA = !isNaN(nA), hasB = !isNaN(nB);
    if (hasA && hasB) return nB - nA || a.nom.localeCompare(b.nom, 'fr');
    if (hasA) return -1;
    if (hasB) return 1;
    return a.nom.localeCompare(b.nom, 'fr');
  });
}

// ── Auto-resize textarea ──────────────────────────────────────────────────────
function autoResizeTextarea(el) {
  el.style.height = '0';
  el.style.height = el.scrollHeight + 'px';
}

// ── Formatter date ────────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function statutBadge(statut) {
  if (statut === 'Fait') return `<span class="badge badge-fait">✔️ Fait</span>`;
  if (statut === 'En cours') return `<span class="badge badge-en-cours">⏳ En cours</span>`;
  return `<span class="badge badge-pas-fait">❌ Pas fait</span>`;
}

// ── Router ────────────────────────────────────────────────────────────────────
const views = {};

function registerView(name, renderFn) {
  views[name] = renderFn;
}

function navigate(path) {
  location.hash = path;
}

function resolveRoute() {
  const path = location.hash.replace('#', '') || '/';
  const map = {
    '/':          'accueil',
    '/classes':   'classes',
    '/devoirs':   'devoirs',
    '/projection':'projection',
    '/parametres':'parametres',
  };
  const name = map[path] || 'accueil';

  // Active nav link
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.route === path);
  });

  const content = document.getElementById('app-content');
  if (views[name]) {
    views[name](content);
  } else {
    content.innerHTML = '<p class="empty-state">Page introuvable</p>';
  }
}

// ── ENT link dans sidebar ─────────────────────────────────────────────────────
async function loadEntLink() {
  try {
    const config = await api('GET', '/api/config');
    State.config = config;
    const lien = config.lien_ent;
    if (lien && lien.url) {
      const link = document.getElementById('ent-link');
      const text = document.getElementById('ent-link-text');
      link.href = lien.url;
      text.textContent = lien.texte || 'ENT';
      link.classList.remove('hidden');
    }
  } catch (_) {}
}

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener('hashchange', resolveRoute);

document.addEventListener('DOMContentLoaded', async () => {
  await loadEntLink();
  resolveRoute();
});
