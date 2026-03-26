/* ═══════════════════════════════════════════════════════════════════════════
   classes.js — Gestion des classes
   ═══════════════════════════════════════════════════════════════════════════ */

registerView('accueil', renderAccueil);
registerView('classes', renderClasses);

// ── Accueil ───────────────────────────────────────────────────────────────────
async function renderAccueil(container) {
  container.innerHTML = `
    <div class="welcome-banner">
      <h2>👋 Bienvenue dans Mes Devoirs</h2>
      <p>Gérez les devoirs de vos classes et affichez-les en projection.</p>
    </div>
    <div class="accueil-grid">
      <a class="accueil-card" href="#/classes">
        <span class="accueil-card-icon">🎓</span>
        <div class="accueil-card-title">Classes</div>
        <div class="accueil-card-desc">Créer et gérer vos classes</div>
      </a>
      <a class="accueil-card" href="#/devoirs">
        <span class="accueil-card-icon">📝</span>
        <div class="accueil-card-title">Devoirs</div>
        <div class="accueil-card-desc">Ajouter et suivre les devoirs</div>
      </a>
      <a class="accueil-card" href="#/projection">
        <span class="accueil-card-icon">${iconProjection(40)}</span>
        <div class="accueil-card-title">Projection</div>
        <div class="accueil-card-desc">Afficher les devoirs en classe</div>
      </a>
      <a class="accueil-card" href="#/parametres">
        <span class="accueil-card-icon">⚙️</span>
        <div class="accueil-card-title">Paramètres</div>
        <div class="accueil-card-desc">Export, import, configuration</div>
      </a>
    </div>
  `;
}

// ── Classes ───────────────────────────────────────────────────────────────────
async function renderClasses(container) {
  container.innerHTML = `
    <h1 class="page-title">🎓 Gestion des classes</h1>
    <p class="page-subtitle">Ajoutez et modifiez vos classes.</p>

    <!-- Formulaire d'ajout -->
    <div class="add-form-card">
      <div class="card-header">➕ Ajouter une classe</div>
      <div class="add-form-row">
        <div class="form-group">
          <label for="cls-nom">Nom de la classe</label>
          <input id="cls-nom" class="form-control" placeholder="ex : 6°A" maxlength="20">
        </div>
        <div class="form-group">
          <label for="cls-effectif">Effectif</label>
          <input id="cls-effectif" class="form-control" type="number" min="0" placeholder="0" style="width:90px">
        </div>
        <div class="form-group color-group">
          <label for="cls-couleur">Couleur</label>
          <input id="cls-couleur" type="color" value="#62a0ea">
        </div>
        <button id="cls-add-btn" class="btn btn-primary">Ajouter</button>
      </div>
    </div>

    <!-- Liste des classes -->
    <div id="classes-list" class="classes-list">
      <div class="empty-state"><span class="empty-state-icon">⏳</span>Chargement…</div>
    </div>
  `;

  // Bind add
  document.getElementById('cls-add-btn').addEventListener('click', addClasse);
  document.getElementById('cls-nom').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addClasse();
  });

  await loadClasses();
}

async function loadClasses() {
  try {
    State.classes = await api('GET', '/api/classes');
    renderClassesList();
  } catch (err) {
    toast('Erreur lors du chargement des classes : ' + err.message, 'error');
  }
}

function renderClassesList() {
  const list = document.getElementById('classes-list');
  if (!list) return;

  if (!State.classes.length) {
    list.innerHTML = `
      <div class="empty-state">
        <span class="empty-state-icon">🎓</span>
        Aucune classe. Créez-en une ci-dessus.
      </div>`;
    return;
  }

  list.innerHTML = sortClasses(State.classes).map((c) => {
    const idx = State.classes.indexOf(c); // conserver l'index serveur réel
    return `
    <div class="classe-card card-animate" id="cls-card-${idx}" style="${colorStyle(c.couleur)}" data-index="${idx}">
      <label class="classe-color-dot" style="background:${c.couleur}" title="Changer la couleur">
        <input type="color" class="color-swatch" value="${c.couleur}" data-index="${idx}">
      </label>
      <div class="classe-info">
        <div class="classe-nom-wrap">
          <input class="inline-edit cls-nom-input"
                 value="${escHtml(c.nom)}"
                 data-original="${escHtml(c.nom)}"
                 data-index="${idx}"
                 title="Cliquer pour modifier le nom"
                 aria-label="Nom de la classe">
        </div>
        <div class="classe-effectif">
          👥
          <input class="inline-edit cls-effectif-input"
                 type="number" min="0" style="width:52px"
                 value="${c.effectif}"
                 data-original="${c.effectif}"
                 data-index="${idx}"
                 title="Cliquer pour modifier l'effectif"
                 aria-label="Effectif">
        </div>
      </div>
      <div class="classe-actions">
        <button class="btn-icon danger cls-delete-btn" data-index="${idx}" title="Supprimer la classe">🗑️</button>
      </div>
    </div>
  `;
  }).join('');

  // Délai échelonné + retrait de card-animate après animation
  list.querySelectorAll('.classe-card').forEach((card, i) => {
    card.style.animationDelay = `${i * 60}ms`;
    card.addEventListener('animationend', () => {
      card.classList.remove('card-animate');
      card.style.animationDelay = '';
    }, { once: true });
  });

  // Bind events
  list.querySelectorAll('.cls-nom-input').forEach(input => {
    input.addEventListener('blur', () => saveClasseField(input, 'nom'));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { input.blur(); }
      if (e.key === 'Escape') { input.value = input.dataset.original; input.blur(); }
    });
  });

  list.querySelectorAll('.cls-effectif-input').forEach(input => {
    input.addEventListener('blur', () => saveClasseField(input, 'effectif'));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') input.blur();
      if (e.key === 'Escape') { input.value = input.dataset.original; input.blur(); }
    });
  });

  list.querySelectorAll('.color-swatch').forEach(input => {
    input.addEventListener('change', () => saveClasseColor(input));
  });

  list.querySelectorAll('.cls-delete-btn').forEach(btn => {
    btn.addEventListener('click', () => deleteClasse(parseInt(btn.dataset.index)));
  });
}

async function addClasse() {
  const nom = document.getElementById('cls-nom').value.trim();
  const effectif = parseInt(document.getElementById('cls-effectif').value) || 0;
  const couleur = document.getElementById('cls-couleur').value;

  if (!nom) { toast('Veuillez saisir un nom de classe', 'error'); return; }

  try {
    await api('POST', '/api/classes', { nom, effectif, couleur });
    document.getElementById('cls-nom').value = '';
    document.getElementById('cls-effectif').value = '';
    toast('Classe ajoutée', 'success');
    await loadClasses();
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function saveClasseField(input, field) {
  const idx = parseInt(input.dataset.index);
  const val = field === 'effectif' ? parseInt(input.value) : input.value.trim();
  const original = field === 'effectif' ? parseInt(input.dataset.original) : input.dataset.original;

  if (val === original || (field === 'nom' && !val)) {
    input.value = original;
    return;
  }

  try {
    await api('PUT', `/api/classes/${idx}`, { [field]: val });
    input.dataset.original = val;
    if (field === 'nom') toast('Nom mis à jour', 'success');
    await loadClasses();
  } catch (err) {
    toast(err.message, 'error');
    input.value = original;
  }
}

async function saveClasseColor(input) {
  const idx = parseInt(input.dataset.index);
  const couleur = input.value;
  try {
    await api('PUT', `/api/classes/${idx}`, { couleur });
    await loadClasses();
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function deleteClasse(idx) {
  const classe = State.classes[idx];
  if (!classe) return;

  // Vérification des devoirs orphelins via la réponse API
  const ok = await confirmer({
    titre: '🗑️ Supprimer la classe',
    message: `Supprimer la classe <strong>${escHtml(classe.nom)}</strong> ? Les devoirs associés deviendront orphelins.`,
    labelOk: 'Supprimer',
    danger: true,
  });
  if (!ok) return;

  try {
    const res = await api('DELETE', `/api/classes/${idx}`);
    if (res.devoirs_orphelins > 0) {
      toast(`Classe supprimée. ${res.devoirs_orphelins} devoir(s) associé(s) sont orphelins.`, 'info');
    } else {
      toast('Classe supprimée', 'success');
    }
    await loadClasses();
  } catch (err) {
    toast(err.message, 'error');
  }
}

// Échapper le HTML
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
