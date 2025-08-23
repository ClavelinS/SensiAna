from matplotlib.patches import FancyBboxPatch
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np


def rounded_bar_plot(ax, x, heights, width=0.5, colors=None, edgecolor=None, radius=0.1):
    """
    Trace des barres arrondies sur un axe matplotlib.
    
    - ax : axe matplotlib
    - x : liste/array des positions x
    - heights : hauteurs des barres
    - width : largeur des barres
    - colors : liste de couleurs ou une couleur unique
    - edgecolor : couleur des bords
    - radius : rayon d'arrondi
    """
    if colors is None:
        colors = ['#4C72B0'] * len(x)
    elif isinstance(colors, str):
        colors = [colors] * len(x)

    for i, (xi, hi) in enumerate(zip(x, heights)):
        color = colors[i % len(colors)]
        patch = FancyBboxPatch(
            (xi - width/2, 0), width, hi,
            boxstyle=f"round,pad=0,rounding_size={radius}",
            linewidth=0.8 if edgecolor else 0,
            facecolor=color,
            edgecolor=edgecolor or 'none'
        )
        ax.add_patch(patch)

    # Ajustement automatique de l’axe
    ax.set_xlim(min(x) - width, max(x) + width)
    ax.set_ylim(0, max(heights) * 1.1)

# def plot_sobol_indices_with_total(param_names, val1, val2, val1_conf=None, val2_conf=None, title="", label1="", label2="", y_label=""):
#     """plots double bar graph with val1 and val 2 and respectively label1 and label2 and val1_conf and val2_conf for the confidence rate"""
#     x = np.arange(len(param_names))

#     fig, ax = plt.subplots(figsize=(5, 2.5))

#     # Couleurs
#     cmap_val1 = cm.get_cmap('viridis')
#     cmap_val2 = cm.get_cmap('plasma')
#     colors_val1 = cmap_val1(np.linspace(0.3, 0.9, len(val1)))
#     colors_val2 = cmap_val2(np.linspace(0.3, 0.9, len(val2)))

#     # Tracer val2 (en fond, plus grand)
#     ax.bar(
#         x, val2, width=0.4,
#         color=colors_val2,
#         edgecolor='black',
#         alpha=0.5,
#         label=label2,
#         yerr=val2_conf if val2_conf is not None else None,
#         capsize=3,
#         zorder=1
#     )

#     # Tracer val1 (par dessus, plus petit)
#     ax.bar(
#         x, val1, width=0.25,
#         color=colors_val1,
#         edgecolor='black',
#         label=label1,
#         yerr=val1_conf if val1_conf is not None else None,
#         capsize=3,
#         zorder=2
#     )

#     # Ticks et labels
#     ax.set_xticks(x)
#     ax.set_xticklabels(param_names, rotation=45, ha='right')
#     ax.set_ylabel(y_label)
#     ax.set_title(title)
#     ax.yaxis.grid(True, linestyle='--', alpha=0.7)
#     ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

#     # Légende
#     ax.legend(loc='upper right', fontsize=8)

#     fig.tight_layout()
#     return fig

from matplotlib.patches import FancyBboxPatch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

def plot_sobol_indices_with_total(param_names, val1, val2, val1_conf=None, val2_conf=None,
                                   title="", label1="", label2="", y_label=""):
    """Plots two sets of rounded bars (val1 and val2), with separate labels and confidence intervals. val2 is behind val1 so it needs to be bigger than val1. They need to be the same size too."""
    x = np.arange(len(param_names))
    fig, ax = plt.subplots(figsize=(6, 3))

    # Couleurs
    cmap_val1 = cm.get_cmap('viridis')
    cmap_val2 = cm.get_cmap('plasma')
    colors_val1 = cmap_val1(np.linspace(0.3, 0.9, len(val1)))
    colors_val2 = cmap_val2(np.linspace(0.3, 0.9, len(val2)))

    # Tracer les barres de val2 (ST - en fond)
    rounded_bar_plot(
        ax=ax,
        x=x,
        heights=val2,
        width=0.4,
        colors=colors_val2,
        edgecolor='black',
        radius=0.07
    )

    # Tracer les barres de val1 (S1 - au-dessus)
    rounded_bar_plot(
        ax=ax,
        x=x,
        heights=val1,
        width=0.25,
        colors=colors_val1,
        edgecolor='black',
        radius=0.07
    )

    # Ajouter les barres d'erreur (en haut des barres)
    if val1_conf is not None:
        ax.errorbar(x, val1, yerr=val1_conf, fmt='none', ecolor='black', capsize=3, zorder=3)
    if val2_conf is not None:
        ax.errorbar(x, val2, yerr=val2_conf, fmt='none', ecolor='black', capsize=3, zorder=1)

    # Étiquettes attachées à chaque groupe de barres
    for xi, y1, y2 in zip(x, val1, val2):
        ax.text(xi + 0.08, y1 + 0.02, label1, ha='center', va='bottom', fontsize=6, color='black', zorder=4)
        ax.text(xi + 0.08, y2 + 0.02, label2, ha='center', va='bottom', fontsize=6, color='black', alpha=0.6, zorder=2)

    # Axes et style
    ax.set_xticks(x)
    ax.set_xticklabels(param_names, rotation=45, ha='right')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    # ax.spines[['top', 'right', 'left', 'bottom']] = [False]*4
    for side in ['top', 'right', 'left', 'bottom']:
        ax.spines[side].set_visible(False)

    ax.set_ylim(0, max(max(val1), max(val2)) * 1.2)

    # # Légende facultative
    # ax.legend([label1, label2], loc='upper right', fontsize=8)

    fig.tight_layout()
    return fig
