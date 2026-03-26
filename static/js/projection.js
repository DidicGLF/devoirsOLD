/* ═══════════════════════════════════════════════════════════════════════════
   projection.js — Mode projection
   Utilisé à la fois dans index.html (vue /projection) et projection.html
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Vue dans l'app principale (onglet /projection) ────────────────────────────
if (typeof registerView !== 'undefined') {
  registerView('projection', renderProjectionView);
}

async function renderProjectionView(container) {
  try {
    State.classes = await api('GET', '/api/classes');
    State.devoirs = await api('GET', '/api/devoirs');
  } catch (err) {
    container.innerHTML = `<p class="empty-state">Erreur : ${err.message}</p>`;
    return;
  }

  const classesOptions = sortClasses(State.classes).map(c =>
    `<option value="${escHtml(c.nom)}">${escHtml(c.nom)}</option>`
  ).join('');

  container.innerHTML = `
    <h1 class="page-title">${iconProjection(22)} Projection</h1>
    <p class="page-subtitle">Sélectionnez les devoirs à projeter, puis ouvrez la projection dans un nouvel onglet.</p>

    <div class="proj-select-card">
      <div class="card-header">🎓 Classe</div>
      <div class="form-group mb-4">
        <select id="proj-main-classe" class="form-select">
          <option value="">— Choisir une classe —</option>
          ${classesOptions}
        </select>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <button id="proj-main-all" class="btn btn-secondary btn-sm">Tout sélectionner</button>
        <button id="proj-main-none" class="btn btn-secondary btn-sm">Tout désélectionner</button>
      </div>
      <div id="proj-main-list" class="proj-devoirs-checkboxes">
        <p class="empty-state" style="padding:16px 0">Choisissez une classe pour voir ses devoirs</p>
      </div>
    </div>

    <div style="display:flex;gap:10px;align-items:center">
      <button id="proj-main-launch" class="btn btn-primary btn-lg" disabled>
        ▶️ Ouvrir la projection
      </button>
      <span style="font-size:13px;color:var(--text-muted)">S'ouvre dans un nouvel onglet</span>
    </div>
  `;

  const classeSelect = document.getElementById('proj-main-classe');
  const listEl = document.getElementById('proj-main-list');
  const launchBtn = document.getElementById('proj-main-launch');

  classeSelect.addEventListener('change', () => {
    renderProjMainList(classeSelect.value, listEl, launchBtn);
  });

  document.getElementById('proj-main-all').addEventListener('click', () => {
    listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
    updateLaunchBtn(launchBtn, listEl);
  });

  document.getElementById('proj-main-none').addEventListener('click', () => {
    listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    updateLaunchBtn(launchBtn, listEl);
  });

  launchBtn.addEventListener('click', () => {
    const selectedDevoirs = getSelectedDevoirs(classeSelect.value, listEl);
    if (!selectedDevoirs.length) return;
    localStorage.setItem('projection_data', JSON.stringify({
      classe_nom: classeSelect.value,
      devoirs: selectedDevoirs,
      timestamp: Date.now()
    }));
    window.open('/projection', '_blank');
  });
}

function renderProjMainList(classeNom, listEl, launchBtn) {
  if (!classeNom) {
    listEl.innerHTML = '<p class="empty-state" style="padding:16px 0">Choisissez une classe</p>';
    launchBtn.disabled = true;
    return;
  }

  const devoirs = State.devoirs.filter(d => d.classe_nom === classeNom && d.statut !== 'Fait');

  if (!devoirs.length) {
    listEl.innerHTML = '<p class="empty-state" style="padding:16px 0">Aucun devoir à faire pour cette classe</p>';
    launchBtn.disabled = true;
    return;
  }

  listEl.innerHTML = devoirs.map(d => `
    <label class="proj-devoir-item">
      <input type="checkbox" checked data-index="${d.index}">
      <span class="proj-devoir-classe" style="${tagStyle(d.classe_couleur)}">${escHtml(d.classe_nom)}</span>
      <span class="proj-devoir-date">${formatDate(d.date)}</span>
      <span class="proj-devoir-contenu">${escHtml(d.contenu)}</span>
    </label>
  `).join('');

  listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => updateLaunchBtn(launchBtn, listEl));
  });

  updateLaunchBtn(launchBtn, listEl);
}

function updateLaunchBtn(launchBtn, listEl) {
  const checked = listEl.querySelectorAll('input[type="checkbox"]:checked').length;
  launchBtn.disabled = checked === 0;
}

function getSelectedDevoirs(classeNom, listEl) {
  const checked = [...listEl.querySelectorAll('input[type="checkbox"]:checked')];
  return checked.map(cb => {
    const idx = parseInt(cb.dataset.index);
    return State.devoirs.find(d => d.index === idx);
  }).filter(Boolean);
}

// ─────────────────────────────────────────────────────────────────────────────
// Logique de la page projection.html (onglet dédié)
// ─────────────────────────────────────────────────────────────────────────────
if (document.getElementById('proj-selection')) {
  initProjectionPage();
}

async function initProjectionPage() {
  const classeSelect = document.getElementById('proj-classe-select');
  const devoirsList = document.getElementById('proj-devoirs-list');
  const launchBtn = document.getElementById('proj-launch-btn');
  const selectionDiv = document.getElementById('proj-selection');
  const displayDiv = document.getElementById('proj-display');

  // Charger les classes
  let allClasses = [], allDevoirs = [];
  try {
    const [classes, devoirs] = await Promise.all([
      fetch('/api/classes').then(r => r.json()),
      fetch('/api/devoirs').then(r => r.json())
    ]);
    allClasses = classes;
    allDevoirs = devoirs;
  } catch (_) {}

  const sorted = [...allClasses].sort((a, b) => {
    const nA = parseInt(a.nom.match(/\d+/)?.[0] ?? 'NaN');
    const nB = parseInt(b.nom.match(/\d+/)?.[0] ?? 'NaN');
    const hasA = !isNaN(nA), hasB = !isNaN(nB);
    if (hasA && hasB) return nB - nA || a.nom.localeCompare(b.nom, 'fr');
    return hasA ? -1 : hasB ? 1 : a.nom.localeCompare(b.nom, 'fr');
  });
  sorted.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.nom;
    opt.textContent = c.nom;
    classeSelect.appendChild(opt);
  });

  // Pré-remplir depuis localStorage si données récentes (< 10 min)
  const stored = localStorage.getItem('projection_data');
  if (stored) {
    try {
      const data = JSON.parse(stored);
      if (Date.now() - data.timestamp < 600000 && data.devoirs && data.classe_nom) {
        afficherProjection(data.classe_nom, data.devoirs, selectionDiv, displayDiv);
        return;
      }
    } catch (_) {}
  }

  // Mode sélection
  classeSelect.addEventListener('change', () => {
    renderProjPageList(classeSelect.value, allDevoirs, devoirsList, launchBtn);
  });

  document.getElementById('proj-select-all').addEventListener('click', () => {
    devoirsList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
    updateProjLaunchBtn(launchBtn, devoirsList);
  });

  document.getElementById('proj-deselect-all').addEventListener('click', () => {
    devoirsList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    updateProjLaunchBtn(launchBtn, devoirsList);
  });

  launchBtn.addEventListener('click', () => {
    const selected = getProjSelectedDevoirs(allDevoirs, devoirsList);
    if (selected.length) {
      afficherProjection(classeSelect.value, selected, selectionDiv, displayDiv);
    }
  });
}

function renderProjPageList(classeNom, allDevoirs, listEl, launchBtn) {
  if (!classeNom) {
    listEl.innerHTML = '<p class="empty-state">Choisissez une classe</p>';
    launchBtn.disabled = true;
    return;
  }

  const devoirs = allDevoirs.filter(d => d.classe_nom === classeNom && d.statut !== 'Fait');

  if (!devoirs.length) {
    listEl.innerHTML = '<p class="empty-state">Aucun devoir à faire pour cette classe</p>';
    launchBtn.disabled = true;
    return;
  }

  listEl.innerHTML = devoirs.map(d => {
    const couleur = d.classe_couleur || '#808080';
    const { r, g, b } = hexToRgbProj(couleur);
    const tagBg = `rgba(${r},${g},${b},0.25)`;
    return `
      <label class="proj-devoir-item">
        <input type="checkbox" checked data-index="${d.index}">
        <span class="proj-devoir-classe" style="background:${tagBg}">${escHtmlProj(d.classe_nom)}</span>
        <span class="proj-devoir-date">${formatDateProj(d.date)}</span>
        <span class="proj-devoir-contenu">${escHtmlProj(d.contenu)}</span>
      </label>
    `;
  }).join('');

  listEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => updateProjLaunchBtn(launchBtn, listEl));
  });
  updateProjLaunchBtn(launchBtn, listEl);
}

function updateProjLaunchBtn(launchBtn, listEl) {
  launchBtn.disabled = listEl.querySelectorAll('input[type="checkbox"]:checked').length === 0;
}

function getProjSelectedDevoirs(allDevoirs, listEl) {
  return [...listEl.querySelectorAll('input[type="checkbox"]:checked')]
    .map(cb => allDevoirs.find(d => d.index === parseInt(cb.dataset.index)))
    .filter(Boolean);
}

function afficherProjection(classeNom, devoirs, selectionDiv, displayDiv) {
  selectionDiv.classList.add('hidden');
  displayDiv.classList.remove('hidden');

  document.getElementById('proj-display-classe').innerHTML = `${iconProjection(22)} ${escHtmlProj(classeNom)}`;

  // Grouper par date
  const byDate = {};
  devoirs.forEach(d => {
    if (!byDate[d.date]) byDate[d.date] = [];
    byDate[d.date].push(d);
  });

  const sortedDates = Object.keys(byDate).sort();
  const content = document.getElementById('proj-display-content');

  content.innerHTML = sortedDates.map(date => {
    const items = byDate[date].map(d =>
      `<div class="proj-devoir-line">
        <span class="proj-devoir-bullet">›</span>
        <span>${escHtmlProj(d.contenu)}</span>
      </div>`
    ).join('');

    return `
      <div class="proj-date-group">
        <div class="proj-date-title">📅 Séance du ${formatDateProj(date)}</div>
        ${items}
      </div>
    `;
  }).join('');

  document.getElementById('proj-close-btn').addEventListener('click', () => {
    displayDiv.classList.add('hidden');
    selectionDiv.classList.remove('hidden');
    localStorage.removeItem('projection_data');
  });
}

// Helpers autonomes pour projection.html (sans dépendance à app.js)
if (typeof iconProjection === 'undefined') {
  window.iconProjection = function(size = 18) {
    return `<span style="font-size:${size}px;line-height:1;vertical-align:middle">🖥️</span>`;
  };
}
function hexToRgbProj(hex) {
  const c = hex.replace('#', '');
  return {
    r: parseInt(c.substring(0, 2), 16),
    g: parseInt(c.substring(2, 4), 16),
    b: parseInt(c.substring(4, 6), 16)
  };
}
function escHtmlProj(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatDateProj(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}
