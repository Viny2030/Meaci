"""
Scraper del DOJ — FCPA Press Releases
URL base: https://www.justice.gov/criminal/fraud/fcpa/cases
Corre diariamente via cron. Solo agrega casos nuevos (por URL).
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

DOJ_FCPA_URL = "https://www.justice.gov/criminal/fraud/fcpa/cases"
DOJ_BASE = "https://www.justice.gov"


def obtener_casos_recientes(limite: int = 20) -> list[dict]:
    """
    Retorna lista de casos FCPA recientes desde el portal DOJ.
    Cada item: {titulo, url, fecha, descripcion}
    """
    try:
        resp = httpx.get(DOJ_FCPA_URL, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[DOJ scraper] Error al conectar: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    casos = []

    # El portal DOJ lista los casos en tablas o listas — ajustar según estructura real
    filas = soup.select("table tr, .views-row")
    for fila in filas[:limite]:
        link = fila.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = DOJ_BASE + href
        texto = link.get_text(strip=True)
        if len(texto) < 5:
            continue

        fecha_tag = fila.find(class_=re.compile(r"date|fecha|year", re.I))
        fecha = fecha_tag.get_text(strip=True) if fecha_tag else ""

        casos.append({
            "titulo": texto,
            "url": href,
            "fecha": fecha,
            "fuente": "DOJ",
        })

    logger.info(f"[DOJ scraper] {len(casos)} casos encontrados")
    return casos


def extraer_detalle_caso(url: str) -> Optional[dict]:
    """
    Dado el URL de un press release DOJ, extrae empresa, monto y tipo de resolución.
    Retorna None si no puede parsear.
    """
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[DOJ scraper] Error al obtener {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    texto = soup.get_text(" ", strip=True)

    # Extraer monto con regex
    patron_monto = re.search(
        r"\$\s?([\d,]+(?:\.\d+)?)\s?(million|billion|M|B)",
        texto,
        re.IGNORECASE,
    )
    monto_raw = patron_monto.group(0) if patron_monto else None

    # Detectar tipo de resolución
    tipo = "desconocido"
    for t in ["Deferred Prosecution Agreement", "DPA", "Non-Prosecution Agreement", "NPA",
              "Plea Agreement", "Guilty Plea", "Declination"]:
        if t.lower() in texto.lower():
            tipo = t
            break

    return {
        "url": url,
        "monto_raw": monto_raw,
        "tipo_resolucion": tipo,
        "texto_completo": texto[:2000],  # primeros 2000 chars para NER posterior
    }
