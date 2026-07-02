"""
buscar_cuits_gemini.py
======================
⚠️  DESHABILITADO POR DEFECTO — LEER ANTES DE USAR ⚠️

Este script fue el origen de los CUITs inválidos que estuvieron cargados en
producción hasta 2026-07: le pedía CUITs a Gemini y los escribía directo en
la base de datos SIN validar el dígito verificador de AFIP ni ninguna otra
fuente. Los 15 CUITs que generó fallaban el checksum — o sea, no eran CUITs
reales, eran números con forma de CUIT inventados por el modelo.

Un LLM sin acceso a una fuente de datos real (AFIP, Boletín Oficial,
cuitonline, etc.) no tiene forma de "saber" un CUIT — solo completa el
patrón. Por eso esto NO es una fuente confiable de identificadores fiscales,
por más alta que diga que es su "confianza".

Si en algún momento hace falta buscar CUITs faltantes, la forma correcta es:
  1. Buscar la razón social real de la filial argentina en fuentes públicas
     (Boletín Oficial, cuitonline.com, AFIP).
  2. Validar el CUIT encontrado con el dígito verificador (módulo 11).
  3. Cargarlo a mano en data/ocde_seed.py con una fuente citada.

Este script ahora valida el checksum antes de escribir cualquier cosa (ver
_cuit_valido más abajo) y requiere el flag --escribir-de-todos-modos además
de --dry-run=False para tocar la base, precisamente para que nadie lo corra
sin querer. Aun así, el propio texto que Gemini devuelve sigue sin ser
confiable — este script queda para referencia histórica, no como herramienta
recomendada.

Uso (solo lectura, no escribe nada):
    python buscar_cuits_gemini.py --solo-mostrar

Requisitos:
    pip install requests google-generativeai
    Variable de entorno: GEMINI_API_KEY=tu_clave
    (o crear archivo .env con GEMINI_API_KEY=...)
"""

import argparse
import json
import os
import re
import sys
import time

import requests

# ── Config ─────────────────────────────────────────────────────────────────────

MEACI_API = "https://meaci-production.up.railway.app"
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
PAUSA = 2.0  # segundos entre consultas a Gemini


def _cuit_valido(cuit: str) -> bool:
    """Valida el dígito verificador AFIP (módulo 11). Espera 11 dígitos."""
    if len(cuit) != 11 or not cuit.isdigit():
        return False
    mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    s = sum(int(d) * m for d, m in zip(cuit[:10], mult))
    v = 11 - (s % 11)
    if v == 11:
        v = 0
    if v == 10:
        return False
    return v == int(cuit[10])


# ── 1. Obtener empresas sin CUIT de la API ─────────────────────────────────────

def obtener_sin_cuit() -> list[dict]:
    r = requests.get(f"{MEACI_API}/api/empresas?presencia_ar=true", timeout=15)
    r.raise_for_status()
    empresas = r.json()
    sin_cuit = [
        e for e in empresas
        if not e.get("cuits_ar") or e["cuits_ar"] in ("[]", "", None, [])
    ]
    return sin_cuit


# ── 2. Consultar Gemini ────────────────────────────────────────────────────────

def consultar_gemini(nombre_matriz: str, filiales_ar: str) -> dict | None:
    """
    Pregunta a Gemini el CUIT argentino de la filial de una empresa OCDE.
    Devuelve {"cuit": "XXXXXXXXXXX", "nombre_filial": "...", "confianza": "alta/media"}
    o None si no encuentra.
    """
    if not GEMINI_KEY:
        print("  ⚠️  GEMINI_API_KEY no configurada")
        return None

    prompt = f"""Necesito el CUIT argentino (11 dígitos) de la filial en Argentina de la empresa multinacional "{nombre_matriz}".

Filiales conocidas: {filiales_ar if filiales_ar and filiales_ar != '[]' else 'desconocida'}

Respondé ÚNICAMENTE con un JSON válido, sin texto adicional, sin markdown, sin explicaciones:
{{"cuit": "XXXXXXXXXXX", "nombre_filial": "nombre exacto de la filial AR", "confianza": "alta o media o baja"}}

Si no conocés el CUIT con certeza, respondé:
{{"cuit": null, "nombre_filial": null, "confianza": "baja"}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200}
    }

    try:
        r = requests.post(url, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Limpiar markdown si lo hay
        texto = re.sub(r"```json|```", "", texto).strip()

        resultado = json.loads(texto)
        return resultado
    except json.JSONDecodeError:
        print(f"  ⚠️  Gemini devolvió texto no parseable: {texto[:100]}")
        return None
    except Exception as e:
        print(f"  ⚠️  Error consultando Gemini: {e}")
        return None


# ── 3. Actualizar DB local ─────────────────────────────────────────────────────

def actualizar_db(empresa_id: int, nombre_matriz: str, cuit: str) -> bool:
    """Actualiza cuits_ar en la DB local vía SQLAlchemy."""
    try:
        sys.path.insert(0, ".")
        from api.models import SessionLocal, Empresa

        db = SessionLocal()
        emp = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not emp:
            emp = db.query(Empresa).filter(Empresa.nombre_matriz == nombre_matriz).first()
        if emp:
            emp.cuits_ar = json.dumps([cuit])
            db.commit()
            db.close()
            return True
        db.close()
        return False
    except Exception as e:
        print(f"  ⚠️  Error actualizando DB: {e}")
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Busca CUITs faltantes con Gemini (solo lectura por defecto)")
    parser.add_argument("--dry-run", action="store_true", help="No actualiza DB (default si no se pasa --escribir-de-todos-modos)")
    parser.add_argument("--solo-mostrar", action="store_true", help="Solo lista empresas sin CUIT")
    parser.add_argument(
        "--escribir-de-todos-modos", action="store_true",
        help="Requerido para escribir en la DB. Sin este flag el script SIEMPRE corre en modo dry-run, "
             "aunque hayas encontrado candidatos con checksum válido. Usalo solo después de verificar "
             "cada CUIT a mano contra una fuente pública."
    )
    args = parser.parse_args()
    if not args.escribir_de_todos_modos:
        args.dry_run = True

    print("🔍 MEACI — Buscador de CUITs faltantes\n")

    # Obtener empresas sin CUIT
    try:
        sin_cuit = obtener_sin_cuit()
    except Exception as e:
        print(f"❌ Error conectando a la API MEACI: {e}")
        return

    if not sin_cuit:
        print("✅ Todas las empresas con presencia AR tienen CUIT cargado")
        return

    print(f"📋 {len(sin_cuit)} empresa(s) sin CUIT:\n")
    for e in sin_cuit:
        print(f"  • {e['nombre_matriz']} ({e['pais_sede']}) — filiales: {e['filiales_ar']}")

    if args.solo_mostrar:
        return

    if not GEMINI_KEY:
        print("\n⚠️  Configurá GEMINI_API_KEY para buscar automáticamente:")
        print("   set GEMINI_API_KEY=tu_clave_aqui")
        print("   python buscar_cuits_gemini.py")
        return

    print(f"\n🤖 Consultando Gemini para {len(sin_cuit)} empresa(s)...\n")

    encontrados = []
    no_encontrados = []

    for emp in sin_cuit:
        nombre = emp["nombre_matriz"]
        filiales = emp.get("filiales_ar", "[]")
        print(f"📌 {nombre}")

        resultado = consultar_gemini(nombre, filiales)

        if resultado and resultado.get("cuit") and resultado["confianza"] != "baja":
            cuit = re.sub(r"\D", "", resultado["cuit"])
            filial = resultado.get("nombre_filial", "")
            confianza = resultado.get("confianza", "?")

            if len(cuit) == 11 and _cuit_valido(cuit):
                print(f"   ✅ CUIT con checksum válido: {cuit} | {filial} | confianza declarada: {confianza}")
                print(f"      ⚠️  Esto solo confirma que el número TIENE la forma de un CUIT real.")
                print(f"      ⚠️  NO confirma que sea el CUIT correcto de esta empresa — verificar a mano")
                print(f"      ⚠️  contra cuitonline.com o el Boletín Oficial antes de cargarlo.")
                encontrados.append({
                    "id": emp["id"],
                    "nombre_matriz": nombre,
                    "cuit": cuit,
                    "nombre_filial": filial,
                    "confianza": confianza,
                })
            elif len(cuit) == 11:
                print(f"   ❌ CUIT con dígito verificador INVÁLIDO (no es un CUIT real): {resultado['cuit']}")
                no_encontrados.append(nombre)
            else:
                print(f"   ⚠️  CUIT inválido recibido: {resultado['cuit']}")
                no_encontrados.append(nombre)
        else:
            print(f"   ❌ No encontrado o baja confianza")
            no_encontrados.append(nombre)

        time.sleep(PAUSA)

    # Resumen
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMEN")
    print(f"  Encontrados : {len(encontrados)}")
    print(f"  No encontrados: {len(no_encontrados)}")

    if no_encontrados:
        print(f"\n  ❌ Sin CUIT (revisar manualmente):")
        for n in no_encontrados:
            print(f"     • {n}")

    if not encontrados:
        return

    if args.dry_run:
        print("\n🔍 DRY RUN — no se actualizó la DB")
        print("  CUITs que se agregarían:")
        for e in encontrados:
            print(f"  {e['nombre_matriz']}: {e['cuit']}")
        return

    # Actualizar DB
    print(f"\n💾 Actualizando DB local...")
    actualizados = 0
    for e in encontrados:
        ok = actualizar_db(e["id"], e["nombre_matriz"], e["cuit"])
        status = "✅" if ok else "❌"
        print(f"  {status} {e['nombre_matriz']}: {e['cuit']}")
        if ok:
            actualizados += 1

    print(f"\n✅ {actualizados}/{len(encontrados)} empresas actualizadas en DB")
    print("\n📌 Próximo paso: hacer push para que Railway actualice el frontend")
    print("   git add -A && git commit -m 'feat: CUITs filiales AR actualizados' && git push")


if __name__ == "__main__":
    main()
