from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./meaci.db")

# Railway entrega postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Caso(Base):
    __tablename__ = "casos"

    id               = Column(Integer, primary_key=True, index=True)
    nombre_caso      = Column(String(200), nullable=False, index=True)
    anio_resolucion  = Column(Integer, index=True)
    fuente           = Column(String(50))          # DOJ / SFO / PNF / OCDE
    monto_total_usd  = Column(Float)               # USD constantes 2024
    tipo_resolucion  = Column(String(100))         # DPA / NPA / Plea / CJIP / Leniency / mix
    paises           = Column(String(300))         # separados por " · "
    estado           = Column(String(30), default="cerrado")  # cerrado / activo / consecutivo
    notas            = Column(Text)
    creado_en        = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    actualizado_en   = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc))

    resoluciones     = relationship("Resolucion", back_populates="caso", cascade="all, delete-orphan")


class Empresa(Base):
    __tablename__ = "empresas"

    id                  = Column(Integer, primary_key=True, index=True)
    nombre_matriz       = Column(String(200), nullable=False, index=True)
    pais_sede           = Column(String(100))
    sector              = Column(String(100))
    presencia_argentina = Column(Boolean, default=False)
    filiales_ar         = Column(Text)             # JSON string con lista de razones sociales
    cuits_ar            = Column(Text)             # JSON string con lista de CUITs
    notas               = Column(Text)
    creado_en           = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resoluciones        = relationship("Resolucion", back_populates="empresa")
    presencia           = relationship("PresenciaAR", back_populates="empresa", uselist=False)
    alertas             = relationship("Alerta", back_populates="empresa")


class Resolucion(Base):
    __tablename__ = "resoluciones"

    id          = Column(Integer, primary_key=True, index=True)
    caso_id     = Column(Integer, ForeignKey("casos.id"), nullable=False)
    empresa_id  = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    autoridad   = Column(String(100))   # DOJ / SEC / SFO / PNF / CGU / etc.
    pais        = Column(String(100))
    tipo        = Column(String(50))    # DPA / NPA / Plea / CJIP / Leniency / C-ADR / etc.
    monto_usd   = Column(Float)
    monto_orig  = Column(Float)         # monto en moneda original
    moneda_orig = Column(String(10))    # USD / GBP / EUR / CHF / BRL
    anio        = Column(Integer)
    url_fuente  = Column(String(500))
    notas       = Column(Text)

    caso        = relationship("Caso", back_populates="resoluciones")
    empresa     = relationship("Empresa", back_populates="resoluciones")


class PresenciaAR(Base):
    __tablename__ = "presencia_ar"

    id                    = Column(Integer, primary_key=True, index=True)
    empresa_id            = Column(Integer, ForeignKey("empresas.id"), unique=True, nullable=False)
    cuit                  = Column(String(20), index=True)
    razon_social_ar       = Column(String(300))
    tipo_vinculo          = Column(String(100))   # filial / sucursal / distribuidor / contratista
    organismos_contratantes = Column(Text)        # JSON string
    monto_contratos_ar    = Column(Float)         # ARS acumulado en COMPR.AR
    contratos_activos     = Column(Integer, default=0)
    ultima_verificacion   = Column(DateTime)
    fuente_verificacion   = Column(String(100))   # AFIP / COMPR.AR / BORA / manual

    empresa               = relationship("Empresa", back_populates="presencia")


class Alerta(Base):
    __tablename__ = "alertas"

    id               = Column(Integer, primary_key=True, index=True)
    empresa_id       = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    plataforma       = Column(String(100))   # contratos_v2 / ejecutivo / iri / senadores
    tipo_alerta      = Column(String(100))   # sancionada_ocde / pep_vinculo / ddjj_conflicto
    nivel            = Column(String(20))    # alta / media / baja
    descripcion      = Column(Text)
    datos_extra      = Column(Text)          # JSON string con detalles del cruce
    activa           = Column(Boolean, default=True)
    fecha_deteccion  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_resolucion = Column(DateTime, nullable=True)

    empresa          = relationship("Empresa", back_populates="alertas")


def crear_tablas():
    Base.metadata.create_all(bind=engine)
