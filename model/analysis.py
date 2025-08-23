import numpy as np
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from SALib.sample import saltelli
from SALib.analyze import sobol
from sklearn.cluster import DBSCAN

from model.meshManager import MeshManager
from model.utils import addOneToAIndex, subtractOneToAIndex

import random
from itertools import product

from model.data import SingletonData

class SensitivityAnalyzer:
    def __init__(self,mesh, param_names) -> None:
        '''evaluate_model : fonction pour évaluer la fonction (nécessaire si high_precision_analysis=True)'''
        self.data = SingletonData()
        self.mesh:MeshManager = mesh
        self.param_names=param_names
        if self.data.dataFile.high_precision_analysis:
            self.evaluate_model = self.mesh.theFunction
        else:
            self.evaluate_model = None
        self.n_sample = self.data.dataFile.n_sample

        return None

    def run_analysis(self):
        """
        Analyse combinée PCA, Spearman, Sobol.
        """
        X_vals, y = self.mesh_to_array()

        try:
            self.pca = PCA(n_components=min(5, len(self.param_names)))
            self.pca.fit(X_vals)
        except Exception as e:
            self.pca = None
            print(f"Error while computing pca :\n{e}")

        try:
            self.corr_spearman = []
            for i in range(len(self.param_names)):
                corr, pval = spearmanr(X_vals[:, i], y)
                self.corr_spearman.append((self.param_names[i], corr, pval))
        except Exception as e:
            self.corr_spearman=None
            print(f"Error while computing spearman coefficients :\n{e}")

        problem = {
            'num_vars': len(self.param_names),
            'names': self.param_names,
            'bounds': [(self.mesh.axis[i][0], self.mesh.axis[i][-1]) for i in range(len(self.param_names))]
        }

        sobol_param_values = saltelli.sample(problem, self.n_sample, calc_second_order=False) # Échantillonnage Sobol
        try:
            if self.data.dataFile.high_precision_analysis:
                self.si = self.eval_sobol_with_recalc(problem, sobol_param_values)
            else:
                self.si = self.eval_sobol_with_interpolation(problem=problem,param_values=sobol_param_values)
        except Exception as e:
            self.si=None
            print(f"Error while computing Sobol first and total order coefficients :\n{e}")

        self._criticalAnalysis()

        self.cluster_summary = None
        self.pca_proj_clustering = None
        self.critical_labels = None
        try:
            self.cluster_critical_nodes()
            self.cluster_summary = self.summarize_clusters()
            self.pca_proj_clustering = self.compute_pca_projection()
        except Exception as e:
            print(f"Error while clustering critical nodes:\n{e}")
            self.cluster_summary = None
            self.pca_proj_clustering = None
            self.critical_labels = None

    def interpolated_model(self, coordinates: tuple[float]) -> float:
        """
        Interpolation linéaire N-D dans self.mesh.map pour des coordonnées quelconques.
        Le maillage est supposé uniforme.
        """
        n_dim = len(coordinates)
        root_idx = self.mesh.getIndexRootNode(coordinates)
        steps = self.data.dataFile.axis_step
        borders = self.data.dataFile.axis_borders

        # Normalisation des coordonnées entre 0 et 1 dans la cellule
        local_coords = []
        for i in range(n_dim):
            min_val = borders[i][0]
            max_val = borders[i][1]
            delta = (max_val - min_val) / steps[i]
            x0 = root_idx[i] * delta + min_val
            xi = (coordinates[i] - x0) / delta
            xi = np.clip(xi, 0, 1)  # pour éviter les dépassements
            local_coords.append(xi)

        # Interpolation linéaire : somme pondérée des 2^N coins
        result = 0.0
        for corner in product([0, 1], repeat=n_dim):
            weight = 1.0
            idx = list(root_idx)
            for d in range(n_dim):
                if corner[d] == 1:
                    weight *= local_coords[d]
                    idx[d] += 1
                else:
                    weight *= 1 - local_coords[d]

            try:
                value = self.mesh.map[tuple(idx)]
                result += weight * value
            except IndexError:
                # En cas de dépassement de bordure, on ignore ce coin (ou tu peux extrapoler si besoin)
                continue

        return result

    def eval_sobol_with_interpolation(self, problem, param_values):
        """
        Évalue les indices de Sobol via interpolation à partir d'un maillage existant.
        
        Parameters:
        - problem: dict SALib {'num_vars', 'names', 'bounds'}
        - calc_second_order: bool, True pour inclure les indices d'ordre 2
        """        
        # Évaluation du modèle par interpolation
        Y = np.array([self.interpolated_model(p) for p in param_values])

        # Vérification de la taille attendue
        D = len(problem["names"])
        expected_size = self.n_sample * (D + 2)
        if len(Y) != expected_size:
            raise ValueError(
                f"Longueur Y attendue: {expected_size}, obtenue: {len(Y)}. "
                "Vérifie que N est cohérent et que calc_second_order est utilisé de façon identique "
                "dans saltelli.sample et sobol.analyze."
            )

        # Analyse Sobol
        Si = sobol.analyze(problem, Y, calc_second_order=False, print_to_console=False)

        return Si

    def eval_sobol_with_recalc(self, problem, param_values):
        """
        Analyse de Sobol en recalculant la fonction pour chaque point.
        evaluate_model : fonction qui prend une liste de valeurs réelles (float) et retourne la sortie scalaire.
        """
        # Remise à l'échelle
        for i, ax in enumerate(self.mesh.axis):
            param_values[:, i] = param_values[:, i] * (ax[-1] - ax[0]) + ax[0]

        # Calcul des valeurs
        values = np.array([self.evaluate_model(val) for val in param_values])

        # Analyse Sobol
        Si = sobol.analyze(problem, values, calc_second_order=False, print_to_console=False)

        return Si

    def mesh_to_array(self):
        """
        Convertit le mesh.map en tableau (X: coordonnées physiques, y: sorties)
        """
        shape = self.mesh.map.shape
        axis = self.mesh.axis

        # 1. Coordonnées entières : (n_points, n_dims)
        all_indices = np.array(np.meshgrid(*[range(s) for s in shape], indexing='ij')).reshape(len(shape), -1).T

        # 2. Convertir indices -> valeurs physiques
        X_vals = np.zeros_like(all_indices, dtype=float)
        for i in range(len(axis)):
            X_vals[:, i] = axis[i][all_indices[:, i]]

        # 3. Valeurs de sortie (mesh.map est un ndarray)
        y = self.mesh.map.flatten()

        return X_vals, y
    
    def _criticalAnalysis(self) -> None:
        '''analyses the influence of each components on the number of critical nodes'''
        #number of critical nodes
        how_many_critical:list[np.ndarray[int]] = [np.zeros(shape=(self.data.dataFile.axis_step[axis_index])) for axis_index in range(self.mesh.n_axis)] #for each axis, number of critical mesh per step (all the steps of the other compoenents used)

        for critical_node in self.mesh.critical_domain:
            for axis_index, node_index in enumerate(critical_node):
                how_many_critical[axis_index][node_index] += 1

        #stats
        self.critical_stats:list[dict[str:float|int]] = []
        for axis_nb_critical in how_many_critical:
            stats = {"min":int(np.min(axis_nb_critical))}
            stats["max"] = int(np.max(axis_nb_critical))
            stats["median"] = int(np.median(axis_nb_critical))
            stats["mean"] = np.mean(axis_nb_critical)
            stats["var"] = np.var(axis_nb_critical)
            self.critical_stats.append(stats)
        
        return None
    
    def _errorHypothesisLittleVariationsOnCell(self) -> list[float] | None:
        '''return the error made while doing the little variations in one cell hypothesis
        used when high_precision_analysis is False so interpolation for Sobol
        returns a number between 0 and 1
        takes 1000 existing points per dimension/parameter and compare, for each point Xi, i representing the node index for a dimension, f(Xi) to (f(Xi+1)-f(Xi-1))/2 since the mesh is uniform'''
        if self.data.dataFile.high_precision_analysis:
            return None
        else:
            error_per_axis = []
            for axis_index in range(len(self.data.dataFile.axis_borders)):
                list_of_coords = self._generateRandomIndexCoordinates()

                error = 0
                for coords in list_of_coords:
                    exact_value = self.mesh.map[coords]
                    value_after = self.mesh.map[addOneToAIndex(coords, axis_index)]
                    value_before = self.mesh.map[subtractOneToAIndex(coords, axis_index)]

                    approx = (value_after+value_before)/2
                    if exact_value != 0:
                        error += abs((approx-exact_value)/exact_value)
                    else:
                        error += abs(approx)
                error_per_axis.append(error/self.data.random_points_test_hypothesis)
            
            return error_per_axis

    def _generateRandomIndexCoordinates(self) -> list[tuple[int]]:
        '''generates nb_coordinates random index coordinates'''
        #generating a liste of random indices per axis
        coord_per_axis = []
        for nb_step in self.data.dataFile.axis_step:
            coord_per_axis.append(random.choices(range(1, nb_step-1), k=self.data.random_points_test_hypothesis)) #repetitions authorized

        list_of_coords = list(zip(*coord_per_axis))

        return list_of_coords

    def cluster_critical_nodes(self, eps=0.1, min_samples=5):
        """
        Applique un clustering (DBSCAN) sur les nœuds critiques.
        - eps : rayon maximal pour regrouper deux points
        - min_samples : nombre min de points pour former un cluster
        """
        if not self.mesh.critical_domain:
            self.critical_clusters = []
            self.critical_coords = []
            self.critical_labels = []
            return

        # 1. Extraire les coordonnées physiques
        physical_coords = []
        index_coords = []
        for index in self.mesh.critical_domain:
            coord = [self.mesh.axis[dim][i] for dim, i in enumerate(index)]
            physical_coords.append(coord)
            index_coords.append(index)

        X = np.array(physical_coords)
        # plot_k_distances(X)
        maxi = np.max(self.mesh.map)
        mini = np.min(self.mesh.map)
        eps = (maxi-mini)*0.07 #0.07 empirique
        # print(eps)

        # 2. DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        labels = clustering.labels_

        # 3. Stocker tout proprement
        self.critical_coords = X
        self.critical_labels = labels
        self.critical_clusters = [
            {"index": index_coords[i], "coord": X[i], "label": labels[i]}
            for i in range(len(X))
        ]

    def summarize_clusters(self):
        summaries = []
        labels = set(self.critical_labels)

        # for label in sorted(labels):
        for label in labels:
            if label == -1:
                continue  # Ignorer les points de bruit (non clusterisés)

            # Points du cluster courant
            cluster_points = [c for c in self.critical_clusters if c["label"] == label]
            size = len(cluster_points)
            coords:np.ndarray = np.array([c["coord"] for c in cluster_points])  # shape: (n_points, n_params)

            # Moyenne et variance globale of coordinates
            mean_vals:np.ndarray = np.mean(coords, axis=0)
            var_vals:np.ndarray = np.var(coords, axis=0)

            # Paramètres dominants : ceux avec plus grande variance
            dominant_indices = np.argsort(var_vals)[-3:][::-1]  # top 3, triés par importance
            dominant_param_names = [self.param_names[i] for i in dominant_indices]
            dominant_means = mean_vals[dominant_indices]
            dominant_vars = var_vals[dominant_indices]

            # Pour le spider plot (profil moyen de tous les paramètres)
            mean_profile = mean_vals  # déjà de taille n_params

            # Pour la table : on peut utiliser la moyenne de sortie comme première composante
            mean_value = np.mean(mean_vals)  # ou autre heuristique

            summary = {
                "label": label,
                "size": size,
                "mean": mean_vals,
                "variance": var_vals,
                "mean_value": mean_value,
                "dominant_params": dominant_param_names,
                "dominant_means": dominant_means,
                "dominant_vars": dominant_vars,
                "mean_profile": mean_profile,
            }

            summaries.append(summary)

        sorted_summary = sorted(summaries,
                                key=lambda dominant_vars_cluster:
                                (np.prod(dominant_vars_cluster["dominant_vars"]), #sorting through cluster size
                                 dominant_vars_cluster["size"]), #in case of equality when sorting
                                reverse=True)

        return sorted_summary
    
    def compute_pca_projection(self, n_components=3):
        """
        Calcule la projection PCA des coordonnées critiques (pour visualisation).
        Résultat stocké dans self.pca_3d.
        """
        n_components=min(n_components,len(self.mesh.axis)) #max 3
        if not hasattr(self, 'critical_coords') or len(self.critical_coords) == 0:
            self.pca_3d = None
            return None

        pca = PCA(n_components=n_components)
        self.pca_3d = pca.fit_transform(self.critical_coords)
        return self.pca_3d
    
#détectoin visuelle du cooude : le faire en algo (exemple d'utilisation au dessus de dbscan, le coude est le spilon du dbscan mais faire la moyenne avec le mien de eps)
def plot_k_distances(X, k=5):
    from sklearn.neighbors import NearestNeighbors
    import matplotlib.pyplot as plt
    nbrs = NearestNeighbors(n_neighbors=k).fit(X)
    distances, _ = nbrs.kneighbors(X)
    k_distances = np.sort(distances[:, -1])  # distance au k-ième plus proche voisin
    plt.figure()
    plt.plot(k_distances)
    plt.ylabel(f"{k}-ème plus proche voisin")
    plt.xlabel("Points triés")
    plt.title("Méthode du coude pour choisir eps")
    plt.grid(True)
    plt.show()
