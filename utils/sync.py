"""
utils/sync.py
Revisión semanal de novedades — SOLO INFORMA, no escribe en la base.

Antes este script insertaba en la base de producción todo lo que encontraban
los scrapers: títulos de expedientes del DOJ como si fueran empresas
("U.S. v. Gunvor S.A.: Docket No. ..."), con año 2024 y monto 0, y duplicaba
casos ya cargados (en una copia local agregaba 36 casos falsos). Ahora compara
contra data/ocde_seed.py y lista lo que conviene revisar; la carga sigue
siendo manual, igual que en el cron diario de la app.

Uso:
  python utils/sync.py            # imprime el informe (en Actions queda en el resumen del job)
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.ocde_seed import CASOS_OCDE
from scraper.novedades import detectar_novedades, ANIO_MINIMO

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    nombres = [c["nombre_caso"] for c in CASOS_OCDE] + [c["empresa"]["nombre_matriz"] for c in CASOS_OCDE]
    urls = {r.get("url_fuente") for c in CASOS_OCDE for r in c["resoluciones"] if r.get("url_fuente")}
    novedades = detectar_novedades(nombres, urls)

    lineas = [f"## MEACI — novedades del DOJ (desde {ANIO_MINIMO}) que no están en la base", ""]
    if novedades:
        for n in novedades:
            lineas.append(f"- [{n['anio']}] **{n['empresa']}** — {n['url']}")
        lineas += ["", "Revisar si son casos multijurisdiccionales antes de cargarlos en data/ocde_seed.py."]
    else:
        lineas.append("Sin novedades.")
    texto = "\n".join(lineas)
    print(texto)

    resumen = os.getenv("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write(texto + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
