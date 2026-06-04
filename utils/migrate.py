"""
utils/migrate.py
Crea todas las tablas en la base de datos configurada en DATABASE_URL.
Uso:
  DATABASE_URL=postgresql://... python utils/migrate.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import Base, engine, DATABASE_URL

def main():
    print(f"Conectando a: {DATABASE_URL[:40]}...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas correctamente:")
        for table in Base.metadata.tables.keys():
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()