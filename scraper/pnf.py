"""
Scraper del PNF (Parquet National Financier) — Francia
CJIPs publicados: https://www.tribunal-de-paris.justice.fr
Corre incrementalmente — solo agrega resoluciones nuevas.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

PNF_CJIP_URL = "https://www.tribunal-de-paris.justice.fr/75477/pages/parquet-national-financier/cjip-convention-judiciaire-d-interet-public"
PNF_BASE = "https://www.tribunal-de-paris.justice.fr"

HEADERS = {
    "User-Agent": "MEACI-Monitor/1.0 (academic research)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def obtener_cjips() -> list[dict]:
    """
    Retorna lista de CJIPs publicados por el PNF.
    Cada item: {empresa, url, fecha, monto_eur}
    """
    try:
        resp = httpx.get(PNF_CJIP_URL, timeout=30, follow_redirects=True, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[PNF scraper] Error al conectar: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    cjips = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        texto = link.get_text(strip=True)
        if not texto or len(texto) < 4:
            continue
        if "cjip" not in href.lower() and "cjip" not in texto.lower():
            continue
        if not href.startswith("http"):
            href = PNF_BASE + href

        cjips.append({
            "empresa": texto,
            "url": href,
            "fecha": "",
            "fuente": "PNF",
        })

    logger.info(f"[PNF scraper] {len(cjips)} CJIPs encontrados")
    return cjips


def extraer_monto_cjip(url: str) -> Optional[float]:
    """
    Dado el URL de un CJIP del PNF, extrae el monto de la amende d'intérêt public.
    Retorna monto en millones EUR o None.
    """
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[PNF scraper] Error al obtener {url}: {e}")
        return None

    texto = BeautifulSoup(resp.text, "lxml").get_text(" ", strip=True)

    # Formatos: "180 000 000 euros" o "180M€" o "180 millions d'euros"
    patrones = [
        r"([\d\s]+(?:\.\d+)?)\s*(?:millions?\s+d['\"]euros?|M\s*€|M\s*EUR)",
        r"€\s?([\d\s,]+(?:\.\d+)?)\s*(?:million|M\b)",
    ]
    for patron in patrones:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            val = m.group(1).replace(" ", "").replace(",", ".")
            try:
                return float(val)
            except ValueError:
                continue

    return None


# CJIPs conocidos del PNF (referencia estática para seed)
CJIPS_PNF_CONOCIDOS = [
    {"empresa": "Airbus SE", "anio": 2020, "monto_eur": 2083.14,
     "url": "https://www.agence-francaise-anticorruption.gouv.fr/files/files/CJIP%20AIRBUS_English%20version.pdf"},
    {"empresa": "Société Générale S.A.", "anio": 2018, "monto_eur": 292.76,
     "url": "https://www.agence-francaise-anticorruption.gouv.fr/files/files/2018-10/24.05.18_-_CJIP.pdf"},
    {"empresa": "Credit Suisse Securities (Europe) Ltd", "anio": 2022, "monto_eur": 123.0,
     "url": "https://www.tribunal-de-paris.justice.fr/sites/default/files/2022-10/CJIP%20Credit%20Suisse%20sign%C3%A9e%20%202021%20%202022.pdf"},
    {"empresa": "TechnipFMC plc", "anio": 2019, "monto_eur": 0.0,
     "url": ""},
    {"empresa": "Balt SAS", "anio": 2026, "monto_eur": 1.8,
     "url": "https://www.agence-francaise-anticorruption.gouv.fr/files/files/2026-03/CJIP%20BALT.pdf"},
    {"empresa": "Surys", "anio": 2025, "monto_eur": 3.37,
     "url": "https://www.tribunal-de-paris.justice.fr/sites/default/files/2025-09/CJIP.pdf"},
]
