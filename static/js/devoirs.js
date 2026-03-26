/* ═══════════════════════════════════════════════════════════════════════════
   devoirs.js — Gestion des devoirs + drag & drop
   ═══════════════════════════════════════════════════════════════════════════ */

registerView('devoirs', renderDevoirs);

let dropIndicatorEl = null;
let dragState = null;   // état de drag unifié (souris + tactile)
let dragWasActive = false; // vrai si le dernier mousedown s'est terminé en drag

// ── Render ────────────────────────────────────────────────────────────────────
async function renderDevoirs(container) {
  // Charger les classes pour le select
  try {
    State.classes = await api('GET', '/api/classes');
  } catch (_) {}

  const classesOptions = sortClasses(State.classes).map(c =>
    `<option value="${escHtml(c.nom)}">${escHtml(c.nom)}</option>`
  ).join('');

  const today = new Date().toISOString().split('T')[0];

  container.innerHTML = `
    <h1 class="page-title">📝 Gestion des devoirs</h1>
    <p class="page-subtitle">Ajoutez, modifiez et suivez les devoirs de vos classes.</p>

    <!-- Zone figée au scroll -->
    <div class="devoirs-sticky">

    <!-- Formulaire d'ajout -->
    <div class="add-form-card">
      <div class="add-form-row" style="flex-wrap:wrap">
        <div class="form-group" style="flex:0 0 auto;min-width:130px">
          <label for="dv-classe">Classe</label>
          <select id="dv-classe" class="form-select" style="min-width:130px">
            <option value="">— Classe —</option>
            ${classesOptions}
          </select>
        </div>
        <div class="form-group" style="flex:0 0 auto">
          <label for="dv-date">Date</label>
          <input id="dv-date" class="form-control" type="date" value="${today}">
        </div>
        <div class="form-group" style="flex:1;min-width:200px">
          <label for="dv-contenu">Contenu <span style="font-size:11px;color:var(--text-muted)">(Ctrl+Entrée pour ajouter)</span></label>
          <textarea id="dv-contenu" class="form-control" placeholder="Décrire le devoir…" rows="1" maxlength="1000" style="resize:none;overflow:hidden"></textarea>
        </div>
        <button id="dv-add-btn" class="btn btn-primary" style="align-self:flex-end">Ajouter</button>
      </div>
    </div>

    <!-- Barre d'outils tri + projection -->
    <div class="devoirs-toolbar">
      <span style="font-size:13px;color:var(--text-secondary);font-weight:500;">Trier :</span>
      <button class="sort-btn active" data-sort="manuel">Manuel</button>
      <button class="sort-btn" data-sort="date">Date</button>
      <button class="sort-btn" data-sort="classe">Classe</button>
      <div class="sort-separator"></div>
      <button id="dv-pause-btn" class="btn btn-secondary btn-sm">⏸ Pause</button>
      <button id="dv-proj-btn" class="btn btn-secondary btn-sm">${iconProjection(14)} Projection</button>
    </div>

    </div><!-- fin .devoirs-sticky -->

    <!-- Liste des devoirs -->
    <div id="devoirs-list" class="devoirs-list"></div>
  `;

  // Bind add
  document.getElementById('dv-add-btn').addEventListener('click', addDevoir);
  const formTextarea = document.getElementById('dv-contenu');
  formTextarea.addEventListener('input', () => autoResizeTextarea(formTextarea));
  formTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); addDevoir(); }
  });

  // Bind sort
  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      State.sortMode = btn.dataset.sort;
      renderDevoirsList(State.devoirs);
    });
  });

  // Pause
  document.getElementById('dv-pause-btn').addEventListener('click', async () => {
    try {
      const newPause = await api('POST', '/api/devoirs', { type: 'pause', contenu: 'Pause' });
      State.devoirs.push(newPause);
      appendCardToList(newPause);
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  // Projection
  document.getElementById('dv-proj-btn').addEventListener('click', () => {
    window.open('/projection', '_blank');
  });

  // Ombre sur la zone sticky quand elle est collée en haut
  const sticky = container.querySelector('.devoirs-sticky');
  const sentinel = document.createElement('div');
  sentinel.style.cssText = 'height:1px;margin-top:-1px;pointer-events:none';
  container.insertBefore(sentinel, sticky);
  new IntersectionObserver(([entry]) => {
    sticky.classList.toggle('is-stuck', !entry.isIntersecting);
  }).observe(sentinel);

  await loadDevoirs();
}

async function loadDevoirs() {
  try {
    State.devoirs = await api('GET', '/api/devoirs');
    renderDevoirsList(State.devoirs);
  } catch (err) {
    toast('Erreur chargement devoirs : ' + err.message, 'error');
  }
}

function getSortedDevoirs(devoirs) {
  const list = [...devoirs];
  if (State.sortMode === 'date') {
    list.sort((a, b) => a.date.localeCompare(b.date));
  } else if (State.sortMode === 'classe') {
    list.sort((a, b) => a.classe_nom.localeCompare(b.classe_nom));
  }
  return list;
}

function renderDevoirsList(devoirs, animate = true) {
  const container = document.getElementById('devoirs-list');
  if (!container) return;

  const sorted = getSortedDevoirs(devoirs);

  if (!sorted.length) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="empty-state-icon">📝</span>
        Aucun devoir. Ajoutez-en un ci-dessus.
      </div>`;
    return;
  }

  container.innerHTML = '';

  sorted.forEach((devoir, displayIdx) => {
    const card = devoir.type === 'pause'
      ? createPauseCard(devoir, devoir.index)
      : createDevoirCard(devoir, devoir.index);
    if (animate) {
      card.classList.add('card-animate');
      card.style.animationDelay = `${displayIdx * 60}ms`;
      card.addEventListener('animationend', () => {
        card.classList.remove('card-animate');
        card.style.animationDelay = '';
      }, { once: true });
    }
    container.appendChild(card);
  });

  container.querySelectorAll('.dv-contenu-input').forEach(autoResizeTextarea);

  if (State.sortMode === 'manuel') setupDragDrop(container);
}

// Supprime une carte avec animation et met à jour les indices dans le DOM et State
function removeCardFromDOM(card, deletedIndex) {
  const height = card.offsetHeight;
  card.style.transition = 'opacity .18s ease, transform .18s ease';
  card.style.opacity = '0';
  card.style.transform = 'translateX(16px)';

  setTimeout(() => {
    card.style.transition = 'max-height .18s ease, padding .18s ease, margin .18s ease';
    card.style.overflow = 'hidden';
    card.style.maxHeight = height + 'px';
    requestAnimationFrame(() => {
      card.style.maxHeight = '0';
      card.style.paddingTop = '0';
      card.style.paddingBottom = '0';
      card.style.marginBottom = '0';
    });
    setTimeout(() => {
      card.remove();
      // Mettre à jour State
      State.devoirs = State.devoirs.filter(d => d.index !== deletedIndex);
      State.devoirs.forEach(d => { if (d.index > deletedIndex) d.index--; });
      // Mettre à jour data-index sur les cartes restantes
      document.querySelectorAll('#devoirs-list [data-index]').forEach(c => {
        const i = parseInt(c.dataset.index);
        if (i > deletedIndex) c.dataset.index = i - 1;
      });
      // Afficher empty state si plus rien
      const list = document.getElementById('devoirs-list');
      if (list && !list.querySelector('[data-index]')) {
        list.innerHTML = `<div class="empty-state"><span class="empty-state-icon">📝</span>Aucun devoir. Ajoutez-en un ci-dessus.</div>`;
      }
    }, 200);
  }, 180);
}

// Ajoute une seule carte à la liste avec animation
function appendCardToList(devoir) {
  const container = document.getElementById('devoirs-list');
  if (!container) return;
  // Supprimer l'empty state s'il est présent
  container.querySelector('.empty-state')?.remove();

  const card = devoir.type === 'pause'
    ? createPauseCard(devoir, devoir.index)
    : createDevoirCard(devoir, devoir.index);
  card.classList.add('card-animate');
  card.addEventListener('animationend', () => card.classList.remove('card-animate'), { once: true });
  container.appendChild(card);
  container.querySelectorAll('.dv-contenu-input').forEach(autoResizeTextarea);
  if (State.sortMode === 'manuel') setupDragDrop(container);
}

function createPauseCard(devoir, realIndex) {
  const card = document.createElement('div');
  card.className = 'pause-card';
  card.dataset.index = realIndex;

  card.innerHTML = `
    <div class="pause-divider-line"></div>
    <input class="pause-contenu-input"
           value="${escHtml(devoir.contenu)}"
           data-original="${escHtml(devoir.contenu)}"
           title="Cliquer pour renommer"
           aria-label="Libellé de la pause">
    <div class="pause-divider-line"></div>
    <button class="btn-icon danger dv-delete-btn" title="Supprimer">🗑️</button>
  `;

  const input = card.querySelector('.pause-contenu-input');
  // Ajuster la largeur dynamiquement
  function resizeInput() {
    input.style.width = Math.max(60, input.value.length * 8) + 'px';
  }
  resizeInput();
  input.addEventListener('input', resizeInput);
  input.addEventListener('blur', async () => {
    const idx = parseInt(card.dataset.index);
    const val = input.value.trim();
    if (!val || val === input.dataset.original) { input.value = input.dataset.original; return; }
    try {
      await api('PUT', `/api/devoirs/${idx}`, { contenu: val });
      input.dataset.original = val;
      const d = State.devoirs.find(d => d.index === idx);
      if (d) d.contenu = val;
    } catch (err) { toast(err.message, 'error'); input.value = input.dataset.original; }
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') input.blur();
    if (e.key === 'Escape') { input.value = input.dataset.original; input.blur(); }
  });

  card.querySelector('.dv-delete-btn').addEventListener('click', async (e) => {
    e.stopPropagation();
    const ok = await confirmer({ titre: '🗑️ Supprimer la pause', message: 'Supprimer cette pause ?', labelOk: 'Supprimer', danger: true });
    if (!ok) return;
    const idx = parseInt(card.dataset.index);
    try {
      await api('DELETE', `/api/devoirs/${idx}`);
      removeCardFromDOM(card, idx);
    } catch (err) { toast(err.message, 'error'); }
  });

  [input, card.querySelector('.dv-delete-btn')].forEach(el => {
    el.addEventListener('mousedown', (e) => e.stopPropagation());
  });

  return card;
}

function createDevoirCard(devoir, realIndex) {
  const card = document.createElement('div');
  card.className = 'devoir-card';
  card.dataset.index = realIndex;
  card.style.cssText = colorStyle(devoir.classe_couleur || '#808080');

  const classeStyle = tagStyle(devoir.classe_couleur || '#808080');
  const dateStr = formatDate(devoir.date);
  const isoDate = devoir.date;

  card.innerHTML = `
    <input type="checkbox" class="devoir-checkbox" ${devoir.statut === 'Fait' ? 'checked' : ''}
           title="Marquer comme ${devoir.statut === 'Fait' ? 'pas fait' : 'fait'}">
    <span class="devoir-classe-tag" style="${classeStyle}">${escHtml(devoir.classe_nom)}</span>
    <span class="devoir-date">
      <input type="date" class="dv-date-input" value="${isoDate}">
    </span>
    <textarea class="inline-edit dv-contenu-input"
              data-original="${escHtml(devoir.contenu)}"
              aria-label="Contenu du devoir"
              rows="1">${escHtml(devoir.contenu)}</textarea>
    ${statutBadge(devoir.statut)}
    <button class="btn-icon danger dv-delete-btn" title="Supprimer">🗑️</button>
  `;

  // Checkbox statut — mise à jour du badge en place, pas de rechargement
  const checkbox = card.querySelector('.devoir-checkbox');
  checkbox.addEventListener('change', async (e) => {
    e.stopPropagation();
    const idx = parseInt(card.dataset.index);
    const newStatut = checkbox.checked ? 'Fait' : 'Pas fait';
    try {
      await api('PUT', `/api/devoirs/${idx}`, { statut: newStatut });
      // Mettre à jour le badge en place
      const badge = card.querySelector('.badge');
      if (badge) badge.outerHTML = statutBadge(newStatut);
      // Mettre à jour State
      const d = State.devoirs.find(d => d.index === idx);
      if (d) d.statut = newStatut;
    } catch (err) {
      toast(err.message, 'error');
      checkbox.checked = !checkbox.checked;
    }
  });

  // Édition inline contenu (textarea)
  const contenuInput = card.querySelector('.dv-contenu-input');

  contenuInput.addEventListener('input', () => autoResizeTextarea(contenuInput));

  contenuInput.addEventListener('blur', async () => {
    const idx = parseInt(card.dataset.index);
    const val = contenuInput.value.trim();
    if (val === contenuInput.dataset.original || !val) {
      contenuInput.value = contenuInput.dataset.original;
      autoResizeTextarea(contenuInput);
      return;
    }
    try {
      await api('PUT', `/api/devoirs/${idx}`, { contenu: val });
      contenuInput.dataset.original = val;
      const d = State.devoirs.find(d => d.index === idx);
      if (d) d.contenu = val;
      toast('Devoir mis à jour', 'success');
    } catch (err) {
      toast(err.message, 'error');
      contenuInput.value = contenuInput.dataset.original;
      autoResizeTextarea(contenuInput);
    }
  });
  contenuInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); contenuInput.blur(); }
    if (e.key === 'Escape') { contenuInput.value = contenuInput.dataset.original; autoResizeTextarea(contenuInput); contenuInput.blur(); }
  });

  // Édition date — mise à jour State uniquement, pas de rechargement
  const dateInput = card.querySelector('.dv-date-input');
  dateInput.addEventListener('change', async () => {
    const idx = parseInt(card.dataset.index);
    try {
      await api('PUT', `/api/devoirs/${idx}`, { date: dateInput.value });
      const d = State.devoirs.find(d => d.index === idx);
      if (d) d.date = dateInput.value;
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  // Supprimer — animation en place, pas de rechargement
  card.querySelector('.dv-delete-btn').addEventListener('click', async (e) => {
    e.stopPropagation();
    const ok = await confirmer({
      titre: '🗑️ Supprimer le devoir',
      message: 'Supprimer ce devoir définitivement ?',
      labelOk: 'Supprimer',
      danger: true,
    });
    if (!ok) return;
    const idx = parseInt(card.dataset.index);
    try {
      await api('DELETE', `/api/devoirs/${idx}`);
      toast('Devoir supprimé', 'success');
      removeCardFromDOM(card, idx);
    } catch (err) {
      toast(err.message, 'error');
    }
  });

  // Clic sur la carte (hors champs) → copier le contenu
  card.addEventListener('click', (e) => {
    if (dragWasActive) return;
    if (e.target.closest('input, textarea, button, select')) return;
    navigator.clipboard.writeText(devoir.contenu)
      .then(() => toast('Contenu copié', 'success'))
      .catch(() => toast('Impossible de copier', 'error'));
  });

  // Empêcher le drag sur les inputs/buttons
  [checkbox, contenuInput, dateInput, card.querySelector('.dv-delete-btn')].forEach(el => {
    el.addEventListener('mousedown', (e) => e.stopPropagation());
  });

  return card;
}

// ── Drag & Drop (mousedown/mousemove/mouseup + touch unifié) ──────────────────
//
// Remplace l'API HTML5 drag (non fiable sur Linux) par un suivi de souris/tactile
// géré manuellement : plus robuste sur tous les OS/navigateurs.

function setupDragDrop(container) {
  container.querySelectorAll('.devoir-card, .pause-card').forEach(card => {
    card.addEventListener('mousedown', onDragPointerDown);
    card.addEventListener('touchstart', onDragPointerDown, { passive: false });
  });
}

function getEventPos(e) {
  if (e.touches)        return { x: e.touches[0].clientX,        y: e.touches[0].clientY };
  if (e.changedTouches) return { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY };
  return { x: e.clientX, y: e.clientY };
}

function onDragPointerDown(e) {
  if (e.button !== undefined && e.button !== 0) return; // clic droit ignoré
  if (e.target.closest('input, textarea, button, select')) return;
  if (State.sortMode !== 'manuel') return;

  const card = e.currentTarget;
  const { x, y } = getEventPos(e);
  const rect = card.getBoundingClientRect();

  dragState = {
    card,
    sourceIndex: parseInt(card.dataset.index),
    offsetX: x - rect.left,
    offsetY: y - rect.top,
    startX: x,
    startY: y,
    ghost: null,
    active: false,
    isTouch: !!e.touches,
  };

  if (e.touches) {
    document.addEventListener('touchmove', onDragPointerMove, { passive: false });
    document.addEventListener('touchend',  onDragPointerUp);
    document.addEventListener('touchcancel', onDragPointerUp);
  } else {
    document.addEventListener('mousemove', onDragPointerMove);
    document.addEventListener('mouseup',   onDragPointerUp);
  }
}

function onDragPointerMove(e) {
  if (!dragState) return;
  e.preventDefault();

  const { x, y } = getEventPos(e);

  // Seuil de 5px avant de considérer que c'est un drag
  if (!dragState.active) {
    const dx = x - dragState.startX;
    const dy = y - dragState.startY;
    if (dx * dx + dy * dy < 25) return;
    dragState.active = true;

    // Créer le fantôme
    const rect = dragState.card.getBoundingClientRect();
    const ghost = dragState.card.cloneNode(true);
    Object.assign(ghost.style, {
      position:     'fixed',
      width:        rect.width + 'px',
      opacity:      '0.85',
      pointerEvents:'none',
      zIndex:       '9999',
      transition:   'none',
      boxShadow:    '0 8px 24px rgba(0,0,0,.25)',
      cursor:       'grabbing',
    });
    document.body.appendChild(ghost);
    dragState.ghost = ghost;
    dragState.card.classList.add('dragging');
    document.body.style.userSelect = 'none';
  }

  dragState.ghost.style.left = (x - dragState.offsetX) + 'px';
  dragState.ghost.style.top  = (y - dragState.offsetY) + 'px';

  const container = document.getElementById('devoirs-list');
  if (container) showDropIndicator(container, getDropPosition(container, y));
}

async function onDragPointerUp(e) {
  if (!dragState) return;

  const { x, y } = getEventPos(e);
  const { card, sourceIndex, active, ghost, isTouch } = dragState;

  // Nettoyer les listeners
  if (isTouch) {
    document.removeEventListener('touchmove', onDragPointerMove);
    document.removeEventListener('touchend',  onDragPointerUp);
    document.removeEventListener('touchcancel', onDragPointerUp);
  } else {
    document.removeEventListener('mousemove', onDragPointerMove);
    document.removeEventListener('mouseup',   onDragPointerUp);
  }

  card.classList.remove('dragging');
  if (ghost) ghost.remove();
  removeDropIndicator();
  document.body.style.userSelect = '';
  dragWasActive = active;
  dragState = null;

  if (!active) return;

  const container = document.getElementById('devoirs-list');
  if (!container) return;
  const toIndex = getDropPosition(container, y);
  if (toIndex === sourceIndex || toIndex === sourceIndex + 1) return;

  try {
    const updated = await api('POST', '/api/devoirs/reorder', { from_index: sourceIndex, to_index: toIndex });
    State.devoirs = updated;
    renderDevoirsList(State.devoirs, false);
  } catch (err) {
    toast('Erreur lors du déplacement : ' + err.message, 'error');
    await loadDevoirs();
  }
}

function getDropPosition(container, clientY) {
  const cards = [...container.querySelectorAll('.devoir-card:not(.dragging), .pause-card:not(.dragging)')];
  for (let i = 0; i < cards.length; i++) {
    const rect = cards[i].getBoundingClientRect();
    if (clientY < rect.top + rect.height / 2) return parseInt(cards[i].dataset.index);
  }
  return State.devoirs.length;
}

function showDropIndicator(container, insertBeforeIndex) {
  removeDropIndicator();
  const indicator = document.createElement('div');
  indicator.className = 'drop-indicator';
  const target = [...container.querySelectorAll('[data-index]')]
    .find(c => parseInt(c.dataset.index) === insertBeforeIndex);
  if (target) container.insertBefore(indicator, target);
  else        container.appendChild(indicator);
  dropIndicatorEl = indicator;
}

function removeDropIndicator() {
  if (dropIndicatorEl) { dropIndicatorEl.remove(); dropIndicatorEl = null; }
}

// ── Add devoir ────────────────────────────────────────────────────────────────
async function addDevoir() {
  const classe_nom = document.getElementById('dv-classe').value;
  const date = document.getElementById('dv-date').value;
  const contenu = document.getElementById('dv-contenu').value.trim();

  if (!classe_nom) { toast('Veuillez choisir une classe', 'error'); return; }
  if (!contenu) { toast('Veuillez saisir le contenu du devoir', 'error'); return; }
  if (!date) { toast('Veuillez saisir une date', 'error'); return; }

  try {
    const newDevoir = await api('POST', '/api/devoirs', { classe_nom, date, contenu });
    State.devoirs.push(newDevoir);
    // Si le tri est actif, réorganiser silencieusement ; sinon juste ajouter la carte
    if (State.sortMode !== 'manuel') {
      renderDevoirsList(State.devoirs, false);
    } else {
      appendCardToList(newDevoir);
    }
    const ta = document.getElementById('dv-contenu');
    ta.value = '';
    ta.style.height = '0';
    ta.style.height = ta.scrollHeight + 'px';
    toast('Devoir ajouté', 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
}
