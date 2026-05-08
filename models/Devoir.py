from datetime import datetime

class Devoir:
    def __init__(self, contenu, classe_objet, date=None, statut="Pas fait", annotation=None):
        self.contenu = contenu
        self.classe_objet = classe_objet  # maintenant un objet Classe
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")
        self.statut = statut
        self.annotation = annotation  # dict {text, color, side} ou None

    def marquer_comme_fait(self):
        self.statut = "Fait"

    def afficher(self):
        nom_classe = self.classe_objet.nom if self.classe_objet else "Inconnue"
        return f"Devoir : {self.contenu} | Classe : {nom_classe} | Échéance : {self.date} | Statut : {self.statut}"

    def est_en_retard(self):
        if self.statut == "Fait":
            return False
        try:
            date_echeance = datetime.strptime(self.date, "%Y-%m-%d")
            return date_echeance < datetime.now()
        except ValueError:
            return False