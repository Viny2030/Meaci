"""
scraper_cuits_filiales.py
=========================
Busca los CUITs de las filiales argentinas de empresas MEACI
usando cuitonline.com y la API pública de AFIP.

Resultado: genera data/meaci_cuits_extra.json con los CUITs encontrados
para que scraper_meaci.py los sume al siguiente ciclo.

Uso:
    python scraper_cuits_filiales.py
    python scraper_cuits_filiales.py --dry-run

Requisitos: pip install requests beautifulsoup4
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Filiales argentinas conocidas ──────────────────────────────────────────────
# (empresa_matriz, nombre_filial_ar, cuit_conocido_o_None)
FILIALES = [
    ("Siemens AG",                          "Siemens S.A. Argentina",                   "30546675813"),
    ("ABB Ltd",                             "ABB S.A. Argentina",                        "30576558683"),
    ("Odebrecht S.A.",                      "CNO S.A. (ex Constructora Norberto Odebrecht)", "30708817331"),
    ("SAP SE",                              "SAP Argentina S.A.",                        "30691426657"),
    # Sin CUIT — hay que buscar:
    ("Airbus SE",                           "Airbus Argentina SRL",                      None),
    ("Braskem S.A.",                        "Braskem Idesa Argentina",                   None),
    ("Embraer S.A.",                        "Embraer Argentina",                         None),
    ("Rolls-Royce plc",                     "Rolls-Royce Energy Systems Argentina",      None),
    ("Goldman Sachs Group Inc.",            "Goldman Sachs Argentina LLC",               None),
    ("McKinsey & Co Inc.",                  "McKinsey and Company Argentina",            None),
    ("Teva Pharmaceutical Industries Ltd.", "Teva Argentina S.A.",                       None),
    ("Honeywell International Inc.",        "Honeywell Argentina S.R.L.",                None),
    ("Credit Suisse Group AG",              "Credit Suisse AG Sucursal Argentina",       None),
    ("TechnipFMC plc",                      "Technip Argentina S.A.",                    None),
    ("Glencore International AG",           "Glencore Argentina S.A.",                   None),
]

OUTPUT_EXTRA = Path("data/meaci_cuits_extra.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
PAUSA = 1.5


# ── Fuente 1: AFIP SOA público ─────────────────────────────────────────────────

def buscar_afip_por_cuit(cuit: str) -> dict | None:
    """Valida un CUIT conocido contra AFIP SOA."""
    digits = re.sub(r"\D", "", cuit)
    url = f"https://soa.afip.gob.ar/sr-padron/v2/persona/{digits}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return {
                "cuit": digits,
                "nombre": data.get("razonSocial") or
                          f"{data.get('nombre','')} {data.get('apellido','')}".strip(),
                "fuente": "AFIP-SOA",
            }
    except Exception as e:
        print(f"    AFIP error: {e}")
    return None


# ── Fuente 2: cuitonline.com ───────────────────────────────────────────────────

def buscar_cuitonline(nombre: str) -> list[dict]:
    """Busca por nombre en cuitonline.com y devuelve lista de coincidencias."""
    url = f"https://www.cuitonline.com/search.php?q={requests.utils.quote(nombre)}"
    resultados = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")

        # Los resultados están en tabla con clase "table"
        tabla = soup.find("table", {"class": "table"})
        if not tabla:
            # Intentar buscar cualquier tabla
            tabla = soup.find("table")
        if not tabla:
            return []

        for fila in tabla.find_all("tr")[1:]:  # saltar header
            celdas = [td.get_text(strip=True) for td in fila.find_all("td")]
            if len(celdas) < 2:
                continue
            # Buscar CUIT (11 dígitos) en cualquier celda
            cuit = None
            for c in celdas:
                m = re.search(r"\b(\d{2}-\d{8}-\d|\d{11})\b", c)
                if m:
                    cuit = re.sub(r"\D", "", m.group(1))
                    break
            nombre_res = celdas[0] if celdas else ""
            if cuit:
                resultados.append({
                    "cuit": cuit,
                    "nombre": nombre_res,
                    "fuente": "cuitonline",
                })
        return resultados[:3]  # máximo 3 resultados por búsqueda
    except Exception as e:
        print(f"    cuitonline error: {e}")
        return []


# ── Fuente 3: API pública argentina datos.gob.ar ──────────────────────────────

def buscar_en_comprar(nombre: str) -> str | None:
    """Busca en el dataset de adjudicaciones de comprar.ar por nombre de proveedor."""
    # Dataset de adjudicaciones con CUIT
    resource_ids = [
        "a4b60b28-5b28-4c9e-87c3-1a6b3db70a07",  # adjudicaciones recientes
        "301b8c68-ebcc-4598-95f9-38dfa6e554af",  # proveedores SIPRO
    ]
    for rid in resource_ids:
        url = f"https://datos.gob.ar/api/3/action/datastore_search?resource_id={rid}&q={requests.utils.quote(nombre)}&limit=3"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                recs = data.get("result", {}).get("records", [])
                for rec in recs:
                    # Buscar columna CUIT
                    for k, v in rec.items():
                        if "cuit" in k.lower() and v:
                            digits = re.sub(r"\D", "", str(v))
                            if len(digits) == 11:
                                return digits
        except Exception:
            pass
    return None


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("🔍 Buscando CUITs de filiales argentinas MEACI\n")

    encontrados = {}
    ya_conocidos = {}

    for matriz, filial, cuit_conocido in FILIALES:
        print(f"📌 {filial}")

        if cuit_conocido:
            # Validar CUIT conocido contra AFIP
            digits = re.sub(r"\D", "", cuit_conocido)
            info = buscar_afip_por_cuit(digits)
            if info:
                print(f"   ✅ Confirmado por AFIP: {digits} ({info['nombre']})")
                ya_conocidos[matriz] = {"cuit": digits, "nombre_filial": filial, "nombre_afip": info["nombre"]}
            else:
                print(f"   ⚠️  CUIT conocido {digits} no confirmado por AFIP (puede ser error de red)")
                ya_conocidos[matriz] = {"cuit": digits, "nombre_filial": filial, "nombre_afip": ""}
            time.sleep(PAUSA)
            continue

        # Buscar en cuitonline
        resultados = buscar_cuitonline(filial)
        if resultados:
            print(f"   🌐 cuitonline: {len(resultados)} resultado(s)")
            for res in resultados:
                print(f"      CUIT {res['cuit']} | {res['nombre']}")
            # Tomar el primero como candidato
            encontrados[matriz] = {
                "cuit": resultados[0]["cuit"],
                "nombre_filial": filial,
                "nombre_encontrado": resultados[0]["nombre"],
                "fuente": "cuitonline",
            }
        else:
            # Intentar en comprar.ar
            cuit_comprar = buscar_en_comprar(filial.split(" ")[0])  # primera palabra
            if cuit_comprar:
                print(f"   📦 comprar.ar: {cuit_comprar}")
                encontrados[matriz] = {
                    "cuit": cuit_comprar,
                    "nombre_filial": filial,
                    "fuente": "comprar.ar",
                }
            else:
                print(f"   ❌ No encontrado — revisar manualmente")

        time.sleep(PAUSA)

    # ── Resumen ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN")
    print(f"  Ya conocidos (validados): {len(ya_conocidos)}")
    print(f"  Nuevos encontrados:       {len(encontrados)}")
    print(f"  Sin CUIT:                 {len(FILIALES) - len(ya_conocidos) - len(encontrados)}")

    todos_cuits = (
        [v["cuit"] for v in ya_conocidos.values()] +
        [v["cuit"] for v in encontrados.values()]
    )
    todos_cuits = sorted(set(todos_cuits))

    if encontrados:
        print(f"\n  🆕 CUITs nuevos a agregar:")
        for m, v in encontrados.items():
            print(f"     {m}: {v['cuit']} ({v['nombre_filial']})")

    if args.dry_run:
        print("\n🔍 DRY RUN — no se guardó nada")
        return

    # Guardar en meaci_cuits_extra.json para que scraper_meaci.py los sume
    OUTPUT_EXTRA.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "descripcion": "CUITs de filiales argentinas de empresas MEACI/OCDE",
        "cuits": todos_cuits,
        "detalle": {
            **{m: v for m, v in ya_conocidos.items()},
            **{m: v for m, v in encontrados.items()},
        }
    }
    with open(OUTPUT_EXTRA, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Guardado en {OUTPUT_EXTRA}")
    print(f"   → Ahora corré: python scraper_meaci.py")
    print(f"      para regenerar data/meaci_cuits.json con todos los CUITs")


if __name__ == "__main__":
    main()