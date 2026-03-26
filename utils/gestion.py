# utils/gestion.py
import json
import os
import sys
import tempfile
from datetime import datetime
from models.Classe import Classe
from models.Devoir import Devoir

# Fonction pour obtenir le bon chemin, que ce soit en développement ou en .exe
def get_data_path():
    """Retourne le chemin vers le dossier data, en mode dev ou exe"""
    if getattr(sys, 'frozen', False):
        # Mode .exe : le dossier data doit être à côté du .exe
        application_path = os.path.dirname(sys.executable)
    else:
        # Mode développement : chemin relatif classique
        application_path = os.path.dirname(os.path.dirname(__file__))
    
    data_path = os.path.join(application_path, 'data')
    os.makedirs(data_path, exist_ok=True)  # Créer le dossier s'il n'existe pas
    return data_path

# Utiliser la fonction pour définir les chemins
DATA_DIR = get_data_path()
CLASSES_FILE = os.path.join(DATA_DIR, 'classes.json')
DEVOIRS_FILE = os.path.join(DATA_DIR, 'devoirs.json')

_COLOR_MAP = {
    "gris": "128, 128, 128",
    "bleu": "0, 0, 255",
    "vert": "0, 128, 0",
    "rouge": "255, 0, 0",
    "jaune": "255, 255, 0",
    "orange": "255, 165, 0",
    "violet": "128, 0, 128",
    "rose": "255, 192, 203",
    "noir": "0, 0, 0",
    "blanc": "255, 255, 255",
}

def couleur_to_rgb(couleur):
    """Convertit un nom de couleur ou un code hex en chaîne 'r, g, b'"""
    if couleur.startswith('#'):
        h = couleur.lstrip('#')
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
    return _COLOR_MAP.get(couleur.lower(), "128, 128, 128")


def _ecriture_atomique(chemin, data):
    """Écrit data en JSON de façon atomique : temp file + rename.
    Évite qu'un lecteur concurrent trouve un fichier vide pendant l'écriture."""
    dossier = os.path.dirname(chemin)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8',
                                     dir=dossier, delete=False, suffix='.tmp') as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, chemin)  # atomique sur Linux/macOS/Windows


def charger_classes():
    """Charge les classes depuis le fichier JSON et retourne une liste d'instances de Classe"""
    if not os.path.exists(CLASSES_FILE):
        return []  # Retourne une liste vide si le fichier n'existe pas

    with open(CLASSES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Reconstruire les instances de Classe
    classes = []
    for item in data:
        classe = Classe(
            nom=item["nom"],
            effectif=item["effectif"],
            couleur=item.get("couleur", "gris")  # valeur par défaut si absent
        )
        classes.append(classe)

    return classes

def sauvegarder_classes(classes):
    """Sauvegarde une liste d'instances de Classe dans un fichier JSON"""
    # Convertir chaque instance en dictionnaire
    data = []
    for classe in classes:
        data.append({
            "nom": classe.nom,
            "effectif": classe.effectif,
            "couleur": classe.couleur
        })

    os.makedirs(os.path.dirname(CLASSES_FILE), exist_ok=True)
    _ecriture_atomique(CLASSES_FILE, data)

def charger_devoirs(classes=None):
    """Charge les devoirs depuis le fichier JSON et retourne une liste d'instances de Devoir.

    Accepte une liste de classes déjà chargées pour éviter une double lecture disque.
    """
    if not os.path.exists(DEVOIRS_FILE):
        return []

    with open(DEVOIRS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if classes is None:
        classes = charger_classes()
    classes_dict = {classe.nom: classe for classe in classes}

    # Reconstruire les instances de Devoir
    devoirs = []
    for item in data:
        nom_classe = item.get("classe_nom") or ""
        if not nom_classe:
            # Pause : classe fantôme sans nom
            classe_objet = Classe(nom="", effectif=0, couleur="#e2e8f0")
        else:
            classe_objet = classes_dict.get(nom_classe)
            if not classe_objet:
                classe_objet = Classe(nom=nom_classe, effectif=0, couleur="gris")

        devoir = Devoir(
            contenu=item["contenu"],
            classe_objet=classe_objet,
            date=item["date"],
            statut=item["statut"]
        )
        devoirs.append(devoir)

    return devoirs

def sauvegarder_devoirs(devoirs):
    """Sauvegarde une liste d'instances de Devoir dans un fichier JSON"""
    # Convertir chaque instance en dictionnaire
    data = []
    for devoir in devoirs:
        data.append({
            "contenu": devoir.contenu,
            "classe_nom": devoir.classe_objet.nom or None,  # None pour les pauses
            "date": devoir.date,
            "statut": devoir.statut
        })

    os.makedirs(os.path.dirname(DEVOIRS_FILE), exist_ok=True)
    _ecriture_atomique(DEVOIRS_FILE, data)