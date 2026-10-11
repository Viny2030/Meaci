"""
scraper/novedades.py
Detecta resoluciones corporativas nuevas publicadas por el DOJ (FCPA) que no
están en la base del MEACI. NO carga nada en casos/empresas/resoluciones: la
carga sigue siendo manual, después de verificar que sea un caso
multijurisdiccional (ver data/ocde_seed.py). Así se evita el problema de
utils/sync.py anterior, que insertaba títulos de expedientes como empresas,
con año 2024 y monto 0.

Una novedad es un caso del DOJ:
  - de ANIO_MINIMO en adelante (el informe OCDE cubre hasta marzo 2026), y
  - cuya URL no está en las resoluciones cargadas, y
  - cuya empresa no coincide con ninguna empresa/caso ya cargado.
"""
from __future__ import annotations

import re
import unicodedata

from rapidfuzz import fuzz

from scraper.doj import obtener_casos_recientes

ANIO_MINIMO = 2025

_SUFIJOS = {
    "sa", "s", "a", "sas", "sau", "srl", "ltd", "ltda", "limited", "inc", "llc", "lp", "plc",
    "ag", "se", "nv", "bv", "co", "company", "corp", "corporation", "the", "group", "holding",
    "holdings", "pty", "and", "de", "cv", "ca", "spa", "gmbh", "international", "et", "al",
}


def _norm(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\(.*?\)", " ", t)              # "(DPA)", "(Smartmatic)"
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return [w for w in t.split() if w not in _SUFIJOS and len(w) > 1]


def empresa_desde_titulo(titulo: str) -> str:
    """'U.S. v. Gunvor S.A.: Docket No. 1:24-cr-...' → 'Gunvor S.A.'"""
    t = titulo.strip()
    t = re.split(r"[:,;]?\s*(?:Docket|Court Docket|Case No)\b", t, maxsplit=1, flags=re.I)[0]
    t = re.sub(r"^(?:U\.?\s?S\.?|United States(?: of America)?)\s+v\.?\s+", "", t, flags=re.I)
    t = re.sub(r"^In re\s+", "", t, flags=re.I)
    return t.strip(" .:-")


def _coincide(nombre: str, conocidos: list[list[str]]) -> bool:
    toks = _norm(nombre)
    if not toks:
        return False
    for k in conocidos:
        if not k:
            continue
        if toks[0] == k[0] and len(toks[0]) >= 3:
            return True
        if fuzz.token_set_ratio(" ".join(toks), " ".join(k)) >= 90:
            return True
    return False


def detectar_novedades(nombres_conocidos: list[str], urls_conocidas: set[str],
                       limite: int = 40) -> list[dict]:
    conocidos = [_norm(n) for n in nombres_conocidos]
    salida = []
    for c in obtener_casos_recientes(limite=limite):
        anio = int(c["fecha"]) if str(c.get("fecha", "")).isdigit() else 0
        if anio < ANIO_MINIMO or c["url"] in urls_conocidas:
            continue
        empresa = empresa_desde_titulo(c["titulo"])
        if _coincide(empresa, conocidos):
            continue
        salida.append({
            "fuente": "DOJ",
            "titulo": c["titulo"],
            "empresa": empresa,
            "anio": anio,
            "url": c["url"],
        })
    return salida
