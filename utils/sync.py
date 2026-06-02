"""
utils/sync.py
Corre todos los scrapers y hace upsert en la DB de Railway.
Uso:
  DATABASE_URL=postgresql://... python utils/sync.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import SessionLocal, Caso, Empresa, Resolucion
from scraper.doj import obtener_casos_recientes, extraer_detalle_caso
from scraper.sfo import obtener_dpas, DPAS_SFO_CONOCIDOS
from scraper.pnf import obtener_cjips, CJIPS_PNF_CONOCIDOS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def upsert_empresa(db, nombre: str, pais: str = "", sector: str = "") -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.nombre_matriz == nombre).first()
    if not empresa:
        empresa = Empresa(nombre_matriz=nombre, pais_sede=pais, sector=sector)
        db.add(empresa)
        db.flush()
        logger.info(f"  + Empresa nueva: {nombre}")
    return empresa


def upsert_caso(db, nombre: str, anio: int, fuente: str, tipo: str, monto: float, paises: str) -> Caso:
    caso = db.query(Caso).filter(Caso.nombre_caso == nombre).first()
    if not caso:
        caso = Caso(
            nombre_caso=nombre,
            anio_resolucion=anio,
            fuente=fuente,
            tipo_resolucion=tipo,
            monto_total_usd=monto,
            paises=paises,
        )
        db.add(caso)
        db.flush()
        logger.info(f"  + Caso nuevo: {nombre} ({anio})")
    return caso


def upsert_resolucion(db, caso_id: int, empresa_id: int, autoridad: str,
                      tipo: str, monto: float, anio: int, url: str) -> bool:
    existe = db.query(Resolucion).filter(
        Resolucion.caso_id == caso_id,
        Resolucion.empresa_id == empresa_id,
        Resolucion.autoridad == autoridad,
    ).first()
    if not existe:
        res = Resolucion(
            caso_id=caso_id,
            empresa_id=empresa_id,
            autoridad=autoridad,
            tipo=tipo,
            monto_usd=monto,
            anio=anio,
            url_fuente=url,
        )
        db.add(res)
        return True
    return False


def sync_sfo(db):
    logger.info("=== SFO scraper ===")
    nuevas = 0

    # Primero seed estático conocido
    for item in DPAS_SFO_CONOCIDOS:
        empresa = upsert_empresa(db, item["empresa"], pais="Reino Unido")
        caso = upsert_caso(db, item["empresa"], item["anio"], "SFO", "DPA",
                           item["monto_gbp"] * 1.27, "Reino Unido · Estados Unidos")
        agregado = upsert_resolucion(db, caso.id, empresa.id, "SFO", "DPA",
                                     item["monto_gbp"] * 1.27, item["anio"], item["url"])
        if agregado:
            nuevas += 1

    # Luego scraping dinámico
    for item in obtener_dpas():
        empresa = upsert_empresa(db, item["empresa"], pais="Reino Unido")
        anio = 2024  # fallback si no se puede parsear fecha
        caso = upsert_caso(db, item["empresa"], anio, "SFO", "DPA", 0, "Reino Unido")
        agregado = upsert_resolucion(db, caso.id, empresa.id, "SFO", "DPA", 0, anio, item["url"])
        if agregado:
            nuevas += 1

    db.commit()
    logger.info(f"SFO: {nuevas} resoluciones nuevas")


def sync_pnf(db):
    logger.info("=== PNF scraper ===")
    nuevas = 0

    for item in CJIPS_PNF_CONOCIDOS:
        empresa = upsert_empresa(db, item["empresa"], pais="Francia")
        monto_usd = item["monto_eur"] * 1.08  # EUR → USD aprox
        caso = upsert_caso(db, item["empresa"], item["anio"], "PNF", "CJIP",
                           monto_usd, "Francia · Estados Unidos")
        agregado = upsert_resolucion(db, caso.id, empresa.id, "PNF", "CJIP",
                                     monto_usd, item["anio"], item.get("url", ""))
        if agregado:
            nuevas += 1

    for item in obtener_cjips():
        empresa = upsert_empresa(db, item["empresa"], pais="Francia")
        anio = 2024
        caso = upsert_caso(db, item["empresa"], anio, "PNF", "CJIP", 0, "Francia")
        agregado = upsert_resolucion(db, caso.id, empresa.id, "PNF", "CJIP", 0, anio, item["url"])
        if agregado:
            nuevas += 1

    db.commit()
    logger.info(f"PNF: {nuevas} resoluciones nuevas")


def sync_doj(db):
    logger.info("=== DOJ scraper ===")
    nuevas = 0

    for item in obtener_casos_recientes(limite=30):
        detalle = extraer_detalle_caso(item["url"])
        tipo = detalle["tipo_resolucion"] if detalle else "desconocido"
        monto = 0.0

        empresa = upsert_empresa(db, item["titulo"], pais="Estados Unidos")
        anio = 2024
        caso = upsert_caso(db, item["titulo"], anio, "DOJ", tipo, monto, "Estados Unidos")
        agregado = upsert_resolucion(db, caso.id, empresa.id, "DOJ", tipo, monto, anio, item["url"])
        if agregado:
            nuevas += 1

    db.commit()
    logger.info(f"DOJ: {nuevas} casos nuevos")


def main():
    logger.info("Iniciando sync completo MEACI...")
    db = SessionLocal()
    try:
        sync_sfo(db)
        sync_pnf(db)
        sync_doj(db)
        logger.info("✅ Sync completado")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error en sync: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
