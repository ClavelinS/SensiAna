import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer

from model.meshManager import MeshManager
from model.analysis import SensitivityAnalyzer
from model.data import SingletonData
from view.view import MainView  # votre nouvelle vue PySide6

class MainPresenter:
    def __init__(self, root: QWidget, mesh_manager=None, sensitivity_analizer=None):
        self.data = SingletonData()

        if mesh_manager==None:
            self.mesh = MeshManager()
        else:
            self.mesh=mesh_manager
        
        if sensitivity_analizer==None:
            self.sensitivity_analizer = SensitivityAnalyzer(self.mesh, self.data.dataFile.axis_name[:-1])
            self.sensitivity_analizer.run_analysis()
        else:
            self.sensitivity_analizer=sensitivity_analizer

        self.slider_update_timer = QTimer()
        self.slider_update_timer.setSingleShot(True)
        # self.slider_update_timer.timeout.connect(self.view.visu_tab.plot_surface)
        
        self.param_names = self.data.dataFile.axis_name[:-1]  # dernier = Z axis
        self._createAxisNamesToAxisIndex()
        
        # Valeurs initiales fixes pour les paramètres hors axes affichés
        self.fixed_params = {
            p: self.mesh.axis[p_index][int(self.data.dataFile.axis_step[p_index] / 2)]
            for p_index, p in enumerate(self.param_names)
        }
        
        self.axis_i = self.param_names[0]
        self.axis_j = self.param_names[1]

        self.root = root
        # Instanciation de la vue PySide6, avec self comme presenter
        self.view = MainView(self)
        self.root.setCentralWidget(self.view)  # mettre ta vue comme widget central de la fenêtre
        
        self.view.visu_tab.set_param_options(self.param_names)
        self.build_sliders()
        self.update_plot()

    def _createAxisNamesToAxisIndex(self):
        self.axisNameToIndex = {name: idx for idx, name in enumerate(self.param_names)}

    def build_sliders(self):
        self.view.visu_tab.clear_sliders()
        for p_index, p in enumerate(self.param_names):
            if p not in (self.axis_i, self.axis_j):
                self.view.visu_tab.add_slider(
                    param_name=p,
                    min_val=self.data.dataFile.axis_borders[p_index][0],
                    max_val=self.data.dataFile.axis_borders[p_index][1],
                    initial_val=self.fixed_params[p],
                    resolution=1 / (self.data.dataFile.axis_step[p_index] - 1),
                    callback=self.on_slider_change
                )

    def on_slider_change(self, param_name, value):
        self.fixed_params[param_name] = value
        self.update_plot()

    def update_axes(self, axis_i, axis_j):
        if axis_i == axis_j:
            return
        self.axis_i = axis_i
        self.axis_j = axis_j
        self.build_sliders()
        self.update_plot()

    def update_plot(self):
        x = self.mesh.axis[self.axisNameToIndex[self.axis_i]]
        y = self.mesh.axis[self.axisNameToIndex[self.axis_j]]
        Xj, Xi = np.meshgrid(y, x)
        Z = np.zeros((len(x), len(y)))

        critical_ij = []
        for i in range(len(x)):
            for j in range(len(y)):
                coord = ()
                for name in self.param_names:
                    if name == self.axis_i:
                        coord += (i,)
                    elif name == self.axis_j:
                        coord += (j,)
                    else:
                        idx, _ = self.mesh.getClosestIndexFromValue(
                            self.mesh.axis[self.axisNameToIndex[name]],
                            self.fixed_params[name]
                        )
                        coord += (idx,)
                value = self.mesh.map[coord]
                Z[i, j] = value
                if self.mesh.theCriticalFunc(value):
                    critical_ij.append((i, j))

        self.view.visu_tab.plot_surface(Xi, Xj, Z, threshold=self.data.dataFile.critical_value, critical=critical_ij)

    def query_model(self, coord):
        return self.mesh.map[coord]

    def open_new_window(self):
        from PySide6.QtWidgets import QMainWindow
        new_window = QMainWindow()
        presenter = MainPresenter(new_window, self.mesh, self.sensitivity_analizer)
        new_window.show()
