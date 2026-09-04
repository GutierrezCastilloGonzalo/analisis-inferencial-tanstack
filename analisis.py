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
