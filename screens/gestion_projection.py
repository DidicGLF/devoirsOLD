# screens/gestion_projection.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QCheckBox, QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from datetime import datetime

from utils.gestion import charger_classes, charger_devoirs

class ProjectionWidget(QWidget):
    """Écran de sélection des devoirs à projeter"""
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.classes_list = []
        self.devoirs_list = []
        self.devoirs_checkboxes = []  # Liste des (checkbox, devoir)
        self.init_ui()

    def init_ui(self):
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 30)

        # Titre
        titre = QLabel("Sélection des devoirs à projeter")
        titre.setFont(QFont("Arial", 18, QFont.Bold))
        titre.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(titre)

        # Sélecteur de classe (centré)
        classe_layout = QHBoxLayout()
        classe_layout.addStretch()
        classe_label = QLabel("Classe :")
        classe_label.setFont(QFont("Arial", 14))
        classe_layout.addWidget(classe_label)

        self.combo_classe = QComboBox()
        self.combo_classe.setFixedHeight(35)
        self.combo_classe.setFixedWidth(200)
        self.combo_classe.setFont(QFont("Arial", 12))
        self.combo_classe.currentIndexChanged.connect(self.charger_devoirs_classe)
        classe_layout.addWidget(self.combo_classe)
        classe_layout.addStretch()

        main_layout.addLayout(classe_layout)

        # Boutons de sélection (centrés)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_tout_selectionner = QPushButton("Tout sélectionner")
        btn_tout_selectionner.setFixedSize(150, 35)
        btn_tout_selectionner.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        btn_tout_selectionner.clicked.connect(self.tout_selectionner)
        buttons_layout.addWidget(btn_tout_selectionner)

        btn_tout_deselectionner = QPushButton("Tout désélectionner")
        btn_tout_deselectionner.setFixedSize(150, 35)
        btn_tout_deselectionner.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_tout_deselectionner.clicked.connect(self.tout_deselectionner)
        buttons_layout.addWidget(btn_tout_deselectionner)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)


        # Zone scrollable pour les devoirs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
        """)

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_widget.setLayout(self.scroll_layout)
        scroll_area.setWidget(self.scroll_widget)

        main_layout.addWidget(scroll_area)

        # Bouton Afficher
        btn_afficher = QPushButton("Afficher la projection")
        btn_afficher.setFixedHeight(50)
        btn_afficher.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_afficher.clicked.connect(self.afficher_projection)
        main_layout.addWidget(btn_afficher)

        self.setLayout(main_layout)

        # Charger les classes
        self.charger_classes()

    def charger_classes(self):
        """Charge les classes dans le combo"""
        self.classes_list = charger_classes()
        self.combo_classe.clear()
        
        for classe in self.classes_list:
            self.combo_classe.addItem(classe.nom)
        
        if self.classes_list:
            self.charger_devoirs_classe()

    def charger_devoirs_classe(self):
        """Charge les devoirs de la classe sélectionnée"""
        if self.combo_classe.currentIndex() == -1:
            return

        # Vider la liste
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.devoirs_checkboxes.clear()

        # Récupérer la classe sélectionnée
        classe_nom = self.combo_classe.currentText()
        
        # Charger tous les devoirs en réutilisant les classes déjà chargées
        tous_devoirs = charger_devoirs(classes=self.classes_list)

        # Filtrer par classe et trier par date
        devoirs_classe = [d for d in tous_devoirs if d.classe_objet.nom == classe_nom]
        devoirs_classe.sort(key=lambda d: d.date)

        if not devoirs_classe:
            label_vide = QLabel("Aucun devoir pour cette classe")
            label_vide.setAlignment(Qt.AlignCenter)
            label_vide.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            self.scroll_layout.addWidget(label_vide)
            return

        # Afficher les devoirs avec checkbox
        for devoir in devoirs_classe:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 5, 5, 5)

            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # Tout sélectionné par défaut
            item_layout.addWidget(checkbox)

            # Date
            try:
                date_obj = datetime.strptime(devoir.date, "%Y-%m-%d")
                date_affichage = date_obj.strftime("%d/%m/%Y")
            except ValueError:
                date_affichage = devoir.date

            date_label = QLabel(date_affichage)
            date_label.setFont(QFont("Arial", 11, QFont.Bold))
            date_label.setStyleSheet("color: #4A90E2;")
            date_label.setFixedWidth(100)
            item_layout.addWidget(date_label)

            # Contenu
            contenu_label = QLabel(devoir.contenu)
            contenu_label.setWordWrap(True)
            contenu_label.setFont(QFont("Arial", 11))
            item_layout.addWidget(contenu_label, 1)

            item_widget.setLayout(item_layout)
            item_widget.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)

            self.scroll_layout.addWidget(item_widget)
            self.devoirs_checkboxes.append((checkbox, devoir))

    def tout_selectionner(self):
        """Sélectionne tous les devoirs"""
        for checkbox, _ in self.devoirs_checkboxes:
            checkbox.setChecked(True)

    def tout_deselectionner(self):
        """Désélectionne tous les devoirs"""
        for checkbox, _ in self.devoirs_checkboxes:
            checkbox.setChecked(False)

    def afficher_projection(self):
        """Affiche la page de projection avec les devoirs sélectionnés"""
        # Récupérer les devoirs sélectionnés
        devoirs_selectionnes = [
            devoir for checkbox, devoir in self.devoirs_checkboxes 
            if checkbox.isChecked()
        ]

        if not devoirs_selectionnes:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Aucun devoir sélectionné",
                "Veuillez sélectionner au moins un devoir à projeter."
            )
            return

        # Créer et afficher la page de projection
        classe_nom = self.combo_classe.currentText()
        page_projection = PageProjection(devoirs_selectionnes, classe_nom, self.main_window)
        
        if self.main_window:
            current_page = self.main_window.stacked_widget.currentWidget()
            page_complete = self.main_window.create_page_with_back_button(
                page_projection,
                f"Projection - {classe_nom}",
                back_widget=current_page
            )
            self.main_window.stacked_widget.addWidget(page_complete)
            self.main_window.stacked_widget.setCurrentWidget(page_complete)


class PageProjection(QWidget):
    """Page d'affichage pour la projection"""
    def __init__(self, devoirs, classe_nom, main_window=None):
        super().__init__()
        self.devoirs = devoirs
        self.classe_nom = classe_nom
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(50, 30, 50, 30)

        # Titre avec nom de classe
        titre = QLabel(f"Devoirs - {self.classe_nom}")
        titre.setFont(QFont("Arial", 28, QFont.Bold))
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet("color: #2c3e50; padding: 20px;")
        layout.addWidget(titre)

        # Ligne de séparation
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        separator.setFixedHeight(2)
        layout.addWidget(separator)

        # Zone scrollable pour les devoirs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setAlignment(Qt.AlignTop)

        # Grouper les devoirs par date
        devoirs_par_date = {}
        for devoir in self.devoirs:
            try:
                date_obj = datetime.strptime(devoir.date, "%Y-%m-%d")
                date_affichage = date_obj.strftime("%d/%m/%Y")
            except ValueError:
                date_affichage = devoir.date
            
            if date_affichage not in devoirs_par_date:
                devoirs_par_date[date_affichage] = []
            devoirs_par_date[date_affichage].append(devoir)

        # Afficher par date
        for date_affichage, devoirs_date in devoirs_par_date.items():
            # Groupe de date
            groupe_widget = QFrame()
            groupe_widget.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #4A90E2;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 5px;
                }
            """)
            
            groupe_layout = QVBoxLayout()
            groupe_layout.setSpacing(8)
            groupe_layout.setContentsMargins(10, 10, 10, 10)
            
            # En-tête de date
            date_header = QLabel(f"Séance du {date_affichage}")
            date_header.setFont(QFont("Arial", 32, QFont.Bold))
            date_header.setStyleSheet("color: #4A90E2; border: none; padding-bottom: 5px;")
            groupe_layout.addWidget(date_header)
            
            # Ligne de séparation
            separator_date = QFrame()
            separator_date.setFrameShape(QFrame.HLine)
            separator_date.setStyleSheet("background-color: #4A90E2; border: none;")
            separator_date.setFixedHeight(1)
            groupe_layout.addWidget(separator_date)
            
            # Espacement
            groupe_layout.addSpacing(5)

            # Liste des devoirs pour cette date
            for devoir in devoirs_date:
                contenu_label = QLabel(f"• {devoir.contenu}")
                contenu_label.setWordWrap(True)
                contenu_label.setFont(QFont("Arial", 28))
                contenu_label.setStyleSheet("color: #2c3e50; border: none; padding: 3px 0px 3px 10px;")
                groupe_layout.addWidget(contenu_label)
            
            groupe_widget.setLayout(groupe_layout)
            scroll_layout.addWidget(groupe_widget)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        self.setLayout(layout)