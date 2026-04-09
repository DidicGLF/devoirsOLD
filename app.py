from flask import Flask, jsonify, request, render_template, send_file
import sys
import os
import io
import json
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.gestion import (
    charger_classes, sauvegarder_classes,
    charger_devoirs, sauvegarder_devoirs,
    CLASSES_FILE, DEVOIRS_FILE
)
from utils.config_manager import charger_config, sauvegarder_config, set_lien_ent
from models.Classe import Classe
from models.Devoir import Devoir

if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(_base, 'templates'),
            static_folder=os.path.join(_base, 'static'))
app.json.ensure_ascii = False


def classe_to_dict(classe, index):
    return {
        "index": index,
        "nom": classe.nom,
        "effectif": classe.effectif,
        "couleur": classe.couleur
    }


def devoir_to_dict(devoir, index):
    is_pause = not devoir.classe_objet.nom
    return {
        "index": index,
        "type": "pause" if is_pause else "devoir",
        "contenu": devoir.contenu,
        "classe_nom": devoir.classe_objet.nom or None,
        "classe_couleur": devoir.classe_objet.couleur if not is_pause else None,
        "date": devoir.date if not is_pause else None,
        "statut": devoir.statut if not is_pause else None,
    }


# ── Routes HTML ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/projection')
def projection_page():
    return render_template('projection.html')


@app.route('/icons-preview')
def icons_preview():
    return render_template('icons_preview.html')


# ── API Classes ──────────────────────────────────────────────────────────────

@app.route('/api/classes', methods=['GET'])
def get_classes():
    classes = charger_classes()
    return jsonify([classe_to_dict(c, i) for i, c in enumerate(classes)])


@app.route('/api/classes', methods=['POST'])
def create_classe():
    data = request.json
    nom = data.get('nom', '').strip()
    if not nom:
        return jsonify({'error': 'Le nom de la classe est requis'}), 400
    try:
        effectif = int(data.get('effectif', 0))
        if effectif < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': "L'effectif doit être un entier positif"}), 400

    classes = charger_classes()
    if any(c.nom == nom for c in classes):
        return jsonify({'error': 'Une classe avec ce nom existe déjà'}), 409

    nouvelle = Classe(nom=nom, effectif=effectif, couleur=data.get('couleur', '#808080'))
    classes.append(nouvelle)
    sauvegarder_classes(classes)
    return jsonify(classe_to_dict(nouvelle, len(classes) - 1)), 201


@app.route('/api/classes/<int:index>', methods=['PUT'])
def update_classe(index):
    classes = charger_classes()
    if index >= len(classes):
        return jsonify({'error': 'Classe introuvable'}), 404

    data = request.json
    ancien_nom = classes[index].nom

    if 'nom' in data:
        nouveau_nom = data['nom'].strip()
        if not nouveau_nom:
            return jsonify({'error': 'Le nom ne peut pas être vide'}), 400
        # Mettre à jour les références dans les devoirs si le nom change
        if nouveau_nom != ancien_nom:
            devoirs = charger_devoirs()
            for d in devoirs:
                if d.classe_objet.nom == ancien_nom:
                    d.classe_objet.nom = nouveau_nom
            sauvegarder_devoirs(devoirs)
        classes[index].nom = nouveau_nom

    if 'effectif' in data:
        try:
            effectif = int(data['effectif'])
            if effectif < 0:
                raise ValueError
            classes[index].effectif = effectif
        except (ValueError, TypeError):
            return jsonify({'error': "L'effectif doit être un entier positif"}), 400

    if 'couleur' in data:
        classes[index].couleur = data['couleur']

    sauvegarder_classes(classes)
    return jsonify(classe_to_dict(classes[index], index))


@app.route('/api/classes/<int:index>', methods=['DELETE'])
def delete_classe(index):
    classes = charger_classes()
    if index >= len(classes):
        return jsonify({'error': 'Classe introuvable'}), 404

    nom = classes[index].nom
    devoirs = charger_devoirs()
    orphelins = sum(1 for d in devoirs if d.classe_objet.nom == nom)

    classes.pop(index)
    sauvegarder_classes(classes)
    return jsonify({'success': True, 'devoirs_orphelins': orphelins})


# ── API Devoirs ───────────────────────────────────────────────────────────────

@app.route('/api/devoirs', methods=['GET'])
def get_devoirs():
    devoirs = charger_devoirs()
    return jsonify([devoir_to_dict(d, i) for i, d in enumerate(devoirs)])


@app.route('/api/devoirs', methods=['POST'])
def create_devoir():
    data = request.json

    # Cas spécial : pause (pas de classe)
    if data.get('type') == 'pause':
        classe_obj = Classe(nom='', effectif=0, couleur='#e2e8f0')
        devoir = Devoir(
            contenu=data.get('contenu', 'Pause').strip() or 'Pause',
            classe_objet=classe_obj,
            date=None,
            statut='pause'
        )
        devoirs = charger_devoirs()
        devoirs.append(devoir)
        sauvegarder_devoirs(devoirs)
        return jsonify(devoir_to_dict(devoir, len(devoirs) - 1)), 201

    contenu = data.get('contenu', '').strip()
    if not contenu:
        return jsonify({'error': 'Le contenu du devoir est requis'}), 400

    classes = charger_classes()
    classe_obj = next((c for c in classes if c.nom == data.get('classe_nom')), None)
    if not classe_obj:
        return jsonify({'error': 'Classe introuvable'}), 404

    devoir = Devoir(
        contenu=contenu,
        classe_objet=classe_obj,
        date=data.get('date') or datetime.now().strftime('%Y-%m-%d')
    )
    devoirs = charger_devoirs()
    devoirs.append(devoir)
    sauvegarder_devoirs(devoirs)
    return jsonify(devoir_to_dict(devoir, len(devoirs) - 1)), 201


@app.route('/api/devoirs/<int:index>', methods=['PUT'])
def update_devoir(index):
    devoirs = charger_devoirs()
    if index >= len(devoirs):
        return jsonify({'error': 'Devoir introuvable'}), 404

    data = request.json
    if 'contenu' in data:
        devoirs[index].contenu = data['contenu'].strip()
    if 'statut' in data:
        devoirs[index].statut = data['statut']
    if 'date' in data:
        devoirs[index].date = data['date']

    sauvegarder_devoirs(devoirs)
    return jsonify(devoir_to_dict(devoirs[index], index))


@app.route('/api/devoirs/<int:index>', methods=['DELETE'])
def delete_devoir(index):
    devoirs = charger_devoirs()
    if index >= len(devoirs):
        return jsonify({'error': 'Devoir introuvable'}), 404
    devoirs.pop(index)
    sauvegarder_devoirs(devoirs)
    return jsonify({'success': True})


@app.route('/api/devoirs/delete-batch', methods=['POST'])
def delete_devoirs_batch():
    data = request.json
    indices = data.get('indices', [])
    if not indices:
        return jsonify({'error': 'Aucun indice fourni'}), 400
    devoirs = charger_devoirs()
    for idx in sorted(set(indices), reverse=True):
        if 0 <= idx < len(devoirs):
            devoirs.pop(idx)
    sauvegarder_devoirs(devoirs)
    return jsonify({'success': True})


@app.route('/api/devoirs/reorder', methods=['POST'])
def reorder_devoirs():
    data = request.json
    from_i = data.get('from_index')
    to_i = data.get('to_index')

    devoirs = charger_devoirs()
    n = len(devoirs)
    if from_i is None or to_i is None or not (0 <= from_i < n) or not (0 <= to_i <= n):
        return jsonify({'error': 'Indices invalides'}), 400

    devoir = devoirs.pop(from_i)
    # Ajuster l'index cible après le pop
    if to_i > from_i:
        to_i -= 1
    devoirs.insert(to_i, devoir)
    sauvegarder_devoirs(devoirs)
    return jsonify([devoir_to_dict(d, i) for i, d in enumerate(devoirs)])


# ── API Config ────────────────────────────────────────────────────────────────

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(charger_config())


@app.route('/api/config', methods=['PUT'])
def update_config():
    data = request.json
    if 'lien_ent' in data:
        lien = data['lien_ent']
        set_lien_ent(lien.get('url', ''), lien.get('texte', ''))
    return jsonify(charger_config())


# ── Export / Import ───────────────────────────────────────────────────────────

@app.route('/api/export')
def export_data():
    classes = charger_classes()
    devoirs = charger_devoirs()
    export = {
        "version": "1.0",
        "date_export": datetime.now().isoformat(),
        "classes": [
            {"nom": c.nom, "effectif": c.effectif, "couleur": c.couleur}
            for c in classes
        ],
        "devoirs": [
            {"contenu": d.contenu, "classe_nom": d.classe_objet.nom,
             "date": d.date, "statut": d.statut}
            for d in devoirs
        ]
    }
    buf = io.BytesIO(json.dumps(export, ensure_ascii=False, indent=2).encode('utf-8'))
    fname = f"sauvegarde_devoirs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name=fname)


@app.route('/api/import', methods=['POST'])
def import_data():
    data = request.json
    if not data or 'classes' not in data or 'devoirs' not in data:
        return jsonify({'error': 'Format de fichier invalide'}), 400

    # Backup automatique
    backup_dir = os.path.join(os.path.dirname(CLASSES_FILE), 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    for src, name in [(CLASSES_FILE, 'classes'), (DEVOIRS_FILE, 'devoirs')]:
        if os.path.exists(src):
            shutil.copy(src, os.path.join(backup_dir, f'{name}_backup_{ts}.json'))

    nouvelles_classes = [
        Classe(nom=c["nom"], effectif=int(c.get("effectif", 0)), couleur=c.get("couleur", "#808080"))
        for c in data['classes']
    ]
    sauvegarder_classes(nouvelles_classes)

    classes_dict = {c.nom: c for c in nouvelles_classes}
    nouveaux_devoirs = []
    for d in data['devoirs']:
        nom_classe = d.get("classe_nom") or ""
        classe_obj = classes_dict.get(nom_classe, Classe(nom=nom_classe, effectif=0, couleur="#808080"))
        nouveaux_devoirs.append(Devoir(
            contenu=d["contenu"],
            classe_objet=classe_obj,
            date=d.get("date"),
            statut=d.get("statut", "Pas fait")
        ))
    sauvegarder_devoirs(nouveaux_devoirs)

    return jsonify({'success': True, 'backup_path': backup_dir})


@app.route('/api/reset', methods=['POST'])
def reset_data():
    # Backup puis réinitialisation
    backup_dir = os.path.join(os.path.dirname(DEVOIRS_FILE), 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    if os.path.exists(DEVOIRS_FILE):
        shutil.copy(DEVOIRS_FILE, os.path.join(backup_dir, f'devoirs_backup_{ts}.json'))
    sauvegarder_devoirs([])
    return jsonify({'success': True})


if __name__ == '__main__':
    import threading
    import webbrowser
    threading.Timer(1.2, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(debug=False, port=5000)
