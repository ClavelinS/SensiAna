from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from view.visuTab import VisuTab
from view.anaTab import AnaTab
from view.utils.style_sheet import StyleSheets
from view.parTab import ParallelTab

class MainView(QWidget):
    def __init__(self, presenter):
        super().__init__()
        self.setWindowTitle("Analyse multi-paramètres")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        layout.addWidget(self.tabs)

        self.tabs.setStyleSheet(StyleSheets().tab)


        self.visu_tab = VisuTab(presenter)
        self.par_tab = ParallelTab(presenter)
        self.ana_tab = AnaTab(presenter.sensitivity_analizer)

        self.tabs.addTab(self.visu_tab, "3D Visualisation")
        self.tabs.addTab(self.par_tab, "Parallel Coordinates")
        self.tabs.addTab(self.ana_tab, "Analysis")
