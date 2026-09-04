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
    # Fijan la semilla: sin esto, una implementacion que ignore `semilla` y
    # use otro generador seguiria pareciendo "reproducible" y pasaria igual.
    assert [i["number"] for i in a[:5]] == [510, 5546, 628, 5873, 4225]


def test_la_muestra_es_sin_reemplazo_y_del_tamano_pedido():
    m = A.extraer_muestra(A.cargar_censo())
    assert len(m) == 100
    assert len({i["number"] for i in m}) == 100


def test_no_hace_falta_correccion_por_poblacion_finita():
    # n/N < 5 % es lo que permite omitir la correccion por poblacion finita.
    # El denominador sale del censo, no de un literal: si la poblacion
    # cambiara de tamano, este test tiene que enterarse.
    N = len(A.cargar_censo())
    assert A.N_MUESTRA / N < 0.05


def test_ic_media_coincide_con_scipy():
    from scipy.stats import norm
    r = A.ic_media(media=1200.0, sigma=2951.2547, n=100)
    ee = 2951.2547 / math.sqrt(100)
    assert math.isclose(r["error_estandar"], ee, rel_tol=1e-12)
    assert math.isclose(r["margen"], 1.96 * ee, rel_tol=1e-12)
    assert math.isclose(r["li"], 1200.0 - 1.96 * ee, rel_tol=1e-12)
    assert round(norm.ppf(0.975), 2) == 1.96


def test_ic_proporcion_coincide_con_scipy():
    from scipy.stats import norm
    r = A.ic_proporcion(p=0.52, n=100)
    ee = math.sqrt(0.52 * 0.48 / 100)
    assert math.isclose(r["error_estandar"], ee, rel_tol=1e-12)
    assert math.isclose(r["margen"], 1.96 * ee, rel_tol=1e-12)
    assert r["np_"] == 52 and r["nq"] == 48
    assert r["normal_valida"] is True
    assert round(norm.ppf(0.975), 2) == 1.96


def test_la_proporcion_de_la_muestra_admite_aproximacion_normal():
    m = A.extraer_muestra(A.cargar_censo())
    k = sum(1 for i in m if A.horas_resolucion(i) < A.UMBRAL_H)
    r = A.ic_proporcion(k / len(m), len(m))
    assert r["np_"] >= 10 and r["nq"] >= 10, "la aproximacion normal no seria valida"


def test_el_ic_de_la_media_contiene_el_parametro_real():
    censo = A.cargar_censo()
    pob = A.parametros_poblacionales(censo)
    d = A.descriptivos(A.extraer_muestra(censo))
    r = A.ic_media(d["media"], pob["sigma"], d["n"])
    assert r["li"] <= pob["mu"] <= r["ls"], (
        f"el IC [{r['li']:.1f}, {r['ls']:.1f}] no contiene mu={pob['mu']:.1f}"
    )


def test_la_poblacion_esta_sesgada_a_la_derecha():
    pob = A.parametros_poblacionales(A.cargar_censo())
    assert pob["mu"] / pob["mediana"] > 5, "sin sesgo, el argumento del TLC pierde fuerza"
