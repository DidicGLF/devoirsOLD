# screens/gestion_devoirs.py - VERSION AMÉLIORÉE
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QDateEdit, QComboBox,
    QLineEdit, QPushButton, QFrame, QLabel, QSpacerItem, QSizePolicy, QScrollArea, QCheckBox, QApplication
)
from PySide6.QtCore import Qt, QDate, QTimer, QEvent, QMimeData, QPoint, QRect, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QFont, QPalette, QDrag, QPixmap, QPainter, QPen

from datetime import datetime

from utils.gestion import charger_classes, charger_devoirs, sauvegarder_devoirs, couleur_to_rgb
from models.Devoir import Devoir


class DropIndicatorLine(QWidget):
    """Ligne indicatrice simple qui ne perturbe pas le layout"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Ne capte pas les événements souris
        self.setStyleSheet("""
            QWidget {
                background-color: #4A90E2;
                border-radius: 1px;
            }
        """)
        self.hide()


class DevoirsWidget(QWidget):
    """Écran de gestion des devoirs — partie saisie + liste des devoirs (design personnalisé)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.classes_list = []
        self.devoirs_list = []
        self.drop_indicator = None  # Ligne indicatrice
        self.drop_target_index = -1  # Position cible pour le drop
        self.current_drag_index = -1  # Index de la carte en cours de drag
        self.init_ui()

    def init_ui(self):
        # Layout principal (vertical)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 0, 50, 50)

        # Ligne de saisie (horizontal)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        # 1. Classe (QComboBox)
        self.combo_classe = QComboBox()
        self.combo_classe.setFixedWidth(120)
        input_layout.addWidget(self.combo_classe)

        # 2. Sélecteur de date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setFixedWidth(120)
        input_layout.addWidget(self.date_edit)

        # 3. Contenu (QLineEdit)
        self.line_content = QLineEdit()
        self.line_content.setPlaceholderText("Description du devoir...")
        self.line_content.setFixedHeight(30)
        input_layout.addWidget(self.line_content, 1)

        # 5. Bouton Ajouter
        self.btn_ajouter = QPushButton("Ajouter")
        self.btn_ajouter.setFixedSize(100, 40)
        self.btn_ajouter.setStyleSheet("""
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
        """)
        input_layout.addWidget(self.btn_ajouter)

        main_layout.addLayout(input_layout)
        main_layout.addSpacing(20)

        # Barre de tri (centrée)
        tri_layout = QHBoxLayout()
        tri_layout.setSpacing(10)
        tri_layout.setContentsMargins(0, 0, 0, 10)
        tri_layout.addStretch()

        tri_label = QLabel("Trier par :")
        tri_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        tri_layout.addWidget(tri_label)

        # Bouton tri par date
        self.btn_tri_date = QPushButton("Date")
        self.btn_tri_date.setFixedSize(100, 35)
        self.btn_tri_date.setCheckable(True)
        self.btn_tri_date.clicked.connect(self.trier_par_date)
        tri_layout.addWidget(self.btn_tri_date)

        # Bouton tri par classe
        self.btn_tri_classe = QPushButton("Classe")
        self.btn_tri_classe.setFixedSize(100, 35)
        self.btn_tri_classe.setCheckable(True)
        self.btn_tri_classe.clicked.connect(self.trier_par_classe)
        tri_layout.addWidget(self.btn_tri_classe)

        # Bouton ordre manuel
        self.btn_tri_manuel = QPushButton("Manuel")
        self.btn_tri_manuel.setFixedSize(100, 35)
        self.btn_tri_manuel.setCheckable(True)
        self.btn_tri_manuel.setChecked(True)
        self.btn_tri_manuel.clicked.connect(self.trier_manuel)
        tri_layout.addWidget(self.btn_tri_manuel)
        
        # Bouton Projection
        self.btn_projection = QPushButton("Projection")
        self.btn_projection.setFixedSize(120, 35)
        self.btn_projection.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 2px solid #28a745;
                border-radius: 8px;
                font-size: 12px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #218838;
                border-color: #218838;
            }
            QPushButton:checked {
                background-color: #1e7e34;
                border-color: #1e7e34;
            }
        """)
        self.btn_projection.clicked.connect(self.ouvrir_projection)
        tri_layout.addWidget(self.btn_projection)

        # Style des boutons de tri
        style_btn_tri = """
            QPushButton {
                background-color: white;
                color: #333;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 12px;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
            QPushButton:checked {
                background-color: #4A90E2;
                color: white;
                border-color: #4A90E2;
            }
        """
        self.btn_tri_date.setStyleSheet(style_btn_tri)
        self.btn_tri_classe.setStyleSheet(style_btn_tri)
        self.btn_tri_manuel.setStyleSheet(style_btn_tri)
        tri_layout.addStretch()

        main_layout.addLayout(tri_layout)

        # Zone de scroll pour la liste des devoirs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Conteneur pour la liste des devoirs
        self.scroll_container = QWidget()
        self.scroll_container.setAcceptDrops(True)  # Important pour le drop global
        self.scroll_container.dragEnterEvent = self.container_drag_enter
        self.scroll_container.dragMoveEvent = self.container_drag_move
        self.scroll_container.dragLeaveEvent = self.container_drag_leave
        self.scroll_container.dropEvent = self.container_drop
        
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_container.setLayout(self.scroll_layout)
        
        # Créer la ligne indicatrice (overlay qui ne perturbe pas le layout)
        self.drop_indicator = DropIndicatorLine(self.scroll_container)

        scroll_area.setWidget(self.scroll_container)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

        # Charger les classes et devoirs
        self.charger_classes_from_utils()
        self.charger_devoirs_from_utils()

        # Connexion du bouton
        self.btn_ajouter.clicked.connect(self.ajouter_devoir)

    def charger_classes_from_utils(self):
        """Charge les classes depuis utils/gestion.py et les ajoute au QComboBox"""
        classes = charger_classes()
        self.classes_list = classes
        self.combo_classe.clear()
        for classe in classes:
            self.combo_classe.addItem(classe.nom)

    def charger_devoirs_from_utils(self):
        """Charge les devoirs depuis utils/gestion.py et les affiche dans la liste personnalisée"""
        devoirs = charger_devoirs(classes=self.classes_list)
        self.devoirs_list = devoirs

        # Vider la liste
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.scroll_layout.removeItem(item)

        # Ajouter chaque devoir comme une carte personnalisée
        for devoir in devoirs:
            card = DevoirCard(devoir, self)
            self.scroll_layout.addWidget(card)

        # Ajouter un espaceur à la fin
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)

    def ajouter_devoir(self):
        """Ajoute un devoir à la liste et sauvegarde"""
        contenu = self.line_content.text().strip()
        
        if not contenu or self.combo_classe.currentIndex() == -1:
            return
        
        classe_index = self.combo_classe.currentIndex()
        classe_objet = self.classes_list[classe_index]
        date = self.date_edit.date().toString("yyyy-MM-dd")
        statut = "Pas fait"
        
        nouveau_devoir = Devoir(
            contenu=contenu,
            classe_objet=classe_objet,
            date=date,
            statut=statut
        )
        
        self.devoirs_list.append(nouveau_devoir)
        sauvegarder_devoirs(self.devoirs_list)
        self.charger_devoirs_from_utils()
        self.line_content.clear()

    def supprimer_devoir(self, devoir):
        """Supprime un devoir de la liste et sauvegarde"""
        if devoir in self.devoirs_list:
            self.devoirs_list.remove(devoir)
            sauvegarder_devoirs(self.devoirs_list)
            self.charger_devoirs_from_utils()

    def trier_par_date(self):
        """Trie les devoirs par date (tri visuel uniquement, non sauvegardé)"""
        self.btn_tri_classe.setChecked(False)
        self.btn_tri_manuel.setChecked(False)
        
        if not self.btn_tri_date.isChecked():
            self.btn_tri_manuel.setChecked(True)
            self.trier_manuel()
            return
        
        devoirs_tries = sorted(self.devoirs_list, key=lambda d: d.date)
        self.afficher_devoirs(devoirs_tries)

    def trier_par_classe(self):
        """Trie les devoirs par classe (tri visuel uniquement, non sauvegardé)"""
        self.btn_tri_date.setChecked(False)
        self.btn_tri_manuel.setChecked(False)
        
        if not self.btn_tri_classe.isChecked():
            self.btn_tri_manuel.setChecked(True)
            self.trier_manuel()
            return
        
        devoirs_tries = sorted(self.devoirs_list, key=lambda d: d.classe_objet.nom)
        self.afficher_devoirs(devoirs_tries)

    def trier_manuel(self):
        """Revient à l'ordre manuel (celui du fichier JSON)"""
        self.btn_tri_date.setChecked(False)
        self.btn_tri_classe.setChecked(False)
        self.btn_tri_manuel.setChecked(True)
        self.charger_devoirs_from_utils()

    def afficher_devoirs(self, devoirs):
        """Affiche une liste de devoirs (sans sauvegarder)"""
        # Vider la liste
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.spacerItem():
                self.scroll_layout.removeItem(item)

        # Ajouter chaque devoir comme une carte personnalisée
        for devoir in devoirs:
            card = DevoirCard(devoir, self)
            self.scroll_layout.addWidget(card)

        # Ajouter un espaceur à la fin
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)

    def ouvrir_projection(self):
        """Ouvre la page de projection"""
        from screens.gestion_projection import ProjectionWidget
        
        if hasattr(self, 'parent') and self.parent():
            main_window = self.parent()
            while main_window.parent():
                main_window = main_window.parent()

            current_page = main_window.stacked_widget.currentWidget()
            page_projection = ProjectionWidget(main_window=main_window)
            page_complete = main_window.create_page_with_back_button(
                page_projection,
                "Projection",
                back_widget=current_page
            )
            main_window.stacked_widget.addWidget(page_complete)
            main_window.stacked_widget.setCurrentWidget(page_complete)

    def show_drop_indicator(self, y_position):
        """Affiche la ligne indicatrice à la position Y donnée"""
        if self.drop_indicator:
            self.drop_indicator.move(0, y_position)
            self.drop_indicator.setFixedWidth(self.scroll_container.width())
            self.drop_indicator.show()
            self.drop_indicator.raise_()  # Mettre au premier plan

    def hide_drop_indicator(self):
        """Cache la ligne indicatrice"""
        if self.drop_indicator:
            self.drop_indicator.hide()

    def get_drop_position(self, y_pos):
        """Calcule la position Y où afficher la ligne et l'index de drop"""
        local_y = y_pos
        
        # Chercher entre quelles cartes on doit insérer
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), DevoirCard):
                widget = item.widget()
                widget_y = widget.y()
                widget_height = widget.height()
                widget_center = widget_y + widget_height / 2
                
                # Si on est au-dessus du centre, insérer avant
                if local_y < widget_center:
                    self.drop_target_index = i
                    return widget_y - 5  # Position de la ligne juste au-dessus
        
        # Si on arrive ici, insérer à la fin
        # Trouver la dernière carte
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), DevoirCard):
                widget = item.widget()
                self.drop_target_index = i + 1
                return widget.y() + widget.height() + 5  # Position après la dernière carte
        
        # Aucune carte trouvée
        self.drop_target_index = 0
        return 0

    def container_drag_enter(self, event):
        """Gère l'entrée du drag dans le conteneur"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def container_drag_move(self, event):
        """Gère le mouvement du drag dans le conteneur"""
        if event.mimeData().hasText():
            # Calculer la position de drop
            local_pos = event.position().toPoint()
            y_position = self.get_drop_position(local_pos.y())
            
            # Afficher la ligne indicatrice
            self.show_drop_indicator(y_position)
            
            event.acceptProposedAction()

    def container_drag_leave(self, event):
        """Gère la sortie du drag du conteneur"""
        self.hide_drop_indicator()
        self.drop_target_index = -1

    def container_drop(self, event):
        """Gère le drop dans le conteneur"""
        if event.mimeData().hasText():
            source_index = int(event.mimeData().text())
            
            # Cacher l'indicateur
            self.hide_drop_indicator()
            
            if self.drop_target_index < 0:
                # Pas de position cible, abandon
                event.acceptProposedAction()
                return
            
            # Calculer le vrai index dans devoirs_list
            # Compter combien de DevoirCard il y a avant la position cible
            real_target_index = 0
            for i in range(self.drop_target_index):
                item = self.scroll_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), DevoirCard):
                    real_target_index += 1
            
            if source_index != real_target_index:
                # Réorganiser la liste
                devoir_deplace = self.devoirs_list.pop(source_index)
                
                # Ajuster l'index si nécessaire
                if real_target_index > source_index:
                    real_target_index -= 1
                
                self.devoirs_list.insert(real_target_index, devoir_deplace)
                
                # Sauvegarder
                sauvegarder_devoirs(self.devoirs_list)
                
                # Recharger
                self.charger_devoirs_from_utils()
            
            self.drop_target_index = -1
            event.acceptProposedAction()


class DevoirCard(QFrame):
    """Widget personnalisé pour afficher un devoir sous forme de carte - VERSION AMÉLIORÉE"""
    def __init__(self, devoir, parent_widget=None):
        super().__init__()
        self.devoir = devoir
        self.parent_widget = parent_widget
        self.setAcceptDrops(False)  # IMPORTANT : ne pas accepter les drops sur les cartes individuelles !
        self.drag_start_position = None
        self.is_being_dragged = False
        self.init_ui()

    def init_ui(self):
        self.rgb_values = couleur_to_rgb(self.devoir.classe_objet.couleur)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({rgb_values}, 0.15);
                border-radius: 10px;
                border: 1px solid rgba({rgb_values}, 0.3);
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                font-size: 14px;
                color: #333;
                padding: 5px;
                background-color: transparent;
            }}
        """)

        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Ligne principale
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Case à cocher
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(30, 30)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 25px;
                height: 25px;
                border-radius: 5px;
                border: 2px solid #4A90E2;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border-color: #28a745;
            }
        """)
        if self.devoir.statut in ["Fait", "Terminé"]:
            self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.changer_statut)
        top_layout.addWidget(self.checkbox)

        # Classe
        label_classe = QLabel(f"📚 {self.devoir.classe_objet.nom}")
        label_classe.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(label_classe)

        # Date
        date_affichage = self.devoir.date
        try:
            date_obj = datetime.strptime(self.devoir.date, "%Y-%m-%d")
            date_affichage = date_obj.strftime("%d-%m-%Y")
        except ValueError:
            pass
        
        label_date = QLabel(f"📅 {date_affichage}")
        label_date.setStyleSheet("font-size: 13px; color: #666;")
        top_layout.addWidget(label_date)

        # Contenu
        self.label_contenu = QLabel(self.devoir.contenu)
        self.label_contenu.setWordWrap(True)
        self.label_contenu.setStyleSheet("font-size: 14px; color: #333;")
        self.label_contenu.setCursor(Qt.PointingHandCursor)
        self.label_contenu.mousePressEvent = self.activer_edition_contenu
        top_layout.addWidget(self.label_contenu, 1)
        
        # Champ d'édition
        self.line_edit_contenu = QLineEdit(self.devoir.contenu)
        self.line_edit_contenu.setStyleSheet("font-size: 14px; color: #333;")
        self.line_edit_contenu.hide()
        self.line_edit_contenu.returnPressed.connect(self.sauvegarder_contenu)
        self.line_edit_contenu.editingFinished.connect(self.sauvegarder_contenu)
        top_layout.addWidget(self.line_edit_contenu, 1)

        # Statut
        self.label_statut = QLabel(self.devoir.statut)
        self.label_statut.setObjectName("statut")
        if self.devoir.statut in ("Fait", "Terminé"):
            self.label_statut.setStyleSheet("font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: #28a745; color: white;")
        else:
            self.label_statut.setStyleSheet("font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: #dc3545; color: white;")

        top_layout.addWidget(self.label_statut)

        # Bouton supprimer
        btn_supprimer = QPushButton("🗑️")
        btn_supprimer.setFixedSize(35, 35)
        btn_supprimer.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #dc3545;
                border: 2px solid #dc3545;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffe6e6;
            }
            QPushButton:pressed {
                background-color: #ffcccc;
            }
        """)
        btn_supprimer.clicked.connect(self.supprimer)
        top_layout.addWidget(btn_supprimer)

        layout.addLayout(top_layout)
        self.setLayout(layout)

        self.setMouseTracking(True)
        self.installEventFilter(self)

    def mousePressEvent(self, event):
        """Démarre le drag & drop"""
        if event.button() == Qt.LeftButton:
            widget_under_mouse = QApplication.widgetAt(event.globalPosition().toPoint())
            if widget_under_mouse in [self.checkbox, self.label_contenu, self.line_edit_contenu]:
                super().mousePressEvent(event)
                return
            if isinstance(widget_under_mouse, QPushButton):
                super().mousePressEvent(event)
                return
                
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Gère le déplacement pendant le drag - VERSION AMÉLIORÉE"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.drag_start_position is None:
            return
        
        # Distance de déclenchement réduite pour plus de réactivité  
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        # Marquer comme en cours de déplacement
        self.is_being_dragged = True
        
        # Informer le parent du début du drag
        if self.parent_widget:
            self.parent_widget.current_drag_index = self.parent_widget.devoirs_list.index(self.devoir)
        
        # Créer le drag
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Stocker l'index de cette carte
        index = self.parent_widget.devoirs_list.index(self.devoir)
        mime_data.setText(str(index))
        drag.setMimeData(mime_data)
        
        # Créer une silhouette améliorée avec ombre portée
        pixmap = self.create_drag_pixmap()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        # Rendre semi-transparent pendant le drag
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({self.rgb_values}, 0.05);
                border-radius: 10px;
                border: 2px dashed rgba({self.rgb_values}, 0.3);
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                font-size: 14px;
                color: #999;
                padding: 5px;
                background-color: transparent;
            }}
        """)

        # Exécuter le drag
        result = drag.exec(Qt.MoveAction)
        
        # Restaurer l'apparence normale
        self.is_being_dragged = False
        if self.parent_widget:
            self.parent_widget.current_drag_index = -1
            self.parent_widget.hide_drop_indicator()
        self.restaurer_style_normal()

    def create_drag_pixmap(self):
        """Crée un pixmap amélioré pour le drag avec ombre portée"""
        # Taille avec marge pour l'ombre
        shadow_offset = 8
        pixmap_width = self.width() + shadow_offset * 2
        pixmap_height = self.height() + shadow_offset * 2
        
        pixmap = QPixmap(pixmap_width, pixmap_height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dessiner l'ombre portée
        shadow_rect = QRect(shadow_offset + 4, shadow_offset + 4, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.drawRoundedRect(shadow_rect, 10, 10)
        
        # Dessiner la carte elle-même avec une légère transparence
        painter.setOpacity(0.85)
        self.render(painter, QPoint(shadow_offset, shadow_offset))
        
        # Ajouter une bordure bleue pour indiquer le drag
        painter.setOpacity(1.0)
        painter.setPen(QPen(QColor(74, 144, 226), 3))
        painter.setBrush(Qt.NoBrush)
        card_rect = QRect(shadow_offset, shadow_offset, self.width(), self.height())
        painter.drawRoundedRect(card_rect, 10, 10)
        
        painter.end()
        return pixmap

    def mouseReleaseEvent(self, event):
        """Fin du drag"""
        self.drag_start_position = None
        super().mouseReleaseEvent(event)

    def supprimer(self):
        """Supprime ce devoir"""
        if self.parent_widget:
            self.parent_widget.supprimer_devoir(self.devoir)

    def changer_statut(self, state):
        """Change le statut du devoir en fonction de l'état de la case à cocher"""
        if state == Qt.Checked:
            self.devoir.statut = "Fait"
        else:
            self.devoir.statut = "Pas fait"
        
        self.mettre_a_jour_affichage_statut()
        
        if self.parent_widget:
            sauvegarder_devoirs(self.parent_widget.devoirs_list)

    def activer_edition_contenu(self, event):
        """Active le mode édition du contenu"""
        self.label_contenu.hide()
        self.line_edit_contenu.setText(self.devoir.contenu)
        self.line_edit_contenu.show()
        self.line_edit_contenu.setFocus()
        self.line_edit_contenu.selectAll()

    def copier_contenu(self):
        """Copie le contenu du devoir dans le presse-papier"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.devoir.contenu)
        
        # Animation de feedback
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(33, 150, 243, 0.25);
                border-radius: 10px;
                border: 2px solid #2196F3;
                padding: 10px;
                margin: 5px;
            }}
        """)
        
        QTimer.singleShot(200, self.restaurer_style_normal)

    def sauvegarder_contenu(self):
        """Sauvegarde le contenu modifié"""
        nouveau_contenu = self.line_edit_contenu.text().strip()
        
        if nouveau_contenu:
            self.devoir.contenu = nouveau_contenu
            self.label_contenu.setText(nouveau_contenu)
            
            if self.parent_widget:
                sauvegarder_devoirs(self.parent_widget.devoirs_list)
        
        self.line_edit_contenu.hide()
        self.label_contenu.show()

    def mettre_a_jour_affichage_statut(self):
        """Met à jour l'affichage du label de statut"""
        self.label_statut.setText(self.devoir.statut)
        if self.devoir.statut in ("Fait", "Terminé"):
            self.label_statut.setStyleSheet("font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: #28a745; color: white;")
        else:
            self.label_statut.setStyleSheet("font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: #dc3545; color: white;")

    def restaurer_style_normal(self):
        """Restaure le style normal avec la couleur de la classe"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({self.rgb_values}, 0.15);
                border-radius: 10px;
                border: 1px solid rgba({self.rgb_values}, 0.3);
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                font-size: 14px;
                color: #333;
                padding: 5px;
                background-color: transparent;
            }}
        """)

    def eventFilter(self, obj, event):
        if obj == self:
            if event.type() == QEvent.MouseButtonPress:
                widget_under_mouse = QApplication.widgetAt(event.globalPosition().toPoint())
                if widget_under_mouse not in [self.checkbox, self.label_contenu, self.line_edit_contenu]:
                    if not isinstance(widget_under_mouse, QPushButton):
                        self.copier_contenu()
            elif event.type() == QEvent.Enter:
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: rgba({self.rgb_values}, 0.25);
                        border-radius: 10px;
                        border: 2px solid rgba({self.rgb_values}, 0.5);
                        padding: 10px;
                        margin: 5px;
                    }}
                    QLabel {{
                        font-size: 14px;
                        color: #333;
                        padding: 5px;
                        background-color: transparent;
                    }}
                """)
            elif event.type() == QEvent.Leave:
                if not self.is_being_dragged:
                    self.restaurer_style_normal()
        return super().eventFilter(obj, event)