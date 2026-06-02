"""
Scraper del SFO (Serious Fraud Office) — UK
DPA documents: https://www.sfo.gov.uk/publications/deferred-prosecution-agreements/
Corre incrementalmente — solo agrega resoluciones nuevas.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

SFO_DPA_URL = "https://www.sfo.gov.uk/publications/deferred-prosecution-agreements/"
SFO_BASE = "https://www.sfo.gov.uk"


def obtener_dpas() -> list[dict]:
    """
    Retorna lista de DPAs publicados por el SFO.
    Cada item: {empresa, url, fecha, monto_gbp}
    """
    try:
        resp = httpx.get(SFO_DPA_URL, timeout=30, follow_redirects=True,
                         headers={"User-Agent": "MEACI-Monitor/1.0 (academic research)"})
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[SFO scraper] Error al conectar: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    dpas = []

    for item in soup.select("article, .publication-item, li"):
        link = item.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = SFO_BASE + href
        if "deferred-prosecution" not in href.lower() and "dpa" not in href.lower():
            continue

        texto = link.get_text(strip=True)
        if len(texto) < 4:
            continue

        fecha_tag = item.find(class_=re.compile(r"date|time|published", re.I))
        fecha = fecha_tag.get_text(strip=True) if fecha_tag else ""

        dpas.append({
            "empresa": texto,
            "url": href,
            "fecha": fecha,
            "fuente": "SFO",
        })

    logger.info(f"[SFO scraper] {len(dpas)} DPAs encontrados")
    return dpas


def extraer_monto_dpa(url: str) -> Optional[float]:
    """
    Dado el URL de un DPA del SFO, intenta extraer el monto en GBP.
    Retorna el monto en millones o None.
    """
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True,
                         headers={"User-Agent": "MEACI-Monitor/1.0"})
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[SFO scraper] Error al obtener {url}: {e}")
        return None

    texto = BeautifulSoup(resp.text, "lxml").get_text(" ", strip=True)

    patron = re.search(
        r"£\s?([\d,]+(?:\.\d+)?)\s?(million|billion|m\b|bn\b)",
        texto,
        re.IGNORECASE,
    )
    if not patron:
        return None

    monto_str = patron.group(1).replace(",", "")
    multiplicador = 1000 if "billion" in patron.group(2).lower() or "bn" in patron.group(2).lower() else 1
    try:
        return float(monto_str) * multiplicador
    except ValueError:
        return None


# DPAs conocidos del SFO (referencia estática para seed)
DPAS_SFO_CONOCIDOS = [
    {"empresa": "Rolls-Royce plc", "anio": 2017, "monto_gbp": 497.25,
     "url": "https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-rolls-royce"},
    {"empresa": "Airbus SE", "anio": 2020, "monto_gbp": 990.96,
     "url": "https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-airbus"},
    {"empresa": "Amec Foster Wheeler", "anio": 2021, "monto_gbp": 103.0,
     "url": "https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-amec-foster-wheeler"},
    {"empresa": "Standard Bank PLC", "anio": 2015, "monto_gbp": 16.8,
     "url": "https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-standard-bank"},
    {"empresa": "Glencore Energy UK Ltd", "anio": 2022, "monto_gbp": 276.7,
     "url": "https://www.judiciary.uk/wp-content/uploads/2022/11/Sentencing-Remarks-Glencore.pdf"},
]
