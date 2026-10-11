# MEACI · Monitor de Empresas Argentinas en Casos Internacionales de Corrupción

**Ph.D. Vicente Humberto Monteverde · Algoritmos contra la Corrupción**

Novena plataforma del [Mapa de Transparencia del Estado Argentino](https://mapatransparencia-production.up.railway.app).

---

## Qué es

El MEACI monitorea empresas con presencia en Argentina que han sido sancionadas en casos internacionales de corrupción transnacional (resoluciones multijurisdiccionales — MJRs), basándose en los datos del informe OCDE 2026 *"Sanctioning foreign bribery through multijurisdictional resolutions"*.

**Según la OCDE:** 31 casos MJR · 114 resoluciones · 12 jurisdicciones · más de USD 33.700M en sanciones (USD constantes 2024, dic-2008 a mar-2026).

**Base del MEACI:** los 31 casos con sus resoluciones principales (73 cargadas) y el monto global anunciado de cada caso en USD nominales (suma: USD 24.670,2M). No es comparable con el total de la OCDE, que está en USD constantes 2024 y cuenta las 114 resoluciones.

---

## Estructura del repo

```
meaci/
├── api/
│   ├── main.py          # FastAPI — todos los endpoints
│   └── models.py        # SQLAlchemy — Caso, Empresa, Resolucion, PresenciaAR, Alerta
├── data/
│   └── ocde_seed.py     # Los 31 casos OCDE pre-cargados
├── matcher/
│   └── fuzzy_match.py   # Cruce nombre/CUIT con empresas del Estado
├── scraper/
│   └── doj.py           # Scraper DOJ FCPA press releases (incremental)
├── frontend/
│   └── index.html       # Dashboard
├── cron.py              # Job diario (Railway cron)
├── Procfile
└── requirements.txt
```

---

## Setup local

```bash
git clone https://github.com/Viny2030/meaci
cd meaci
pip install -r requirements.txt
cp .env.example .env
# editar .env con DATABASE_URL

# Iniciar (carga seed automáticamente si la DB está vacía)
uvicorn api.main:app --reload

# O cargar seed manualmente:
python -m data.ocde_seed
```

---

## Producción: base Postgres en Railway

Sin `DATABASE_URL` la app usa SQLite dentro del contenedor y la base se borra en
cada deploy (se vuelve a cargar el seed, pero se pierden las novedades revisadas).
Para que persista:

1. En el proyecto de Railway: **New → Database → PostgreSQL**.
2. En el servicio de MEACI → **Variables**: `DATABASE_URL = ${{Postgres.DATABASE_URL}}`
   y `REFRESH_TOKEN = <una clave propia>`.
3. Al redeployar, la app crea las tablas y carga los 31 casos sola. `GET /health`
   muestra `"base": "postgres"`.

Para marcar una novedad revisada:
`POST /api/novedades/{id}?estado=descartado&token=<REFRESH_TOKEN>` (o `cargado`).

## API

| Endpoint | Descripción |
|---|---|
| `GET /api/resumen` | KPIs globales |
| `GET /api/casos` | Lista de 31 casos MJR (filtrable) |
| `GET /api/casos/{id}` | Detalle con resoluciones |
| `GET /api/empresas` | Empresas sancionadas |
| `GET /api/empresas/cuit/{cuit}` | Buscar por CUIT AR |
| `GET /api/presencia-ar` | Empresas con filiales en Argentina |
| `GET /api/cruce-compr?cuit=XX` | Flag OCDE para inyectar en otros monitores |
| `GET /api/alertas` | Alertas activas por plataforma |
| `GET /docs` | Swagger UI |

---

## Integración con otras plataformas

El endpoint `/api/cruce-compr?cuit={cuit}` está diseñado para ser consumido por:

- **Contratos v2** — agregar flag `sancionada_ocde` en columna riesgo
- **Contratos v1** — idem
- **Monitor Ejecutivo** — Nivel 4 de alerta en cruce de proveedores
- **Monitor IRI** — nueva dimensión `R_Internacional`

---

## Fuentes

- OCDE (2026). *Sanctioning foreign bribery through multijurisdictional resolutions*. OECD Publishing.
- U.S. Department of Justice — FCPA Corporate Enforcement Actions: https://www.justice.gov/criminal/criminal-fraud/corporate-enforcement-actions
- UK Serious Fraud Office — DPA documents: https://www.sfo.gov.uk
- France PNF — CJIP: https://www.tribunal-de-paris.justice.fr
- World Bank Debarment List: https://www.worldbank.org/en/projects-operations/procurement/debarred-firms

---

⚠️ **Aviso:** Herramienta experimental y académica. Los datos provienen de fuentes públicas oficiales. Los resultados son indicadores algorítmicos de riesgo — no implican juicio de valor, acusación ni determinación de responsabilidad. El objetivo es promover la transparencia y el debate informado.

[github.com/Viny2030](https://github.com/Viny2030) · vhmonte@retina.ar
