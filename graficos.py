#!/usr/bin/env python3
"""Figuras del informe, en PDF vectorial: rasterizadas se ven sucias impresas."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import analisis as A

IMG = Path(__file__).parent / "img"
IMG.mkdir(exist_ok=True)
ROJO, TINTA = "#B50D30", "#1F1B1C"


def histograma(censo, pob):
    """El sesgo de la poblacion: es lo que justifica invocar el TLC."""
    h = [A.horas_resolucion(i) for i in censo]
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ax.hist([x for x in h if x <= 2000], bins=50, color=TINTA, alpha=0.85)
    ax.axvline(pob["mediana"], color=ROJO, lw=1.6, ls="--",
               label=f'Mediana = {pob["mediana"]:.0f} h')
    ax.axvline(pob["mu"], color=ROJO, lw=1.6,
               label=f'Media = {pob["mu"]:.0f} h')
    ax.set_xlabel("Tiempo de resolución (horas)")
    ax.set_ylabel("Frecuencia")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "histograma-poblacion.pdf")
    plt.close(fig)


def caja(muestra):
    fig, ax = plt.subplots(figsize=(6.2, 2.2))
    ax.boxplot([A.horas_resolucion(i) for i in muestra], vert=False, widths=0.5)
    ax.set_xlabel("Tiempo de resolución (horas)")
    ax.set_yticks([])
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "caja-muestra.pdf")
    plt.close(fig)


if __name__ == "__main__":
    censo = A.cargar_censo()
    histograma(censo, A.parametros_poblacionales(censo))
    caja(A.extraer_muestra(censo))
    print("figuras escritas en", IMG)
