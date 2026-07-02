"""
utils/reseed.py
Borra los datos actuales de casos/empresas/resoluciones/presencia_ar/alertas
y vuelve a cargar el seed desde data/ocde_seed.py (con los CUITs verificados).

Uso contra Railway (producción):
  DATABASE_URL="postgresql://usuario:pass@host:puerto/db" python utils/reseed.py

Uso contra Railway sin copiar la URL a mano (recomendado si tenés Railway CLI):
  railway run python utils/reseed.py

Por seguridad, pide confirmación explícita antes de borrar nada.
Usá --si para saltear la confirmación (por ejemplo, en un pipeline no interactivo).
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import SessionLocal, DATABASE_URL, crear_tablas, Alerta, PresenciaAR, Resolucion, Empresa, Caso


def borrar_todo(db):
    """Borra en el orden correcto para respetar las foreign keys."""
    borrados = {}
    for modelo in (Alerta, PresenciaAR, Resolucion, Empresa, Caso):
        n = db.query(modelo).delete()
        borrados[modelo.__tablename__] = n
    db.commit()
    return borrados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--si", action="store_true", help="Salteá la confirmación interactiva")
    args = parser.parse_args()

    print(f"Conectando a: {DATABASE_URL[:40]}...")

    if not args.si:
        print("\n⚠️  Esto va a BORRAR todos los casos, empresas, resoluciones,")
        print("   presencia_ar y alertas de la base conectada arriba, y volver a")
        print("   cargar data/ocde_seed.py (con los CUITs verificados).")
        print("   Esta acción no se puede deshacer.\n")
        resp = input("Escribí 'si' para confirmar: ").strip().lower()
        if resp != "si":
            print("Cancelado. No se modificó nada.")
            sys.exit(0)

    db = SessionLocal()
    try:
        crear_tablas()  # asegura que las tablas existan (no-op si ya están creadas)
        borrados = borrar_todo(db)
        print("✅ Datos anteriores eliminados:")
        for tabla, n in borrados.items():
            print(f"   - {tabla}: {n} filas")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al borrar: {e}")
        sys.exit(1)
    finally:
        db.close()

    try:
        from data.ocde_seed import seed
        seed()
    except Exception as e:
        print(f"❌ Error al re-sembrar: {e}")
        sys.exit(1)

    print("\n✅ Re-siembra completa con los CUITs verificados.")


if __name__ == "__main__":
    main()
