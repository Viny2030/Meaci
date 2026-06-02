from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from contextlib import asynccontextmanager
from typing import Optional
import os
from pathlib import Path

from .models import (
    get_db, crear_tablas, SessionLocal,
    Caso, Empresa, Resolucion, PresenciaAR, Alerta
)


# ── LIFESPAN (reemplaza on_event deprecated) ──────────────────────────────────

def _run_cron():
    """Corre el ciclo diario del MEACI — llamado por APScheduler."""
    import logging
    import json
    log = logging.getLogger("meaci.cron")
    log.info("[cron] Ciclo diario iniciado")

    db = SessionLocal()
    try:
        # 1. Verificar presencia AR (log + preparación para Fase 2)
        from .models import Empresa, Alerta, Resolucion
        empresas_ar = db.query(Empresa).filter(
            Empresa.presencia_argentina == True,
            Empresa.cuits_ar != "[]",
        ).all()
        log.info(f"[cron] {len(empresas_ar)} empresas con CUIT AR verificadas")

        # 2. Generar alertas para empresas sin alerta activa
        nuevas = 0
        for emp in db.query(Empresa).filter(Empresa.presencia_argentina == True).all():
            existe = db.query(Alerta).filter(
                Alerta.empresa_id == emp.id,
                Alerta.plataforma == "contratos_v2",
                Alerta.activa == True,
            ).first()
            if existe:
                continue
            casos = (
                db.query(Caso)
                .join(Resolucion)
                .filter(Resolucion.empresa_id == emp.id)
                .all()
            )
            if not casos:
                continue
            c = casos[0]
            db.add(Alerta(
                empresa_id=emp.id,
                plataforma="contratos_v2",
                tipo_alerta="sancionada_ocde",
                nivel="alta" if (c.monto_total_usd or 0) > 500 else "media",
                descripcion=(
                    f"{emp.nombre_matriz} sancionada en caso {c.nombre_caso} "
                    f"({c.anio_resolucion}) — USD {c.monto_total_usd}M. "
                    f"Filiales AR: {emp.filiales_ar}"
                ),
                datos_extra=json.dumps({
                    "caso_id": c.id,
                    "cuits_ar": emp.cuits_ar,
                    "paises": c.paises,
                }),
            ))
            nuevas += 1

        db.commit()
        log.info(
            f"[cron] Listo — alertas nuevas: {nuevas} | "
            f"total activas: {db.query(Alerta).filter(Alerta.activa == True).count()}"
        )
    except Exception as e:
        db.rollback()
        logging.getLogger("meaci.cron").error(f"[cron] ERROR: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    from apscheduler.schedulers.background import BackgroundScheduler

    # ── Startup ────────────────────────────────────────────────────────────────
    crear_tablas()

    # Seed inicial si la DB está vacía
    db = next(get_db())
    try:
        if db.query(Caso).count() == 0:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from data.ocde_seed import seed
            seed()
    finally:
        db.close()

    # Scheduler diario a las 06:00 hora Argentina
    scheduler = BackgroundScheduler(timezone="America/Argentina/Buenos_Aires")
    scheduler.add_job(
        _run_cron,
        trigger="cron",
        hour=6,
        minute=0,
        id="ciclo_diario",
        replace_existing=True,
    )
    scheduler.start()
    logging.getLogger("meaci").info("[scheduler] Cron diario activo — dispara a las 06:00 AR")

    yield

    # ── Shutdown ────────────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    logging.getLogger("meaci").info("[scheduler] Cron detenido")


app = FastAPI(
    title="MEACI — Monitor de Empresas Argentinas en Casos Internacionales",
    description="Ph.D. Vicente H. Monteverde · Algoritmos contra la Corrupción",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# ── FRONTEND ──────────────────────────────────────────────────────────────────

frontend_path = Path(__file__).parent.parent / "frontend"

@app.get("/", include_in_schema=False)
async def root():
    index = frontend_path / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"mensaje": "MEACI API activa — ver /docs"}


# ── RESUMEN GLOBAL ────────────────────────────────────────────────────────────

@app.get("/api/resumen", tags=["Resumen"])
def resumen(db: Session = Depends(get_db)):
    total_casos       = db.query(Caso).count()
    total_empresas    = db.query(Empresa).count()
    con_presencia_ar  = db.query(Empresa).filter(Empresa.presencia_argentina == True).count()
    total_resoluciones = db.query(Resolucion).count()
    monto_total       = db.query(func.sum(Caso.monto_total_usd)).scalar() or 0
    alertas_activas   = db.query(Alerta).filter(Alerta.activa == True).count()

    return {
        "total_casos": total_casos,
        "total_empresas": total_empresas,
        "con_presencia_argentina": con_presencia_ar,
        "total_resoluciones": total_resoluciones,
        "monto_total_usd_millones": round(monto_total, 1),
        "alertas_activas": alertas_activas,
        "nota": "Monto en USD constantes 2024. Fuente: OCDE 2026.",
    }


# ── CASOS ─────────────────────────────────────────────────────────────────────

@app.get("/api/casos", tags=["Casos"])
def listar_casos(
    anio_desde: Optional[int] = None,
    anio_hasta: Optional[int] = None,
    pais: Optional[str] = None,
    presencia_ar: Optional[bool] = None,
    tipo: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Caso).join(Resolucion, isouter=True).join(Empresa, isouter=True)

    if anio_desde:
        query = query.filter(Caso.anio_resolucion >= anio_desde)
    if anio_hasta:
        query = query.filter(Caso.anio_resolucion <= anio_hasta)
    if pais:
        query = query.filter(Caso.paises.ilike(f"%{pais}%"))
    if tipo:
        query = query.filter(Caso.tipo_resolucion.ilike(f"%{tipo}%"))
    if q:
        query = query.filter(Caso.nombre_caso.ilike(f"%{q}%"))
    if presencia_ar is not None:
        query = query.filter(Empresa.presencia_argentina == presencia_ar)

    casos = query.distinct().all()

    return [_serializar_caso(c, db) for c in casos]


@app.get("/api/casos/{caso_id}", tags=["Casos"])
def detalle_caso(caso_id: int, db: Session = Depends(get_db)):
    caso = db.query(Caso).filter(Caso.id == caso_id).first()
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return _serializar_caso(caso, db, detallado=True)


def _serializar_caso(caso: Caso, db: Session, detallado=False):
    empresa = db.query(Empresa).join(Resolucion).filter(Resolucion.caso_id == caso.id).first()
    data = {
        "id": caso.id,
        "nombre_caso": caso.nombre_caso,
        "anio_resolucion": caso.anio_resolucion,
        "fuente": caso.fuente,
        "monto_total_usd_millones": caso.monto_total_usd,
        "tipo_resolucion": caso.tipo_resolucion,
        "paises": caso.paises,
        "estado": caso.estado,
        "presencia_argentina": empresa.presencia_argentina if empresa else False,
        "filiales_ar": empresa.filiales_ar if empresa else "[]",
    }
    if detallado:
        resoluciones = db.query(Resolucion).filter(Resolucion.caso_id == caso.id).all()
        data["resoluciones"] = [
            {
                "autoridad": r.autoridad,
                "pais": r.pais,
                "tipo": r.tipo,
                "monto_usd_millones": r.monto_usd,
                "anio": r.anio,
                "url_fuente": r.url_fuente,
            }
            for r in resoluciones
        ]
    return data


# ── EMPRESAS ──────────────────────────────────────────────────────────────────

@app.get("/api/empresas", tags=["Empresas"])
def listar_empresas(
    presencia_ar: Optional[bool] = None,
    sector: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Empresa)
    if presencia_ar is not None:
        query = query.filter(Empresa.presencia_argentina == presencia_ar)
    if sector:
        query = query.filter(Empresa.sector.ilike(f"%{sector}%"))
    if q:
        query = query.filter(
            or_(
                Empresa.nombre_matriz.ilike(f"%{q}%"),
                Empresa.filiales_ar.ilike(f"%{q}%"),
            )
        )
    return [_serializar_empresa(e) for e in query.all()]


@app.get("/api/empresas/cuit/{cuit}", tags=["Empresas"])
def empresa_por_cuit(cuit: str, db: Session = Depends(get_db)):
    empresa = db.query(Empresa).filter(Empresa.cuits_ar.ilike(f"%{cuit}%")).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada para ese CUIT")
    return _serializar_empresa(empresa)


def _serializar_empresa(e: Empresa):
    return {
        "id": e.id,
        "nombre_matriz": e.nombre_matriz,
        "pais_sede": e.pais_sede,
        "sector": e.sector,
        "presencia_argentina": e.presencia_argentina,
        "filiales_ar": e.filiales_ar,
        "cuits_ar": e.cuits_ar,
    }


# ── PRESENCIA AR ──────────────────────────────────────────────────────────────

@app.get("/api/presencia-ar", tags=["Presencia Argentina"])
def presencia_argentina(db: Session = Depends(get_db)):
    empresas = db.query(Empresa).filter(Empresa.presencia_argentina == True).all()
    return [
        {
            "empresa": e.nombre_matriz,
            "sector": e.sector,
            "filiales_ar": e.filiales_ar,
            "cuits_ar": e.cuits_ar,
            "presencia": db.query(PresenciaAR).filter(PresenciaAR.empresa_id == e.id).first(),
        }
        for e in empresas
    ]


# ── CRUCE CON COMPR.AR ────────────────────────────────────────────────────────

@app.get("/api/cruce-compr", tags=["Cruces"])
def cruce_comprarg(
    cuit: str = Query(..., description="CUIT a verificar contra lista OCDE"),
    db: Session = Depends(get_db),
):
    """
    Dado un CUIT, verifica si pertenece a una empresa o filial sancionada por OCDE.
    Usar desde Contratos v1, v2 y Monitor Ejecutivo para inyectar el flag.
    """
    empresa = db.query(Empresa).filter(Empresa.cuits_ar.ilike(f"%{cuit}%")).first()
    if not empresa:
        return {"cuit": cuit, "sancionada_ocde": False, "datos": None}

    casos = (
        db.query(Caso)
        .join(Resolucion)
        .filter(Resolucion.empresa_id == empresa.id)
        .all()
    )

    return {
        "cuit": cuit,
        "sancionada_ocde": True,
        "empresa_matriz": empresa.nombre_matriz,
        "pais_sede": empresa.pais_sede,
        "casos": [
            {
                "nombre": c.nombre_caso,
                "anio": c.anio_resolucion,
                "monto_usd_millones": c.monto_total_usd,
                "tipo": c.tipo_resolucion,
                "paises": c.paises,
            }
            for c in casos
        ],
    }


# ── ALERTAS ───────────────────────────────────────────────────────────────────

@app.get("/api/alertas", tags=["Alertas"])
def listar_alertas(
    plataforma: Optional[str] = None,
    nivel: Optional[str] = None,
    activa: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Alerta).filter(Alerta.activa == activa)
    if plataforma:
        query = query.filter(Alerta.plataforma.ilike(f"%{plataforma}%"))
    if nivel:
        query = query.filter(Alerta.nivel == nivel)

    return [
        {
            "id": a.id,
            "empresa": db.query(Empresa).filter(Empresa.id == a.empresa_id).first().nombre_matriz,
            "plataforma": a.plataforma,
            "tipo_alerta": a.tipo_alerta,
            "nivel": a.nivel,
            "descripcion": a.descripcion,
            "fecha_deteccion": a.fecha_deteccion.isoformat() if a.fecha_deteccion else None,
        }
        for a in query.all()
    ]


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────

@app.get("/health", include_in_schema=False)
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "casos": db.query(Caso).count(),
        "empresas": db.query(Empresa).count(),
    }


# ── CRON MANUAL ───────────────────────────────────────────────────────────────

@app.post("/api/cron", tags=["Admin"])
def ejecutar_cron_manual(
    token: str = Query(..., description="REFRESH_TOKEN del .env"),
):
    """
    Dispara el ciclo diario manualmente sin esperar las 06:00.
    Requiere el REFRESH_TOKEN configurado en las variables de entorno.
    """
    import os
    if token != os.getenv("REFRESH_TOKEN", "dev"):
        raise HTTPException(status_code=403, detail="Token inválido")
    try:
        _run_cron()
        return {"status": "ok", "mensaje": "Ciclo diario ejecutado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── STATIC FILES (siempre al final — no interfiere con rutas /api) ────────────

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
