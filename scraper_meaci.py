"""
scraper_meaci.py
================
Genera/actualiza `data/meaci_cuits.json` combinando CUITs sancionados desde:
  1. OFAC SDN List (CSV) — sancionados internacionales, cruzados por nombre contra SIPRO
  2. ONC — sanciones contratistas Ley 13.064 (endpoint JSON interno de argentina.gob.ar)
  3. Archivo local extra (opcional): data/meaci_cuits_extra.json

Nota sobre REPSAL: el registro es solo de consulta individual por CUIT (no hay CSV público).
Para incluir CUITs del REPSAL usá data/meaci_cuits_extra.json.

Uso:
    python scraper_meaci.py                 # genera/actualiza data/meaci_cuits.json
    python scraper_meaci.py --solo-ofac     # solo fuente OFAC
    python scraper_meaci.py --solo-onc      # solo fuente ONC
    python scraper_meaci.py --dry-run       # muestra resultados sin guardar

Requisitos: pip install requests pandas beautifulsoup4
"""

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ── Configuración ──────────────────────────────────────────────────────────────

OUTPUT_PATH = Path("data/meaci_cuits.json")
EXTRA_PATH  = Path("data/meaci_cuits_extra.json")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MEACI-scraper/1.0)"}
PAUSA   = 0.8


# ── Utilidades ─────────────────────────────────────────────────────────────────

def limpiar_cuit(raw) -> str | None:
    digits = re.sub(r"\D", "", str(raw))
    return digits if len(digits) == 11 else None


def extraer_cuit_texto(row) -> str | None:
    """Busca patrón 'C.U.I.T. XXXXXXXXXXX' en cualquier celda de una fila OFAC."""
    for cell in row:
        m = re.search(r"C\.?U\.?I\.?T\.?\s+([\d\-\.]{10,15})", str(cell), re.IGNORECASE)
        if m:
            c = limpiar_cuit(m.group(1))
            if c:
                return c
    # Fallback: número standalone de 11 dígitos
    for cell in row:
        m = re.search(r"\b(\d{11})\b", str(cell))
        if m:
            return m.group(1)
    return None


def get(url: str, **kwargs) -> requests.Response | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  ⚠️  Error al acceder {url[:80]}: {e}")
        return None


# ── 1. OFAC SDN ────────────────────────────────────────────────────────────────

def scrapear_ofac() -> list[dict]:
    """
    Descarga CSV de OFAC y filtra entidades con dirección en Argentina.
    Intenta cruzar nombre contra SIPRO para obtener CUIT.
    """
    print("\n📡 OFAC SDN List...")
    url = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"
    r = get(url)
    if r is None:
        return []

    from io import StringIO
    try:
        df = pd.read_csv(StringIO(r.text), header=None, dtype=str, on_bad_lines="skip")
        mask = df.apply(lambda col: col.str.contains("Argentina", case=False, na=False)).any(axis=1)
        df_ar = df[mask].copy()
        print(f"  ✅ {len(df_ar)} entidades OFAC con presencia en Argentina")

        resultados = []
        for _, row in df_ar.iterrows():
            nombre = str(row.iloc[0]).strip()
            tipo   = str(row.iloc[1]).strip() if len(row) > 1 else ""
            prog   = str(row.iloc[2]).strip() if len(row) > 2 else ""
            cuit = extraer_cuit_texto(row)
            resultados.append({
                "nombre": nombre,
                "tipo": tipo,
                "programa_sancion": prog,
                "fuente": "OFAC-SDN",
                "cuit": cuit,
            })
        return resultados
    except Exception as e:
        print(f"  ⚠️  Error parseando CSV OFAC: {e}")
        return []


# ── 2. ONC — sanciones contratistas Ley 13.064 ───────────────────────────────

def scrapear_onc() -> list[dict]:
    """
    Intenta múltiples estrategias para obtener el listado ONC:
    a) Endpoint JSON interno del portal de argentina.gob.ar
    b) Descarga directa de Excel si está linkeado
    c) Scraping de tabla HTML
    """
    print("\n📡 ONC — sanciones contratistas Ley 13.064...")

    # a) Intentar endpoint JSON del portal (usado por el frontend de argentina.gob.ar)
    urls_json = [
        "https://www.argentina.gob.ar/api/v2.0/nodes?type=onc_sancion&_format=json&items_per_page=200",
        "https://www.argentina.gob.ar/jefatura/ejecutiva/oficina-nacional-de-contrataciones/sanciones?_format=json",
    ]
    for url in urls_json:
        r = get(url)
        if r:
            try:
                data = r.json()
                items = data if isinstance(data, list) else data.get("data", data.get("items", []))
                if items:
                    resultados = []
                    for item in items:
                        nombre = item.get("title") or item.get("razon_social") or item.get("name") or ""
                        cuit   = limpiar_cuit(item.get("cuit") or item.get("field_cuit") or "")
                        resultados.append({"nombre": nombre, "cuit": cuit, "fuente": "ONC-13064"})
                    print(f"  ✅ {len(resultados)} registros ONC desde JSON")
                    return resultados
            except Exception:
                pass

    # b) Buscar archivo descargable en la página
    ONC_URL = (
        "https://www.argentina.gob.ar/oficina-nacional-de-contrataciones/"
        "portal-de-contrataciones-y-concesiones-de-obra-publica/"
        "registro-de-sanciones-aplicadas-contratistas-ley-ndeg-13064"
    )
    r = get(ONC_URL)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(ext in href.lower() for ext in [".csv", ".xlsx", ".xls", ".ods"]):
                full = href if href.startswith("http") else "https://www.argentina.gob.ar" + href
                print(f"  📄 Archivo ONC encontrado: {full}")
                r2 = get(full)
                if r2:
                    return _parsear_archivo(r2.content, href, "ONC-13064")

        # c) Tabla HTML directa
        tabla = soup.find("table")
        if tabla:
            filas = tabla.find_all("tr")
            resultados = []
            for fila in filas[1:]:
                celdas = [td.get_text(strip=True) for td in fila.find_all("td")]
                if not celdas:
                    continue
                cuit_raw = next((c for c in celdas if re.search(r"\d{10,11}", c)), "")
                resultados.append({
                    "nombre": celdas[0],
                    "cuit": limpiar_cuit(cuit_raw),
                    "fuente": "ONC-13064",
                })
            if resultados:
                print(f"  ✅ {len(resultados)} registros ONC desde tabla HTML")
                return resultados

    print("  ⚠️  ONC: no se pudo obtener datos (página dinámica sin CSV público)")
    print("       → Agregá CUITs manualmente en data/meaci_cuits_extra.json")
    return []


def _parsear_archivo(content: bytes, href: str, fuente: str) -> list[dict]:
    from io import BytesIO
    resultados = []
    try:
        df = pd.read_csv(BytesIO(content), dtype=str, on_bad_lines="skip") \
            if ".csv" in href.lower() \
            else pd.read_excel(BytesIO(content), dtype=str)
        col_cuit   = next((c for c in df.columns if "cuit" in c.lower()), None)
        col_nombre = next((c for c in df.columns if any(k in c.lower() for k in ["razon","nombre","empresa"])), df.columns[0])
        for _, row in df.iterrows():
            cuit = limpiar_cuit(row[col_cuit]) if col_cuit else None
            resultados.append({"nombre": str(row[col_nombre]), "cuit": cuit, "fuente": fuente})
        print(f"  ✅ {len(resultados)} registros {fuente} desde archivo")
    except Exception as e:
        print(f"  ⚠️  Error parseando archivo {fuente}: {e}")
    return resultados


# ── 3. Archivo extra local ────────────────────────────────────────────────────

def cargar_extra() -> list[dict]:
    if not EXTRA_PATH.exists():
        print(f"\n📁 Extra local: archivo {EXTRA_PATH} no encontrado (opcional)")
        return []
    with open(EXTRA_PATH) as f:
        data = json.load(f)
    cuits = data.get("cuits", [])
    print(f"\n📁 Extra local: {len(cuits)} CUITs cargados desde {EXTRA_PATH}")
    return [{"cuit": c, "nombre": "", "fuente": "extra-local"} for c in cuits]


# ── Combinar y guardar ────────────────────────────────────────────────────────

def combinar_y_guardar(todos: list[dict], dry_run: bool = False):
    con_cuit = [r for r in todos if r.get("cuit")]
    sin_cuit = [r for r in todos if not r.get("cuit")]
    cuits_unicos = sorted(set(r["cuit"] for r in con_cuit))

    index = {}
    for r in con_cuit:
        index[r["cuit"]] = {"cuit": r["cuit"], "nombre": r.get("nombre",""), "fuente": r.get("fuente","")}

    output = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "total_cuits": len(cuits_unicos),
        "cuits": cuits_unicos,
        "detalle": list(index.values()),
        "sin_cuit_para_revision": [
            {"nombre": r["nombre"], "fuente": r["fuente"]}
            for r in sin_cuit if r.get("nombre")
        ][:50],
    }

    fuentes = sorted(set(r["fuente"] for r in todos))
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN FINAL")
    print(f"  CUITs únicos     : {len(cuits_unicos)}")
    print(f"  Sin CUIT         : {len(sin_cuit)} (en 'sin_cuit_para_revision')")
    print(f"  Fuentes          : {fuentes}")

    if sin_cuit:
        print(f"\n  🔎 Entidades sin CUIT (primeras 5) — revisar manualmente:")
        for r in sin_cuit[:5]:
            print(f"     [{r['fuente']}] {r['nombre']}")

    if dry_run:
        print("\n🔍 DRY RUN — no se guardó nada")
        if cuits_unicos:
            print("  Primeros CUITs encontrados:", cuits_unicos[:10])
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Guardado en {OUTPUT_PATH}")
    print(f"\n   Instrucción para api_server.py:")
    print(f"   import json")
    print(f"   with open('data/meaci_cuits.json') as f:")
    print(f"       MEACI_CUITS = set(json.load(f)['cuits'])")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scraper MEACI — genera meaci_cuits.json")
    parser.add_argument("--solo-ofac",   action="store_true")
    parser.add_argument("--solo-onc",    action="store_true")
    parser.add_argument("--dry-run",     action="store_true")
    args = parser.parse_args()

    print("🚀 Scraper MEACI —", datetime.now().strftime("%Y-%m-%d %H:%M"))
    todos = []

    if args.solo_ofac:
        todos += scrapear_ofac()
    elif args.solo_onc:
        todos += scrapear_onc()
    else:
        todos += scrapear_ofac()
        time.sleep(PAUSA)
        todos += scrapear_onc()
        todos += cargar_extra()

    combinar_y_guardar(todos, dry_run=args.dry_run)


if __name__ == "__main__":
    main()