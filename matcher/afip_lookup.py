"""
Lookup de razón social por CUIT en fuentes públicas argentinas.
Usa la API pública de AFIP / datos.gob.ar cuando está disponible.
Fallback: tabla estática de CUITs conocidos de empresas OCDE.
"""
import httpx
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

# API pública que expone datos de AFIP (no requiere auth)
AFIP_API = "https://afip.tangofactura.com/Rest/GetContribuyenteFull?cuit={cuit}"
ARGENTINADATOS_API = "https://api.argentinadatos.com/v1/cuit/{cuit}"


def limpiar_cuit(cuit: str) -> str:
    """Normaliza CUIT: elimina guiones y espacios, retorna solo dígitos."""
    return re.sub(r"[^0-9]", "", cuit)


def consultar_afip(cuit: str) -> Optional[dict]:
    """
    Consulta la razón social de un CUIT en AFIP via API pública.
    Retorna dict con razon_social, actividad, estado o None si no encuentra.
    """
    cuit_limpio = limpiar_cuit(cuit)
    if len(cuit_limpio) != 11:
        return None

    # Intentar ArgentinaDatos primero (más confiable)
    try:
        url = ARGENTINADATOS_API.format(cuit=cuit_limpio)
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("razonSocial"):
                return {
                    "cuit": cuit,
                    "razon_social": data.get("razonSocial", ""),
                    "actividad": data.get("actividadPrincipal", {}).get("descripcion", ""),
                    "estado": data.get("estadoClave", ""),
                    "fuente": "argentinadatos",
                }
    except Exception as e:
        logger.debug(f"[AFIP] ArgentinaDatos falló para {cuit}: {e}")

    # Fallback: TangoFactura
    try:
        url = AFIP_API.format(cuit=cuit_limpio)
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        if resp.status_code == 200:
            data = resp.json()
            contrib = data.get("Contribuyente", {})
            if contrib.get("razonSocial"):
                return {
                    "cuit": cuit,
                    "razon_social": contrib.get("razonSocial", ""),
                    "actividad": contrib.get("descripcionActividad", ""),
                    "estado": contrib.get("estadoClave", ""),
                    "fuente": "tangofactura",
                }
    except Exception as e:
        logger.debug(f"[AFIP] TangoFactura falló para {cuit}: {e}")

    return None


def verificar_cuit_en_lista_ocde(cuit: str) -> Optional[str]:
    """
    Verifica si un CUIT está en la tabla estática de empresas OCDE sancionadas.
    Retorna el nombre de la empresa o None.
    Esta función es el fallback offline — no requiere red.
    """
    from matcher.fuzzy_match import CUITS_CONOCIDOS
    cuit_limpio = limpiar_cuit(cuit)
    for cuit_ref, empresa in CUITS_CONOCIDOS.items():
        if limpiar_cuit(cuit_ref) == cuit_limpio:
            return empresa
    return None


def enriquecer_presencia_ar(cuit: str) -> dict:
    """
    Punto de entrada principal.
    Dado un CUIT, retorna toda la información disponible:
    razón social AFIP + si es empresa OCDE sancionada.
    """
    resultado = {
        "cuit": cuit,
        "razon_social": None,
        "actividad": None,
        "estado_afip": None,
        "empresa_ocde": verificar_cuit_en_lista_ocde(cuit),
        "fuente": None,
    }

    datos_afip = consultar_afip(cuit)
    if datos_afip:
        resultado.update({
            "razon_social": datos_afip["razon_social"],
            "actividad": datos_afip["actividad"],
            "estado_afip": datos_afip["estado"],
            "fuente": datos_afip["fuente"],
        })

    return resultado
