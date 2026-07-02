"""
Seed inicial con los 31 casos MJR del informe OCDE 2026
"Sanctioning foreign bribery through multijurisdictional resolutions"
Datos extraídos de Annex C (Table A C.1) y tablas del cuerpo del informe.
Ejecutar una sola vez: python -m data.ocde_seed
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import SessionLocal, crear_tablas, Caso, Empresa, Resolucion


# ── DATOS MAESTROS ────────────────────────────────────────────────────────────

CASOS_OCDE = [
    {
        "nombre_caso": "Siemens AG",
        "anio_resolucion": 2008,
        "fuente": "DOJ/SEC/Munich",
        "monto_total_usd": 1600,
        "tipo_resolucion": "Plea+OWiG+SEC Injunction",
        "paises": "Estados Unidos · Alemania · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Siemens AG",
            "pais_sede": "Alemania",
            "sector": "Tecnología industrial",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Siemens S.A."]),
            "cuits_ar": json.dumps(["33716578939"]),  # verificado cuitonline/BORA 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":448.5,"anio":2008,"url_fuente":"https://www.justice.gov/sites/default/files/criminal-fraud/legacy/2013/05/02/12-15-08siemensakt-plea.pdf"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Civil Injunction","monto_usd":350.0,"anio":2008,"url_fuente":"https://www.sec.gov/files/litigation/complaints/2008/comp20829.pdf"},
            {"autoridad":"Munich Public Prosecutor","pais":"Alemania","tipo":"OWiG Fine","monto_usd":800.0,"anio":2008,"url_fuente":"https://assets.new.siemens.com/siemens/assets/api/uuid:0d6eee47-5b44-4ad6-bd5d-34de580085ae/MucStaats.pdf"},
        ]
    },
    {
        "nombre_caso": "ABB Ltd",
        "anio_resolucion": 2022,
        "fuente": "DOJ/SEC/OAG/NPA-ZA",
        "monto_total_usd": 315,
        "tipo_resolucion": "DPA+Plea+C-Settlement+Summary Penalty",
        "paises": "Estados Unidos · Sudáfrica · Suiza · Alemania",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "ABB Ltd",
            "pais_sede": "Suiza",
            "sector": "Tecnología eléctrica",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["ABB S.A.U."]),
            "cuits_ar": json.dumps(["30503948164"]),  # verificado BORA 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":315.0,"anio":2022,"url_fuente":"https://www.justice.gov/criminal/media/1263851/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":72.5,"anio":2022,"url_fuente":"https://www.sec.gov/files/litigation/admin/2022/34-96444.pdf"},
            {"autoridad":"South Africa NPA","pais":"Sudáfrica","tipo":"Comprehensive Settlement","monto_usd":57.5,"anio":2022,"url_fuente":"https://www.npa.gov.za/media/step-towards-accountability-state-capture-corruption-eskom-abb-pay-over-r25-billion-punitive"},
            {"autoridad":"Swiss OAG","pais":"Suiza","tipo":"Summary Penalty","monto_usd":4.0,"anio":2022,"url_fuente":"https://www.news.admin.ch/en/nsb?id=92020"},
        ]
    },
    {
        "nombre_caso": "Airbus SE",
        "anio_resolucion": 2020,
        "fuente": "DOJ/SFO/PNF",
        "monto_total_usd": 3900,
        "tipo_resolucion": "DPA+DPA+CJIP",
        "paises": "Estados Unidos · Reino Unido · Francia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Airbus SE",
            "pais_sede": "Países Bajos / Francia",
            "sector": "Aeronáutica y defensa",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Airbus Argentina S.A."]),
            "cuits_ar": json.dumps(["30716262762"]),  # verificado cuitonline 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":2083.1,"anio":2020,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1242051/dl?inline"},
            {"autoridad":"UK SFO","pais":"Reino Unido","tipo":"DPA","monto_usd":1092.0,"anio":2020,"url_fuente":"https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-airbus"},
            {"autoridad":"France PNF","pais":"Francia","tipo":"CJIP","monto_usd":724.9,"anio":2020,"url_fuente":"https://www.agence-francaise-anticorruption.gouv.fr/files/files/CJIP%20AIRBUS_English%20version.pdf"},
        ]
    },
    {
        "nombre_caso": "Odebrecht S.A.",
        "anio_resolucion": 2016,
        "fuente": "DOJ/CGU/OAG",
        "monto_total_usd": 4500,
        "tipo_resolucion": "Plea+Leniency+Summary Penalty",
        "paises": "Estados Unidos · Brasil · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Odebrecht S.A.",
            "pais_sede": "Brasil",
            "sector": "Construcción e ingeniería",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["CNO S.A. (ex Constructora Norberto Odebrecht)"]),
            "cuits_ar": json.dumps(["30630692373"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":2600.0,"anio":2016,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/920101/dl?inline"},
            {"autoridad":"Brazil CGU/AGU","pais":"Brasil","tipo":"Leniency Agreement","monto_usd":1800.0,"anio":2016,"url_fuente":"https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/acordo-leniencia/acordos-firmados/AcordoOdebrecht.pdf"},
            {"autoridad":"Swiss OAG","pais":"Suiza","tipo":"Summary Penalty","monto_usd":117.0,"anio":2016,"url_fuente":"https://www.admin.ch/en/nsb?id=65077"},
        ]
    },
    {
        "nombre_caso": "Braskem S.A.",
        "anio_resolucion": 2016,
        "fuente": "DOJ/SEC/CGU",
        "monto_total_usd": 957,
        "tipo_resolucion": "Plea+Civil+Leniency+Summary Penalty",
        "paises": "Estados Unidos · Brasil · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Braskem S.A.",
            "pais_sede": "Brasil",
            "sector": "Petroquímica",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Braskem Argentina S.A."]),
            "cuits_ar": json.dumps(["30691215446"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":632.6,"anio":2016,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/920091/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Civil Resolution","monto_usd":65.0,"anio":2016,"url_fuente":"https://www.sec.gov/files/litigation/complaints/2016/comp-pr2016-271.pdf"},
            {"autoridad":"Brazil CGU","pais":"Brasil","tipo":"Leniency Agreement","monto_usd":260.0,"anio":2016,"url_fuente":"https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/acordo-leniencia/acordos-firmados/AcordoBRASKEMS.A.pdf"},
        ]
    },
    {
        "nombre_caso": "Embraer S.A.",
        "anio_resolucion": 2016,
        "fuente": "DOJ/SEC/CVM",
        "monto_total_usd": 205,
        "tipo_resolucion": "DPA+Admin Settlement",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Embraer S.A.",
            "pais_sede": "Brasil",
            "sector": "Aeronáutica",
            "presencia_argentina": True,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),  # sin filial verificable en fuentes públicas — pendiente
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":107.0,"anio":2016,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/904636/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Civil Complaint","monto_usd":98.0,"anio":2016,"url_fuente":"https://www.sec.gov/files/litigation/complaints/2016/comp-pr2016-224.pdf"},
        ]
    },
    {
        "nombre_caso": "Rolls-Royce plc",
        "anio_resolucion": 2017,
        "fuente": "DOJ/SFO/CGU",
        "monto_total_usd": 800,
        "tipo_resolucion": "DPA+DPA+Leniency",
        "paises": "Estados Unidos · Reino Unido · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Rolls-Royce plc",
            "pais_sede": "Reino Unido",
            "sector": "Motores y defensa",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["MTU Detroit Diesel-Allison Argentina S.A."]),
            "cuits_ar": json.dumps(["30708587482"]),  # unidad Power Systems de Rolls-Royce, verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"UK SFO","pais":"Reino Unido","tipo":"DPA","monto_usd":497.0,"anio":2017,"url_fuente":"https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-rolls-royce"},
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":169.9,"anio":2017,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/929126/dl?inline"},
            {"autoridad":"Brazil CGU/AGU","pais":"Brasil","tipo":"Leniency Agreement","monto_usd":25.6,"anio":2017,"url_fuente":"https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/acordo-leniencia/acordos-firmados/AcordoRollsRoycePLC.pdf"},
        ]
    },
    {
        "nombre_caso": "Goldman Sachs",
        "anio_resolucion": 2020,
        "fuente": "DOJ/SEC/FCA/PRA/AGC/SFC",
        "monto_total_usd": 2900,
        "tipo_resolucion": "DPA+Plea+NPA+Final Notice+Disciplinary",
        "paises": "Estados Unidos · Reino Unido · Singapur · Hong Kong (China) · Malasia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Goldman Sachs Group Inc.",
            "pais_sede": "Estados Unidos",
            "sector": "Banca de inversión",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Goldman Sachs Argentina LLC Suc. Arg."]),
            "cuits_ar": json.dumps(["30680753543"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":2315.0,"anio":2020,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1329926/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":606.0,"anio":2020,"url_fuente":"https://www.sec.gov/files/litigation/admin/2020/34-90243.pdf"},
            {"autoridad":"UK FCA","pais":"Reino Unido","tipo":"Final Notice","monto_usd":96.6,"anio":2020,"url_fuente":"https://www.fca.org.uk/publication/final-notices/gsi-2020.pdf"},
            {"autoridad":"Singapore AGC","pais":"Singapur","tipo":"Conditional Warning (NPA-like)","monto_usd":122.0,"anio":2020,"url_fuente":"https://www.mas.gov.sg/news/media-releases/2020/agc-cad-and-mas-take-action-against-goldman-sachs-singapore-pte-on-1mdb-bond-offerings"},
        ]
    },
    {
        "nombre_caso": "SAP SE",
        "anio_resolucion": 2024,
        "fuente": "DOJ/SEC/NPA-ZA",
        "monto_total_usd": 220,
        "tipo_resolucion": "DPA+Cease-and-Desist+C-ADR",
        "paises": "Estados Unidos · Sudáfrica",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "SAP SE",
            "pais_sede": "Alemania",
            "sector": "Software empresarial",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["SAP Argentina S.A."]),
            "cuits_ar": json.dumps(["30685163701"]),  # verificado cuitonline/BORA 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":118.8,"anio":2024,"url_fuente":"https://www.justice.gov/criminal/media/1333316/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":85.0,"anio":2024,"url_fuente":"https://www.sec.gov/files/litigation/admin/2024/34-99308.pdf"},
            {"autoridad":"South Africa NPA","pais":"Sudáfrica","tipo":"C-ADR","monto_usd":16.2,"anio":2024,"url_fuente":"https://www.npa.gov.za/sites/default/files/uploads/SAP%20Summary.pdf"},
        ]
    },
    {
        "nombre_caso": "McKinsey Africa",
        "anio_resolucion": 2024,
        "fuente": "DOJ/NPA-ZA",
        "monto_total_usd": 122.9,
        "tipo_resolucion": "DPA+C-ADR",
        "paises": "Estados Unidos · Sudáfrica",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "McKinsey & Co Inc.",
            "pais_sede": "Estados Unidos",
            "sector": "Consultoría de gestión",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["McKinsey Argentina SRL"]),
            "cuits_ar": json.dumps(["30708724811"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":122.9,"anio":2024,"url_fuente":"https://www.justice.gov/criminal/media/1379476/dl?inline"},
            {"autoridad":"South Africa NPA","pais":"Sudáfrica","tipo":"C-ADR","monto_usd":0.0,"anio":2024,"url_fuente":"https://www.sanews.gov.za/south-africa/npa-reaches-resolution-mckinsey-south-africa"},
        ]
    },
    {
        "nombre_caso": "Teva Pharmaceutical",
        "anio_resolucion": 2016,
        "fuente": "DOJ/SEC/NL-OM/IL",
        "monto_total_usd": 519,
        "tipo_resolucion": "DPA+Cease-and-Desist+Settlement",
        "paises": "Estados Unidos · Países Bajos · Israel",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Teva Pharmaceutical Industries Ltd.",
            "pais_sede": "Israel",
            "sector": "Farmacéutica",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["IVAX Argentina S.A."]),
            "cuits_ar": json.dumps(["33501707029"]),  # razón social legal de Teva Argentina, verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":283.2,"anio":2016,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/920436/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":236.0,"anio":2016,"url_fuente":"https://www.sec.gov/files/litigation/complaints/2016/comp-pr2016-277.pdf"},
        ]
    },
    {
        "nombre_caso": "Honeywell / UOP",
        "anio_resolucion": 2022,
        "fuente": "DOJ/SEC/CGU",
        "monto_total_usd": 202,
        "tipo_resolucion": "DPA+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Honeywell International Inc.",
            "pais_sede": "Estados Unidos",
            "sector": "Tecnología industrial y aeroespacial",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Honeywell SAIC"]),
            "cuits_ar": json.dumps(["30580523508"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":79.0,"anio":2022,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1558776/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":81.6,"anio":2022,"url_fuente":"https://www.sec.gov/files/litigation/admin/2022/34-96529.pdf"},
        ]
    },
    {
        "nombre_caso": "Credit Suisse",
        "anio_resolucion": 2021,
        "fuente": "DOJ/SEC/FCA/PNF",
        "monto_total_usd": 475,
        "tipo_resolucion": "DPA+Plea+CJIP+Final Notice",
        "paises": "Estados Unidos · Reino Unido · Francia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Credit Suisse Group AG",
            "pais_sede": "Suiza",
            "sector": "Banca",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Credit Suisse (Argentina) S.R.L."]),
            "cuits_ar": json.dumps(["30699030496"]),  # verificado 2026-07, absorbida por UBS
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":247.5,"anio":2021,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1444986/dl?inline"},
            {"autoridad":"UK FCA","pais":"Reino Unido","tipo":"Final Notice","monto_usd":103.4,"anio":2021,"url_fuente":"https://www.fca.org.uk/publication/final-notices/credit-suisse-2021.pdf"},
            {"autoridad":"France PNF","pais":"Francia","tipo":"CJIP","monto_usd":123.0,"anio":2022,"url_fuente":"https://www.tribunal-de-paris.justice.fr/sites/default/files/2022-10/CJIP%20Credit%20Suisse%20sign%C3%A9e%20%202021%20%202022.pdf"},
        ]
    },
    {
        "nombre_caso": "TechnipFMC",
        "anio_resolucion": 2019,
        "fuente": "DOJ/SEC/CGU/PNF",
        "monto_total_usd": 296.2,
        "tipo_resolucion": "DPA+Cease-and-Desist+Leniency+CJIP",
        "paises": "Estados Unidos · Brasil · Francia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "TechnipFMC plc",
            "pais_sede": "Reino Unido / Francia",
            "sector": "Oil & Gas servicios",
            "presencia_argentina": True,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),  # sin CUIT verificable en fuentes públicas — pendiente
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":296.2,"anio":2019,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1225061/dl?inline"},
            {"autoridad":"Brazil CGU","pais":"Brasil","tipo":"Leniency Agreement","monto_usd":214.0,"anio":2019,"url_fuente":"https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/acordo-leniencia/acordos-firmados/TechnipBrasil.pdf"},
        ]
    },
    {
        "nombre_caso": "Société Générale",
        "anio_resolucion": 2018,
        "fuente": "DOJ/CFTC/PNF",
        "monto_total_usd": 860,
        "tipo_resolucion": "DPA+CJIP+Remedial Sanction",
        "paises": "Estados Unidos · Francia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Société Générale S.A.",
            "pais_sede": "Francia",
            "sector": "Banca",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":860.0,"anio":2018,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1072451/dl?inline"},
            {"autoridad":"France PNF","pais":"Francia","tipo":"CJIP","monto_usd":292.8,"anio":2018,"url_fuente":"https://www.agence-francaise-anticorruption.gouv.fr/files/files/2018-10/24.05.18_-_CJIP.pdf"},
        ]
    },
    {
        "nombre_caso": "Glencore",
        "anio_resolucion": 2022,
        "fuente": "DOJ/CFTC/SFO/OAG",
        "monto_total_usd": 1100,
        "tipo_resolucion": "Plea+Plea+Summary Penalty+Consent Order",
        "paises": "Estados Unidos · Reino Unido · Suiza · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Glencore International AG",
            "pais_sede": "Suiza",
            "sector": "Commodities y minería",
            "presencia_argentina": True,
            "filiales_ar": json.dumps(["Glencore Cereales S.A."]),
            "cuits_ar": json.dumps(["30585180528"]),  # verificado 2026-07
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":700.5,"anio":2022,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1508931/dl?inline"},
            {"autoridad":"UK SFO","pais":"Reino Unido","tipo":"Plea/Sentencing","monto_usd":280.0,"anio":2022,"url_fuente":"https://www.judiciary.uk/wp-content/uploads/2022/11/Sentencing-Remarks-Glencore.pdf"},
            {"autoridad":"Swiss OAG","pais":"Suiza","tipo":"Summary Penalty","monto_usd":120.0,"anio":2024,"url_fuente":"https://www.sdc-cva.ch/en/nsb?id=101995"},
        ]
    },
    {
        "nombre_caso": "Keppel O&M",
        "anio_resolucion": 2017,
        "fuente": "DOJ/CGU/AGC",
        "monto_total_usd": 422.2,
        "tipo_resolucion": "DPA+Leniency+Conditional Warning",
        "paises": "Estados Unidos · Brasil · Singapur",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Keppel O&M Ltd.",
            "pais_sede": "Singapur",
            "sector": "Construcción naval y offshore",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":422.2,"anio":2017,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1021786/dl?inline"},
            {"autoridad":"Singapore AGC","pais":"Singapur","tipo":"Conditional Warning","monto_usd":105.5,"anio":2022,"url_fuente":"https://www.cpib.gov.sg/press-room/press-releases/conditional-warning-issued-keppel-offshore-marine-ltd/"},
        ]
    },
    {
        "nombre_caso": "SBM Offshore",
        "anio_resolucion": 2014,
        "fuente": "DOJ/NL-OM/CGU/OAG",
        "monto_total_usd": 762,
        "tipo_resolucion": "DPA+Settlement+Leniency+Summary Penalty",
        "paises": "Estados Unidos · Países Bajos · Brasil · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "SBM Offshore N.V.",
            "pais_sede": "Países Bajos",
            "sector": "Equipos offshore y FPSO",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":238.0,"anio":2017,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1017346/dl?inline"},
            {"autoridad":"Netherlands OM","pais":"Países Bajos","tipo":"Transactional Settlement","monto_usd":240.0,"anio":2014,"url_fuente":"https://www.om.nl/actueel/nieuws/2014/11/12/sbm-offshore-n.v.-betaalt-ususd-240.000.000-wegens-omkoping"},
        ]
    },
    {
        "nombre_caso": "Telia Company",
        "anio_resolucion": 2017,
        "fuente": "DOJ/SEC/NL-OM",
        "monto_total_usd": 965,
        "tipo_resolucion": "DPA+Cease-and-Desist+Transactional Settlement",
        "paises": "Estados Unidos · Países Bajos",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Telia Company AB",
            "pais_sede": "Suecia",
            "sector": "Telecomunicaciones",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":548.6,"anio":2017,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/998601/dl?inline"},
            {"autoridad":"Netherlands OM","pais":"Países Bajos","tipo":"Transactional Settlement","monto_usd":274.0,"anio":2017,"url_fuente":"https://www.prosecutionservice.nl/site/binaries/site-collections/documents/fp/hoge-transacties/feitenrelaas/statement-of-facts-telia-company/statement_of_facts_telia+%281%29.pdf"},
        ]
    },
    {
        "nombre_caso": "VimpelCom",
        "anio_resolucion": 2016,
        "fuente": "DOJ/SEC/NL-OM",
        "monto_total_usd": 795,
        "tipo_resolucion": "DPA+Plea+Transactional Settlement",
        "paises": "Estados Unidos · Países Bajos",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "VimpelCom Ltd.",
            "pais_sede": "Países Bajos",
            "sector": "Telecomunicaciones",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":460.0,"anio":2016,"url_fuente":"https://www.justice.gov/archives/opa/pr/vimpelcom-limited-and-unitel-llc-enter-global-foreign-bribery-resolution-more-795-million"},
            {"autoridad":"Netherlands OM","pais":"Países Bajos","tipo":"Transactional Settlement","monto_usd":335.0,"anio":2016,"url_fuente":"https://www.prosecutionservice.nl/latest/news/2016/02/18/vimpelcom-pays-close-to-400-million-dollars-to-the-netherlands-for-bribery-in-uzbekistan"},
        ]
    },
    {
        "nombre_caso": "Standard Bank",
        "anio_resolucion": 2015,
        "fuente": "SFO/SEC",
        "monto_total_usd": 33.2,
        "tipo_resolucion": "DPA+Cease-and-Desist",
        "paises": "Reino Unido · Estados Unidos",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Standard Bank Group Ltd.",
            "pais_sede": "Sudáfrica",
            "sector": "Banca",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"UK SFO","pais":"Reino Unido","tipo":"DPA","monto_usd":16.8,"anio":2015,"url_fuente":"https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-standard-bank"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":16.4,"anio":2015,"url_fuente":"https://www.sec.gov/files/litigation/admin/2015/33-9981.pdf"},
        ]
    },
    {
        "nombre_caso": "Amec Foster Wheeler",
        "anio_resolucion": 2021,
        "fuente": "DOJ/SEC/SFO/CGU",
        "monto_total_usd": 177,
        "tipo_resolucion": "DPA+DPA+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Reino Unido · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "AFW plc (Wood Group)",
            "pais_sede": "Reino Unido",
            "sector": "Ingeniería y construcción",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":79.5,"anio":2021,"url_fuente":"https://www.justice.gov/archives/opa/press-release/file/1411296/dl?inline"},
            {"autoridad":"UK SFO","pais":"Reino Unido","tipo":"DPA","monto_usd":48.1,"anio":2021,"url_fuente":"https://www.gov.uk/government/publications/sfo-deferred-prosecution-agreement-with-amec-foster-wheeler"},
        ]
    },
    {
        "nombre_caso": "Petrobras",
        "anio_resolucion": 2018,
        "fuente": "DOJ/SEC/CGU/MPF",
        "monto_total_usd": 853.2,
        "tipo_resolucion": "NPA+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Petróleo Brasileiro S.A.",
            "pais_sede": "Brasil",
            "sector": "Petróleo y gas estatal",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"NPA","monto_usd":853.2,"anio":2018,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1097256/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":933.5,"anio":2018,"url_fuente":"https://www.sec.gov/files/litigation/admin/2018/33-10561.pdf"},
        ]
    },
    {
        "nombre_caso": "Vitol Inc.",
        "anio_resolucion": 2020,
        "fuente": "DOJ/CFTC/CGU",
        "monto_total_usd": 163,
        "tipo_resolucion": "DPA+Consent Order+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Vitol Holding B.V.",
            "pais_sede": "Países Bajos",
            "sector": "Trading de commodities energéticos",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":135.0,"anio":2020,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1346651/dl?inline"},
            {"autoridad":"CFTC","pais":"Estados Unidos","tipo":"Consent Order","monto_usd":28.0,"anio":2020,"url_fuente":"https://www.cftc.gov/media/5346/enfvitolorder120320/download"},
        ]
    },
    {
        "nombre_caso": "Gunvor S.A.",
        "anio_resolucion": 2024,
        "fuente": "DOJ/OAG",
        "monto_total_usd": 661.5,
        "tipo_resolucion": "Plea+Summary Penalty",
        "paises": "Estados Unidos · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Gunvor Group Ltd.",
            "pais_sede": "Chipre / Suiza",
            "sector": "Trading de petróleo",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":374.6,"anio":2024,"url_fuente":"https://www.justice.gov/criminal/media/1340966/dl?inline"},
            {"autoridad":"Swiss OAG","pais":"Suiza","tipo":"Summary Penalty","monto_usd":82.3,"anio":2024,"url_fuente":"https://www.admin.ch/en/nsb?id=100264"},
        ]
    },
    {
        "nombre_caso": "Stericycle Inc.",
        "anio_resolucion": 2022,
        "fuente": "DOJ/SEC/CGU",
        "monto_total_usd": 84,
        "tipo_resolucion": "DPA+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Stericycle Inc.",
            "pais_sede": "Estados Unidos",
            "sector": "Gestión de residuos sanitarios",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":52.5,"anio":2022,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1496296/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":28.2,"anio":2022,"url_fuente":"https://www.sec.gov/files/litigation/admin/2022/34-94760.pdf"},
        ]
    },
    {
        "nombre_caso": "J&F / JBS",
        "anio_resolucion": 2020,
        "fuente": "DOJ/SEC/CGU",
        "monto_total_usd": 512.5,
        "tipo_resolucion": "Plea+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "J&F Investimentos S.A.",
            "pais_sede": "Brasil",
            "sector": "Alimentación / agroindústria",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":256.5,"anio":2020,"url_fuente":"https://www.justice.gov/criminal/criminal-fraud/file/1334241/dl?inline"},
            {"autoridad":"SEC","pais":"Estados Unidos","tipo":"Cease-and-Desist","monto_usd":27.0,"anio":2020,"url_fuente":"https://www.sec.gov/files/litigation/admin/2020/34-90170.pdf"},
        ]
    },
    {
        "nombre_caso": "Freepoint Commodities",
        "anio_resolucion": 2023,
        "fuente": "DOJ/CFTC/CGU",
        "monto_total_usd": 98,
        "tipo_resolucion": "DPA+Consent Order+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Freepoint LLC",
            "pais_sede": "Estados Unidos",
            "sector": "Trading de commodities",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":68.0,"anio":2023,"url_fuente":"https://www.justice.gov/criminal/media/1329231/dl?inline"},
            {"autoridad":"CFTC","pais":"Estados Unidos","tipo":"Consent Order","monto_usd":61.0,"anio":2023,"url_fuente":"https://www.cftc.gov/media/9906/enffreepointcommoditiesorder120423/download"},
        ]
    },
    {
        "nombre_caso": "Trafigura Beheer",
        "anio_resolucion": 2024,
        "fuente": "DOJ/CGU/Swiss",
        "monto_total_usd": 126.8,
        "tipo_resolucion": "Plea+Leniency+Federal Criminal Conviction",
        "paises": "Estados Unidos · Brasil · Suiza",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Trafigura Beheer B.V.",
            "pais_sede": "Países Bajos",
            "sector": "Trading de commodities",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Plea Agreement","monto_usd":80.5,"anio":2024,"url_fuente":"https://www.justice.gov/criminal/media/1345976/dl?inline"},
            {"autoridad":"Brazil CGU/AGU","pais":"Brasil","tipo":"Leniency Agreement","monto_usd":26.8,"anio":2025,"url_fuente":"https://www.gov.br/cgu/pt-br/assuntos/integridade-privada/acordo-leniencia/arquivos/SEI_3569333_Acordo_de_Lenienciatarjado.pdf"},
        ]
    },
    {
        "nombre_caso": "GOL Linhas Aéreas",
        "anio_resolucion": 2022,
        "fuente": "DOJ/SEC/CGU",
        "monto_total_usd": 41.5,
        "tipo_resolucion": "DPA+Cease-and-Desist+Leniency",
        "paises": "Estados Unidos · Brasil",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "GOL Linhas Aéreas Inteligentes S.A.",
            "pais_sede": "Brasil",
            "sector": "Aviación civil",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"DPA","monto_usd":17.0,"anio":2022,"url_fuente":"https://www.justice.gov/criminal/media/1245506/dl?inline"},
        ]
    },
    {
        "nombre_caso": "Balt SAS",
        "anio_resolucion": 2026,
        "fuente": "DOJ/PNF",
        "monto_total_usd": 3.2,
        "tipo_resolucion": "Declination+CJIP",
        "paises": "Estados Unidos · Francia",
        "estado": "cerrado",
        "empresa": {
            "nombre_matriz": "Balt SAS",
            "pais_sede": "Francia",
            "sector": "Dispositivos médicos",
            "presencia_argentina": False,
            "filiales_ar": json.dumps([]),
            "cuits_ar": json.dumps([]),
        },
        "resoluciones": [
            {"autoridad":"DOJ","pais":"Estados Unidos","tipo":"Declination (NPA-like)","monto_usd":1.2,"anio":2026,"url_fuente":"https://www.justice.gov/opa/pr/justice-department-resolves-foreign-bribery-investigation-balt-sas-healthcare-executive-and"},
            {"autoridad":"France PNF","pais":"Francia","tipo":"CJIP","monto_usd":1.8,"anio":2026,"url_fuente":"https://www.agence-francaise-anticorruption.gouv.fr/files/files/2026-03/CJIP%20BALT.pdf"},
        ]
    },
]


# ── FUNCIÓN PRINCIPAL ─────────────────────────────────────────────────────────

def seed():
    crear_tablas()
    db = SessionLocal()

    try:
        if db.query(Caso).count() > 0:
            print(f"[seed] Base ya tiene {db.query(Caso).count()} casos. Salteando.")
            return

        total_casos = 0
        total_empresas = 0
        total_resoluciones = 0

        for datos in CASOS_OCDE:
            emp_datos = datos["empresa"]
            empresa = Empresa(
                nombre_matriz=emp_datos["nombre_matriz"],
                pais_sede=emp_datos["pais_sede"],
                sector=emp_datos["sector"],
                presencia_argentina=emp_datos["presencia_argentina"],
                filiales_ar=emp_datos["filiales_ar"],
                cuits_ar=emp_datos["cuits_ar"],
            )
            db.add(empresa)
            db.flush()
            total_empresas += 1

            caso = Caso(
                nombre_caso=datos["nombre_caso"],
                anio_resolucion=datos["anio_resolucion"],
                fuente=datos["fuente"],
                monto_total_usd=datos["monto_total_usd"],
                tipo_resolucion=datos["tipo_resolucion"],
                paises=datos["paises"],
                estado=datos["estado"],
            )
            db.add(caso)
            db.flush()
            total_casos += 1

            for r in datos["resoluciones"]:
                res = Resolucion(
                    caso_id=caso.id,
                    empresa_id=empresa.id,
                    autoridad=r["autoridad"],
                    pais=r["pais"],
                    tipo=r["tipo"],
                    monto_usd=r["monto_usd"],
                    anio=r["anio"],
                    url_fuente=r.get("url_fuente", ""),
                )
                db.add(res)
                total_resoluciones += 1

        db.commit()
        print(f"[seed] OK — {total_casos} casos, {total_empresas} empresas, {total_resoluciones} resoluciones cargadas.")

    except Exception as e:
        db.rollback()
        print(f"[seed] ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
