from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QScrollArea, QFrame, QSizePolicy, QToolButton
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import numpy as np

from view.utils.style_sheet import StyleSheets
from view.utils.collapsableBox import CollapsableBox
from view.utils.plot import rounded_bar_plot, plot_sobol_indices_with_total

class AnaTab(QWidget):
    # def __init__(self, pca=None, corr_spearman=None, sobol_indices=None, error_interpolation = None, critical_stats = None, clustering = None, pca_proj_clustering=None, param_names=None):
    def __init__(self, sensitivity_analizer):
        super().__init__()
        self.sensitivity_analizer = sensitivity_analizer
        self.pca = sensitivity_analizer.pca
        self.corr_spearman = sensitivity_analizer.corr_spearman
        self.sobol_indices = sensitivity_analizer.si
        self.critical_stats = sensitivity_analizer.critical_stats
        self.clustering = sensitivity_analizer.cluster_summary
        self.pca_proj_clustering = sensitivity_analizer.pca_proj_clustering
        self.cluster_labels = sensitivity_analizer.critical_labels
        self.param_names = sensitivity_analizer.param_names
        self.error_interpolation = sensitivity_analizer._errorHypothesisLittleVariationsOnCell()

        self.style_sheets = StyleSheets()

        # Scroll Area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Layout principal du AnaTab
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # ========== PCA ==========
        if self.pca:
            pca_group = self._create_pca_group()
            main_layout.addWidget(pca_group)

        # ========== Spearman ==========
        if self.corr_spearman:
            spearman_group = self._create_spearman_group()
            main_layout.addWidget(spearman_group)

        # ========== Sobol ==========
        if self.sobol_indices and 'S1' in self.sobol_indices and 'ST' in self.sobol_indices:
            sobol_group = self._create_sobol_group()
            main_layout.addWidget(sobol_group)

        # ========== Analyse complémentaire sur les éléments critiques ==========
        stat_group = self._create_stat_group()
        main_layout.addWidget(stat_group)

        # ========== Clustering ==========
        if self.clustering is not None and self.pca_proj_clustering is not None:
            cluster_group = self._create_cluster_group()
            main_layout.addWidget(cluster_group)

        if not any([self.pca, self.corr_spearman, self.sobol_indices]):
            main_layout.addWidget(QLabel("Aucune autre analyse disponible."))

    def _create_stat_group(self):
        try:
            stat_group = CollapsableBox("Répartition des noeuds critiques par paramètre")
            stat_group.setToolTip(
                    "Ce tableau montre, pour chaque paramètre de l'analyse de sensibilité"
                    "des statistiques sur le nombre d'éléments considérés comme critiques.\n"
                )

            stat_layout = stat_group.content_layout

                # Données fictives pour l'exemple
            categories = list(self.critical_stats[0].keys())
            n_components = len(self.critical_stats)

            stat_table = QTableWidget()
            stat_table.setRowCount(n_components)
            stat_table.setColumnCount(len(categories))
            stat_table.setHorizontalHeaderLabels(categories)
            stat_table.setVerticalHeaderLabels([f"{self.param_names[i]}" for i in range(n_components)])

            for j, cat in enumerate(categories):
                # Récupération des valeurs numériques pour la colonne
                col_values = []
                for i in range(n_components):
                    val = self.critical_stats[i][cat]
                    if isinstance(val, (int, float)):
                        col_values.append((i, float(val)))

                if not col_values:
                    continue  # colonne non numérique

                values_only = [val for _, val in col_values]
                min_val = min(values_only)
                max_val = max(values_only)

                for i in range(n_components):
                    val = self.critical_stats[i][cat]

                    if cat in ["mean", "var"]:
                        item = QTableWidgetItem(f"{val:.2e}")
                    else:
                        list_str_value = [char for char in f"{val}"]
                        list_str_value.reverse()
                        readable_str_value = ""
                        for index_digit, char in enumerate(list_str_value, 1):
                            readable_str_value = char + readable_str_value
                            if index_digit % 3 == 0 and index_digit != len(list_str_value):
                                readable_str_value = " " + readable_str_value
                        item = QTableWidgetItem(readable_str_value)

                    item.setToolTip(f"{cat} des éléments critiques pour le paramètre {self.param_names[i]}")

                    # Appliquer la couleur
                    if isinstance(val, (int, float)):
                        if min_val == max_val:
                            item.setBackground(QColor("#ffffff"))  # Vert clair unique
                        elif val == min_val:
                            item.setBackground(QColor("#d1f7d1"))  # Vert clair
                        elif val == max_val:
                            item.setBackground(QColor("#f7d1d1"))  # Rouge clair

                    stat_table.setItem(i, j, item)

            stat_table.setStyleSheet(self.style_sheets.table_style_sheet)
            stat_table.resizeColumnsToContents()
            stat_table.resizeRowsToContents()
            stat_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._getTableNonEditable(stat_table)

            stat_layout.addWidget(stat_table)
        except Exception as e:
            stat_layout.addWidget(QLabel(f"Erreur dans les statistiques d'éléments critiques : {e}"))

        return stat_group

    def _create_sobol_group(self):
        sobol_group = CollapsableBox("Indices de Sobol (1er ordre et contribution totale)")
        sobol_group.setToolTip(
                "Indices de Sobol (sensibilité globale) :\n"
                "     - S1 estime combien chaque paramètre contribue à la variance de la sortie, sans interaction avec les autres, c'est son importance seul.\n"
                "     - ST estime combien chaque paramètre contribue à la variance de la sortie, avec interactions avec les autres, c'est sa contribution totale.\n"
                "     - Plus S1 est élevé, plus le paramètre est important SEUL.\n"
                "     - Entre parenthèses les indices de confiance des indices de Sobol.\n"
                "     - En rouge les moins influents, en vert les plus influents.\n"
                "     - L'erreur moyenne est l'erreur faite en faisant l'hypothèse des petites variations linéaires sur une maille."
            )
        sobol_layout = sobol_group.content_layout

        try:
            n_columns = 4 if self.error_interpolation else 3
            sobol_table = QTableWidget(len(self.param_names), n_columns)
            sobol_table.setHorizontalHeaderLabels(["Parameter", "Sobol Ordre 1", "Sobol Total", "Error (%)"])

            min_S1_val = min(self.sobol_indices['S1'])
            max_S1_val = max(self.sobol_indices['S1'])

            min_ST_val = min(self.sobol_indices['ST'])
            max_ST_val = max(self.sobol_indices['ST'])

            for i, name in enumerate(self.param_names):
                s1 = self.sobol_indices["S1"][i]
                st = self.sobol_indices["ST"][i]
                s1_conf = self.sobol_indices["S1_conf"][i]
                st_conf = self.sobol_indices["ST_conf"][i]

                sobol_table.setItem(i, 0, QTableWidgetItem(name))

                item_s1 = QTableWidgetItem(f"{s1:.4f} ({s1_conf:.4f})")
                item_st = QTableWidgetItem(f"{st:.4f} ({st_conf:.4f})")

                # Coloration S1
                if isinstance(s1, (int, float)):
                    if min_S1_val == max_S1_val:
                        item_s1.setBackground(QColor("#ffffff"))
                    elif s1 == max_S1_val:
                        item_s1.setBackground(QColor("#d1f7d1"))
                    elif s1 == min_S1_val:
                        item_s1.setBackground(QColor("#f7d1d1"))

                # Coloration ST
                if isinstance(st, (int, float)):
                    if min_ST_val == max_ST_val:
                        item_st.setBackground(QColor("#ffffff"))
                    elif st == max_ST_val:
                        item_st.setBackground(QColor("#d1f7d1"))
                    elif st == min_ST_val:
                        item_st.setBackground(QColor("#f7d1d1"))

                sobol_table.setItem(i, 1, item_s1)
                sobol_table.setItem(i, 2, item_st)

                if n_columns == 4:
                    sobol_table.setItem(i, 3, QTableWidgetItem(f"{100*self.error_interpolation[i]:.4f}"))

            sobol_table.setStyleSheet("font-family: monospace;")
            sobol_table.setStyleSheet(self.style_sheets.table_style_sheet)
            sobol_table.resizeColumnsToContents()
            sobol_table.resizeRowsToContents()
            sobol_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._getTableNonEditable(sobol_table)
            sobol_layout.addWidget(sobol_table)


            if self.error_interpolation:
                mean_error = f"Total mean interpolation error : {100*np.array(self.error_interpolation).mean():.2f}%"

                mean_error_label = QLabel(mean_error)
                mean_error_label.setStyleSheet("font-family: monospace")
                sobol_layout.addWidget(mean_error_label)

            fig = plot_sobol_indices_with_total(
                param_names=self.param_names,
                val1=self.sobol_indices["S1"],
                val2=self.sobol_indices["ST"],
                val1_conf=self.sobol_indices.get("S1_conf"),
                val2_conf=self.sobol_indices.get("ST_conf"),label1="S1",label2="ST",title="Indices de Sobol : S1 & ST",y_label="Indice"
            )
            canvas_sobol = FigureCanvasQTAgg(fig)
            canvas_sobol.setMinimumHeight(250)  # ou 300 ou + selon tes besoins
            canvas_sobol.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sobol_layout.addWidget(canvas_sobol)
            sobol_layout.addWidget(canvas_sobol)

        except Exception as e:
            sobol_layout.addWidget(QLabel(f"Erreur Sobol : {e}"))

        return sobol_group

    def _create_spearman_group(self):
        spearman_group = CollapsableBox("Corrélation de Spearman")
        spearman_group.setToolTip(
                "Corrélation de Spearman :\n"
                "     - Mesure non-linéaire de l'influence d'un paramètre sur la sortie.\n"
                "     - ρ = +1 : forte relation croissante, ρ = -1 : forte relation décroissante.\n"
                "     - Plus |ρ| est grand, plus le paramètre influence la sortie.\n"
                "     - p-valeur : probabilité que la corrélation soit due au hasard."
            )

        spearman_layout = spearman_group.content_layout

        try:
            spearman_table = QTableWidget(len(self.corr_spearman), 3)
            spearman_table.setHorizontalHeaderLabels(["Paramètre", "ρ", "p"])

            for i, (name, corr, pval) in enumerate(self.corr_spearman):
                spearman_table.setItem(i, 0, QTableWidgetItem(name))
                spearman_table.setItem(i, 1, QTableWidgetItem(f"{corr:+.3f}"))
                spearman_table.setItem(i, 2, QTableWidgetItem(f"{pval:.1e}"))

            spearman_table.setStyleSheet("font-family: monospace;")
            spearman_table.setStyleSheet(self.style_sheets.table_style_sheet)
            spearman_table.resizeColumnsToContents()
            spearman_table.resizeRowsToContents()
            spearman_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._getTableNonEditable(spearman_table)

            spearman_layout.addWidget(spearman_table)
        except Exception as e:
            spearman_layout.addWidget(QLabel(f"Erreur Spearman : {e}"))

        return spearman_group

    def _create_pca_group(self):
        pca_group = CollapsableBox("Analyse en Composantes Principales (PCA)")
        pca_group.setToolTip(
                "Analyse en Composantes Principales (PCA) :\n"
                "     - Réduction de dimension : identifie les directions dans l'espace des paramètres qui expliquent le plus de variation dans la sortie.\n"
                "     - Explique la variance du nuage de points des paramètres en entrée.\n"
                "     - Si les premières composantes expliquent la majorité de la variance,\n"
                "     - cela signifie que la sortie dépend principalement de quelques combinaisons de paramètres.\n"
                "     - En vert les plus grosses contributions, en rouge les plus faible.\n"
                "     - En grisé les paramètres qui ne contribuent pas pour la PCA de la ligne en question.\n"
            )

        pca_layout = pca_group.content_layout

        try:
            # Table PCA
            pca_table = QTableWidget()
            n_components = len(self.pca.explained_variance_ratio_)
            n_features = len(self.param_names)
            pca_table.setRowCount(n_components)
            pca_table.setColumnCount(n_features + 1)

            headers = ["% Variance"] + self.param_names
            pca_table.setHorizontalHeaderLabels(headers)
            max_val = max(self.pca.components_[:, 0])
            min_val = min(self.pca.components_[:, 0])

            for i in range(n_components):
                var_pct = self.pca.explained_variance_ratio_[i] * 100
                item = QTableWidgetItem(f"{var_pct:.2f}%")
                item.setToolTip("Pourcentage de variance expliquée par cette composante")
                # Appliquer la couleur
                if isinstance(var_pct, (int, float)):
                    if min_val == max_val:
                        item.setBackground(QColor("#ffffff"))  # Vert clair unique
                    elif var_pct == min_val:
                        item.setBackground(QColor("#d1f7d1"))  # Vert clair
                    elif var_pct == max_val:
                        item.setBackground(QColor("#f7d1d1"))  # Rouge clair
                pca_table.setItem(i, 0, item)

                for j in range(n_features):
                    loading = self.pca.components_[i, j]
                    item = QTableWidgetItem(f"{loading:+.2f}")
                    item.setToolTip(
                            f"Contribution de la variable '{self.param_names[j]}' à la PC{i+1}.\n"
                            f"Les signes indiquent la direction, la valeur absolue indique l'importance."
                        )
                    if abs(loading) < 0.01: #because .2f
                        item.setForeground(QBrush(QColor("#999999")))  # gris clair
                    pca_table.setItem(i, j + 1, item)
                    pca_table.setVerticalHeaderLabels([f"PC{i+1}" for i in range(n_components)])

            pca_table.setStyleSheet(self.style_sheets.table_style_sheet)
            pca_table.resizeColumnsToContents()# pour ne pas compresser tableau
            pca_table.resizeRowsToContents()# pour ne pas compresser tableau
            pca_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)# pour ne pas compresser tableau

            self._getTableNonEditable(pca_table)
            pca_layout.addWidget(pca_table)

                # Graphique
            fig_pca, ax_pca = plt.subplots(figsize=(4, 2))
            x = list(range(1, len(self.pca.explained_variance_ratio_) + 1))
            cmap = cm.get_cmap('plasma')  # ou 'coolwarm', 'viridis', etc.
            colors = cmap(np.linspace(0, 1, len(self.pca.explained_variance_ratio_)))
            rounded_bar_plot(
                    ax_pca,
                    x,
                    self.pca.explained_variance_ratio_,
                    width=0.1,
                    colors=colors,
                    edgecolor='black',
                    radius=0.05
                )
            ax_pca.set_xticks(x)
            ax_pca.set_xticklabels([f"PC{i}" for i in x])

            ax_pca.set_title("Variance expliquée (PCA)")
            ax_pca.set_xlabel("Composante principale")
            ax_pca.set_ylabel("Variance")
            ax_pca.spines['top'].set_visible(False)
            ax_pca.spines['right'].set_visible(False)
            ax_pca.spines['left'].set_visible(False)
            ax_pca.spines['bottom'].set_visible(False)
            ax_pca.tick_params(left=True, bottom=False)
            ax_pca.yaxis.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
            ax_pca.set_xticks(x)
            ax_pca.set_xticklabels([f"PC{i}" for i in x], rotation=45, ha='right')

            fig_pca.tight_layout()
            canvas_pca = FigureCanvasQTAgg(fig_pca)
            canvas_pca.setMinimumHeight(250)  # pour ne pas compresser figure
            canvas_pca.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)# pour ne pas compresser figure

            pca_layout.addWidget(canvas_pca)
        except Exception as e:
            pca_layout.addWidget(QLabel(f"Erreur PCA : {e}"))

        return pca_group

    def _create_cluster_group(self):
        cluster_group = CollapsableBox("Analyse par Clusters")
        cluster_group.setToolTip(
            "Analyse par Clusters :\n"
            "     - Regroupe les configurations critiques similaires en fonction de leurs paramètres.\n"
            "     - Le tableau résume les propriétés moyennes de chaque cluster :\n"
            "         • Nombre d'éléments\n"
            "         • Valeur moyenne de sortie\n"
            "         • Paramètres dominants (plus grande variance)\n"
            "         • Moyennes et variances associées\n"
            "     - Le graphique 3D projette les clusters dans l’espace réduit (PCA).\n"
            "     - Le diagramme radar compare les profils moyens des 3 premiers clusters (taille)."
        )

        layout = cluster_group.content_layout

        try:
            # Tableau récapitulatif
            cluster_table = QTableWidget()
            n_clusters = len(self.clustering)
            cluster_table.setRowCount(n_clusters)
            cluster_table.setColumnCount(5)
            headers = ["Taille", "Valeur moyenne", "Paramètres dominants", "Moyenne dom.", "Variance dom."]
            cluster_table.setHorizontalHeaderLabels(headers)

            for i, summary in enumerate(self.clustering):
                cluster_table.setVerticalHeaderItem(i, QTableWidgetItem(f"#{summary['label']}"))

                row_items = [
                    QTableWidgetItem(str(summary['size'])),
                    QTableWidgetItem(f"{summary['mean_value']:.3f}"),
                    QTableWidgetItem(", ".join(summary['dominant_params'])),
                    QTableWidgetItem(", ".join(f"{v:.2f}" for v in summary['dominant_means'])),
                    QTableWidgetItem(", ".join(f"{v:.2f}" for v in summary['dominant_vars'])),
                ]

                for j, item in enumerate(row_items):
                    cluster_table.setItem(i, j, item)

            cluster_table.setStyleSheet(self.style_sheets.table_style_sheet)
            cluster_table.resizeColumnsToContents()
            cluster_table.resizeRowsToContents()
            cluster_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._getTableNonEditable(cluster_table)
            layout.addWidget(cluster_table)

            # # Plot 3D
            # fig_3d = plt.figure(figsize=(4, 3))
            # ax_3d = fig_3d.add_subplot(111, projection='3d')
            # colors = cm.get_cmap('tab10')(self.cluster_labels / (max(self.cluster_labels) + 1))
            # scatter = ax_3d.scatter(
            #     self.pca_proj_clustering[:, 0], self.pca_proj_clustering[:, 1], self.pca_proj_clustering[:, 2],
            #     c=colors, s=20, alpha=0.8
            # )
            # ax_3d.set_xlabel("PC1")
            # ax_3d.set_ylabel("PC2")
            # ax_3d.set_zlabel("PC3")
            # ax_3d.set_title("Clusters dans l'espace PCA")
            # fig_3d.tight_layout()
            # canvas_3d = FigureCanvasQTAgg(fig_3d)
            # canvas_3d.setMinimumHeight(300)
            # canvas_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # layout.addWidget(canvas_3d)

            # Obtenir les labels des 5 premiers clusters triés
            top_clusters = self.clustering[:5]
            top_labels = {c['label'] for c in top_clusters}

            # Filtrer les points à afficher
            mask = np.array([label in top_labels for label in self.cluster_labels])
            filtered_coords = self.pca_proj_clustering[mask]
            filtered_labels = np.array(self.cluster_labels)[mask]

            # Re-mapper les labels pour les indexer de 0 à 4 (facilite les couleurs)
            label_to_index = {label: i for i, label in enumerate(sorted(top_labels))}
            mapped_labels = np.array([label_to_index[l] for l in filtered_labels])

            # Couleurs
            cmap = cm.get_cmap('tab10')
            colors = cmap(mapped_labels / max(1, len(top_labels) - 1))  # évite division par zéro

            # Affichage 3D
            fig_3d = plt.figure(figsize=(4, 3))
            ax_3d = fig_3d.add_subplot(111, projection='3d')
            ax_3d.scatter(
                filtered_coords[:, 0], filtered_coords[:, 1], filtered_coords[:, 2],
                c=colors, s=20, alpha=0.8
            )
            ax_3d.set_xlabel("PC1")
            ax_3d.set_ylabel("PC2")
            ax_3d.set_zlabel("PC3")
            ax_3d.set_title("Top 5 clusters dans l'espace PCA")
            fig_3d.tight_layout()
            canvas_3d = FigureCanvasQTAgg(fig_3d)
            canvas_3d.setMinimumHeight(300)
            canvas_3d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(canvas_3d)


            # # Spider plot (max 3 clusters)
            # fig_radar, ax_radar = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
            # theta = np.linspace(0, 2 * np.pi, len(self.param_names), endpoint=False)
            # theta = np.concatenate((theta, [theta[0]]))  # fermeture

            # for i in range(min(3, len(self.clustering))):
            #     profile = self.clustering[i]['mean_profile']
            #     r = np.concatenate((profile, [profile[0]]))
            #     ax_radar.plot(theta, r, label=f"Cluster {i}")
            #     ax_radar.fill(theta, r, alpha=0.1)

            # ax_radar.set_xticks(theta[:-1])
            # ax_radar.set_xticklabels(self.param_names, fontsize=8)
            # ax_radar.set_title("Profils moyens des clusters")
            # ax_radar.legend(loc='upper right', fontsize=8)
            # fig_radar.tight_layout()

            # Spider plot (max 3 clusters), avec normalisation
            fig_radar, ax_radar = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
            theta = np.linspace(0, 2 * np.pi, len(self.param_names), endpoint=False)
            theta = np.concatenate((theta, [theta[0]]))  # fermeture

            # Récupérer tous les profils
            profiles = np.array([c['mean_profile'] for c in self.clustering[:3]])
            # Normalisation : paramètre par paramètre
            min_vals = profiles.min(axis=0)
            ptp_vals = np.ptp(profiles, axis=0) + 1e-8  # éviter division par 0
            norm_profiles = (profiles - min_vals) / ptp_vals

            for i, cluster in enumerate(self.clustering[:3]):
                r = np.concatenate((norm_profiles[i], [norm_profiles[i][0]]))
                ax_radar.plot(theta, r, label=f"Cluster #{cluster['label']} ({cluster['size']} pts)")
                ax_radar.fill(theta, r, alpha=0.1)

            ax_radar.set_xticks(theta[:-1])
            ax_radar.set_xticklabels(self.param_names, fontsize=8)
            ax_radar.set_title("Profils moyens normalisés des clusters")
            ax_radar.legend(loc='upper right', fontsize=8)
            fig_radar.tight_layout()

            canvas_radar = FigureCanvasQTAgg(fig_radar)
            canvas_radar.setMinimumHeight(300)
            canvas_radar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(canvas_radar)

        except Exception as e:
            layout.addWidget(QLabel(f"Erreur dans l'analyse des clusters : {e}"))

        return cluster_group

    def _getTableNonEditable(self, table:QTableWidget) -> None:
        '''avoid modifying the table and align the values'''
        rows = table.rowCount()
        cols = table.columnCount()

        for i in range(rows):
            for j in range(cols):
                item = table.item(i, j)
                if item is None:
                    item = QTableWidgetItem("")
                    table.setItem(i, j, item)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
            
        return None
