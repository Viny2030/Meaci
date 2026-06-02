"""
Cron diario del MEACI.
En Railway: configurar como worker o usar APScheduler dentro de la misma app.
También puede ejecutarse manualmente: python cron.py
"""
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="America/Argentina/Buenos_Aires")


def job_verificar_presencia_ar():
    """
    Para cada empresa con presencia_argentina=True que tenga CUITs conocidos,
    consulta la API de COMPR.AR y actualiza contratos_activos.
    Fase 1: solo log. Fase 2: escritura en DB.
    """
    logger.info("[cron] Verificando presencia AR...")
    from api.models import SessionLocal, Empresa, PresenciaAR
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        empresas = db.query(Empresa).filter(
            Empresa.presencia_argentina == True,
            Empresa.cuits_ar != "[]",
        ).all()
        logger.info(f"[cron] {len(empresas)} empresas con CUIT AR para verificar")
        for emp in empresas:
            logger.info(f"  → {emp.nombre_matriz} | CUITs: {emp.cuits_ar}")
        # TODO Fase 2: llamar a API de COMPR.AR por cada CUIT y actualizar PresenciaAR
    finally:
        db.close()


def job_generar_alertas():
    """
    Para cada empresa con presencia AR confirmada, genera una alerta en la tabla alertas
    si no existe ya una activa del mismo tipo.
    """
    logger.info("[cron] Generando alertas OCDE...")
    from api.models import SessionLocal, Empresa, Alerta, Resolucion, Caso
    import json

    db = SessionLocal()
    try:
        empresas = db.query(Empresa).filter(Empresa.presencia_argentina == True).all()
        nuevas = 0
        for emp in empresas:
            # Verificar si ya existe alerta activa para contratos_v2
            existe = db.query(Alerta).filter(
                Alerta.empresa_id == emp.id,
                Alerta.plataforma == "contratos_v2",
                Alerta.activa == True,
            ).first()

            if not existe:
                casos = (
                    db.query(Caso)
                    .join(Resolucion)
                    .filter(Resolucion.empresa_id == emp.id)
                    .all()
                )
                if casos:
                    caso_ref = casos[0]
                    alerta = Alerta(
                        empresa_id=emp.id,
                        plataforma="contratos_v2",
                        tipo_alerta="sancionada_ocde",
                        nivel="alta" if caso_ref.monto_total_usd and caso_ref.monto_total_usd > 500 else "media",
                        descripcion=(
                            f"{emp.nombre_matriz} sancionada en caso {caso_ref.nombre_caso} "
                            f"({caso_ref.anio_resolucion}) — USD {caso_ref.monto_total_usd}M. "
                            f"Filiales AR: {emp.filiales_ar}"
                        ),
                        datos_extra=json.dumps({
                            "caso_id": caso_ref.id,
                            "cuits_ar": emp.cuits_ar,
                            "paises": caso_ref.paises,
                        }),
                    )
                    db.add(alerta)
                    nuevas += 1

        db.commit()
        logger.info(f"[cron] {nuevas} alertas nuevas generadas")
    finally:
        db.close()


def job_resumen():
    from api.models import SessionLocal, Caso, Empresa, Alerta
    db = SessionLocal()
    try:
        logger.info(
            f"[cron] Resumen — Casos: {db.query(Caso).count()} | "
            f"Empresas: {db.query(Empresa).count()} | "
            f"Alertas activas: {db.query(Alerta).filter(Alerta.activa==True).count()}"
        )
    finally:
        db.close()


# ── Programación ──────────────────────────────────────────────────────────────

@scheduler.scheduled_job("cron", hour=6, minute=0)
def ciclo_diario():
    logger.info(f"[cron] Ciclo diario iniciado — {datetime.now(timezone.utc).isoformat()}")
    job_verificar_presencia_ar()
    job_generar_alertas()
    job_resumen()


if __name__ == "__main__":
    # Ejecutar una vez inmediatamente y luego según schedule
    logger.info("[cron] Ejecución manual iniciada")
    ciclo_diario()
    # Descomentar para modo daemon:
    # scheduler.start()
