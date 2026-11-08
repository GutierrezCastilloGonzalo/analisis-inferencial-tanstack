"""Tests del APF2: las cuentas a mano deben coincidir con scipy."""
import pytest

import analisis_apf2 as B


@pytest.fixture(scope="module")
def r():
    return B.informe()


def test_controles_contra_scipy(r):
    assert all(r["controles"].values()), r["controles"]


def test_misma_muestra_que_el_apf1(r):
    assert r["muestra"]["n"] == 100
    assert r["muestra"]["media"] == pytest.approx(1312.9532, abs=1e-4)


def test_signos_cuenta_todos(r):
    s = r["signos"]
    assert s["mas"] + s["menos"] == s["n"] == 100


def test_ic_mediana_cubre_al_menos_95(r):
    assert r["ic_mediana"]["cobertura_exacta"] >= 0.95
    assert r["ic_mediana"]["li"] <= r["ic_mediana"]["mediana"] <= r["ic_mediana"]["ls"]


def test_chi_esperados_minimos(r):
    assert r["chi_independencia"]["min_esperado"] >= 5


def test_poisson_clases_con_esperado_suficiente(r):
    assert all(c["e"] >= 5 for c in r["poisson"]["clases"])
    assert sum(c["o"] for c in r["poisson"]["clases"]) == r["poisson"]["semanas"]


def test_grupos_kruskal_de_al_menos_cinco(r):
    assert all(g["n"] >= 5 for g in r["kruskal"]["grupos"])
