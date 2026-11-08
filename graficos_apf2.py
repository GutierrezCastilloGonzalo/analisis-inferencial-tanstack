#!/usr/bin/env python3
"""Figuras del APF2, en PDF vectorial."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

import analisis as A
import analisis_apf2 as B

IMG = Path(__file__).parent / "img"
IMG.mkdir(exist_ok=True)
ROJO, TINTA, GRIS = "#B50D30", "#1F1B1C", "#8C8C8C"


def _limpio(ax):
    ax.spines[["top", "right"]].set_visible(False)


def qq_normal(h):
    """Cuantiles de la muestra contra los de la normal: la cola se despega."""
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    (teo, obs), (pend, orden, _) = stats.probplot(h, dist="norm")
    ax.scatter(teo, obs, s=12, color=TINTA)
    ax.plot(teo, pend * np.array(teo) + orden, color=ROJO, lw=1.4,
            label="Recta de una distribución normal")
    ax.set_xlabel("Cuantil teórico de la normal estándar")
    ax.set_ylabel("Tiempo de resolución (horas)")
    ax.legend(frameon=False, loc="upper left")
    _limpio(ax)
    fig.tight_layout()
    fig.savefig(IMG / "qq-normal-muestra.pdf")
    plt.close(fig)


def caja_por_grupo(muestra):
    """Dos paneles: etapa del proyecto (Kruskal-Wallis) y discusion (Mann-Whitney)."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 3.2), sharey=True,
                                 gridspec_kw={"width_ratios": [2, 1.1]})
    per = {p: [] for p in B.PERIODOS}
    for i in muestra:
        per[B.periodo(i)].append(A.horas_resolucion(i))
    a1.boxplot([per[p] for p in B.PERIODOS], widths=0.55, medianprops={"color": ROJO})
    a1.set_xticks(range(1, len(B.PERIODOS) + 1),
                  [f"{p}\n(n={len(per[p])})" for p in B.PERIODOS], fontsize=8)
    a1.set_title("Etapa de creación", fontsize=9)
    a1.set_yscale("log")
    a1.set_ylabel("Horas hasta el cierre (escala log)")
    a1.axhline(A.UMBRAL_H, color=ROJO, lw=1, ls="--")
    corte = B.mann_whitney(muestra)["corte_comentarios"]
    g1 = [A.horas_resolucion(i) for i in muestra if i["comments"] <= corte]
    g2 = [A.horas_resolucion(i) for i in muestra if i["comments"] > corte]
    a2.boxplot([g1, g2], widths=0.55, medianprops={"color": ROJO})
    a2.set_xticks([1, 2], [f"0–{int(corte)} com.\n(n={len(g1)})",
                           f"{int(corte) + 1}+ com.\n(n={len(g2)})"], fontsize=8)
    a2.set_title("Nivel de discusión", fontsize=9)
    a2.axhline(A.UMBRAL_H, color=ROJO, lw=1, ls="--")
    for ax in (a1, a2):
        _limpio(ax)
    fig.tight_layout()
    fig.savefig(IMG / "caja-por-grupo.pdf")
    plt.close(fig)


def poisson(censo):
    r = B.bondad_poisson(censo)
    cl = r["clases"]
    x = np.arange(len(cl))
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    ax.bar(x - 0.2, [c["o"] for c in cl], width=0.4, color=TINTA, label="Observadas")
    ax.bar(x + 0.2, [c["e"] for c in cl], width=0.4, color=GRIS,
           label=f"Esperadas, Poisson(λ = {r['lambda']:.2f})")
    ax.set_xticks(x, [c["clase"] for c in cl])
    ax.set_xlabel(f"Issues creados en la semana ({r['anio']})")
    ax.set_ylabel("Número de semanas")
    ax.legend(frameon=False)
    _limpio(ax)
    fig.tight_layout()
    fig.savefig(IMG / "poisson-semanas.pdf")
    plt.close(fig)


if __name__ == "__main__":
    censo = A.cargar_censo()
    muestra = A.extraer_muestra(censo)
    qq_normal([A.horas_resolucion(i) for i in muestra])
    caja_por_grupo(muestra)
    poisson(censo)
    print("figuras escritas en", IMG)
