#!/usr/bin/env python3
"""Analisis del APF1: muestreo, descriptivos e intervalos de confianza.

Todas las cifras del informe salen de aca. El .tex no transcribe ningun numero
a mano: lee resultados.json.
"""
import datetime
import json
import math
import random
import statistics
from pathlib import Path

SEMILLA = 20260907        # la fecha de entrega; fija, nunca se cambia
N_MUESTRA = 100
UMBRAL_H = 168.0          # 7 dias, el umbral de la proporcion
CONFIANZA = 0.95
Z_TABLA = 1.96            # valor de tabla para el 95 %

CENSO = Path(__file__).parent / "datos" / "censo.json"


def horas_resolucion(issue):
    """Horas entre la creacion y el cierre de un issue."""
    a = datetime.datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
    b = datetime.datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
    return (b - a).total_seconds() / 3600


def cargar_censo(ruta=None):
    return json.loads(Path(ruta or CENSO).read_text(encoding="utf8"))


def parametros_poblacionales(censo):
    """Los parametros de verdad. Se conocen porque se tiene la poblacion entera."""
    h = [horas_resolucion(i) for i in censo]
    n = len(h)
    return {
        "N": n,
        "mu": statistics.mean(h),
        "sigma": statistics.pstdev(h),          # poblacional, divide por N
        "mediana": statistics.median(h),
        "pi": sum(1 for x in h if x < UMBRAL_H) / n,
    }


def extraer_muestra(censo, n=N_MUESTRA, semilla=SEMILLA):
    """Muestreo aleatorio simple SIN reemplazo, reproducible por la semilla."""
    return random.Random(semilla).sample(censo, n)


def descriptivos(muestra):
    """Medidas de tendencia central y de dispersion de la muestra."""
    h = sorted(horas_resolucion(i) for i in muestra)
    n = len(h)
    # Cuartiles por interpolacion lineal entre estadisticos de orden (metodo
    # "inclusive" = numpy.percentile / scipy / Excel / matplotlib.boxplot).
    # Con los estadisticos de orden crudos, h[n//4] y h[3n//4], la caja del
    # diagrama no coincidiria con los cuartiles citados en el informe.
    q1, _, q3 = statistics.quantiles(h, n=4, method="inclusive")
    return {
        "n": n,
        "media": statistics.mean(h),
        "mediana": statistics.median(h),
        "desv": statistics.stdev(h),        # muestral, divide por n-1
        "q1": q1,
        "q3": q3,
        "minimo": h[0],
        "maximo": h[-1],
        "sesgo": statistics.mean(h) / statistics.median(h),
    }


def ic_media(media, sigma, n, z=Z_TABLA):
    """IC para la media con sigma CONOCIDA: por eso Z y no T de Student."""
    ee = sigma / math.sqrt(n)
    margen = z * ee
    return {"z": z, "error_estandar": ee, "margen": margen,
            "li": media - margen, "ls": media + margen}


def ic_proporcion(p, n, z=Z_TABLA):
    """IC para la proporcion. Comprueba np y nq antes de confiar en la normal."""
    ee = math.sqrt(p * (1 - p) / n)
    margen = z * ee
    k = round(p * n)
    return {"z": z, "error_estandar": ee, "margen": margen,
            "li": p - margen, "ls": p + margen,
            "np_": k, "nq": n - k, "normal_valida": min(k, n - k) >= 10}


def informe():
    """Arma el diccionario del que sale TODA cifra del documento."""
    censo = cargar_censo()
    pob = parametros_poblacionales(censo)
    muestra = extraer_muestra(censo)
    desc = descriptivos(muestra)
    k = sum(1 for i in muestra if horas_resolucion(i) < UMBRAL_H)
    p = k / desc["n"]
    # La media es de la muestra, pero la sigma es la POBLACIONAL: se conoce
    # porque se tiene el censo entero. Pasar desc["desv"] (la muestral) aca
    # seria el error clasico, y el IC resultante seguiria "viendose bien".
    icm = ic_media(desc["media"], pob["sigma"], desc["n"])
    icp = ic_proporcion(p, desc["n"])
    return {
        "poblacion": pob,
        "muestra": {**desc, "k_bajo_umbral": k, "p": p,
                    "fraccion_muestreada": desc["n"] / pob["N"]},
        "ic_media": icm,
        "ic_proporcion": icp,
        "validacion": {
            "ic_media_contiene_mu": icm["li"] <= pob["mu"] <= icm["ls"],
            "ic_proporcion_contiene_pi": icp["li"] <= pob["pi"] <= icp["ls"],
            "correccion_poblacion_finita_necesaria": desc["n"] / pob["N"] >= 0.05,
        },
    }


if __name__ == "__main__":
    r = informe()
    salida = Path(__file__).parent / "resultados.json"
    salida.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    print(f"\nescrito en {salida}")
