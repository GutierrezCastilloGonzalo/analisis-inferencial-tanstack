# analisis-inferencial-tanstack

Análisis estadístico de la gestión de defectos del repositorio `TanStack/router`,
para el curso de Estadística Inferencial de la UTP.

**Vive en su propio repositorio a propósito.** El repo del periodo no aloja
subproyectos ni datasets: el ciclo anterior creció a 12,14 GB por eso. Allá queda
un puntero `.repo.yaml` de cuatro líneas.

Sirve a las tres entregas del mismo caso: el APF1 (intervalos de confianza), el
APF2 (pruebas de hipótesis) y el proyecto final (regresión).

## Correr

    uv run --system-certs python descargar_censo.py    # una sola vez
    uv run --system-certs --with scipy --with numpy python analisis.py
    uv run --system-certs --with matplotlib --with scipy --with numpy python graficos.py

## Tests

    uv run --system-certs --with pytest --with scipy --with numpy python -m pytest -v

## El censo

`datos/censo.json` es una **proyección congelada** a los cinco campos que el
análisis usa. La respuesta cruda de la API (11 MB) queda gitignorada. Se congela
porque el censo cambia con el tiempo: rebajarlo dentro de un mes daría otro `N` y
los números del informe dejarían de reproducirse.
