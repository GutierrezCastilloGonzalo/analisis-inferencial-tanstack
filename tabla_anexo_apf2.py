"""Escribe la tabla del anexo del APF2 (los 100 issues con anio y comentarios)."""
import sys
from pathlib import Path
import analisis as A

def num(x):
    return f"${x:,.2f}$".replace(",", "X").replace(".", "{,}").replace("X", "")

m = sorted(A.extraer_muestra(A.cargar_censo()), key=lambda i: i["number"])
filas = [(i["number"], i["created_at"][:4], A.horas_resolucion(i), i["comments"]) for i in m]
k = 34
cols = [filas[j:j + k] for j in range(0, len(filas), k)]
out = []
for r in range(k):
    celdas = []
    for c in cols:
        if r < len(c):
            n, a, h, co = c[r]
            celdas += [str(n), a, num(h), str(co)]
        else:
            celdas += ["", "", "", ""]
    out.append(" & ".join(celdas) + r" \\")
Path(sys.argv[1]).write_text("\n".join(out) + "\n", encoding="utf8")
