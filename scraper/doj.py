"""
Scraper del DOJ — FCPA Corporate Enforcement Actions
URL base: https://www.justice.gov/criminal/criminal-fraud/corporate-enforcement-actions
Corre diariamente via cron. Solo agrega casos nuevos (por URL).

Nota (2026-07): la URL anterior (/criminal/fraud/fcpa/cases) da 404 — el DOJ
reorganizó el sitio. Esta es la URL vigente verificada. Si vuelve a devolver
404 en el futuro, revisar https://www.justice.gov/criminal/criminal-fraud/enforcement-actions
para encontrar el nuevo destino antes de asumir que el scraper "no encontró casos".
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

DOJ_FCPA_URL = "https://www.justice.gov/criminal/criminal-fraud/corporate-enforcement-actions"
DOJ_BASE = "https://www.justice.gov"


def obtener_casos_recientes(limite: int = 20) -> list[dict]:
    """
    Retorna lista de casos FCPA corporativos desde el portal DOJ, ordenados
    por año descendente (los más recientes primero).
    Cada item: {titulo, url, fecha, descripcion}
    """
    try:
        resp = httpx.get(DOJ_FCPA_URL, timeout=30, follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"[DOJ scraper] Error al conectar: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    casos = []

    # La página lista cada caso como <p><a href="...">Título</a>, AÑO</p>
    for p in soup.select("p"):
        link = p.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = DOJ_BASE + href
        texto = link.get_text(strip=True)
        if len(texto) < 5:
            continue

        resto = p.get_text(" ", strip=True).replace(texto, "", 1)
        anio_match = re.search(r"(19|20)\d{2}", resto)
        anio = anio_match.group(0) if anio_match else ""

        casos.append({
            "titulo": texto,
            "url": href,
            "fecha": anio,
            "fuente": "DOJ",
        })

    # Ordenar por año descendente (los sin año conocido quedan al final)
    casos.sort(key=lambda c: int(c["fecha"]) if c["fecha"] else 0, reverse=True)

    logger.info(f"[DOJ scraper] {len(casos)} casos encontrados en total")
    return casos[:limite]


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
