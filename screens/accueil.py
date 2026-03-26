from PySide6.QtWidgets import (QMainWindow, QWidget, QPushButton,
                               QVBoxLayout, QLabel, QStackedWidget, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.config_manager import get_lien_ent

# Imports des modules des écrans
try:
    from screens import gestion_classes
except Exception as e:
    print(f"Erreur d'import gestion_classes: {e}")
    gestion_classes = None

try:
    from screens import gestion_devoirs
except Exception as e:
    print(f"Erreur d'import gestion_devoirs: {e}")
    gestion_devoirs = None

try:
    from screens import gestion_parametres
except Exception as e:
    print(f"Erreur d'import gestion_parametres: {e}")
    gestion_parametres = None

class AccueilPage(QWidget):
    """Page d'accueil avec les boutons de navigation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Espacement
        layout.addStretch()
        
        # Dimensions des boutons
        button_width = 300
        button_height = 80
        
        # Style des boutons
        button_style = """
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A8;
            }
        """
        
        # Bouton Gestion Classes
        self.btn_classes = QPushButton("Gestion des Classes")
        self.btn_classes.setFixedSize(button_width, button_height)
        self.btn_classes.setStyleSheet(button_style)
        layout.addWidget(self.btn_classes, alignment=Qt.AlignCenter)
        
        # Bouton Gestion Devoirs
        self.btn_devoirs = QPushButton("Gestion des Devoirs")
        self.btn_devoirs.setFixedSize(button_width, button_height)
        self.btn_devoirs.setStyleSheet(button_style)
        layout.addWidget(self.btn_devoirs, alignment=Qt.AlignCenter)
        
        # Bouton Gestion Paramètres
        self.btn_parametres = QPushButton("Gestion des Paramètres")
        self.btn_parametres.setFixedSize(button_width, button_height)
        self.btn_parametres.setStyleSheet(button_style)
        layout.addWidget(self.btn_parametres, alignment=Qt.AlignCenter)

        # Espacement
        layout.addStretch()

        # Lien clickable en bas de page
        self.footer_label = QLabel()
        self.update_footer_link()  # Charger le lien depuis la config
        self.footer_label.setOpenExternalLinks(True)
        self.footer_label.setAlignment(Qt.AlignCenter)
        self.footer_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.footer_label)

        

        self.setLayout(layout)    

    def update_footer_link(self):
        """Met à jour le lien du footer depuis la configuration"""
        lien = get_lien_ent()
        url = lien.get("url", "").strip()
        texte = lien.get("texte", "").strip()
        
        if url and texte:
            # Lien configuré : afficher le lien cliquable en bleu
            self.footer_label.setText(f'<a href="{url}">{texte}</a>')
            self.footer_label.setStyleSheet("color: #4A90E2; text-decoration: underline;")
        else:
            # Lien non configuré : afficher un message informatif en gris
            self.footer_label.setText("💡 Configurez votre lien personnalisé dans les Paramètres")
            self.footer_label.setStyleSheet("color: #999; font-style: italic;")


class AccueilWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mes devoirs")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central avec navigation par stack
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Page d'accueil
        self.page_accueil = AccueilPage()
        self.stacked_widget.addWidget(self.page_accueil)
        
        # Connexion des boutons de la page d'accueil
        self.page_accueil.btn_classes.clicked.connect(self.show_gestion_classes)
        self.page_accueil.btn_devoirs.clicked.connect(self.show_gestion_devoirs)
        self.page_accueil.btn_parametres.clicked.connect(self.show_gestion_parametres)
        
        # Pages des modules (lazy loading)
        self.page_classes = None
        self.page_devoirs = None
        self.page_parametres = None
    
    def create_page_with_back_button(self, content_widget, title, back_widget=None):
        """Crée une page avec un bouton retour.

        Si back_widget est fourni, le retour va vers cette page et supprime la page courante.
        Sinon, le retour va à l'accueil (comportement pour les pages principales).
        """
        page_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre supérieure avec bouton retour
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #fcfcfd;")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 10, 10, 10)

        # Bouton retour à gauche
        btn_back = QPushButton("← Retour")
        btn_back.setFixedSize(120, 40)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A8;
            }
        """)

        if back_widget is not None:
            def go_back(checked=False, pw=page_widget, bw=back_widget):
                self.stacked_widget.setCurrentWidget(bw)
                self.stacked_widget.removeWidget(pw)
                pw.deleteLater()
            btn_back.clicked.connect(go_back)
        else:
            btn_back.clicked.connect(self.show_accueil)

        # Titre au centre
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        # Espaceur invisible à droite pour équilibrer (même taille que le bouton)
        right_spacer = QWidget()
        right_spacer.setFixedSize(120, 40)

        top_bar_layout.addWidget(btn_back)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(right_spacer)
        top_bar.setLayout(top_bar_layout)

        layout.addWidget(top_bar)
        layout.addWidget(content_widget)

        page_widget._content = content_widget
        page_widget.setLayout(layout)
        return page_widget
    
    def show_accueil(self):
        """Affiche la page d'accueil et supprime les pages temporaires (projection, etc.)"""
        permanent = {self.page_accueil, self.page_classes, self.page_devoirs, self.page_parametres}
        to_remove = [
            self.stacked_widget.widget(i)
            for i in range(self.stacked_widget.count())
            if self.stacked_widget.widget(i) not in permanent
        ]
        for w in to_remove:
            self.stacked_widget.removeWidget(w)
            w.deleteLater()
        self.stacked_widget.setCurrentWidget(self.page_accueil)
    
    def show_gestion_classes(self):
        """Affiche la page de gestion des classes"""
        if self.page_classes is None and gestion_classes:
            try:
                if hasattr(gestion_classes, 'ClassesWidget'):
                    content = gestion_classes.ClassesWidget(main_window=self)
                    self.page_classes = self.create_page_with_back_button(
                        content, "Gestion des Classes"
                    )
                    self.stacked_widget.addWidget(self.page_classes)
            except Exception as e:
                print(f"Erreur lors de la création de la page classes: {e}")
                return
        
        if self.page_classes:
            self.stacked_widget.setCurrentWidget(self.page_classes)
    
    def show_gestion_devoirs(self):
        """Affiche la page de gestion des devoirs"""
        if self.page_devoirs is None and gestion_devoirs:
            try:
                if hasattr(gestion_devoirs, 'DevoirsWidget'):
                    content = gestion_devoirs.DevoirsWidget()
                    self.page_devoirs = self.create_page_with_back_button(
                        content, "Gestion des Devoirs"
                    )
                    self.stacked_widget.addWidget(self.page_devoirs)
            except Exception as e:
                print(f"Erreur lors de la création de la page devoirs: {e}")
                return
        
        if self.page_devoirs:
            content = getattr(self.page_devoirs, '_content', None)
            if content and hasattr(content, 'charger_devoirs_from_utils'):
                content.charger_classes_from_utils()
                content.charger_devoirs_from_utils()
            self.stacked_widget.setCurrentWidget(self.page_devoirs)
    
    def show_gestion_parametres(self):
        """Affiche la page de gestion des paramètres"""
        if self.page_parametres is None and gestion_parametres:
            try:
                if hasattr(gestion_parametres, 'ParametresWidget'):
                    content = gestion_parametres.ParametresWidget(main_window=self)
                    self.page_parametres = self.create_page_with_back_button(
                        content, "Gestion des Paramètres"
                    )
                    self.stacked_widget.addWidget(self.page_parametres)
            except Exception as e:
                print(f"Erreur lors de la création de la page paramètres: {e}")
                return
        
        if self.page_parametres:
            self.stacked_widget.setCurrentWidget(self.page_parametres)