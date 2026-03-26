/* ═══════════════════════════════════════════════════════════════════════════
   parametres.js — Paramètres de l'application
   ═══════════════════════════════════════════════════════════════════════════ */

registerView('parametres', renderParametres);

async function renderParametres(container) {
  let config = {};
  try {
    config = await api('GET', '/api/config');
    State.config = config;
  } catch (_) {}

  const lien = config.lien_ent || {};

  container.innerHTML = `
    <h1 class="page-title">⚙️ Paramètres</h1>
    <p class="page-subtitle">Exportez, importez vos données et personnalisez l'application.</p>

    <!-- Données -->
    <div class="settings-section">
      <div class="settings-section-header">📊 Données</div>
      <div class="settings-item">
        <div>
          <div class="settings-item-label">Exporter les données</div>
          <div class="settings-item-desc">Télécharge un fichier JSON avec toutes vos classes et devoirs.</div>
        </div>
        <button id="btn-export" class="btn btn-primary btn-sm">⬇️ Exporter</button>
      </div>
      <div class="settings-item">
        <div>
          <div class="settings-item-label">Importer des données</div>
          <div class="settings-item-desc">Remplace toutes les données par celles du fichier. Une sauvegarde est créée automatiquement.</div>
        </div>
        <label class="btn btn-secondary btn-sm" style="cursor:pointer">
          ⬆️ Importer
          <input id="input-import" type="file" accept=".json" style="display:none">
        </label>
      </div>
      <div class="settings-item">
        <div>
          <div class="settings-item-label">Réinitialiser les devoirs</div>
          <div class="settings-item-desc">Supprime tous les devoirs (les classes sont conservées). Une sauvegarde est créée.</div>
        </div>
        <button id="btn-reset" class="btn btn-danger btn-sm">🗑 Réinitialiser</button>
      </div>
    </div>

    <!-- Préférences -->
    <div class="settings-section">
      <div class="settings-section-header">⚙️ Préférences</div>
      <div class="settings-item">
        <div>
          <div class="settings-item-label">Lien ENT</div>
          <div class="settings-item-desc">
            ${lien.url
              ? `<a href="${escHtml(lien.url)}" target="_blank">${escHtml(lien.texte || lien.url)}</a>`
              : 'Aucun lien configuré'}
          </div>
        </div>
        <button id="btn-ent" class="btn btn-secondary btn-sm">✏️ Modifier</button>
      </div>
    </div>

    <!-- À propos -->
    <div class="settings-section">
      <div class="settings-section-header">ℹ️ À propos</div>
      <div class="settings-item">
        <div>
          <div class="settings-item-label">Mes Devoirs</div>
          <div class="settings-item-desc">Application de gestion des devoirs scolaires — Flask + JavaScript</div>
        </div>
      </div>
    </div>
  `;

  // Export
  document.getElementById('btn-export').addEventListener('click', () => {
    window.location.href = '/api/export';
  });

  // Import
  document.getElementById('input-import').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
      try {
        const data = JSON.parse(ev.target.result);
        if (!data.classes || !data.devoirs) {
          toast('Format de fichier invalide', 'error');
          return;
        }
        const ok = await confirmer({
          titre: '⬆️ Importer des données',
          message: 'Les données actuelles seront <strong>remplacées</strong>. Une sauvegarde sera créée automatiquement.',
          labelOk: 'Importer',
        });
        if (!ok) return;
        await api('POST', '/api/import', data);
        toast('Données importées avec succès', 'success');
        await renderParametres(container); // Refresh
      } catch (err) {
        toast('Erreur lors de l\'import : ' + err.message, 'error');
      }
    };
    reader.readAsText(file, 'utf-8');
    // Reset l'input pour pouvoir réimporter le même fichier
    e.target.value = '';
  });

  // Reset
  document.getElementById('btn-reset').addEventListener('click', () => {
    showResetConfirm();
  });

  // ENT
  document.getElementById('btn-ent').addEventListener('click', () => {
    showEntModal(lien);
  });
}

function showResetConfirm() {
  openModal(`
    <div class="modal-title">🗑️ Réinitialiser les devoirs</div>
    <p style="color:var(--text-secondary);margin-bottom:12px">
      Tous les devoirs seront supprimés. Les classes seront conservées.
      Une sauvegarde sera créée automatiquement.
    </p>
    <p style="font-size:13px;color:var(--danger);font-weight:500">
      ⚠️ Cette action est irréversible (sauf restauration manuelle de la sauvegarde).
    </p>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Annuler</button>
      <button class="btn btn-danger" id="modal-confirm-reset">Confirmer la suppression</button>
    </div>
  `);

  document.getElementById('modal-confirm-reset').addEventListener('click', async () => {
    try {
      await api('POST', '/api/reset');
      closeModal();
      toast('Tous les devoirs ont été supprimés', 'success');
    } catch (err) {
      toast('Erreur : ' + err.message, 'error');
    }
  });
}

function showEntModal(lien) {
  openModal(`
    <div class="modal-title">🔗 Modifier le lien ENT</div>
    <div class="form-group mb-4">
      <label for="modal-ent-url">URL</label>
      <input id="modal-ent-url" class="form-control" type="url" placeholder="https://..."
             value="${escHtml(lien.url || '')}">
    </div>
    <div class="form-group mb-4">
      <label for="modal-ent-texte">Texte affiché</label>
      <input id="modal-ent-texte" class="form-control" placeholder="Mon ENT"
             value="${escHtml(lien.texte || '')}">
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal()">Annuler</button>
      <button class="btn btn-primary" id="modal-save-ent">Enregistrer</button>
    </div>
  `);

  document.getElementById('modal-save-ent').addEventListener('click', async () => {
    const url = document.getElementById('modal-ent-url').value.trim();
    const texte = document.getElementById('modal-ent-texte').value.trim();
    try {
      const config = await api('PUT', '/api/config', { lien_ent: { url, texte } });
      State.config = config;
      closeModal();
      toast('Lien ENT mis à jour', 'success');
      // Mettre à jour la sidebar
      await loadEntLink();
      // Refresh la page paramètres
      const container = document.getElementById('app-content');
      await renderParametres(container);
    } catch (err) {
      toast('Erreur : ' + err.message, 'error');
    }
  });
}
