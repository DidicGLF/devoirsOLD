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

    <!-- Zone figée au scroll -->
    <div class="classes-sticky">
      <div class="add-form-card">
        <div class="add-form-row">
          <div class="form-group" style="max-width:160px">
            <label for="cls-nom">Nom de la classe</label>
            <input id="cls-nom" class="form-control" placeholder="ex : 6°A" maxlength="20">
          </div>
          <div class="form-group effectif-group">
            <label for="cls-effectif">Effectif</label>
            <input id="cls-effectif" class="form-control" type="number" min="0" placeholder="0" style="width:70px">
          </div>
          <div class="form-group color-group">
            <label>Couleur</label>
            <label class="classe-color-dot" id="cls-couleur-dot" style="background:#62a0ea" title="Choisir une couleur">
              <input id="cls-couleur" type="color" class="color-swatch" value="#62a0ea">
            </label>
          </div>
          <button id="cls-add-btn" class="btn btn-primary" style="margin-left:auto">Ajouter</button>
        </div>
      </div>
    </div><!-- fin .classes-sticky -->

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
  document.getElementById('cls-couleur').addEventListener('input', (e) => {
    document.getElementById('cls-couleur-dot').style.background = e.target.value;
  });

  // Ombre sur la zone sticky quand elle est collée en haut
  const sticky = container.querySelector('.classes-sticky');
  const sentinel = document.createElement('div');
  sentinel.style.cssText = 'height:1px;margin-top:-1px;pointer-events:none';
  container.insertBefore(sentinel, sticky);
  new IntersectionObserver(([entry]) => {
    sticky.classList.toggle('is-stuck', !entry.isIntersecting);
  }).observe(sentinel);

  await loadClasses();
}

async function loadClasses(animate = true) {
  try {
    State.classes = await api('GET', '/api/classes');
    renderClassesList(animate);
  } catch (err) {
    toast('Erreur lors du chargement des classes : ' + err.message, 'error');
  }
}

function createClasseCard(c, idx) {
  const card = document.createElement('div');
  card.className = 'classe-card';
  card.id = `cls-card-${idx}`;
  card.style.cssText = colorStyle(c.couleur);
  card.dataset.index = idx;

  card.innerHTML = `
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
  `;

  const nomInput = card.querySelector('.cls-nom-input');
  nomInput.addEventListener('blur', () => saveClasseField(nomInput, 'nom'));
  nomInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') nomInput.blur();
    if (e.key === 'Escape') { nomInput.value = nomInput.dataset.original; nomInput.blur(); }
  });

  const effectifInput = card.querySelector('.cls-effectif-input');
  effectifInput.addEventListener('blur', () => saveClasseField(effectifInput, 'effectif'));
  effectifInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') effectifInput.blur();
    if (e.key === 'Escape') { effectifInput.value = effectifInput.dataset.original; effectifInput.blur(); }
  });

  card.querySelector('.color-swatch').addEventListener('change', (e) => saveClasseColor(e.target));
  card.querySelector('.cls-delete-btn').addEventListener('click', () => deleteClasse(parseInt(card.dataset.index)));

  return card;
}

function renderClassesList(animate = true) {
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

  list.innerHTML = '';
  sortClasses(State.classes).forEach((c, displayIdx) => {
    const idx = State.classes.indexOf(c);
    const card = createClasseCard(c, idx);
    if (animate) {
      card.classList.add('card-animate');
      card.style.animationDelay = `${displayIdx * 60}ms`;
      card.addEventListener('animationend', () => {
        card.classList.remove('card-animate');
        card.style.animationDelay = '';
      }, { once: true });
    }
    list.appendChild(card);
  });
}

function appendClasseCardToList(classe) {
  const list = document.getElementById('classes-list');
  if (!list) return;
  list.querySelector('.empty-state')?.remove();

  const idx = State.classes.length - 1;
  const card = createClasseCard(classe, idx);
  card.classList.add('card-animate');
  card.addEventListener('animationend', () => card.classList.remove('card-animate'), { once: true });
  list.appendChild(card);
}

function removeClasseCardFromDOM(card, deletedIndex) {
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
      State.classes = State.classes.filter((_, i) => i !== deletedIndex);
      // Mettre à jour data-index sur les cartes restantes
      document.querySelectorAll('#classes-list [data-index]').forEach(el => {
        const i = parseInt(el.dataset.index);
        if (i > deletedIndex) el.dataset.index = i - 1;
      });
      document.querySelectorAll('#classes-list .classe-card').forEach(c => {
        const i = parseInt(c.dataset.index);
        c.id = `cls-card-${i}`;
      });
      // Afficher empty state si plus rien
      const list = document.getElementById('classes-list');
      if (list && !list.querySelector('.classe-card')) {
        list.innerHTML = `<div class="empty-state"><span class="empty-state-icon">🎓</span>Aucune classe. Créez-en une ci-dessus.</div>`;
      }
    }, 200);
  }, 180);
}

async function addClasse() {
  const nom = document.getElementById('cls-nom').value.trim();
  const effectif = parseInt(document.getElementById('cls-effectif').value) || 0;
  const couleur = document.getElementById('cls-couleur').value;

  if (!nom) { toast('Veuillez saisir un nom de classe', 'error'); return; }

  try {
    const newClasse = await api('POST', '/api/classes', { nom, effectif, couleur });
    State.classes.push(newClasse);
    document.getElementById('cls-nom').value = '';
    document.getElementById('cls-effectif').value = '';
    appendClasseCardToList(newClasse);
    toast('Classe ajoutée', 'success');
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
    await loadClasses(false);
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
    const card = document.querySelector(`#classes-list [data-index="${idx}"]`);
    if (card) removeClasseCardFromDOM(card, idx);
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
