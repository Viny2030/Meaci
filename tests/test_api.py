"""
Tests automáticos del MEACI.
Correr: pytest tests/ -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


# ── Básicos ───────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["casos"] == 31
    assert data["empresas"] == 31


def test_resumen():
    r = client.get("/api/resumen")
    assert r.status_code == 200
    data = r.json()
    assert data["total_casos"] == 31
    assert data["con_presencia_argentina"] == 15
    assert data["total_resoluciones"] == 73
    assert data["monto_total_usd_millones"] > 0


# ── Casos ─────────────────────────────────────────────────────────────────────

def test_casos_todos():
    r = client.get("/api/casos")
    assert r.status_code == 200
    assert len(r.json()) == 31


def test_casos_filtro_presencia_ar():
    r = client.get("/api/casos?presencia_ar=true")
    assert r.status_code == 200
    casos = r.json()
    assert len(casos) == 15
    for c in casos:
        assert c["presencia_argentina"] is True


def test_casos_filtro_pais():
    r = client.get("/api/casos?pais=Brasil")
    assert r.status_code == 200
    for c in r.json():
        assert "Brasil" in c["paises"]


def test_caso_detalle_siemens():
    r = client.get("/api/casos/1")
    assert r.status_code == 200
    data = r.json()
    assert data["nombre_caso"] == "Siemens AG"
    assert data["anio_resolucion"] == 2008
    assert len(data["resoluciones"]) == 3


def test_caso_no_existe():
    r = client.get("/api/casos/9999")
    assert r.status_code == 404


# ── Empresas ──────────────────────────────────────────────────────────────────

def test_empresas_todas():
    r = client.get("/api/empresas")
    assert r.status_code == 200
    assert len(r.json()) == 31


def test_empresas_presencia_ar():
    r = client.get("/api/empresas?presencia_ar=true")
    assert r.status_code == 200
    assert len(r.json()) == 15


def test_empresa_por_cuit_siemens():
    r = client.get("/api/empresas/cuit/30-54667581-3")
    assert r.status_code == 200
    data = r.json()
    assert data["nombre_matriz"] == "Siemens AG"


def test_empresa_por_cuit_sap():
    r = client.get("/api/empresas/cuit/30-69142665-7")
    assert r.status_code == 200
    assert r.json()["nombre_matriz"] == "SAP SE"


def test_empresa_cuit_inexistente():
    r = client.get("/api/empresas/cuit/99-99999999-9")
    assert r.status_code == 404


# ── Cruce COMPR.AR ────────────────────────────────────────────────────────────

def test_cruce_cuit_sancionado():
    r = client.get("/api/cruce-compr?cuit=30-54667581-3")
    assert r.status_code == 200
    data = r.json()
    assert data["sancionada_ocde"] is True
    assert data["empresa_matriz"] == "Siemens AG"
    assert len(data["casos"]) >= 1


def test_cruce_cuit_libre():
    r = client.get("/api/cruce-compr?cuit=30-12345678-9")
    assert r.status_code == 200
    data = r.json()
    assert data["sancionada_ocde"] is False
    assert data["datos"] is None


def test_cruce_abb():
    r = client.get("/api/cruce-compr?cuit=30-57655868-3")
    assert r.status_code == 200
    data = r.json()
    assert data["sancionada_ocde"] is True
    assert "ABB" in data["empresa_matriz"]


# ── Fuzzy match ───────────────────────────────────────────────────────────────

def test_fuzzy_match_exacto():
    from matcher.fuzzy_match import verificar_proveedor
    r = verificar_proveedor("SAP ARGENTINA SA")
    assert r is not None
    assert r["empresa_ocde"] == "SAP"
    assert r["score"] >= 90


def test_fuzzy_match_siemens():
    from matcher.fuzzy_match import verificar_proveedor
    r = verificar_proveedor("SIEMENS SA ARGENTINA")
    assert r is not None
    assert r["empresa_ocde"] == "Siemens"


def test_fuzzy_match_cuit_directo():
    from matcher.fuzzy_match import verificar_proveedor
    r = verificar_proveedor("CUALQUIER NOMBRE", "30-57655868-3")
    assert r is not None
    assert r["metodo"] == "cuit_exacto"
    assert "ABB" in r["empresa_ocde"]


def test_fuzzy_no_match():
    from matcher.fuzzy_match import verificar_proveedor
    r = verificar_proveedor("PANADERIA DON JORGE SRL")
    assert r is None


# ── Alertas ───────────────────────────────────────────────────────────────────

def test_alertas_endpoint():
    r = client.get("/api/alertas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_presencia_ar_endpoint():
    r = client.get("/api/presencia-ar")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 15
