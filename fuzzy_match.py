"""
Fuzzy matching entre nombres de empresas OCDE y razones sociales de COMPR.AR / AFIP.
Usado por el matcher cuando no hay CUIT directo disponible.
"""
from rapidfuzz import fuzz, process
from typing import Optional
import json


# Lista de nombres canónicos de empresas OCDE y sus variantes conocidas en Argentina
EMPRESAS_OCDE_AR = {
    "Siemens": ["Siemens S.A. Argentina", "Siemens SA", "Siemens Argentina"],
    "ABB": ["ABB S.A. Argentina", "ABB SA", "ABB Argentina"],
    "SAP": ["SAP Argentina S.A.", "SAP Argentina SA"],
    "Airbus": ["Airbus Argentina SRL", "Airbus SRL"],
    "Goldman Sachs": ["Goldman Sachs Argentina LLC", "Goldman Sachs Argentina"],
    "Honeywell": ["Honeywell Argentina S.R.L.", "Honeywell SRL", "Honeywell Argentina"],
    "Teva": ["Teva Argentina S.A.", "Teva Argentina SA", "Teva Pharmaceutical Argentina"],
    "McKinsey": ["McKinsey & Company Argentina", "McKinsey Argentina"],
    "Glencore": ["Glencore Argentina Grain SRL", "Glencore Argentina"],
    "Rolls-Royce": ["Rolls-Royce Energy Systems Argentina", "Rolls Royce Argentina"],
    "Credit Suisse": ["Credit Suisse AG Sucursal Argentina", "UBS Argentina (ex Credit Suisse)"],
    "TechnipFMC": ["Technip Argentina S.A.", "Technip Argentina SA", "TechnipFMC Argentina"],
    "Embraer": ["Embraer Argentina"],
    "Braskem": ["Braskem Idesa Argentina"],
    "Odebrecht": ["CNO S.A.", "Constructora Norberto Odebrecht", "CNO Argentina"],
}

# CUIT conocidos (completar con verificación AFIP)
CUITS_CONOCIDOS = {
    "30-54667581-3": "Siemens",
    "30-57655868-3": "ABB",
    "30-69142665-7": "SAP",
    "30-70881733-1": "Odebrecht / CNO",
}


def buscar_por_nombre(nombre_proveedor: str, umbral: int = 80) -> Optional[dict]:
    """
    Dado un nombre de proveedor (de COMPR.AR o BORA), retorna la empresa OCDE
    si el score de similitud supera el umbral.

    Returns:
        dict con empresa_ocde, variante_encontrada, score | None si no hay match
    """
    nombre_upper = nombre_proveedor.upper().strip()

    # Aplanar todas las variantes en una lista con su empresa asociada
    variantes = []
    mapa = {}
    for empresa, aliases in EMPRESAS_OCDE_AR.items():
        for alias in aliases:
            v = alias.upper()
            variantes.append(v)
            mapa[v] = empresa

    resultado = process.extractOne(
        nombre_upper,
        variantes,
        scorer=fuzz.token_sort_ratio,
    )

    if resultado is None:
        return None

    variante, score, _ = resultado
    if score >= umbral:
        return {
            "empresa_ocde": mapa[variante],
            "variante_encontrada": variante,
            "nombre_buscado": nombre_proveedor,
            "score": score,
            "metodo": "fuzzy_nombre",
        }
    return None


def buscar_por_cuit(cuit: str) -> Optional[dict]:
    """
    Dado un CUIT, retorna la empresa OCDE si está en la tabla conocida.
    """
    cuit_limpio = cuit.replace("-", "").strip()
    for cuit_ref, empresa in CUITS_CONOCIDOS.items():
        if cuit_ref.replace("-", "") == cuit_limpio:
            return {
                "empresa_ocde": empresa,
                "cuit": cuit,
                "metodo": "cuit_exacto",
                "score": 100,
            }
    return None


def verificar_proveedor(nombre: str, cuit: Optional[str] = None) -> Optional[dict]:
    """
    Punto de entrada principal. Intenta CUIT primero, luego fuzzy por nombre.
    """
    if cuit:
        resultado = buscar_por_cuit(cuit)
        if resultado:
            return resultado
    return buscar_por_nombre(nombre)
