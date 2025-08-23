from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QLineEdit, QFileDialog, QMenu, QInputDialog, QListWidget,
    QGroupBox, QFrame, QSpacerItem, QSizePolicy, QCheckBox, QProgressBar, QDialog, QListWidgetItem, QColorDialog
)
from PySide6.QtCore import Qt, QObject, Signal, QThread, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor
import numpy as np

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
import plotly.graph_objects as go
import tempfile
import os

from model.data import SingletonData
from view.utils.collapsableBox import CollapsableBox
from view.utils.style_sheet import StyleSheets
from view.utils.pushButton import PushButton
from model.fav import Favorites
from view.utils.colors import get_contrasting_text_color

class VisuTab(QWidget):
    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.data = SingletonData()
        self.style_sheet = StyleSheets()
        self.temp_html_file = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Paramètres d'affichage ---
        param_group = QGroupBox("Paramètres d'affichage")
        param_group.setStyleSheet(self.style_sheet.group_style_sheet)
        param_layout = QHBoxLayout()
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)

        param_layout.addWidget(QLabel("Axe X :"))
        self.combo_i = QComboBox()
        self.combo_i.setStyleSheet(self.style_sheet.combo_box)
        param_layout.addWidget(self.combo_i)
        param_layout.addStretch()

        param_layout.addWidget(QLabel("Axe Y :"))
        self.combo_j = QComboBox()
        self.combo_j.setStyleSheet(self.style_sheet.combo_box)
        param_layout.addWidget(self.combo_j)
        param_layout.addStretch()

        self.validate_btn = PushButton("Valider")
        self.validate_btn.clicked.connect(self.on_axis_change)
        param_layout.addWidget(self.validate_btn)

        self.reset_zoom_btn = PushButton("Reset zoom")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        param_layout.addWidget(self.reset_zoom_btn)

        # --- Layout sliders + figure ---
        self.slider_figure_layout = QHBoxLayout()
        main_layout.addLayout(self.slider_figure_layout)

        self.slider_box = CollapsableBox()
        self.slider_frame = QWidget()
        self.slider_layout = QVBoxLayout(self.slider_frame)
        self.slider_box.setContentWidget(self.slider_frame)
        self.slider_figure_layout.addWidget(self.slider_box, stretch=1)

        self.plot_view = QWebEngineView()
        self.slider_figure_layout.addWidget(self.plot_view, stretch=3)

        # Connexion du toggle sliders
        self.slider_box_visible = False
        self.slider_box._on_toggle(self.slider_box_visible, self._update_slider_visibility)

        # --- Boutons du bas ---
        self.control_box = QGroupBox("Actions")
        self.control_box.setStyleSheet(self.style_sheet.group_style_sheet)
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        self.control_box.setLayout(control_layout)
        main_layout.addWidget(self.control_box)

        self.export_critical_btn = PushButton("Export Critical")
        control_layout.addWidget(self.export_critical_btn)
        self.export_critical_btn.clicked.connect(self._exportCriticalDomain)

        self.export_img_btn = PushButton("Export Graph")
        control_layout.addWidget(self.export_img_btn)
        self.export_img_btn.clicked.connect(self._export_image)

        self.export_backup = PushButton("Export Backup")
        control_layout.addWidget(self.export_backup)
        self.export_backup.clicked.connect(self._exportBackUp)

        self.new_window_btn = PushButton("New Window")
        control_layout.addWidget(self.new_window_btn)
        self.new_window_btn.clicked.connect(self.presenter.open_new_window)

        # --- Bouton Toggle Dock Favoris ---
        self.toggle_fav_btn = PushButton("Show Fav")
        self.toggle_fav_btn.setCheckable(True)
        self.toggle_fav_btn.toggled.connect(self.toggle_favorites_dock)
        control_layout.addWidget(self.toggle_fav_btn)

        # --- Dock latéral flottant pour favoris (invisible par défaut) ---
        self.fav_dock = QFrame(self)
        self.fav_dock.setFrameShape(QFrame.StyledPanel)
        self.fav_dock.setFixedWidth(250)
        self.fav_dock.setVisible(False)
        self.fav_dock.setStyleSheet(self.style_sheet.dock)

        dock_layout = QVBoxLayout(self.fav_dock)
        dock_layout.setContentsMargins(5, 5, 5, 5)
        dock_layout.setSpacing(10)

        # Bouton "Add"
        self.add_fav_btn = PushButton("Add current view to favorites")
        self.add_fav_btn.clicked.connect(self.add_favorite)
        dock_layout.addWidget(self.add_fav_btn)

        # Liste des favoris
        self.favorite_params = QListWidget()
        self.favorite_params.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favorite_params.customContextMenuRequested.connect(self.show_fav_context_menu)
        self.favorite_params.itemDoubleClicked.connect(self.restore_favorite)
        dock_layout.addWidget(self.favorite_params)

        # Initialisation
        self._actualize_fav()
        self.favorite_params.setDragDropMode(QListWidget.InternalMove)
        self.favorite_params.model().rowsMoved.connect(self.on_rows_moved)
        self._actualize_fav()

        self.resizeEvent = self._on_resize  # gère redimensionnement

        # --- Sliders management ---
        self.slider_widgets = {}

        main_layout.setStretch(0, 1)  # boutons rangée 1 : petit ratio
        main_layout.setStretch(1, 6)  # boutons rangée 2 : petit ratio
        main_layout.setStretch(2, 1)

    def _export_image(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'image",
            filter="PNG (*.png);;JPEG (*.jpg);;HTML (*.html);;All files (*)"
        )
        if not file_path:
            return  # Annulé

        # 1. Déterminer le type de fichier choisi
        ext = os.path.splitext(file_path)[1].lower()
        if ext == "":
            if "PNG" in selected_filter:
                file_path += ".png"
            elif "JPEG" in selected_filter:
                file_path += ".jpg"
            elif "HTML" in selected_filter:
                file_path += ".html"
            else:
                file_path += ".png"

        # 2. Construire la figure Plotly (sans sliders)
        fig = go.Figure()

        critic_mask = np.zeros_like(self.Z, dtype=int)
        for idx in self.critical:
            critic_mask[idx] = 1

        fig.add_trace(go.Surface(
            x=self.X,
            y=self.Y,
            z=self.Z,
            surfacecolor=critic_mask,
            colorscale=[[0, "green"], [1, "red"]],
            cmin=0,
            cmax=1,
            showscale=False
        ))

        if self.threshold:
            for val in self.threshold:
                z_plane = np.full_like(self.Z, val)
                fig.add_trace(go.Surface(x=self.X, y=self.Y, z=z_plane,
                                        showscale=False, opacity=0.3, colorscale=[[0, "red"], [1, "red"]]))

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            scene=dict(
                xaxis_title=self.presenter.axis_i,
                yaxis_title=self.presenter.axis_j,
                zaxis_title=self.data.dataFile.axis_name[-1]
            )
        )

        # 3. Sauvegarde selon extension
        if ext == ".html":
            fig.write_html(file_path, include_plotlyjs="cdn", full_html=True)
        elif ext in [".png", ".jpg", ".jpeg"]:
            fig.write_image(file_path, width=900, height=700)  # Nécessite kaleido

        print(f"Graph exporté vers {file_path}")

        # 4. Sauvegarder les valeurs des paramètres (sliders)
        param_path = os.path.splitext(file_path)[0] + "_params.txt"
        param_values = self.get_current_slider_values()
        with open(param_path, "w") as f:
            for name, val in param_values.items():
                f.write(f"{name}: {val:.4f}\n")

        print(f"Paramètres sauvegardés vers {param_path}")

    def set_param_options(self, param_names):
        self.combo_i.clear()
        self.combo_j.clear()
        self.combo_i.addItems(param_names)
        self.combo_j.addItems(param_names)
        if len(param_names) >= 2:
            self.combo_i.setCurrentIndex(0)
            self.combo_j.setCurrentIndex(1)

    def clear_sliders(self):
        while self.slider_layout.count():
            item = self.slider_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.slider_widgets.clear()

    def add_slider(self, param_name, min_val, max_val, initial_val, resolution, callback):
        param_container = QWidget()
        param_layout = QVBoxLayout(param_container)
        label = QLabel(param_name)
        param_layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setStyleSheet(self.style_sheet.slider)
        slider.setMinimum(int(min_val / resolution))
        slider.setMaximum(int(max_val / resolution))
        slider.setValue(int(initial_val / resolution))

        entry = QLineEdit(f"{initial_val:.4f}")
        entry.setFixedWidth(60)

        row = QHBoxLayout()
        row.addWidget(slider)
        row.addWidget(entry)
        param_layout.addLayout(row)

        self.slider_layout.addWidget(param_container)

        def on_slider_change():
            value_int = slider.value()
            val = value_int * resolution
            entry.setText(f"{val:.4f}")
            callback(param_name, val)  # appelle presenter.on_slider_change(...)

        def on_entry_change():
            try:
                val = float(entry.text())
            except ValueError:
                val = slider.value() * resolution
                entry.setText(f"{val:.4f}")
                return
            clipped_val = max(min(val, max_val), min_val)
            slider.setValue(int(clipped_val / resolution))

        # slider.valueChanged.connect(on_slider_change) #for a maj live while the slider slides but makes the view lagging
        slider.sliderReleased.connect(on_slider_change)
        entry.editingFinished.connect(on_entry_change)
        self.slider_widgets[param_name] = (slider, entry, resolution)

    def set_sliders(self, sliders: dict[str, int]):
        for param_name, val in sliders.items():
            if param_name in self.slider_widgets:
                slider, entry, resolution = self.slider_widgets[param_name]
                slider.setValue(int(val / resolution))
                entry.setText(f"{val:.4f}")

    def get_current_slider_values(self) -> dict[str, int]:
        values = {}
        for param_name, (slider, _, resolution) in self.slider_widgets.items():
            val = slider.value() * resolution
            values[param_name] = float(val)
        return values

    def on_axis_change(self):
        if self.presenter:
            self.presenter.update_axes(self.combo_i.currentText(), self.combo_j.currentText())

    def plot_surface(self, x, y, z, threshold=None, critical=[]):
        self.X, self.Y, self.Z = x, y, z
        self.critical = critical
        self.threshold = threshold

        fig = go.Figure()

        critic_mask = np.zeros_like(z, dtype=int)
        for idx in critical:
            critic_mask[idx] = 1

        fig.add_trace(go.Surface(
            x=x,
            y=y,
            z=z,
            surfacecolor=critic_mask,
            colorscale=[[0, "green"], [0.4999, "green"], [0.5, "red"], [1, "red"]],
            cmin=0,
            cmax=1,
            showscale=False
        ))

        if threshold:
            for val in threshold:
                z_plane = np.full_like(z, val)
                fig.add_trace(go.Surface(x=x, y=y, z=z_plane, showscale=False, opacity=0.3, colorscale=[[0, "red"], [1, "red"]]))

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            scene=dict(
                xaxis_title=self.presenter.axis_i,
                yaxis_title=self.presenter.axis_j,
                zaxis_title=self.data.dataFile.axis_name[-1]
            )
        )

        if self.temp_html_file and os.path.exists(self.temp_html_file):
            os.remove(self.temp_html_file)

        fd, self.temp_html_file = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        fig.write_html(self.temp_html_file, include_plotlyjs='directory', full_html=True)
        self.plot_view.load(QUrl.fromLocalFile(self.temp_html_file))

    def reset_zoom(self):
        self.plot_surface(self.X, self.Y, self.Z, self.threshold, self.critical)

    def set_axis_x(self, axis_name: str):
        self.combo_i.setCurrentText(axis_name)

    def set_axis_y(self, axis_name: str):
        self.combo_j.setCurrentText(axis_name)

    def _exportCriticalDomain(self) -> None:
        self.presenter.mesh.exportCriticalDomain()

        return None
    
    def _exportBackUp(self) -> None:
        '''exports the backup file'''
        n_values = np.prod(self.presenter.mesh.map.shape)
        if n_values > 1000:
            # Boîte indéterminée car on ne peut pas suivre la progression
            self.progress_dialog = IndeterminateProgressDialog(parent=self)
            self.progress_dialog.show()

            self.export_thread = QThread()
            self.export_worker = ExportWorker(self.presenter.mesh.exportBackUp_parallel, parallel=True)
            self.export_worker.moveToThread(self.export_thread)

            # Pas de signal progress_signal ici, juste finished_signal
            self.export_worker.finished_signal.connect(self.progress_dialog.close)
            self.export_worker.finished_signal.connect(self.export_thread.quit)
            self.export_worker.finished_signal.connect(self.export_worker.deleteLater)
            self.export_thread.finished.connect(self.export_thread.deleteLater)

            self.export_thread.started.connect(self.export_worker.run)
            self.export_thread.start()
        else:
            self.progress_dialog = ProgressDialog(n_values, parent=self)
            self.progress_dialog.show()

            self.export_thread = QThread()
            self.export_worker = ExportWorker(self.presenter.mesh.exportBackUp)
            self.export_worker.moveToThread(self.export_thread)

            self.export_worker.progress_signal.connect(self.progress_dialog.update_progress)
            self.export_worker.finished_signal.connect(self.progress_dialog.close)
            self.export_worker.finished_signal.connect(self.export_thread.quit)
            self.export_worker.finished_signal.connect(self.export_worker.deleteLater)
            self.export_thread.finished.connect(self.export_thread.deleteLater)

            self.export_thread.started.connect(self.export_worker.run)
            self.export_thread.start()

    def _update_slider_visibility(self):
        # Réajuste la répartition des espaces dans le layout
        if self.slider_box_visible:
            self.slider_figure_layout.setStretch(0, 1)  # Sliders
            self.slider_figure_layout.setStretch(1, 3)  # Figure
        else:
            self.slider_figure_layout.setStretch(0, 0)  # Sliders cachés
            self.slider_figure_layout.setStretch(1, 1)  # Figure prend tout

    
    def toggle_favorites_dock(self, checked):
        self.fav_dock.setVisible(checked)
        if checked:
            self.toggle_fav_btn.setText("Hide Fav")
            self._actualize_fav()
        else:
            self.toggle_fav_btn.setText("Show Fav")
            self._actualize_fav()

    def _on_resize(self, event):
        self._update_fav_dock_position()
        QWidget.resizeEvent(self, event)

    def _update_fav_dock_position(self):
        # Remplacer canvas par plot_view
        canvas_geom = self.plot_view.geometry()
        x = canvas_geom.right() - self.fav_dock.width()
        y = canvas_geom.top()
        height = canvas_geom.height()
        self.fav_dock.setGeometry(x, y, self.fav_dock.width(), height)

    def show_fav_context_menu(self, position):
        item = self.favorite_params.itemAt(position)
        if item is None:
            return

        fav_name = item.data(256)
        if fav_name not in self.data.fav:
            return

        menu = QMenu()
        rename_action = menu.addAction("Rename")
        color_action = menu.addAction("Set Color")

        action = menu.exec(self.favorite_params.mapToGlobal(position))

        if action == rename_action:
            self.rename_favorite(fav_name)
        elif action == color_action:
            self.change_favorite_color(fav_name)

    def change_favorite_color(self, key: str):
        fav = self.data.fav[key]
        color = QColorDialog.getColor(QColor(fav.color), self, "Choose Favorite Color")
        if color.isValid():
            fav.color = color.name()
            self._actualize_fav()

    def _actualize_fav(self):
        self.favorite_params.clear()
        self.favorite_params.setSpacing(6)

        # for fav_name, fav in self.data.fav.items():
        for fav_name in self.data.fav_order:
            if fav_name not in self.data.fav:
                self.data.fav_order.remove(fav_name)
                continue
            fav = self.data.fav[fav_name]
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(6)

            label = QLabel(fav.name)
            tooltip_text = (
                f"<b>Nom :</b> {fav.name}<br>"
                f"<b>Axes :</b> X = {fav.axis_x}, Y = {fav.axis_y}<br>"
                f"<b>Sliders :</b><br>" +
                "<br>".join(f"&nbsp;&nbsp;- {k}: {v}" for k, v in fav.sliders.items())
            )
            label.setToolTip(tooltip_text)
            # Récupération de la couleur personnalisée
            text_color = get_contrasting_text_color(fav.color)

            # Style général (appliqué au bloc entier)
            item_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {fav.color};
                    border: 0px solid #ccc;
                    border-radius: 8px;
                }}
                QLabel {{
                    font-size: 13px;
                    color: {text_color};
                    padding: 0px;
                    margin: 0px;
                }}
            """)
            layout.addWidget(label, stretch=1)

            delete_btn = QPushButton()
            delete_btn.setIcon(QIcon("view/img/bin.png"))
            delete_btn.setIconSize(QSize(16, 16))
            delete_btn.setFixedSize(24, 24)
            delete_btn.setToolTip("Supprimer ce favori")
            delete_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #e57373;
                    border-radius: 12px;
                }
            """)
            layout.addWidget(delete_btn)

            delete_btn.clicked.connect(lambda _, name=fav_name: self.delete_favorite(name))

            item = QListWidgetItem(self.favorite_params)
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.UserRole, fav_name)  # Stocker le nom du favori dans l'item
            self.favorite_params.addItem(item)
            self.favorite_params.setItemWidget(item, item_widget)

    
    def on_rows_moved(self, parent, start, end, destination, row):
        new_order = []
        for i in range(self.favorite_params.count()):
            item = self.favorite_params.item(i)
            fav_name = item.data(Qt.UserRole)
            if fav_name in self.data.fav:
                new_order.append(fav_name)

        self.data.fav_order = new_order
        # Pas besoin d’appeler _actualize_fav()

    def delete_favorite(self, fav_name):
        if fav_name in self.data.fav:
            del self.data.fav[fav_name]
            if fav_name in self.data.fav_order:
                self.data.fav_order.remove(fav_name)
            self._actualize_fav()
    
    def rename_favorite(self, old_name):
        if old_name not in self.data.fav:
            return

        fav = self.data.fav[old_name]
        new_name, ok = QInputDialog.getText(self, "Rename Favorite", "Enter new name:", text=fav.name)

        if ok and new_name and new_name != old_name:
            # Mettre à jour le dict
            fav.name = new_name
            self.data.fav[new_name] = self.data.fav.pop(old_name)

            # Mettre à jour la liste d'ordre
            if old_name in self.data.fav_order:
                index = self.data.fav_order.index(old_name)
                self.data.fav_order[index] = new_name

            self._actualize_fav()

    def restore_favorite(self, item: QListWidgetItem):
        fav_name = item.data(256)
        if fav_name not in self.data.fav:
            return

        fav = self.data.fav[fav_name]

        # Étape 1 — changer les axes
        self.set_axis_x(fav.axis_x)
        self.set_axis_y(fav.axis_y)

        # Étape 2 — informer le presenter (ce qui déclenche probablement la recréation des sliders)
        self.presenter.update_axes(fav.axis_x, fav.axis_y)

        # Étape 3 — après recréation des sliders, appliquer leurs valeurs
        QTimer.singleShot(0, lambda: self.set_sliders(fav.sliders))

    def add_favorite(self):
        def _add():
            axis_x = self.combo_i.currentText()
            axis_y = self.combo_j.currentText()
            sliders = self.get_current_slider_values()

            # Nom unique simple : incrémenter jusqu'à ce que ça passe
            base_name = "Favorite"
            i = 1
            while f"{base_name} {i}" in self.data.fav:
                i += 1
            name = f"{base_name} {i}"

            fav = Favorites(name=name, axis_x=axis_x, axis_y=axis_y, sliders=sliders)
            self.data.fav[name] = fav
            self.data.fav_order.append(name)
            self._actualize_fav()

        # Laisser à Qt le temps de recréer les sliders après un changement d’axe
        QTimer.singleShot(0, _add)

class ProgressDialog(QDialog):
    def __init__(self, n_values, title="Exporting Backup", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        self.label = QLabel("Backup export running ...", self)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, n_values)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)

    def update_progress(self, value):
        self.progress.setValue(value)
    
class ExportWorker(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, export_backup_func, parallel=False):
        super().__init__()
        self.export_backup_func = export_backup_func
        self.parallel=parallel

    def run(self):
        def progress_callback(current):
            self.progress_signal.emit(current)

        if self.parallel:
            self.export_backup_func()
        else:
            self.export_backup_func(progress_callback)
        self.finished_signal.emit()

class IndeterminateProgressDialog(QDialog):
    def __init__(self, title="Exporting Backup", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        self.label = QLabel("Backup export running, please wait but we launched it on multiple cores to be faster :)", self)
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # mode indéterminé

        layout.addWidget(self.label)
        layout.addWidget(self.progress)

class FavoriteItemWidget(QWidget):
    def __init__(self, fav: Favorites, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Nom du favori
        name_label = QLabel(fav.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)

        # Résumé sliders
        sliders_text = ", ".join(f"{k}={v}" for k, v in fav.sliders.items())
        detail_label = QLabel(sliders_text)
        detail_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(detail_label)

        # Ligne séparatrice (optionnel)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ccc;")
        layout.addWidget(line)
