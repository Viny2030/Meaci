import requests
from bs4 import BeautifulSoup
from thefuzz import process
import re, time

nombres_busqueda = [
    ("Airbus SE", "Airbus Argentina"),
    ("Braskem S.A.", "Braskem Argentina"),
    ("Embraer S.A.", "Embraer Argentina"),
    ("Rolls-Royce plc", "Rolls-Royce Argentina"),
    ("Goldman Sachs", "Goldman Sachs Argentina"),
    ("McKinsey", "McKinsey Argentina"),
    ("Teva", "Teva Argentina"),
    ("Honeywell", "Honeywell Argentina"),
    ("Technip", "Technip Argentina"),
    ("Glencore", "Glencore Argentina"),
]

HEADERS = {"User-Agent": "Mozilla/5.0"}


def buscar_cuit_cuitonline(nombre_filial):
    url = f"https://www.cuitonline.com/search.php?q={requests.utils.quote(nombre_filial)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabla = soup.find("table")
        if not tabla:
            return None, None

        resultados = []
        for fila in tabla.find_all("tr")[1:]:
            celdas = [td.get_text(strip=True) for td in fila.find_all("td")]
            if len(celdas) < 2:
                continue
            cuit = next((re.sub(r"\D", "", c) for c in celdas if re.search(r"\d{11}", c)), None)
            if cuit and celdas[0]:
                resultados.append({"nombre": celdas[0], "cuit": cuit})

        if not resultados:
            return None, None

        # Fuzzy match
        nombres = [r["nombre"] for r in resultados]
        mejor, score = process.extractOne(nombre_filial, nombres)
        if score > 70:
            cuit = next(r["cuit"] for r in resultados if r["nombre"] == mejor)
            return cuit, mejor
    except Exception as e:
        print(f"  Error: {e}")
    return None, None


for matriz, filial in nombres_busqueda:
    cuit, nombre_encontrado = buscar_cuit_cuitonline(filial)
    if cuit:
        print(f"✅ {matriz}: {cuit} ({nombre_encontrado})")
    else:
        print(f"❌ {matriz}: no encontrado")
    time.sleep(1.5)