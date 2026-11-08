#!/usr/bin/env python3
"""Analisis del APF2: pruebas de hipotesis sobre la MISMA muestra del APF1.

Cada prueba se calcula dos veces: a mano, con las formulas del curso (semanas
10 a 12), y con scipy como control. El informe cita la cuenta a mano; si las
dos no coinciden, `controles` lo delata y los tests fallan.

Todas las cifras del informe salen de resultados_apf2.json.
"""
import collections
import datetime
import json
import math
import statistics
from pathlib import Path

import numpy as np
from scipy import stats

import analisis as A

ALFA = 0.05
MU_0 = A.UMBRAL_H            # 168 h: la semana, el mismo umbral del APF1
Z_ALFA_UNI = 1.645           # valor de tabla, cola derecha al 5 %
Z_ALFA_BI = 1.96             # valor de tabla, dos colas al 5 %


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------
def fecha(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def rangos(valores):
    """Rangos 1..n con empates promediados, como en las semanas 11 y 13."""
    return list(stats.rankdata(valores))


def periodo(issue):
    """Etapa del proyecto segun el anio de creacion del issue.

    2019-2023 se agrupa porque en la muestra hay 14 issues de esos cinco anios
    juntos: separados, ningun grupo llega a 5 y Kruskal-Wallis no se sostiene.
    """
    a = int(issue["created_at"][:4])
    return "2019-2023" if a <= 2023 else str(a)


PERIODOS = ["2019-2023", "2024", "2025", "2026"]


# --------------------------------------------------------------------------
# 0. Prueba Z para la media (unidad 2): el puente con el APF1
# --------------------------------------------------------------------------
def prueba_z_media(media, sigma, n, mu0=MU_0):
    """H0: mu <= 168 frente a H1: mu > 168. Sigma conocida: Z, como en el APF1."""
    ee = sigma / math.sqrt(n)
    z = (media - mu0) / ee
    return {"mu0": mu0, "media": media, "sigma": sigma, "n": n,
            "error_estandar": ee, "z": z, "z_critico": Z_ALFA_UNI,
            "p_valor": 1 - stats.norm.cdf(z), "rechaza_h0": bool(z > Z_ALFA_UNI)}


# --------------------------------------------------------------------------
# 1. Normalidad (semana 12): Kolmogorov-Smirnov con correccion de Stephens
#    y Shapiro-Wilk
# --------------------------------------------------------------------------
def kolmogorov_smirnov(h):
    x = sorted(h)
    n = len(x)
    m, s = statistics.mean(x), statistics.stdev(x)
    d_mas = max((i + 1) / n - stats.norm.cdf((xi - m) / s) for i, xi in enumerate(x))
    d_menos = max(stats.norm.cdf((xi - m) / s) - i / n for i, xi in enumerate(x))
    d = max(d_mas, d_menos)
    k_n = math.sqrt(n) - 0.01 + 0.85 / math.sqrt(n)
    c_alfa = 0.895                       # fila "Normal", alfa = 0,05
    d_alfa = c_alfa / k_n
    control = stats.kstest(x, stats.norm(m, s).cdf).statistic
    return {"n": n, "media": m, "desv": s, "d_mas": d_mas, "d_menos": d_menos,
            "d": d, "k_n": k_n, "c_alfa": c_alfa, "d_alfa": d_alfa,
            "rechaza_h0": bool(d > d_alfa), "control_scipy_d": control}


def shapiro_wilk(h):
    w, p = stats.shapiro(h)
    return {"w": float(w), "p_valor": float(p), "rechaza_h0": bool(p < ALFA)}


# --------------------------------------------------------------------------
# 2. Rachas (semana 10): ¿los issues lentos llegan agrupados en el tiempo?
# --------------------------------------------------------------------------
def rachas(muestra):
    orden = sorted(muestra, key=lambda i: i["created_at"])
    h = [A.horas_resolucion(i) for i in orden]
    me = statistics.median(h)
    signos = ["+" if x > me else "-" for x in h if x != me]
    n1 = signos.count("+")
    n2 = signos.count("-")
    g = 1 + sum(1 for a, b in zip(signos, signos[1:]) if a != b)
    mu_g = 2 * n1 * n2 / (n1 + n2) + 1
    var_g = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
    z = (g - mu_g) / math.sqrt(var_g)
    return {"mediana": me, "n1": n1, "n2": n2, "rachas": g, "mu_g": mu_g,
            "sigma_g": math.sqrt(var_g), "z": z, "z_critico": Z_ALFA_BI,
            "p_valor": 2 * (1 - stats.norm.cdf(abs(z))),
            "rechaza_h0": abs(z) > Z_ALFA_BI,
            "secuencia": "".join(signos)}


# --------------------------------------------------------------------------
# 3. Signos (semana 10): H0: Me <= 168 frente a H1: Me > 168
# --------------------------------------------------------------------------
def signos(h, me0=MU_0):
    mas = sum(1 for x in h if x > me0)
    menos = sum(1 for x in h if x < me0)
    n = mas + menos
    # aproximacion normal con correccion por continuidad (n > 25)
    z = (mas - 0.5 - n / 2) / math.sqrt(n / 4)
    p_exacto = float(stats.binom.sf(mas - 1, n, 0.5))      # P(X >= mas)
    return {"me0": me0, "mas": mas, "menos": menos, "n": n, "z": z,
            "z_critico": Z_ALFA_UNI, "p_valor_normal": 1 - stats.norm.cdf(z),
            "p_valor_exacto": p_exacto, "rechaza_h0": bool(z > Z_ALFA_UNI)}


def ic_mediana(h, confianza=0.95):
    """IC de la mediana por estadisticos de orden (binomial con p = 1/2)."""
    x = sorted(h)
    n = len(x)
    z = Z_ALFA_BI
    k = math.floor(n / 2 - z * math.sqrt(n) / 2)          # posicion inferior (1..n)
    j = math.ceil(n / 2 + 1 + z * math.sqrt(n) / 2)       # posicion superior
    cobertura = float(stats.binom.cdf(j - 1, n, 0.5) - stats.binom.cdf(k - 1, n, 0.5))
    return {"posicion_li": k, "posicion_ls": j, "li": x[k - 1], "ls": x[j - 1],
            "cobertura_exacta": cobertura, "mediana": statistics.median(x)}


# --------------------------------------------------------------------------
# 4. U de Mann-Whitney (semana 11): poca discusion frente a mucha
# --------------------------------------------------------------------------
def mann_whitney(muestra):
    corte = statistics.median(i["comments"] for i in muestra)
    g1 = [A.horas_resolucion(i) for i in muestra if i["comments"] <= corte]
    g2 = [A.horas_resolucion(i) for i in muestra if i["comments"] > corte]
    n1, n2 = len(g1), len(g2)
    r = rangos(g1 + g2)
    r1, r2 = sum(r[:n1]), sum(r[n1:])
    u1 = n1 * n2 + n1 * (n1 + 1) / 2 - r1
    u2 = n1 * n2 + n2 * (n2 + 1) / 2 - r2
    u = min(u1, u2)
    mu_u = n1 * n2 / 2
    sigma_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu_u) / sigma_u
    control = stats.mannwhitneyu(g1, g2, alternative="two-sided", method="asymptotic",
                                 use_continuity=False)
    return {"corte_comentarios": corte, "n1": n1, "n2": n2,
            "mediana_g1": statistics.median(g1), "mediana_g2": statistics.median(g2),
            "r1": r1, "r2": r2, "u1": u1, "u2": u2, "u": u, "mu_u": mu_u,
            "sigma_u": sigma_u, "z": z, "z_critico": Z_ALFA_BI,
            "p_valor": 2 * stats.norm.cdf(-abs(z)), "rechaza_h0": bool(abs(z) > Z_ALFA_BI),
            "control_scipy_p": float(control.pvalue)}


# --------------------------------------------------------------------------
# 5. Kruskal-Wallis (semana 11): ¿el tiempo cambio entre etapas del proyecto?
# --------------------------------------------------------------------------
def kruskal_wallis(muestra):
    grupos = {p: [] for p in PERIODOS}
    for i in muestra:
        grupos[periodo(i)].append(A.horas_resolucion(i))
    todos = [x for p in PERIODOS for x in grupos[p]]
    r = rangos(todos)
    n = len(todos)
    detalle, pos = [], 0
    for p in PERIODOS:
        ni = len(grupos[p])
        ri = sum(r[pos:pos + ni])
        pos += ni
        detalle.append({"periodo": p, "n": ni, "suma_rangos": ri,
                        "mediana": statistics.median(grupos[p])})
    hh = 12 / (n * (n + 1)) * sum(d["suma_rangos"] ** 2 / d["n"] for d in detalle) - 3 * (n + 1)
    gl = len(PERIODOS) - 1
    critico = float(stats.chi2.ppf(1 - ALFA, gl))
    control = stats.kruskal(*[grupos[p] for p in PERIODOS])
    return {"grupos": detalle, "n": n, "h": hh, "gl": gl, "chi2_critico": critico,
            "p_valor": float(stats.chi2.sf(hh, gl)), "rechaza_h0": bool(hh > critico),
            "control_scipy_h": float(control.statistic)}


# --------------------------------------------------------------------------
# 6. Chi cuadrado de independencia (semana 12): resolver en la semana y etapa
# --------------------------------------------------------------------------
ETAPAS_CHI = ["2019-2024", "2025", "2026"]


def etapa_chi(issue):
    a = int(issue["created_at"][:4])
    return "2019-2024" if a <= 2024 else str(a)


def chi_independencia(muestra):
    filas = ["Dentro de la semana", "Fuera de la semana"]
    obs = [[0] * len(ETAPAS_CHI) for _ in filas]
    for i in muestra:
        f = 0 if A.horas_resolucion(i) < A.UMBRAL_H else 1
        obs[f][ETAPAS_CHI.index(etapa_chi(i))] += 1
    tf = [sum(f) for f in obs]
    tc = [sum(obs[f][c] for f in range(2)) for c in range(len(ETAPAS_CHI))]
    n = sum(tf)
    esp = [[tf[f] * tc[c] / n for c in range(len(ETAPAS_CHI))] for f in range(2)]
    x2 = sum((obs[f][c] - esp[f][c]) ** 2 / esp[f][c]
             for f in range(2) for c in range(len(ETAPAS_CHI)))
    gl = (2 - 1) * (len(ETAPAS_CHI) - 1)
    critico = float(stats.chi2.ppf(1 - ALFA, gl))
    control = stats.chi2_contingency(obs, correction=False)
    return {"filas": filas, "columnas": ETAPAS_CHI, "observados": obs,
            "esperados": esp, "total_filas": tf, "total_columnas": tc, "n": n,
            "x2": x2, "gl": gl, "chi2_critico": critico,
            "p_valor": float(stats.chi2.sf(x2, gl)), "rechaza_h0": x2 > critico,
            "min_esperado": min(min(f) for f in esp),
            "control_scipy_x2": float(control[0])}


# --------------------------------------------------------------------------
# 7. Bondad de ajuste a Poisson (semana 12): llegada semanal de reportes
# --------------------------------------------------------------------------
ANIO_POISSON = 2025


def semanas_del_anio(censo, anio=ANIO_POISSON):
    """Reportes creados en cada semana ISO del anio (las 52 completas)."""
    cuenta = collections.Counter()
    for i in censo:
        f = fecha(i["created_at"])
        iso = f.isocalendar()
        if iso[0] == anio:
            cuenta[iso[1]] += 1
    return [cuenta.get(s, 0) for s in range(1, 53)]


def bondad_poisson(censo, anio=ANIO_POISSON):
    x = semanas_del_anio(censo, anio)
    k = len(x)
    lam = statistics.mean(x)
    # clases de igual probabilidad aproximada; luego se unen las de E < 5
    cortes = [0, 9, 12, 14, 16, 18, 20, 23, math.inf]
    clases = []
    for a, b in zip(cortes, cortes[1:]):
        o = sum(1 for v in x if a <= v < b)
        p = stats.poisson.cdf(b - 1, lam) - (stats.poisson.cdf(a - 1, lam) if a > 0 else 0) \
            if b != math.inf else stats.poisson.sf(a - 1, lam)
        etiqueta = f"{a}-{b - 1}" if b != math.inf else f"{a} o más"
        clases.append({"clase": etiqueta, "o": o, "p": float(p), "e": float(k * p)})
    # unir clases con E < 5 hacia la vecina
    unidas = []
    for c in clases:
        if unidas and (unidas[-1]["e"] < 5):
            u = unidas[-1]
            u.update(clase=u["clase"].split("-")[0] + "-" + c["clase"].split("-")[-1]
                     if "más" not in c["clase"] else u["clase"].split("-")[0] + " o más",
                     o=u["o"] + c["o"], p=u["p"] + c["p"], e=u["e"] + c["e"])
        else:
            unidas.append(dict(c))
    if unidas[-1]["e"] < 5 and len(unidas) > 1:
        ult = unidas.pop()
        u = unidas[-1]
        u.update(clase=u["clase"].split("-")[0] + " o más", o=u["o"] + ult["o"],
                 p=u["p"] + ult["p"], e=u["e"] + ult["e"])
    for c in unidas:
        c["aporte"] = (c["o"] - c["e"]) ** 2 / c["e"]
    x2 = sum(c["aporte"] for c in unidas)
    gl = len(unidas) - 1 - 1                 # K - m - 1, m = 1 (lambda estimada)
    critico = float(stats.chi2.ppf(1 - ALFA, gl))
    return {"anio": anio, "semanas": k, "total": sum(x), "lambda": lam,
            "varianza": statistics.variance(x), "minimo": min(x), "maximo": max(x),
            "conteos": x, "clases": unidas, "x2": x2, "gl": gl,
            "chi2_critico": critico, "p_valor": float(stats.chi2.sf(x2, gl)),
            "rechaza_h0": x2 > critico}


# --------------------------------------------------------------------------
def informe():
    censo = A.cargar_censo()
    pob = A.parametros_poblacionales(censo)
    muestra = A.extraer_muestra(censo)
    h = [A.horas_resolucion(i) for i in muestra]
    desc = A.descriptivos(muestra)
    r = {
        "muestra": desc,
        "z_media": prueba_z_media(desc["media"], pob["sigma"], desc["n"]),
        "ks": kolmogorov_smirnov(h),
        "shapiro": shapiro_wilk(h),
        "rachas": rachas(muestra),
        "signos": signos(h),
        "ic_mediana": ic_mediana(h),
        "mann_whitney": mann_whitney(muestra),
        "kruskal": kruskal_wallis(muestra),
        "chi_independencia": chi_independencia(muestra),
        "poisson": bondad_poisson(censo),
        "poblacion": {"mediana": pob["mediana"], "mu": pob["mu"], "N": pob["N"]},
    }
    r["controles"] = {
        "ks_coincide": bool(abs(r["ks"]["d"] - r["ks"]["control_scipy_d"]) < 1e-9),
        "mann_whitney_coincide": bool(abs(r["mann_whitney"]["p_valor"]
                                     - r["mann_whitney"]["control_scipy_p"]) < 1e-9),
        "kruskal_sin_correccion_empates": bool(abs(r["kruskal"]["h"]
                                              - r["kruskal"]["control_scipy_h"]) < 1e-6),
        "chi_coincide": bool(abs(r["chi_independencia"]["x2"]
                            - r["chi_independencia"]["control_scipy_x2"]) < 1e-9),
    }
    return r


if __name__ == "__main__":
    r = informe()
    salida = Path(__file__).parent / "resultados_apf2.json"
    salida.write_text(json.dumps(r, indent=2, ensure_ascii=False, default=float),
                      encoding="utf8")
    resumen = {k: {kk: vv for kk, vv in v.items()
                   if not isinstance(vv, (list, dict)) or kk in ("grupos", "clases", "observados")}
               for k, v in r.items() if isinstance(v, dict)}
    print(json.dumps(resumen, indent=1, ensure_ascii=False, default=float))
