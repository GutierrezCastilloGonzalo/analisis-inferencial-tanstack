#!/usr/bin/env python3
"""Baja el censo de issues cerrados de TanStack/router, lo valida y lo congela.

Se corre UNA vez. Guarda dos archivos:
  datos/censo-crudo.json  la respuesta completa (11 MB, gitignorada)
  datos/censo.json        la proyeccion a los campos usados (se commitea)

    uv run --system-certs python descargar_censo.py
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = "TanStack/router"
DATOS = Path(__file__).parent / "datos"
CRUDO = DATOS / "censo-crudo.json"
CENSO = DATOS / "censo.json"
CAMPOS = ("number", "created_at", "closed_at", "state_reason", "comments")


def api(ruta):
    """Una llamada a la API de GitHub via el CLI gh, ya autenticado."""
    r = subprocess.run(["gh", "api", ruta], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"fallo la API en {ruta}: {r.stderr[:300]}")
    return json.loads(r.stdout)


def total_declarado():
    """Conteo independiente, por el endpoint de busqueda. Sirve de control."""
    q = f"search/issues?q=repo:{REPO}+type:issue+state:closed&per_page=1"
    return api(q)["total_count"]


def descargar():
    """Pagina /issues y descarta los pull requests, que vienen mezclados."""
    issues, pagina, descartados = [], 1, 0
    while True:
        lote = api(f"repos/{REPO}/issues?state=closed&per_page=100&page={pagina}")
        if not lote:
            break
        for i in lote:
            if "pull_request" in i:
                descartados += 1
            elif i.get("closed_at"):
                issues.append(i)
        pagina += 1
    return issues, descartados


if __name__ == "__main__":
    esperado = total_declarado()
    issues, descartados = descargar()
    print(f"pull requests descartados: {descartados}")
    print(f"issues cerrados recogidos: {len(issues)}")
    print(f"issues cerrados segun el buscador: {esperado}")
    if len(issues) != esperado:
        sys.exit(f"DISCREPANCIA: {len(issues)} != {esperado}. No se guarda nada.")
    DATOS.mkdir(parents=True, exist_ok=True)
    CRUDO.write_text(json.dumps(issues), encoding="utf8")
    proyeccion = [{c: i.get(c) for c in CAMPOS} for i in issues]
    CENSO.write_text(json.dumps(proyeccion), encoding="utf8")
    print(f"crudo:     {CRUDO}  ({CRUDO.stat().st_size / 1e6:.1f} MB, gitignorado)")
    print(f"proyeccion:{CENSO}  ({CENSO.stat().st_size / 1e3:.0f} KB, se commitea)")
