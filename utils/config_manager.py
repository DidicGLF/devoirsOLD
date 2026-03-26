# utils/config_manager.py
import json
import os
import sys

def get_config_path():
    """Retourne le chemin vers le fichier de configuration"""
    if getattr(sys, 'frozen', False):
        # Mode .exe
        application_path = os.path.dirname(sys.executable)
    else:
        # Mode développement
        application_path = os.path.dirname(os.path.dirname(__file__))
    
    data_path = os.path.join(application_path, 'data')
    os.makedirs(data_path, exist_ok=True)
    return os.path.join(data_path, 'config.json')

CONFIG_FILE = get_config_path()

def charger_config():
    """Charge la configuration depuis le fichier JSON"""
    if not os.path.exists(CONFIG_FILE):
        # Configuration par défaut (vide)
        return {
            "lien_ent": {
                "url": "",
                "texte": ""
            }
        }
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "lien_ent": {
                "url": "",
                "texte": ""
            }
        }

def sauvegarder_config(config):
    """Sauvegarde la configuration dans le fichier JSON"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_lien_ent():
    """Retourne le lien ENT (url et texte)"""
    config = charger_config()
    return config.get("lien_ent", {
        "url": "",
        "texte": ""
    })

def set_lien_ent(url, texte):
    """Définit le lien ENT"""
    config = charger_config()
    config["lien_ent"] = {
        "url": url,
        "texte": texte
    }
    sauvegarder_config(config)