"""Verifica analisis.py contra los parametros conocidos y contra SciPy."""
import math

import analisis as A


def test_censo_tiene_2036_issues():
    assert len(A.cargar_censo()) == 2036


def test_parametros_poblacionales_conocidos():
    p = A.parametros_poblacionales(A.cargar_censo())
    assert p["N"] == 2036
    assert math.isclose(p["mu"], 1455.6567, abs_tol=0.01)
    assert math.isclose(p["sigma"], 2951.2547, abs_tol=0.01)
    assert math.isclose(p["pi"], 0.5236, abs_tol=0.0005)


def test_la_muestra_es_reproducible():
    censo = A.cargar_censo()
    a = A.extraer_muestra(censo)
    b = A.extraer_muestra(censo)
    assert [i["number"] for i in a] == [i["number"] for i in b]


def test_la_muestra_es_sin_reemplazo_y_del_tamano_pedido():
    m = A.extraer_muestra(A.cargar_censo())
    assert len(m) == 100
    assert len({i["number"] for i in m}) == 100


def test_no_hace_falta_correccion_por_poblacion_finita():
    assert A.N_MUESTRA / 2036 < 0.05
