import os
import tempfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt

import plotly.graph_objects as go

from model.data import SingletonData

from view.utils.pushButton import PushButton
from view.utils.customLineEdit import CustomLineEdit
from view.utils.colors import getColorScale

class ParallelTab(QWidget):
    def __init__(self, presenter, function_column='f', parent=None):
        super().__init__(parent)
        self.data = presenter.mesh.toDataframe()
        self.function_column = function_column
        self.param_names = [col for col in self.data.columns if col != function_column]

        # Bornes globales
        self.global_min = float(self.data[self.function_column].min())
        self.global_max = float(self.data[self.function_column].max())

        self.layout = QVBoxLayout(self)

        # Web view for Plotly
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view, stretch=1)

        # Bottom bar
        self.toggle_bar = QHBoxLayout()
        self.toggle_bar.setAlignment(Qt.AlignBottom)

        # Export button
        self.export_button = PushButton("Exporter")
        self.export_button.clicked.connect(self.export_plot)
        self.toggle_bar.addWidget(self.export_button)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.toggle_bar.addWidget(separator)

        self.line_edit_min = CustomLineEdit("Min", f"{self.global_min:.3f}")
        self.line_edit_max = CustomLineEdit("Max", f"{self.global_max:.3f}")
        self.toggle_bar.addWidget(self.line_edit_min) #ce sont les labels qui poussent els boutons vers le haut
        self.toggle_bar.addWidget(self.line_edit_max)

        # Apply button
        self.apply_button = PushButton("Apply")
        self.apply_button.clicked.connect(self.apply_filter)
        self.toggle_bar.addWidget(self.apply_button)

        # Reset button
        self.reset_button = PushButton("Reset")
        self.reset_button.clicked.connect(self.reset_filter)
        self.toggle_bar.addWidget(self.reset_button)

        self.layout.addLayout(self.toggle_bar)

        # Temp file handle
        self.temp_html_file = None

        # Initial plot
        self.reset_filter()

    def update_plot(self, vmin=None, vmax=None):
        if vmin is None or vmax is None:
            vmin, vmax = self.global_min, self.global_max

        filtered = self.data[(self.data[self.function_column] >= vmin) &
                            (self.data[self.function_column] <= vmax)]
        outliers = self.data.drop(filtered.index)

        colors = self.data[self.function_column].copy()
        # Marquer les outliers avec une valeur hors échelle
        colors.loc[outliers.index] = vmin - 1e-6  # valeur légèrement inférieure à vmin

        fig = go.Figure(go.Parcoords(
            line=dict(
                color=colors,
                colorscale=getColorScale(SingletonData().dataFile.critical_value, SingletonData().dataFile.criterium, vmin, vmax),
                cmin=vmin,
                cmax=vmax,
                showscale=True
            ),
            dimensions=[dict(label=col, values=self.data[col].to_numpy()) for col in self.param_names]
        ))

        # Nouveau fichier temporaire
        fd, temp_file = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        fig.write_html(temp_file, include_plotlyjs='directory', full_html=True)

        self.web_view.load(QUrl.fromLocalFile(os.path.abspath(temp_file)))

        if self.temp_html_file:
            try:
                os.remove(self.temp_html_file)
            except PermissionError:
                pass

        self.temp_html_file = temp_file
        self.last_figure = fig

    def apply_filter(self):
        try:
            vmin = float(self.line_edit_min.text())
            vmax = float(self.line_edit_max.text())
        except ValueError as e:
            print(f"Error when settings borders : {e}.")
            return
        
        newVmax = max(vmax, vmin)
        vmin = min(vmin, vmax)
        vmax = newVmax

        vmin = max(self.global_min, vmin)
        vmax = min(self.global_max, vmax)

        if vmax == vmin:
            if vmin == self.global_min:
                vmax = vmin*(1+1e-6)
            else:
                vmin = vmax*(1-1e-6)

        self.line_edit_min.setText(f"{vmin}")
        self.line_edit_max.setText(f"{vmax}")

        self.update_plot(vmin, vmax)

    def reset_filter(self):
        self.line_edit_min.setText(f"{self.global_min:.3f}")
        self.line_edit_max.setText(f"{self.global_max:.3f}")
        self.update_plot(self.global_min, self.global_max)

    def export_plot(self):
        if not hasattr(self, "last_figure"):
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le graphique",
            "",
            "Fichier PNG (*.png);;Fichier HTML (*.html)"
        )

        if file_path:
            if file_path.endswith(".png"):
                self.last_figure.write_image(file_path)
            elif file_path.endswith(".html"):
                self.last_figure.write_html(file_path, include_plotlyjs='cdn', full_html=True)

