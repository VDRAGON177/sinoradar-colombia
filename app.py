"""
SinoRadar Colombia v2.1 - Plataforma de Inteligencia Comercial para Importaciones China -> Colombia
Desarrollado en Python con Pandas, NumPy, Plotly, OpenPyXL y Streamlit.

Características principales:
  - Base de datos inicial de 14,400 registros (120 productos reales x 24 meses x 5 ciudades x 10 categorías)
    con identificadores universales EAN_UPC y Partida_Arancelaria (DIAN)
  - Carga directa de archivos Excel (.xlsx / .xls) y CSV en modo Combinar (pd.concat) o Reemplazar
  - Manejo inteligente de SKU: respeta SKUs propios de la empresa o los autogenera con pd.factorize
    si el archivo llega sin columna SKU (o con celdas vacías)
  - Cruce automático de productos externos contra la base de mercado por EAN/UPC, Partida Arancelaria DIAN
    o similitud de nombre (difflib.SequenceMatcher), con prueba interactiva en 1 clic
  - Formulario en vivo para registrar nuevas importaciones y ver su impacto inmediato en KPIs y Semáforo
  - Motor analítico vectorizado en NumPy y Pandas

Equipo del proyecto:
  - Isabella Prieto Morales
  - Santiago Plazas
  - Nicolás Alandete
  - Emmanuel Caballero
"""

import datetime
import io
import os
import re
import unicodedata
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONFIGURACIÓN GENERAL Y ESTILO COMERCIAL (UI / UX)
# ==============================================================================
st.set_page_config(
    page_title="SinoRadar Colombia | Inteligencia de Importaciones",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main {
        background-color: #F8FAFC;
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #0EA5E9 100%);
        padding: 1.7rem 2.1rem;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.14);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.28);
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-bottom: 0.55rem;
        text-transform: uppercase;
    }
    .hero-title {
        font-size: 2.0rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.15;
    }
    .hero-subtitle {
        font-size: 0.96rem;
        color: #E2E8F0;
        margin-top: 0.45rem;
        margin-bottom: 0;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 0.95rem 1.1rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
    }
    .insight-card {
        background-color: #FFFFFF;
        border-left: 5px solid #1E3A8A;
        padding: 1rem 1.25rem;
        border-radius: 10px;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .insight-green { border-left-color: #10B981; }
    .insight-amber { border-left-color: #F59E0B; }
    .insight-red   { border-left-color: #EF4444; }
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

COLUMNAS_MAESTRAS = [
    "Fecha", "Anio", "Mes", "SKU", "EAN_UPC", "Partida_Arancelaria",
    "Producto", "Categoria", "Ciudad_Destino", "Tipo_Transporte",
    "Puerto_Entrada", "Tiempo_Transito_Dias", "TRM_COP", "Precio_FOB_USD",
    "Flete_Unitario_USD", "Arancel_Pct", "IVA_Pct", "Costo_Aterrizado_COP",
    "Precio_Venta_Mercado_COP", "Unidades_Importadas", "Unidades_Vendidas",
    "Competidores_Activos", "Calificacion_Mercado", "Tasa_Devolucion_Pct",
]

# Columnas mínimas que debe traer un archivo externo de empresa
# (SKU, Anio, Mes, EAN_UPC, Partida_Arancelaria, Costo_Aterrizado_COP, etc. se completan automáticamente si faltan)
COLUMNAS_MINIMAS_EXTERNO = [
    "Fecha", "Producto", "Categoria", "Ciudad_Destino", "Tipo_Transporte",
    "TRM_COP", "Precio_FOB_USD", "Flete_Unitario_USD", "Arancel_Pct",
    "Precio_Venta_Mercado_COP", "Unidades_Importadas", "Unidades_Vendidas",
]

NOMBRES_MESES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}

PARTIDAS_DIAN_DEFAULT = {
    "Tecnología": "8528.62.00.00",
    "Hogar Inteligente": "8509.80.20.00",
    "Belleza y Cuidado": "8543.70.90.00",
    "Deportes y Fitness": "9506.91.00.00",
    "Accesorios y Moda": "4202.92.00.00",
    "Mascotas y Eco": "3924.90.00.00",
    "Iluminación y Solar": "9405.42.00.00",
    "Cocina y Mini-Electro": "8509.40.10.00",
    "Gaming y Setup": "8471.60.20.00",
    "Bebés y Juguetería": "9503.00.99.00",
}

if "registros_manuales" not in st.session_state:
    st.session_state["registros_manuales"] = []
if "usar_demo_excel_sin_sku" not in st.session_state:
    st.session_state["usar_demo_excel_sin_sku"] = False


# ==============================================================================
# 2. MOTOR DE DATOS, INGESTA INTELIGENTE (EXCEL/CSV/SKU) Y CRUCE DE MERCADO
# ==============================================================================
def normalizar_texto(texto: object) -> str:
    """Normaliza texto quitando tildes y símbolos para comparación y llaves consistentes."""
    s = "" if pd.isna(texto) else str(texto).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def limpiar_codigo_texto(valor: object) -> str:
    """Limpia códigos leídos desde Excel (evita '.0' en EAN numéricos o textos 'nan')."""
    if pd.isna(valor):
        return ""
    s = str(valor).strip()
    if s.lower() in ("nan", "none", "null", ""):
        return ""
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s


def generar_excel_bytes(df_export: pd.DataFrame, nombre_hoja: str = "Importaciones") -> bytes:
    """Exporta un DataFrame a bytes .xlsx en memoria usando OpenPyXL."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name=nombre_hoja)
    buffer.seek(0)
    return buffer.getvalue()


def _calcular_ean13_fallback(indice_producto: int) -> str:
    """Genera un EAN-13 válido determinístico si la base cargada no traía EAN_UPC."""
    base_12 = f"6901234{indice_producto:05d}"
    suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base_12))
    digito_control = (10 - (suma % 10)) % 10
    return f"{base_12}{digito_control}"


@st.cache_data
def cargar_csv_base(ruta: str = "importaciones_china_colombia.csv") -> pd.DataFrame:
    """
    Carga la base maestra CSV. Si el archivo no existe o está vacío (EmptyDataError / 0 bytes),
    lo regenera automáticamente en el servidor usando generar_datos.py.
    """
    necesita_regenerar = (not os.path.exists(ruta)) or (os.path.getsize(ruta) == 0)
    df_b = None

    if not necesita_regenerar:
        try:
            df_b = pd.read_csv(ruta, dtype={"EAN_UPC": str, "Partida_Arancelaria": str})
            if df_b.empty or len(df_b.columns) == 0:
                necesita_regenerar = True
        except pd.errors.EmptyDataError:
            necesita_regenerar = True

    if necesita_regenerar or df_b is None:
        from generar_datos import generar_base_datos
        df_b = generar_base_datos(ruta_salida=ruta, semilla=42)

    if "EAN_UPC" not in df_b.columns or (df_b["EAN_UPC"].astype(str).str.strip() == "").all():
        skus_unicos = df_b["SKU"].drop_duplicates().tolist()
        mapa_ean = {sku: _calcular_ean13_fallback(idx) for idx, sku in enumerate(skus_unicos, start=1)}
        df_b["EAN_UPC"] = df_b["SKU"].map(mapa_ean).fillna("")

    if "Partida_Arancelaria" not in df_b.columns:
        df_b["Partida_Arancelaria"] = df_b["Categoria"].map(PARTIDAS_DIAN_DEFAULT).fillna("")

    df_b["EAN_UPC"] = df_b["EAN_UPC"].apply(limpiar_codigo_texto)
    df_b["Partida_Arancelaria"] = df_b["Partida_Arancelaria"].apply(limpiar_codigo_texto)
    return df_b


def crear_dataset_demo_empresa_sin_sku(df_mercado: pd.DataFrame) -> pd.DataFrame:
    """
    Crea un Excel realista de ejemplo (10 filas: 5 productos x 2 meses) SIN columna SKU
    ni Costo_Aterrizado_COP para demostrar:
      1) Autogeneración determinística de SKU con pd.factorize
      2) Cálculo aduanero automático
      3) Cruce contra el mercado por EAN/UPC, Partida Arancelaria DIAN y similitud de nombre
    """
    mapa_ean = (
        df_mercado[["SKU", "EAN_UPC"]]
        .drop_duplicates()
        .set_index("SKU")["EAN_UPC"]
        .to_dict()
    )
    ean_bel01 = mapa_ean.get("SR-BEL-01", "6901234000252")
    ean_tec03 = mapa_ean.get("SR-TEC-03", "6901234000030")

    filas = [
        # 1) Cruce por EAN exacto (producto Luz Verde SR-BEL-01) - 2 meses
        {
            "Fecha": "2026-10-01", "Producto": "Masajeador Facial LED Microcorrientes",
            "Categoria": "Belleza y Cuidado", "Ciudad_Destino": "Bogotá", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": ean_bel01, "Partida_Arancelaria": "8543.70.90.00",
            "TRM_COP": 4210.0, "Precio_FOB_USD": 6.20, "Flete_Unitario_USD": 1.70, "Arancel_Pct": 0.15,
            "Precio_Venta_Mercado_COP": 119000, "Unidades_Importadas": 260, "Unidades_Vendidas": 242,
        },
        {
            "Fecha": "2026-11-01", "Producto": "Masajeador Facial LED Microcorrientes",
            "Categoria": "Belleza y Cuidado", "Ciudad_Destino": "Medellín", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": ean_bel01, "Partida_Arancelaria": "8543.70.90.00",
            "TRM_COP": 4240.0, "Precio_FOB_USD": 6.20, "Flete_Unitario_USD": 1.65, "Arancel_Pct": 0.15,
            "Precio_Venta_Mercado_COP": 122000, "Unidades_Importadas": 300, "Unidades_Vendidas": 280,
        },
        # 2) Cruce por Similitud de Nombre + Categoría (sin EAN y sin Partida -> SR-TEC-01) - 2 meses
        {
            "Fecha": "2026-10-01", "Producto": "Proyector mini HD portatil wifi",
            "Categoria": "Tecnología", "Ciudad_Destino": "Bogotá", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": "", "Partida_Arancelaria": "",
            "TRM_COP": 4210.0, "Precio_FOB_USD": 22.80, "Flete_Unitario_USD": 6.00, "Arancel_Pct": 0.05,
            "Precio_Venta_Mercado_COP": 399000, "Unidades_Importadas": 150, "Unidades_Vendidas": 138,
        },
        {
            "Fecha": "2026-11-01", "Producto": "Proyector mini HD portatil wifi",
            "Categoria": "Tecnología", "Ciudad_Destino": "Cali", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": "", "Partida_Arancelaria": "",
            "TRM_COP": 4240.0, "Precio_FOB_USD": 22.80, "Flete_Unitario_USD": 6.10, "Arancel_Pct": 0.05,
            "Precio_Venta_Mercado_COP": 395000, "Unidades_Importadas": 120, "Unidades_Vendidas": 109,
        },
        # 3) Cruce por EAN exacto (producto Alto Riesgo SR-TEC-03) - 2 meses
        {
            "Fecha": "2026-10-01", "Producto": "Reloj Inteligente Deportivo Pantalla AMOLED",
            "Categoria": "Tecnología", "Ciudad_Destino": "Bogotá", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": ean_tec03, "Partida_Arancelaria": "8528.62.00.00",
            "TRM_COP": 4210.0, "Precio_FOB_USD": 11.80, "Flete_Unitario_USD": 1.35, "Arancel_Pct": 0.05,
            "Precio_Venta_Mercado_COP": 105000, "Unidades_Importadas": 350, "Unidades_Vendidas": 225,
        },
        {
            "Fecha": "2026-11-01", "Producto": "Reloj Inteligente Deportivo Pantalla AMOLED",
            "Categoria": "Tecnología", "Ciudad_Destino": "Medellín", "Tipo_Transporte": "Aéreo",
            "EAN_UPC": ean_tec03, "Partida_Arancelaria": "8528.62.00.00",
            "TRM_COP": 4240.0, "Precio_FOB_USD": 11.80, "Flete_Unitario_USD": 1.35, "Arancel_Pct": 0.05,
            "Precio_Venta_Mercado_COP": 102000, "Unidades_Importadas": 280, "Unidades_Vendidas": 175,
        },
        # 4) Cruce por Partida Arancelaria DIAN (sin EAN, nombre distinto a catálogo -> familia Cocina) - 2 meses
        {
            "Fecha": "2026-10-01", "Producto": "Exprimidor Cítricos Inalámbrico USB-C",
            "Categoria": "Cocina y Mini-Electro", "Ciudad_Destino": "Bogotá", "Tipo_Transporte": "Marítimo",
            "EAN_UPC": "", "Partida_Arancelaria": "8509.40.10.00",
            "TRM_COP": 4210.0, "Precio_FOB_USD": 6.90, "Flete_Unitario_USD": 0.95, "Arancel_Pct": 0.10,
            "Precio_Venta_Mercado_COP": 98000, "Unidades_Importadas": 220, "Unidades_Vendidas": 195,
        },
        {
            "Fecha": "2026-11-01", "Producto": "Exprimidor Cítricos Inalámbrico USB-C",
            "Categoria": "Cocina y Mini-Electro", "Ciudad_Destino": "Barranquilla", "Tipo_Transporte": "Marítimo",
            "EAN_UPC": "", "Partida_Arancelaria": "8509.40.10.00",
            "TRM_COP": 4240.0, "Precio_FOB_USD": 6.90, "Flete_Unitario_USD": 0.90, "Arancel_Pct": 0.10,
            "Precio_Venta_Mercado_COP": 96000, "Unidades_Importadas": 180, "Unidades_Vendidas": 162,
        },
        # 5) Producto 100% nuevo sin referencia en base (sin EAN y sin Partida) - 2 meses
        {
            "Fecha": "2026-10-01", "Producto": "Cafetera Cold Brew Acero Inoxidable 1L",
            "Categoria": "Cocina y Mini-Electro", "Ciudad_Destino": "Bogotá", "Tipo_Transporte": "Marítimo",
            "EAN_UPC": "", "Partida_Arancelaria": "",
            "TRM_COP": 4210.0, "Precio_FOB_USD": 10.40, "Flete_Unitario_USD": 1.30, "Arancel_Pct": 0.10,
            "Precio_Venta_Mercado_COP": 159000, "Unidades_Importadas": 200, "Unidades_Vendidas": 186,
        },
        {
            "Fecha": "2026-11-01", "Producto": "Cafetera Cold Brew Acero Inoxidable 1L",
            "Categoria": "Cocina y Mini-Electro", "Ciudad_Destino": "Medellín", "Tipo_Transporte": "Marítimo",
            "EAN_UPC": "", "Partida_Arancelaria": "",
            "TRM_COP": 4240.0, "Precio_FOB_USD": 10.40, "Flete_Unitario_USD": 1.30, "Arancel_Pct": 0.10,
            "Precio_Venta_Mercado_COP": 162000, "Unidades_Importadas": 160, "Unidades_Vendidas": 149,
        },
    ]
    return pd.DataFrame(filas)


def preparar_archivo_externo(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Valida y normaliza un archivo Excel (.xlsx/.xls) o CSV cargado por una empresa:
      - Acepta SKUs propios de la empresa sin exigir prefijo 'SR-'
      - Si no existe la columna SKU o trae celdas vacías, autogenera SKUs determinísticos
        por producto usando pd.factorize (ej. CLI-BEL-001)
      - Calcula automáticamente Anio, Mes y Costo_Aterrizado_COP si el archivo los omite
      - Limpia EAN_UPC y Partida_Arancelaria si están presentes
    """
    df_ext = df_raw.copy()
    df_ext.columns = [str(c).strip() for c in df_ext.columns]

    faltantes = [c for c in COLUMNAS_MINIMAS_EXTERNO if c not in df_ext.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(faltantes)}")

    # Parseo de fecha, año y mes
    fechas = pd.to_datetime(df_ext["Fecha"], errors="coerce")
    if fechas.isna().any():
        raise ValueError("Algunas filas tienen valores inválidos en la columna 'Fecha' (usa formato YYYY-MM-DD).")
    df_ext["Fecha"] = fechas.dt.strftime("%Y-%m-%d")
    if "Anio" not in df_ext.columns or df_ext["Anio"].isna().any():
        df_ext["Anio"] = fechas.dt.year.astype(int)
    else:
        df_ext["Anio"] = pd.to_numeric(df_ext["Anio"], errors="coerce").fillna(fechas.dt.year).astype(int)
    if "Mes" not in df_ext.columns or df_ext["Mes"].isna().any():
        df_ext["Mes"] = fechas.dt.month.astype(int)
    else:
        df_ext["Mes"] = pd.to_numeric(df_ext["Mes"], errors="coerce").fillna(fechas.dt.month).astype(int)

    # Limpieza de textos principales
    df_ext["Producto"] = df_ext["Producto"].astype(str).str.strip()
    df_ext["Categoria"] = df_ext["Categoria"].astype(str).str.strip()
    df_ext["Ciudad_Destino"] = df_ext["Ciudad_Destino"].astype(str).str.strip()
    df_ext["Tipo_Transporte"] = df_ext["Tipo_Transporte"].astype(str).str.strip()

    # Columnas numéricas principales
    for col_num in [
        "TRM_COP", "Precio_FOB_USD", "Flete_Unitario_USD", "Arancel_Pct",
        "Precio_Venta_Mercado_COP", "Unidades_Importadas", "Unidades_Vendidas",
    ]:
        df_ext[col_num] = pd.to_numeric(df_ext[col_num], errors="coerce")
        if df_ext[col_num].isna().any():
            raise ValueError(f"Hay valores no numéricos o vacíos en la columna '{col_num}'.")

    # Si el usuario escribió arancel como porcentaje entero (ej. 15 en vez de 0.15), normalizar
    df_ext["Arancel_Pct"] = np.where(df_ext["Arancel_Pct"] > 1.0, df_ext["Arancel_Pct"] / 100.0, df_ext["Arancel_Pct"])

    # IVA por defecto 19%
    if "IVA_Pct" not in df_ext.columns:
        df_ext["IVA_Pct"] = 0.19
    else:
        df_ext["IVA_Pct"] = pd.to_numeric(df_ext["IVA_Pct"], errors="coerce").fillna(0.19)
        df_ext["IVA_Pct"] = np.where(df_ext["IVA_Pct"] > 1.0, df_ext["IVA_Pct"] / 100.0, df_ext["IVA_Pct"])

    # Identificadores opcionales universales
    if "EAN_UPC" not in df_ext.columns:
        df_ext["EAN_UPC"] = ""
    else:
        df_ext["EAN_UPC"] = df_ext["EAN_UPC"].apply(limpiar_codigo_texto)

    if "Partida_Arancelaria" not in df_ext.columns:
        df_ext["Partida_Arancelaria"] = ""
    else:
        df_ext["Partida_Arancelaria"] = df_ext["Partida_Arancelaria"].apply(limpiar_codigo_texto)

    # Puerto y tránsito si faltan
    if "Puerto_Entrada" not in df_ext.columns or df_ext["Puerto_Entrada"].isna().any():
        puertos_auto = np.where(
            df_ext["Tipo_Transporte"].str.lower().str.contains("aér|aer"),
            "Aéreo El Dorado",
            np.where(df_ext["Ciudad_Destino"].isin(["Bogotá", "Cali", "Pereira"]), "Buenaventura", "Cartagena"),
        )
        if "Puerto_Entrada" not in df_ext.columns:
            df_ext["Puerto_Entrada"] = puertos_auto
        else:
            df_ext["Puerto_Entrada"] = df_ext["Puerto_Entrada"].fillna(pd.Series(puertos_auto, index=df_ext.index))

    if "Tiempo_Transito_Dias" not in df_ext.columns or df_ext["Tiempo_Transito_Dias"].isna().any():
        transito_auto = np.where(df_ext["Tipo_Transporte"].str.lower().str.contains("aér|aer"), 11, 46)
        if "Tiempo_Transito_Dias" not in df_ext.columns:
            df_ext["Tiempo_Transito_Dias"] = transito_auto
        else:
            df_ext["Tiempo_Transito_Dias"] = pd.to_numeric(df_ext["Tiempo_Transito_Dias"], errors="coerce").fillna(
                pd.Series(transito_auto, index=df_ext.index)
            )
    df_ext["Tiempo_Transito_Dias"] = df_ext["Tiempo_Transito_Dias"].astype(int)

    # Costo aterrizado automático con fórmula aduanera de Colombia si falta o viene vacío
    costos_calculados_auto = False
    cif_usd = df_ext["Precio_FOB_USD"] + df_ext["Flete_Unitario_USD"]
    arancel_usd = cif_usd * df_ext["Arancel_Pct"]
    iva_usd = (cif_usd + arancel_usd) * df_ext["IVA_Pct"]
    gastos_nac_usd = cif_usd * 0.08
    costo_auto = (np.round(((cif_usd + arancel_usd + iva_usd + gastos_nac_usd) * df_ext["TRM_COP"]) / 100.0) * 100).astype(int)

    if "Costo_Aterrizado_COP" not in df_ext.columns:
        df_ext["Costo_Aterrizado_COP"] = costo_auto
        costos_calculados_auto = True
    else:
        serie_costo = pd.to_numeric(df_ext["Costo_Aterrizado_COP"], errors="coerce")
        mask_falta_costo = serie_costo.isna() | (serie_costo <= 0)
        if mask_falta_costo.any():
            costos_calculados_auto = True
        df_ext["Costo_Aterrizado_COP"] = np.where(mask_falta_costo, costo_auto, serie_costo).astype(int)

    # Defaults razonables para métricas complementarias si faltan
    if "Competidores_Activos" not in df_ext.columns:
        df_ext["Competidores_Activos"] = 25
    else:
        df_ext["Competidores_Activos"] = pd.to_numeric(df_ext["Competidores_Activos"], errors="coerce").fillna(25).astype(int)

    if "Calificacion_Mercado" not in df_ext.columns:
        df_ext["Calificacion_Mercado"] = 4.5
    else:
        df_ext["Calificacion_Mercado"] = pd.to_numeric(df_ext["Calificacion_Mercado"], errors="coerce").fillna(4.5)

    if "Tasa_Devolucion_Pct" not in df_ext.columns:
        df_ext["Tasa_Devolucion_Pct"] = 2.5
    else:
        df_ext["Tasa_Devolucion_Pct"] = pd.to_numeric(df_ext["Tasa_Devolucion_Pct"], errors="coerce").fillna(2.5)

    df_ext["Unidades_Importadas"] = df_ext["Unidades_Importadas"].astype(int)
    df_ext["Unidades_Vendidas"] = df_ext["Unidades_Vendidas"].astype(int)
    df_ext["Precio_Venta_Mercado_COP"] = df_ext["Precio_Venta_Mercado_COP"].astype(int)

    # ------------------------------------------------------------------
    # MANEJO INTELIGENTE DE SKU (propios vs. autogenerados con pd.factorize)
    # ------------------------------------------------------------------
    if "SKU" not in df_ext.columns:
        skus_raw = pd.Series([""] * len(df_ext), index=df_ext.index)
    else:
        skus_raw = df_ext["SKU"].apply(limpiar_codigo_texto).str.upper()

    mask_sin_sku = skus_raw == ""
    origen_sku_fila = np.where(mask_sin_sku, "Autogenerado (pd.factorize)", "Propio de la empresa")

    skus_finales = skus_raw.copy()
    if mask_sin_sku.any():
        # Factorize determinístico por nombre normalizado de producto: mismo producto => mismo SKU en todos los meses
        llaves_norm = df_ext.loc[mask_sin_sku, "Producto"].apply(normalizar_texto)
        codigos_num, _ = pd.factorize(llaves_norm, sort=False)
        prefijos_cat = (
            df_ext.loc[mask_sin_sku, "Categoria"]
            .apply(lambda c: re.sub(r"[^a-z]", "", normalizar_texto(c))[:3].upper().ljust(3, "X"))
        )
        skus_generados = [
            f"CLI-{pref}-{num + 1:03d}"
            for pref, num in zip(prefijos_cat, codigos_num)
        ]
        skus_finales.loc[mask_sin_sku] = skus_generados

    df_ext["SKU"] = skus_finales
    df_ext["_Origen_SKU"] = origen_sku_fila

    skus_propios = int(df_ext.loc[~mask_sin_sku, "SKU"].nunique())
    skus_auto = int(df_ext.loc[mask_sin_sku, "SKU"].nunique())

    if skus_auto == 0:
        etiqueta_origen = "SKUs propios de la empresa"
    elif skus_propios == 0:
        etiqueta_origen = "Autogenerados con pd.factorize"
    else:
        etiqueta_origen = "Mixto (propios + autogenerados)"

    resumen = {
        "total_filas": len(df_ext),
        "skus_propios": skus_propios,
        "skus_autogenerados": skus_auto,
        "origen_sku": etiqueta_origen,
        "costos_calculados_auto": costos_calculados_auto,
        "mapa_skus": (
            df_ext[["SKU", "Producto", "Categoria", "_Origen_SKU", "EAN_UPC", "Partida_Arancelaria"]]
            .drop_duplicates(subset=["SKU"])
            .reset_index(drop=True)
        ),
    }
    return df_ext[COLUMNAS_MAESTRAS + ["_Origen_SKU"]], resumen


def enriquecer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica limpieza, tipado y cálculos vectorizados con Pandas y NumPy
    para generar todos los indicadores financieros y de inventario.
    """
    data = df.copy()
    data["Fecha"] = pd.to_datetime(data["Fecha"])
    data["Nombre_Mes"] = data["Mes"].map(NOMBRES_MESES)

    # Cálculos vectorizados financieros (NumPy / Pandas)
    data["Ingresos_COP"] = data["Unidades_Vendidas"] * data["Precio_Venta_Mercado_COP"]
    data["Costo_Importacion_Total_COP"] = data["Unidades_Importadas"] * data["Costo_Aterrizado_COP"]
    data["Costo_Mercancia_Vendida_COP"] = data["Unidades_Vendidas"] * data["Costo_Aterrizado_COP"]
    data["Utilidad_Unitaria_COP"] = data["Precio_Venta_Mercado_COP"] - data["Costo_Aterrizado_COP"]
    data["Utilidad_Bruta_COP"] = data["Ingresos_COP"] - data["Costo_Mercancia_Vendida_COP"]

    # Margen bruto (%) protegido contra división por cero mediante np.where
    data["Margen_Bruto_Pct"] = np.where(
        data["Precio_Venta_Mercado_COP"] > 0,
        (data["Utilidad_Unitaria_COP"] / data["Precio_Venta_Mercado_COP"]) * 100.0,
        0.0,
    )

    # Métricas de riesgo de inventario (Sell-Through e inventario estancado)
    data["Inventario_Estancado"] = np.maximum(0, data["Unidades_Importadas"] - data["Unidades_Vendidas"])
    data["Capital_Inmovilizado_COP"] = data["Inventario_Estancado"] * data["Costo_Aterrizado_COP"]
    data["Tasa_Rotacion_Pct"] = np.where(
        data["Unidades_Importadas"] > 0,
        (data["Unidades_Vendidas"] / data["Unidades_Importadas"]) * 100.0,
        0.0,
    )
    return data


def _normalizar_0_100(serie: pd.Series, inverso: bool = False) -> np.ndarray:
    """Normalización Min-Max vectorizada en NumPy (escala 0 a 100)."""
    valores = serie.to_numpy(dtype=float)
    minimo = np.nanmin(valores)
    maximo = np.nanmax(valores)
    if np.isclose(maximo, minimo):
        norm = np.full_like(valores, 50.0)
    else:
        norm = ((valores - minimo) / (maximo - minimo)) * 100.0
    return (100.0 - norm) if inverso else norm


def calcular_radar_productos(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el ranking de productos y el Semáforo de Riesgo de Inventario
    usando agrupaciones de Pandas, regresión lineal (np.polyfit), producto
    punto ponderado (np.dot) y clasificación condicional (np.select).
    """
    resumen = (
        df_filtrado.groupby(["SKU", "Producto", "Categoria", "Tipo_Transporte"], as_index=False)
        .agg(
            Unidades_Vendidas=("Unidades_Vendidas", "sum"),
            Unidades_Importadas=("Unidades_Importadas", "sum"),
            Inventario_Estancado=("Inventario_Estancado", "sum"),
            Ingresos_COP=("Ingresos_COP", "sum"),
            Utilidad_Bruta_COP=("Utilidad_Bruta_COP", "sum"),
            Capital_Inmovilizado_COP=("Capital_Inmovilizado_COP", "sum"),
            Precio_FOB_Prom_USD=("Precio_FOB_USD", "mean"),
            Flete_Prom_USD=("Flete_Unitario_USD", "mean"),
            Arancel_Prom=("Arancel_Pct", "mean"),
            Costo_Aterrizado_Prom=("Costo_Aterrizado_COP", "mean"),
            Precio_Venta_Prom=("Precio_Venta_Mercado_COP", "mean"),
            Margen_Bruto_Pct=("Margen_Bruto_Pct", "mean"),
            Competidores_Prom=("Competidores_Activos", "mean"),
            Calificacion_Prom=("Calificacion_Mercado", "mean"),
            Devolucion_Prom_Pct=("Tasa_Devolucion_Pct", "mean"),
            Transito_Prom_Dias=("Tiempo_Transito_Dias", "mean"),
        )
    )

    resumen["Tasa_Rotacion_Pct"] = np.where(
        resumen["Unidades_Importadas"] > 0,
        (resumen["Unidades_Vendidas"] / resumen["Unidades_Importadas"]) * 100.0,
        0.0,
    )

    # Cálculo de pendiente de crecimiento mensual (%) con np.polyfit por SKU
    tendencias = {}
    serie_mensual = df_filtrado.groupby(["SKU", "Fecha"], as_index=False)["Unidades_Vendidas"].sum()
    for sku, grp in serie_mensual.groupby("SKU", sort=False):
        grp = grp.sort_values("Fecha")
        y = grp["Unidades_Vendidas"].to_numpy(dtype=float)
        if len(y) >= 3 and np.mean(y) > 0:
            x = np.arange(len(y), dtype=float)
            pendiente, _ = np.polyfit(x, y, 1)
            tendencias[sku] = (pendiente / np.mean(y)) * 100.0
        else:
            tendencias[sku] = 0.0
    resumen["Crecimiento_Mensual_Pct"] = resumen["SKU"].map(tendencias).fillna(0.0)

    # Matriz de puntajes normalizados (0-100) en NumPy
    s_margen = _normalizar_0_100(resumen["Margen_Bruto_Pct"], inverso=False)
    s_rotacion = _normalizar_0_100(resumen["Tasa_Rotacion_Pct"], inverso=False)
    s_competencia = _normalizar_0_100(resumen["Competidores_Prom"], inverso=True)
    s_demanda = _normalizar_0_100(resumen["Unidades_Vendidas"], inverso=False)
    s_crecimiento = _normalizar_0_100(resumen["Crecimiento_Mensual_Pct"], inverso=False)
    s_calidad = _normalizar_0_100(resumen["Devolucion_Prom_Pct"], inverso=True)

    matriz_scores = np.column_stack([s_margen, s_rotacion, s_competencia, s_demanda, s_crecimiento, s_calidad])
    pesos = np.array([0.26, 0.24, 0.18, 0.12, 0.12, 0.08])

    resumen["Indice_Oportunidad"] = np.round(np.dot(matriz_scores, pesos), 1)

    # Clasificación del Semáforo de Riesgo de Inventario mediante np.select
    condiciones = [
        (resumen["Indice_Oportunidad"] >= 62.0) & (resumen["Tasa_Rotacion_Pct"] >= 82.0),
        (resumen["Indice_Oportunidad"] >= 42.0) & (resumen["Tasa_Rotacion_Pct"] >= 72.0),
    ]
    etiquetas = [
        "🟢 Alta Oportunidad",
        "🟡 Competitivo",
    ]
    resumen["Semaforo_Riesgo"] = np.select(condiciones, etiquetas, default="🔴 Alto Riesgo")

    acciones = [
        "Importar / Escalar inventario",
        "Evaluar nicho y optimizar costo FOB",
    ]
    resumen["Accion_Recomendada"] = np.select(condiciones, acciones, default="Evitar / Liquidar stock")

    return resumen.sort_values("Indice_Oportunidad", ascending=False).reset_index(drop=True)


def cruzar_contra_mercado(df_empresa_raw: pd.DataFrame, df_mercado_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza los productos cargados por una empresa contra la base de mercado SinoRadar
    en 3 niveles de prioridad sin depender del SKU interno de la empresa:
      1) Código de barras universal (EAN_UPC) -> cruce 1-a-1 exacto
      2) Partida Arancelaria DIAN -> referencia contra el grupo aduanero
      3) Similitud de texto sobre Producto + Categoría (difflib.SequenceMatcher)
    """
    df_emp = enriquecer_dataframe(df_empresa_raw)
    df_mkt = enriquecer_dataframe(df_mercado_raw)
    radar_mkt = calcular_radar_productos(df_mkt)

    # Anexar EAN_UPC y Partida_Arancelaria al radar de mercado
    ids_mkt = (
        df_mkt[["SKU", "EAN_UPC", "Partida_Arancelaria"]]
        .drop_duplicates(subset=["SKU"])
    )
    radar_mkt = radar_mkt.merge(ids_mkt, on="SKU", how="left")
    radar_mkt["Nombre_Norm"] = radar_mkt["Producto"].apply(normalizar_texto)
    radar_mkt["Cat_Norm"] = radar_mkt["Categoria"].apply(normalizar_texto)

    # Promedios de mercado por Partida Arancelaria DIAN
    partidas_mkt = (
        radar_mkt[radar_mkt["Partida_Arancelaria"] != ""]
        .groupby("Partida_Arancelaria", as_index=False)
        .agg(
            Precio_Mercado_Prom=("Precio_Venta_Prom", "mean"),
            Margen_Mercado_Prom=("Margen_Bruto_Pct", "mean"),
            Rotacion_Mercado_Prom=("Tasa_Rotacion_Pct", "mean"),
            Competidores_Mercado=("Competidores_Prom", "mean"),
            Cantidad_SKUs=("SKU", "count"),
            Categoria_Ref=("Categoria", "first"),
        )
    )
    mapa_partidas = partidas_mkt.set_index("Partida_Arancelaria").to_dict(orient="index")
    mapa_ean_mkt = (
        radar_mkt[radar_mkt["EAN_UPC"] != ""]
        .drop_duplicates(subset=["EAN_UPC"])
        .set_index("EAN_UPC")
    )

    # Agrupar productos de la empresa
    emp_grp = (
        df_emp.groupby(["SKU", "Producto", "Categoria"], as_index=False)
        .agg(
            Origen_SKU=("_Origen_SKU", "first"),
            EAN_UPC=("EAN_UPC", lambda s: next((x for x in s if x), "")),
            Partida_Arancelaria=("Partida_Arancelaria", lambda s: next((x for x in s if x), "")),
            Filas=("Fecha", "count"),
            Tu_Costo_COP=("Costo_Aterrizado_COP", "mean"),
            Tu_Precio_COP=("Precio_Venta_Mercado_COP", "mean"),
            Tu_Margen_Pct=("Margen_Bruto_Pct", "mean"),
            Unidades_Imp=("Unidades_Importadas", "sum"),
            Unidades_Ven=("Unidades_Vendidas", "sum"),
        )
    )
    emp_grp["Tu_Rotacion_Pct"] = np.where(
        emp_grp["Unidades_Imp"] > 0,
        (emp_grp["Unidades_Ven"] / emp_grp["Unidades_Imp"]) * 100.0,
        0.0,
    )

    resultados = []
    for _, row in emp_grp.iterrows():
        ean = limpiar_codigo_texto(row["EAN_UPC"])
        partida = limpiar_codigo_texto(row["Partida_Arancelaria"])
        nom_norm = normalizar_texto(row["Producto"])
        cat_norm = normalizar_texto(row["Categoria"])

        metodo = "🆕 Sin referencia directa (nicho propio)"
        ref_txt = "No existe en catálogo base"
        precio_mkt = np.nan
        margen_mkt = np.nan
        rot_mkt = np.nan
        sem_mkt = "Evaluado por métricas propias"

        # NIVEL 1: Cruce exacto por EAN / UPC
        if ean and ean in mapa_ean_mkt.index:
            m = mapa_ean_mkt.loc[ean]
            metodo = "🏷️ Código de Barras (EAN/UPC)"
            ref_txt = f"{m['SKU']} — {m['Producto']}"
            precio_mkt = float(m["Precio_Venta_Prom"])
            margen_mkt = float(m["Margen_Bruto_Pct"])
            rot_mkt = float(m["Tasa_Rotacion_Pct"])
            sem_mkt = str(m["Semaforo_Riesgo"])
        else:
            # Buscar mejor coincidencia por similitud de nombre (SequenceMatcher)
            mejor_sim = 0.0
            mejor_fila = None
            candidatos = radar_mkt[radar_mkt["Cat_Norm"] == cat_norm]
            if candidatos.empty:
                candidatos = radar_mkt
            for _, cand in candidatos.iterrows():
                tokens_emp = set(nom_norm.split())
                tokens_cand = set(cand["Nombre_Norm"].split())
                sim_seq = SequenceMatcher(None, nom_norm, cand["Nombre_Norm"]).ratio()
                sim_jac = len(tokens_emp & tokens_cand) / max(1, len(tokens_emp | tokens_cand))
                sim_total = 0.60 * sim_seq + 0.40 * sim_jac
                if sim_total > mejor_sim:
                    mejor_sim = sim_total
                    mejor_fila = cand

            # NIVEL 2: Similitud alta de nombre (producto equivalente)
            if mejor_fila is not None and mejor_sim >= 0.52:
                metodo = f"🔤 Similitud de Nombre ({mejor_sim * 100:.0f}%)"
                ref_txt = f"{mejor_fila['SKU']} — {mejor_fila['Producto']}"
                precio_mkt = float(mejor_fila["Precio_Venta_Prom"])
                margen_mkt = float(mejor_fila["Margen_Bruto_Pct"])
                rot_mkt = float(mejor_fila["Tasa_Rotacion_Pct"])
                sem_mkt = str(mejor_fila["Semaforo_Riesgo"])
            # NIVEL 3: Cruce por Partida Arancelaria DIAN (grupo aduanero)
            elif partida and partida in mapa_partidas:
                mp = mapa_partidas[partida]
                metodo = f"🛃 Partida DIAN ({partida})"
                ref_txt = f"Familia {mp['Categoria_Ref']} ({mp['Cantidad_SKUs']} SKUs)"
                precio_mkt = float(mp["Precio_Mercado_Prom"])
                margen_mkt = float(mp["Margen_Mercado_Prom"])
                rot_mkt = float(mp["Rotacion_Mercado_Prom"])
                sem_mkt = "Referencia promedio DIAN"

        dif_precio_pct = (
            ((row["Tu_Precio_COP"] - precio_mkt) / precio_mkt) * 100.0
            if pd.notna(precio_mkt) and precio_mkt > 0
            else np.nan
        )

        resultados.append({
            "SKU_Asignado": row["SKU"],
            "Origen_SKU": row["Origen_SKU"],
            "Producto_Empresa": row["Producto"],
            "Categoria": row["Categoria"],
            "Filas": int(row["Filas"]),
            "Metodo_Cruce": metodo,
            "Referencia_Mercado": ref_txt,
            "Tu_Costo_COP": round(float(row["Tu_Costo_COP"]), 0),
            "Tu_Precio_COP": round(float(row["Tu_Precio_COP"]), 0),
            "Precio_Mercado_COP": round(precio_mkt, 0) if pd.notna(precio_mkt) else np.nan,
            "Dif_Precio_Pct": round(dif_precio_pct, 1) if pd.notna(dif_precio_pct) else np.nan,
            "Tu_Margen_Pct": round(float(row["Tu_Margen_Pct"]), 1),
            "Margen_Mercado_Pct": round(margen_mkt, 1) if pd.notna(margen_mkt) else np.nan,
            "Tu_Rotacion_Pct": round(float(row["Tu_Rotacion_Pct"]), 1),
            "Semaforo_Mercado": sem_mkt,
        })

    return pd.DataFrame(resultados)


def formato_cop(valor: float) -> str:
    if abs(valor) >= 1e9:
        return f"${valor / 1e9:,.2f}B COP"
    if abs(valor) >= 1e6:
        return f"${valor / 1e6:,.1f}M COP"
    return f"${valor:,.0f} COP"


# ==============================================================================
# 3. CARGA, FUSIÓN DE DATOS (PD.CONCAT) Y FILTROS LATERALES
# ==============================================================================
df_raw_base = cargar_csv_base()
df_empresa_cargada = None
resumen_carga_ext = None
cruce_mercado_df = None

with st.sidebar:
    st.markdown("## 🚢 SinoRadar Colombia")
    st.caption("Inteligencia Comercial China → Colombia")
    st.divider()

    st.markdown("### 📂 Cargar Excel / CSV de Empresa")
    modo_carga = st.radio(
        "Modo al cargar archivo externo:",
        options=["Sumar a la base actual (pd.concat)", "Reemplazar toda la base"],
        index=0,
    )
    archivo_subido = st.file_uploader(
        "Subir Excel (.xlsx / .xls) o CSV",
        type=["xlsx", "xls", "csv"],
        help="Acepta tus SKUs propios o genera SKUs automáticos (pd.factorize) si tu Excel no tiene columna SKU.",
    )

    df_combinado_raw = df_raw_base.copy()

    # Prioridad: archivo real subido por el usuario; si no hay archivo, revisar si activó el Excel demo sin SKU
    if archivo_subido is not None:
        st.session_state["usar_demo_excel_sin_sku"] = False
        try:
            nombre_arch = archivo_subido.name.lower()
            if nombre_arch.endswith((".xlsx", ".xls")):
                df_leido = pd.read_excel(archivo_subido, dtype={"EAN_UPC": str, "Partida_Arancelaria": str, "SKU": str})
            else:
                df_leido = pd.read_csv(archivo_subido, dtype={"EAN_UPC": str, "Partida_Arancelaria": str, "SKU": str})

            df_empresa_cargada, resumen_carga_ext = preparar_archivo_externo(df_leido)
            cruce_mercado_df = cruzar_contra_mercado(df_empresa_cargada, df_raw_base)

            if modo_carga.startswith("Sumar"):
                df_combinado_raw = pd.concat(
                    [df_combinado_raw, df_empresa_cargada[COLUMNAS_MAESTRAS]],
                    ignore_index=True,
                )
                st.success(f"+{resumen_carga_ext['total_filas']:,} filas sumadas desde `{archivo_subido.name}`.")
            else:
                df_combinado_raw = df_empresa_cargada[COLUMNAS_MAESTRAS].copy()
                st.success(f"Base reemplazada: {len(df_combinado_raw):,} filas.")

            if resumen_carga_ext["skus_autogenerados"] > 0:
                st.info(
                    f"SKU automático: **{resumen_carga_ext['skus_autogenerados']}** productos sin SKU "
                    f"recibieron código único (`pd.factorize`). Ver pestaña **🔗 Carga Excel y Cruce SKU**."
                )
        except Exception as exc:
            st.error(f"Error leyendo el archivo: {exc}")

    elif st.session_state["usar_demo_excel_sin_sku"]:
        df_demo_raw = crear_dataset_demo_empresa_sin_sku(df_raw_base)
        df_empresa_cargada, resumen_carga_ext = preparar_archivo_externo(df_demo_raw)
        cruce_mercado_df = cruzar_contra_mercado(df_empresa_cargada, df_raw_base)

        if modo_carga.startswith("Sumar"):
            df_combinado_raw = pd.concat(
                [df_combinado_raw, df_empresa_cargada[COLUMNAS_MAESTRAS]],
                ignore_index=True,
            )
        else:
            df_combinado_raw = df_empresa_cargada[COLUMNAS_MAESTRAS].copy()

        st.success("🧪 Modo prueba activo: Excel de empresa (10 filas, sin columna SKU).")
        if st.button("✖️ Quitar Excel de prueba", use_container_width=True):
            st.session_state["usar_demo_excel_sin_sku"] = False
            st.rerun()

    # Combinar registros añadidos manualmente en el formulario de la pestaña "➕ Agregar Datos"
    if st.session_state["registros_manuales"]:
        df_manual = pd.DataFrame(st.session_state["registros_manuales"])
        df_combinado_raw = pd.concat([df_combinado_raw, df_manual[COLUMNAS_MAESTRAS]], ignore_index=True)
        st.info(f"Registros añadidos en vivo: **+{len(df_manual)}**")

    df_base = enriquecer_dataframe(df_combinado_raw)

    # Descarga de plantillas en Excel (.xlsx) para pruebas reales
    plantilla_xlsx = generar_excel_bytes(df_raw_base.head(3)[COLUMNAS_MAESTRAS], nombre_hoja="Plantilla_SinoRadar")
    st.download_button(
        "📗 Plantilla Excel completa (.xlsx)",
        data=plantilla_xlsx,
        file_name="plantilla_completa_sinoradar.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    demo_sin_sku_xlsx = generar_excel_bytes(
        crear_dataset_demo_empresa_sin_sku(df_raw_base),
        nombre_hoja="Productos_Empresa_Sin_SKU",
    )
    st.download_button(
        "🧪 Excel de prueba SIN SKU (.xlsx)",
        data=demo_sin_sku_xlsx,
        file_name="ejemplo_empresa_sin_sku.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()
    st.markdown("### 🎛️ Filtros de Mercado")

    anios_disp = sorted(df_base["Anio"].unique().tolist())
    anios_sel = st.multiselect("Año de análisis", options=anios_disp, default=anios_disp)

    cats_disp = sorted(df_base["Categoria"].unique().tolist())
    cats_sel = st.multiselect("Categorías", options=cats_disp, default=cats_disp)

    ciudades_disp = sorted(df_base["Ciudad_Destino"].unique().tolist())
    ciudades_sel = st.multiselect("Ciudades destino", options=ciudades_disp, default=ciudades_disp)

    transp_disp = sorted(df_base["Tipo_Transporte"].unique().tolist())
    transp_sel = st.multiselect("Tipo de transporte", options=transp_disp, default=transp_disp)

    fob_min = float(df_base["Precio_FOB_USD"].min())
    fob_max = float(df_base["Precio_FOB_USD"].max())
    if fob_max <= fob_min:
        fob_max = fob_min + 1.0
    rango_fob = st.slider(
        "Rango Precio FOB en China (USD)",
        min_value=fob_min,
        max_value=fob_max,
        value=(fob_min, fob_max),
        step=0.5,
    )

    st.divider()
    st.caption(
        f"Base activa: **{len(df_base):,}** registros | "
        f"**{df_base['SKU'].nunique()}** SKUs | "
        f"**{df_base['Categoria'].nunique()}** categorías"
    )

# Filtrado booleano en Pandas
mascara = (
    df_base["Anio"].isin(anios_sel)
    & df_base["Categoria"].isin(cats_sel)
    & df_base["Ciudad_Destino"].isin(ciudades_sel)
    & df_base["Tipo_Transporte"].isin(transp_sel)
    & df_base["Precio_FOB_USD"].between(rango_fob[0], rango_fob[1])
)
df = df_base.loc[mascara].copy()

# Banner comercial
st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-badge">Inteligencia Comercial B2B • China → Colombia • {len(df_base):,} Registros Activos</div>
        <h1 class="hero-title">SinoRadar Colombia</h1>
        <p class="hero-subtitle">
            Analítica de demanda sobre <b>{df_base['SKU'].nunique()} productos importados</b> en
            <b>{df_base['Categoria'].nunique()} categorías</b> y <b>{df_base['Ciudad_Destino'].nunique()} ciudades</b>
            para decidir qué importar, cuándo pedir a China y a qué precio vender en Colombia.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

radar_df = calcular_radar_productos(df)

# ==============================================================================
# 4. NAVEGACIÓN POR PESTAÑAS COMERCIALES
# ==============================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Radar Ejecutivo",
    "🚦 Semáforo de Inventario",
    "🧮 Simulador de Importación",
    "📈 Estacionalidad y Pronóstico",
    "🔎 Datos y Correlaciones",
    "🔗 Carga Excel y Cruce SKU",
    "➕ Agregar Datos en Vivo",
    "ℹ️ Metodología y Equipo",
])

# ------------------------------------------------------------------------------
# TAB 1: RADAR EJECUTIVO
# ------------------------------------------------------------------------------
with tab1:
    ingresos_tot = df["Ingresos_COP"].sum()
    unidades_tot = df["Unidades_Vendidas"].sum()
    margen_prom = df["Margen_Bruto_Pct"].mean()
    rotacion_global = (df["Unidades_Vendidas"].sum() / df["Unidades_Importadas"].sum()) * 100.0
    productos_verdes = int((radar_df["Semaforo_Riesgo"] == "🟢 Alta Oportunidad").sum())
    capital_estancado = df["Capital_Inmovilizado_COP"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Volumen de Mercado", formato_cop(ingresos_tot), f"{unidades_tot:,} uds vendidas")
    c2.metric("Margen Bruto Promedio", f"{margen_prom:.1f}%", "Sobre precio local")
    c3.metric("Rotación (Sell-Through)", f"{rotacion_global:.1f}%", "Vendidas / Importadas")
    c4.metric("Productos Luz Verde", f"{productos_verdes} / {len(radar_df)}", "Alta oportunidad")
    c5.metric("Capital Inmovilizado", formato_cop(capital_estancado), "Stock sobrante", delta_color="inverse")

    st.markdown("### 🎯 Matriz Estratégica: Demanda vs. Rentabilidad por Producto")
    col_g1, col_g2 = st.columns([1.45, 1])

    with col_g1:
        color_map = {
            "🟢 Alta Oportunidad": "#10B981",
            "🟡 Competitivo": "#F59E0B",
            "🔴 Alto Riesgo": "#EF4444",
        }
        fig_scatter = px.scatter(
            radar_df,
            x="Margen_Bruto_Pct",
            y="Tasa_Rotacion_Pct",
            size="Ingresos_COP",
            color="Semaforo_Riesgo",
            color_discrete_map=color_map,
            hover_name="Producto",
            hover_data={
                "Categoria": True,
                "Indice_Oportunidad": ":.1f",
                "Competidores_Prom": ":.0f",
                "Precio_Venta_Prom": ":,.0f",
                "Ingresos_COP": ":,.0f",
            },
            labels={
                "Margen_Bruto_Pct": "Margen Bruto Promedio (%)",
                "Tasa_Rotacion_Pct": "Tasa de Rotación de Inventario (%)",
                "Semaforo_Riesgo": "Clasificación",
            },
            height=450,
        )
        fig_scatter.add_vline(x=radar_df["Margen_Bruto_Pct"].median(), line_dash="dot", line_color="#94A3B8")
        fig_scatter.add_hline(y=radar_df["Tasa_Rotacion_Pct"].median(), line_dash="dot", line_color="#94A3B8")
        fig_scatter.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_g2:
        cat_resumen = (
            df.groupby("Categoria", as_index=False)
            .agg(
                Ingresos_COP=("Ingresos_COP", "sum"),
                Margen_Prom=("Margen_Bruto_Pct", "mean"),
                Unidades=("Unidades_Vendidas", "sum"),
            )
            .sort_values("Ingresos_COP", ascending=True)
        )
        fig_cat = px.bar(
            cat_resumen,
            x="Ingresos_COP",
            y="Categoria",
            orientation="h",
            color="Margen_Prom",
            color_continuous_scale="Blues",
            text=cat_resumen["Ingresos_COP"].apply(formato_cop),
            labels={"Ingresos_COP": "Ingresos Estimados (COP)", "Categoria": "", "Margen_Prom": "Margen %"},
            height=450,
        )
        fig_cat.update_traces(textposition="outside")
        fig_cat.update_layout(
            title=f"Ventas y Margen por Categoría ({len(cat_resumen)} Rubros)",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=10, r=55, t=40, b=10),
            coloraxis_colorbar=dict(title="Margen %"),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("### 🏆 Ranking Comercial de Productos Importados")
    col_rk1, col_rk2 = st.columns([2, 1])
    with col_rk1:
        buscar_rk = st.text_input("Filtrar ranking por producto o SKU:", placeholder="Ej: Proyector, Cafetera, SR-TEC, CLI-...")
    with col_rk2:
        opciones_top = [n for n in [15, 30, 50] if n < len(radar_df)] + [len(radar_df)]
        top_n = st.selectbox(
            "Cantidad a mostrar:",
            options=opciones_top,
            index=0,
            format_func=lambda n: f"Todos ({n})" if n == len(radar_df) else f"Top {n}",
        )

    ranking_vista = radar_df.copy()
    if buscar_rk.strip():
        q_rk = buscar_rk.strip().lower()
        ranking_vista = ranking_vista[
            ranking_vista["Producto"].str.lower().str.contains(q_rk)
            | ranking_vista["SKU"].str.lower().str.contains(q_rk)
            | ranking_vista["Categoria"].str.lower().str.contains(q_rk)
        ]

    st.dataframe(
        ranking_vista.head(top_n)[[
            "SKU", "Producto", "Categoria", "Indice_Oportunidad", "Semaforo_Riesgo",
            "Margen_Bruto_Pct", "Tasa_Rotacion_Pct", "Crecimiento_Mensual_Pct",
            "Precio_FOB_Prom_USD", "Precio_Venta_Prom", "Competidores_Prom",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Indice_Oportunidad": st.column_config.ProgressColumn(
                "Score SinoRadar", min_value=0, max_value=100, format="%.1f / 100"
            ),
            "Margen_Bruto_Pct": st.column_config.NumberColumn("Margen %", format="%.1f%%"),
            "Tasa_Rotacion_Pct": st.column_config.NumberColumn("Rotación %", format="%.1f%%"),
            "Crecimiento_Mensual_Pct": st.column_config.NumberColumn("Tendencia/Mes", format="%+.2f%%"),
            "Precio_FOB_Prom_USD": st.column_config.NumberColumn("FOB China", format="$%.2f USD"),
            "Precio_Venta_Prom": st.column_config.NumberColumn("Precio Colombia", format="$%,.0f"),
            "Competidores_Prom": st.column_config.NumberColumn("Competidores", format="%.0f"),
        },
    )

# ------------------------------------------------------------------------------
# TAB 2: SEMÁFORO DE RIESGO DE INVENTARIO
# ------------------------------------------------------------------------------
with tab2:
    st.markdown("### 🚦 Diagnóstico de Riesgo de Estancamiento de Inventario")
    st.caption(
        "El motor de NumPy evalúa cada producto combinando 6 variables normalizadas: Margen Bruto (26%), "
        "Rotación de Inventario (24%), Baja Saturación Competitiva (18%), Demanda (12%), Tendencia de Crecimiento (12%) "
        "y Calidad / Bajas Devoluciones (8%)."
    )

    col_s1, col_s2, col_s3 = st.columns(3)
    verdes_df = radar_df[radar_df["Semaforo_Riesgo"] == "🟢 Alta Oportunidad"]
    amarillos_df = radar_df[radar_df["Semaforo_Riesgo"] == "🟡 Competitivo"]
    rojos_df = radar_df[radar_df["Semaforo_Riesgo"] == "🔴 Alto Riesgo"]

    with col_s1:
        st.markdown(
            f"""
            <div class="insight-card insight-green">
                <h4 style="margin:0;color:#065F46;">🟢 Alta Oportunidad ({len(verdes_df)} SKUs)</h4>
                <p style="margin:0.4rem 0 0 0;font-size:0.9rem;">
                    Rotación media: <b>{verdes_df['Tasa_Rotacion_Pct'].mean() if len(verdes_df) else 0:.1f}%</b><br>
                    Margen medio: <b>{verdes_df['Margen_Bruto_Pct'].mean() if len(verdes_df) else 0:.1f}%</b><br>
                    Recomendación: Priorizar capital de compra.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            f"""
            <div class="insight-card insight-amber">
                <h4 style="margin:0;color:#92400E;">🟡 Mercado Competitivo ({len(amarillos_df)} SKUs)</h4>
                <p style="margin:0.4rem 0 0 0;font-size:0.9rem;">
                    Rotación media: <b>{amarillos_df['Tasa_Rotacion_Pct'].mean() if len(amarillos_df) else 0:.1f}%</b><br>
                    Margen medio: <b>{amarillos_df['Margen_Bruto_Pct'].mean() if len(amarillos_df) else 0:.1f}%</b><br>
                    Recomendación: Diferenciar marca o negociar menor FOB.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s3:
        st.markdown(
            f"""
            <div class="insight-card insight-red">
                <h4 style="margin:0;color:#991B1B;">🔴 Alto Riesgo de Stock ({len(rojos_df)} SKUs)</h4>
                <p style="margin:0.4rem 0 0 0;font-size:0.9rem;">
                    Rotación media: <b>{rojos_df['Tasa_Rotacion_Pct'].mean() if len(rojos_df) else 0:.1f}%</b><br>
                    Capital inmovilizado: <b>{formato_cop(rojos_df['Capital_Inmovilizado_COP'].sum()) if len(rojos_df) else '$0'}</b><br>
                    Recomendación: Evitar importación masiva; alta saturación.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_r1, col_r2 = st.columns([1, 1.4])
    with col_r1:
        conteo_sem = radar_df["Semaforo_Riesgo"].value_counts().reset_index()
        conteo_sem.columns = ["Semaforo_Riesgo", "Cantidad"]
        fig_donut = px.pie(
            conteo_sem,
            names="Semaforo_Riesgo",
            values="Cantidad",
            hole=0.55,
            color="Semaforo_Riesgo",
            color_discrete_map={
                "🟢 Alta Oportunidad": "#10B981",
                "🟡 Competitivo": "#F59E0B",
                "🔴 Alto Riesgo": "#EF4444",
            },
            title=f"Distribución del Portafolio ({len(radar_df)} SKUs)",
            height=390,
        )
        fig_donut.update_layout(paper_bgcolor="#FFFFFF", margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_r2:
        top_riesgo = radar_df.sort_values("Capital_Inmovilizado_COP", ascending=False).head(12)
        fig_riesgo = px.bar(
            top_riesgo.sort_values("Capital_Inmovilizado_COP", ascending=True),
            x="Capital_Inmovilizado_COP",
            y="Producto",
            orientation="h",
            color="Semaforo_Riesgo",
            color_discrete_map={
                "🟢 Alta Oportunidad": "#10B981",
                "🟡 Competitivo": "#F59E0B",
                "🔴 Alto Riesgo": "#EF4444",
            },
            title="Top 12 Productos con Mayor Capital Inmovilizado en Inventario",
            labels={"Capital_Inmovilizado_COP": "Capital Estancado (COP)", "Producto": ""},
            height=390,
        )
        fig_riesgo.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_riesgo, use_container_width=True)

    filtro_sem = st.radio(
        "Filtrar listado completo por semáforo:",
        options=["Todos", "🟢 Alta Oportunidad", "🟡 Competitivo", "🔴 Alto Riesgo"],
        horizontal=True,
    )
    tabla_sem = radar_df if filtro_sem == "Todos" else radar_df[radar_df["Semaforo_Riesgo"] == filtro_sem]
    st.dataframe(
        tabla_sem[[
            "SKU", "Producto", "Categoria", "Semaforo_Riesgo", "Indice_Oportunidad",
            "Tasa_Rotacion_Pct", "Inventario_Estancado", "Capital_Inmovilizado_COP",
            "Competidores_Prom", "Accion_Recomendada",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Indice_Oportunidad": st.column_config.NumberColumn("Score", format="%.1f"),
            "Tasa_Rotacion_Pct": st.column_config.NumberColumn("Rotación %", format="%.1f%%"),
            "Inventario_Estancado": st.column_config.NumberColumn("Uds Sobrantes", format="%d"),
            "Capital_Inmovilizado_COP": st.column_config.NumberColumn("Capital Estancado", format="$%,.0f"),
            "Competidores_Prom": st.column_config.NumberColumn("Competidores", format="%.0f"),
        },
    )

# ------------------------------------------------------------------------------
# TAB 3: SIMULADOR DE IMPORTACIÓN, PRECIOS Y SENSIBILIDAD (NUMPY MESHGRID)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown("### 🧮 Simulador Comercial de Importación y Fijación de Precios")
    st.caption(
        "Selecciona cualquiera de los productos de la base para precargar sus referencias del mercado colombiano "
        "y simular tu inversión, punto de equilibrio y sensibilidad ante cambios de la TRM."
    )

    col_sel1, col_sel2 = st.columns([1, 1.8])
    with col_sel1:
        cat_sim_filter = st.selectbox(
            "Filtrar por categoría:",
            options=["Todas"] + sorted(radar_df["Categoria"].unique().tolist()),
        )
    prods_opciones = (
        radar_df["Producto"].tolist()
        if cat_sim_filter == "Todas"
        else radar_df[radar_df["Categoria"] == cat_sim_filter]["Producto"].tolist()
    )
    with col_sel2:
        prod_sel = st.selectbox("Selecciona un producto de referencia:", options=prods_opciones)

    fila_prod = radar_df[radar_df["Producto"] == prod_sel].iloc[0]
    df_prod_hist = df[df["Producto"] == prod_sel]

    p25_mercado, p50_mercado, p75_mercado = np.percentile(df_prod_hist["Precio_Venta_Mercado_COP"], [25, 50, 75])
    trm_actual_prom = float(df["TRM_COP"].iloc[-1])

    col_inp, col_out = st.columns([1, 1.35])

    with col_inp:
        st.markdown("#### Parámetros de tu Operación")
        unidades_lote = st.number_input("Cantidad a importar (MOQ unidades)", min_value=20, max_value=50000, value=300, step=20)
        fob_sim = st.number_input("Precio FOB negociado en China (USD)", min_value=0.5, max_value=1000.0, value=float(round(fila_prod["Precio_FOB_Prom_USD"], 2)), step=0.5)
        flete_sim = st.number_input("Flete internacional unitario (USD)", min_value=0.2, max_value=200.0, value=float(round(fila_prod["Flete_Prom_USD"], 2)), step=0.2)
        trm_sim = st.slider("TRM proyectada (COP / USD)", min_value=3600, max_value=5000, value=int(np.clip(round(trm_actual_prom, -1), 3600, 5000)), step=20)
        arancel_sim = st.slider("Arancel de importación (%)", min_value=0, max_value=25, value=int(np.clip(round(fila_prod["Arancel_Prom"] * 100), 0, 25)), step=1) / 100.0
        gastos_nac_sim = st.slider("Nacionalización y logística local (% sobre CIF)", min_value=3, max_value=20, value=8, step=1) / 100.0
        tasa_venta_esp = st.slider("Rotación esperada del lote (%)", min_value=50, max_value=100, value=int(np.clip(round(fila_prod["Tasa_Rotacion_Pct"]), 50, 98)), step=1) / 100.0

        precio_sugerido = int(round(p50_mercado / 500.0) * 500)
        precio_venta_sim = st.number_input(
            "Tu precio de venta objetivo en Colombia (COP)",
            min_value=5000,
            max_value=10000000,
            value=max(5000, precio_sugerido),
            step=1000,
        )

    iva_sim = 0.19
    cif_unit_usd = fob_sim + flete_sim
    arancel_unit_usd = cif_unit_usd * arancel_sim
    iva_unit_usd = (cif_unit_usd + arancel_unit_usd) * iva_sim
    nac_unit_usd = cif_unit_usd * gastos_nac_sim
    costo_aterrizado_sim = (cif_unit_usd + arancel_unit_usd + iva_unit_usd + nac_unit_usd) * trm_sim

    inversion_total = costo_aterrizado_sim * unidades_lote
    unidades_vendidas_esp = int(np.floor(unidades_lote * tasa_venta_esp))
    ingresos_esp = unidades_vendidas_esp * precio_venta_sim
    utilidad_unit = precio_venta_sim - costo_aterrizado_sim
    margen_sim = (utilidad_unit / precio_venta_sim * 100.0) if precio_venta_sim > 0 else 0.0
    utilidad_neta_lote = ingresos_esp - inversion_total
    roi_lote = (utilidad_neta_lote / inversion_total * 100.0) if inversion_total > 0 else 0.0
    punto_equilibrio_uds = int(np.ceil(inversion_total / precio_venta_sim)) if precio_venta_sim > 0 else 0

    with col_out:
        st.markdown("#### Resultado Financiero Proyectado")
        k1, k2, k3 = st.columns(3)
        k1.metric("Costo Aterrizado Unit.", f"${costo_aterrizado_sim:,.0f}", f"CIF ${cif_unit_usd:.2f} USD")
        k2.metric("Utilidad Unitaria", f"${utilidad_unit:,.0f}", f"Margen {margen_sim:.1f}%")
        k3.metric("Punto de Equilibrio", f"{punto_equilibrio_uds:,} uds", f"{(punto_equilibrio_uds / unidades_lote * 100):.1f}% del lote")

        k4, k5, k6 = st.columns(3)
        k4.metric("Inversión Total Lote", formato_cop(inversion_total), f"{unidades_lote:,} unidades")
        k5.metric("Utilidad Neta Esperada", formato_cop(utilidad_neta_lote), f"Vendiendo {unidades_vendidas_esp:,} uds")
        k6.metric("ROI del Lote", f"{roi_lote:.1f}%", "Rentable" if roi_lote > 20 else "Ajustado")

        if precio_venta_sim < p25_mercado:
            estado_precio = ("insight-amber", f"⚡ Precio agresivo (por debajo del P25 de ${p25_mercado:,.0f} COP). Acelerará ventas, pero vigila tu margen.")
        elif precio_venta_sim <= p75_mercado:
            estado_precio = ("insight-green", f"✅ Precio en rango competitivo del mercado colombiano (P25: ${p25_mercado:,.0f} — Mediana: ${p50_mercado:,.0f} — P75: ${p75_mercado:,.0f} COP).")
        else:
            estado_precio = ("insight-red", f"⚠️ Precio por encima del P75 del mercado (${p75_mercado:,.0f} COP). Alto riesgo de rotación lenta frente a {fila_prod['Competidores_Prom']:.0f} competidores.")

        st.markdown(f'<div class="insight-card {estado_precio[0]}">{estado_precio[1]}</div>', unsafe_allow_html=True)

        trms_grid = np.linspace(trm_sim * 0.92, trm_sim * 1.08, 5)
        precios_grid = np.linspace(precio_venta_sim * 0.85, precio_venta_sim * 1.15, 5)
        P_mat, T_mat = np.meshgrid(precios_grid, trms_grid)

        costo_mat = (cif_unit_usd + arancel_unit_usd + iva_unit_usd + nac_unit_usd) * T_mat
        inv_mat = costo_mat * unidades_lote
        ing_mat = unidades_vendidas_esp * P_mat
        roi_mat = ((ing_mat - inv_mat) / inv_mat) * 100.0

        fig_sens = go.Figure(
            data=go.Heatmap(
                z=np.round(roi_mat, 1),
                x=[f"${p:,.0f}" for p in precios_grid],
                y=[f"${t:,.0f}" for t in trms_grid],
                colorscale="RdYlGn",
                zmid=15,
                text=np.round(roi_mat, 1),
                texttemplate="%{text}%",
                colorbar=dict(title="ROI %"),
            )
        )
        fig_sens.update_layout(
            title="Análisis de Sensibilidad (NumPy): ROI % según TRM vs. Precio de Venta",
            xaxis_title="Precio de Venta en Colombia (COP)",
            yaxis_title="Escenario TRM (COP/USD)",
            height=330,
            margin=dict(l=10, r=10, t=45, b=10),
        )
        st.plotly_chart(fig_sens, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 4: ESTACIONALIDAD, PRONÓSTICO (NP.POLYFIT) Y ANÁLISIS REGIONAL
# ------------------------------------------------------------------------------
with tab4:
    st.markdown("### 📈 Evolución Mensual, Pronóstico de Demanda y Planificación de Pedidos")

    cat_pronostico = st.selectbox(
        "Analizar tendencia por categoría (o mercado total):",
        options=["Todas las categorías"] + sorted(df["Categoria"].unique().tolist()),
    )
    df_trend = df if cat_pronostico == "Todas las categorías" else df[df["Categoria"] == cat_pronostico]

    serie = (
        df_trend.groupby("Fecha", as_index=False)
        .agg(Unidades_Vendidas=("Unidades_Vendidas", "sum"), Ingresos_COP=("Ingresos_COP", "sum"))
        .sort_values("Fecha")
    )

    x_hist = np.arange(len(serie), dtype=float)
    y_hist = serie["Unidades_Vendidas"].to_numpy(dtype=float)

    if len(serie) >= 2:
        coef = np.polyfit(x_hist, y_hist, 1)
        y_tendencia = np.polyval(coef, x_hist)

        x_futuro = np.arange(len(serie), len(serie) + 3, dtype=float)
        y_futuro = np.maximum(0, np.polyval(coef, x_futuro))
        fechas_futuras = pd.date_range(start=serie["Fecha"].max() + pd.DateOffset(months=1), periods=3, freq="MS")

        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=serie["Fecha"], y=serie["Unidades_Vendidas"],
            mode="lines+markers", name="Ventas Históricas (Uds)",
            line=dict(color="#1E3A8A", width=3),
        ))
        fig_ts.add_trace(go.Scatter(
            x=serie["Fecha"], y=y_tendencia,
            mode="lines", name="Tendencia Lineal (NumPy polyfit)",
            line=dict(color="#94A3B8", width=2, dash="dash"),
        ))
        fig_ts.add_trace(go.Scatter(
            x=fechas_futuras, y=y_futuro,
            mode="lines+markers", name="Proyección 3 Meses",
            line=dict(color="#10B981", width=3, dash="dot"),
            marker=dict(size=9),
        ))
        fig_ts.update_layout(
            title=f"Comportamiento Histórico y Proyección de Demanda — {cat_pronostico}",
            xaxis_title="Mes",
            yaxis_title="Unidades Vendidas",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        est_mes = df_trend.groupby("Mes", as_index=False)["Unidades_Vendidas"].mean()
        mes_pico = int(est_mes.loc[est_mes["Unidades_Vendidas"].idxmax(), "Mes"])
        transito_prom = float(df_trend["Tiempo_Transito_Dias"].mean())
        meses_anticipacion = int(np.ceil((transito_prom + 18) / 30.0))
        mes_pedido = ((mes_pico - 1 - meses_anticipacion) % 12) + 1

        st.markdown(
            f"""
            <div class="insight-card insight-green">
                <b>🗓️ Recomendación Logística para {cat_pronostico}:</b>
                El pico promedio de ventas en Colombia ocurre en <b>{NOMBRES_MESES[mes_pico]}</b>.
                Con un tiempo promedio de tránsito de <b>{transito_prom:.0f} días</b> (más producción y despacho),
                la orden de compra a proveedores en China debe emitirse en <b>{NOMBRES_MESES[mes_pedido]}</b>
                para evitar quiebres de stock en temporada alta.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Se necesitan al menos 2 meses distintos en los datos filtrados para calcular la tendencia lineal (`np.polyfit`).")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        est_chart = df_trend.groupby(["Mes", "Nombre_Mes"], as_index=False)["Unidades_Vendidas"].mean().sort_values("Mes")
        fig_est = px.bar(
            est_chart,
            x="Nombre_Mes",
            y="Unidades_Vendidas",
            color="Unidades_Vendidas",
            color_continuous_scale="Teal",
            title="Estacionalidad Promedio por Mes del Año",
            labels={"Nombre_Mes": "Mes", "Unidades_Vendidas": "Unidades Promedio"},
            height=360,
        )
        fig_est.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", showlegend=False)
        st.plotly_chart(fig_est, use_container_width=True)

    with col_e2:
        ciudad_res = (
            df_trend.groupby("Ciudad_Destino", as_index=False)
            .agg(Ingresos_COP=("Ingresos_COP", "sum"), Margen_Prom=("Margen_Bruto_Pct", "mean"))
            .sort_values("Ingresos_COP", ascending=False)
        )
        fig_ciu = px.bar(
            ciudad_res,
            x="Ciudad_Destino",
            y="Ingresos_COP",
            color="Margen_Prom",
            color_continuous_scale="Blues",
            text=ciudad_res["Ingresos_COP"].apply(formato_cop),
            title=f"Demanda Regional en Colombia ({len(ciudad_res)} Ciudades)",
            labels={"Ciudad_Destino": "Ciudad", "Ingresos_COP": "Ingresos (COP)", "Margen_Prom": "Margen %"},
            height=360,
        )
        fig_ciu.update_traces(textposition="outside")
        fig_ciu.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig_ciu, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 5: EXPLORADOR DE BASE DE DATOS Y ANÁLISIS ESTADÍSTICO
# ------------------------------------------------------------------------------
with tab5:
    st.markdown("### 🔎 Análisis Estadístico y Explorador de Registros")

    col_stat1, col_stat2 = st.columns([1.15, 1])
    with col_stat1:
        cols_corr = [
            "Precio_FOB_USD", "Costo_Aterrizado_COP", "Precio_Venta_Mercado_COP",
            "Margen_Bruto_Pct", "Unidades_Vendidas", "Tasa_Rotacion_Pct",
            "Competidores_Activos", "Tasa_Devolucion_Pct",
        ]
        corr_matrix = df[cols_corr].corr(numeric_only=True)
        fig_corr = px.imshow(
            np.round(corr_matrix, 2),
            text_auto=True,
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Matriz de Correlación de Variables Comerciales (Pandas .corr)",
            height=430,
        )
        fig_corr.update_layout(margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_corr, use_container_width=True)

    with col_stat2:
        st.markdown("#### Estadística Descriptiva (`df.describe()`)")
        desc = df[[
            "TRM_COP", "Precio_FOB_USD", "Costo_Aterrizado_COP",
            "Precio_Venta_Mercado_COP", "Margen_Bruto_Pct",
            "Unidades_Vendidas", "Tasa_Rotacion_Pct", "Competidores_Activos",
        ]].describe().T[["mean", "std", "min", "50%", "max"]]
        desc.columns = ["Promedio", "Desv. Est.", "Mínimo", "Mediana", "Máximo"]
        st.dataframe(desc.style.format("{:,.2f}"), use_container_width=True, height=370)

    st.markdown("#### Buscador de Registros Históricos")
    busqueda = st.text_input(
        "Buscar por producto, SKU, código de barras (EAN), partida DIAN, ciudad o puerto:",
        placeholder="Ej: Cafetera, SR-GAM-01, 6901234000252, 8543.70.90.00, Bucaramanga...",
    )
    df_tabla = df.copy()
    if busqueda.strip():
        q = busqueda.strip().lower()
        df_tabla = df_tabla[
            df_tabla["Producto"].str.lower().str.contains(q)
            | df_tabla["SKU"].str.lower().str.contains(q)
            | df_tabla["EAN_UPC"].astype(str).str.lower().str.contains(q)
            | df_tabla["Partida_Arancelaria"].astype(str).str.lower().str.contains(q)
            | df_tabla["Ciudad_Destino"].str.lower().str.contains(q)
            | df_tabla["Puerto_Entrada"].str.lower().str.contains(q)
        ]

    st.dataframe(
        df_tabla[[
            "Fecha", "SKU", "EAN_UPC", "Partida_Arancelaria", "Producto", "Categoria",
            "Ciudad_Destino", "Tipo_Transporte", "Precio_FOB_USD", "Costo_Aterrizado_COP",
            "Precio_Venta_Mercado_COP", "Unidades_Importadas", "Unidades_Vendidas",
            "Tasa_Rotacion_Pct", "Margen_Bruto_Pct", "Competidores_Activos",
        ]].head(500),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando hasta 500 de {len(df_tabla):,} registros filtrados.")

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_export = df_tabla.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ Descargar registros filtrados (.csv)",
            data=csv_export,
            file_name="sinoradar_datos_filtrados.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_exp2:
        xlsx_export = generar_excel_bytes(df_tabla.head(5000), nombre_hoja="Datos_Filtrados")
        st.download_button(
            label="📗 Descargar registros filtrados en Excel (.xlsx)",
            data=xlsx_export,
            file_name="sinoradar_datos_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

# ------------------------------------------------------------------------------
# TAB 6: CARGA EXCEL, GENERACIÓN AUTOMÁTICA DE SKU Y CRUCE CONTRA EL MERCADO
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("### 🔗 Carga de Excel Externo, Gestión Inteligente de SKU y Cruce con el Mercado")
    st.caption(
        "Módulo implementado para resolver cómo una empresa real sube su propio Excel (.xlsx/.csv) "
        "aunque no tenga columna de SKU ni use los códigos internos de SinoRadar."
    )

    col_exp_a, col_exp_b, col_exp_c = st.columns(3)
    with col_exp_a:
        st.markdown(
            """
            <div class="insight-card insight-green">
                <b>1. Si tu Excel ya trae SKU propio</b><br>
                <span style="font-size:0.89rem;">
                    SinoRadar respeta directamente los códigos internos de tu empresa (ej. <code>EMP-001</code>) sin exigir prefijo <code>SR-</code>.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_exp_b:
        st.markdown(
            """
            <div class="insight-card">
                <b>2. Si tu Excel viene SIN columna SKU</b><br>
                <span style="font-size:0.89rem;">
                    Python crea automáticamente códigos consistentes (<code>CLI-CAT-001</code>) con <code>pd.factorize()</code>: el mismo producto mantiene el mismo SKU en todos los meses.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_exp_c:
        st.markdown(
            """
            <div class="insight-card insight-amber">
                <b>3. Cruce contra el mercado</b><br>
                <span style="font-size:0.89rem;">
                    Compara tus productos contra nuestra base usando <b>Código de Barras (EAN/UPC)</b>, <b>similitud de nombre</b> o <b>Partida Arancelaria DIAN</b>.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if cruce_mercado_df is None or resumen_carga_ext is None:
        st.markdown(
            """
            <div class="insight-card">
                <b>¿Cómo probarlo en segundos?</b><br>
                Puedes subir tu propio archivo <code>.xlsx</code> o <code>.csv</code> en la barra lateral izquierda,
                descargar el <b>Excel de prueba SIN SKU</b> desde la barra lateral, o hacer clic en el botón de abajo
                para cargar una empresa de demostración (5 productos × 2 meses, sin columna SKU ni costo aterrizado) y ver todo el cruce en vivo.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶️ Probar ahora con Excel de ejemplo (sin columna SKU)", type="primary", use_container_width=True):
            st.session_state["usar_demo_excel_sin_sku"] = True
            st.rerun()
    else:
        # KPIs del archivo cargado
        k_e1, k_e2, k_e3, k_e4 = st.columns(4)
        k_e1.metric("Filas cargadas", f"{resumen_carga_ext['total_filas']:,}", resumen_carga_ext["origen_sku"])
        k_e2.metric("SKUs propios respetados", f"{resumen_carga_ext['skus_propios']}")
        k_e3.metric("SKUs autogenerados", f"{resumen_carga_ext['skus_autogenerados']}", "vía pd.factorize")
        emparejados = int((~cruce_mercado_df["Metodo_Cruce"].str.startswith("🆕")).sum())
        k_e4.metric("Emparejados vs. Mercado", f"{emparejados} / {len(cruce_mercado_df)}", "EAN / Nombre / DIAN")

        if resumen_carga_ext["costos_calculados_auto"]:
            st.info(
                "💡 El archivo cargado no traía `Costo_Aterrizado_COP` completo: SinoRadar lo calculó automáticamente "
                "con la fórmula aduanera colombiana `(CIF + Arancel + IVA 19% + 8% Nac.) × TRM`."
            )

        st.markdown("#### 📋 Resultado del Cruce Automático: Tu Empresa vs. Mercado SinoRadar")
        st.dataframe(
            cruce_mercado_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "SKU_Asignado": st.column_config.TextColumn("SKU en Sistema"),
                "Origen_SKU": st.column_config.TextColumn("Origen del SKU"),
                "Producto_Empresa": st.column_config.TextColumn("Tu Producto"),
                "Metodo_Cruce": st.column_config.TextColumn("Cómo se cruzó"),
                "Referencia_Mercado": st.column_config.TextColumn("Referencia en SinoRadar"),
                "Tu_Costo_COP": st.column_config.NumberColumn("Tu Costo", format="$%,.0f"),
                "Tu_Precio_COP": st.column_config.NumberColumn("Tu Precio", format="$%,.0f"),
                "Precio_Mercado_COP": st.column_config.NumberColumn("Precio Mercado", format="$%,.0f"),
                "Dif_Precio_Pct": st.column_config.NumberColumn("Dif. Precio", format="%+.1f%%"),
                "Tu_Margen_Pct": st.column_config.NumberColumn("Tu Margen", format="%.1f%%"),
                "Margen_Mercado_Pct": st.column_config.NumberColumn("Margen Mercado", format="%.1f%%"),
                "Tu_Rotacion_Pct": st.column_config.NumberColumn("Tu Rotación", format="%.1f%%"),
            },
        )

        # Gráfico comparativo Tu Precio vs. Precio Mercado para productos emparejados
        comp_plot = cruce_mercado_df.dropna(subset=["Precio_Mercado_COP"])
        if not comp_plot.empty:
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(
                name="Tu Precio de Venta (COP)",
                x=comp_plot["Producto_Empresa"],
                y=comp_plot["Tu_Precio_COP"],
                marker_color="#1E3A8A",
            ))
            fig_comp.add_trace(go.Bar(
                name="Precio Promedio Mercado SinoRadar (COP)",
                x=comp_plot["Producto_Empresa"],
                y=comp_plot["Precio_Mercado_COP"],
                marker_color="#10B981",
            ))
            fig_comp.update_layout(
                barmode="group",
                title="Comparativa Directa: Tu Precio de Venta vs. Referencia del Mercado Colombiano",
                xaxis_title="Producto de tu archivo",
                yaxis_title="Precio (COP)",
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                height=360,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            xlsx_con_sku = generar_excel_bytes(
                df_empresa_cargada[COLUMNAS_MAESTRAS],
                nombre_hoja="Empresa_Con_SKU_Asignado",
            )
            st.download_button(
                "📗 Descargar tu archivo enriquecido con SKUs y costos (.xlsx)",
                data=xlsx_con_sku,
                file_name="empresa_enriquecida_con_sku_sinoradar.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_d2:
            xlsx_cruce = generar_excel_bytes(cruce_mercado_df, nombre_hoja="Cruce_vs_Mercado")
            st.download_button(
                "📊 Descargar reporte de cruce contra el mercado (.xlsx)",
                data=xlsx_cruce,
                file_name="reporte_cruce_mercado_sinoradar.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

# ------------------------------------------------------------------------------
# TAB 7: AGREGAR NUEVOS PRODUCTOS / IMPORTACIONES EN VIVO
# ------------------------------------------------------------------------------
with tab7:
    st.markdown("### ➕ Registrar Nuevos Productos e Importaciones en Vivo")
    st.caption(
        "Añade nuevos productos o embarques directamente desde la web. Si dejas el SKU en blanco, "
        "la plataforma crea uno automáticamente. El sistema calcula el costo aterrizado en Colombia "
        "(CIF + Arancel + IVA 19% + Nacionalización × TRM), concatena con `pd.concat` y actualiza todo al instante."
    )

    with st.form("form_nuevo_registro", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            nuevo_sku = st.text_input("SKU del producto (opcional — vacío = automático)", value="")
            nuevo_prod = st.text_input("Nombre del producto", placeholder="Ej: Aspiradora Robot Láser LiDAR")
            nueva_cat = st.selectbox("Categoría", options=sorted(df_base["Categoria"].unique().tolist()) + ["Nueva Categoría"])
            if nueva_cat == "Nueva Categoría":
                nueva_cat_custom = st.text_input("Escribe el nombre de la nueva categoría", value="Electrónica Industrial")
            else:
                nueva_cat_custom = nueva_cat
            nueva_ciudad = st.selectbox("Ciudad destino", options=["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Cartagena", "Pereira"])
            nuevo_ean = st.text_input("Código de barras EAN/UPC (opcional)", placeholder="Ej: 6901234000252")

        with f2:
            nueva_fecha = st.date_input("Fecha del embarque / mes", value=datetime.date(2026, 11, 1))
            nuevo_transp = st.selectbox("Tipo de transporte", options=["Marítimo", "Aéreo"])
            nuevo_fob = st.number_input("Precio FOB en China (USD)", min_value=0.5, max_value=2000.0, value=14.5, step=0.5)
            nuevo_flete = st.number_input("Flete unitario (USD)", min_value=0.2, max_value=300.0, value=2.4, step=0.2)
            nuevo_arancel = st.slider("Arancel (%)", min_value=0, max_value=25, value=10, step=1) / 100.0
            nueva_partida = st.text_input("Partida arancelaria DIAN (opcional)", placeholder="Ej: 8509.80.20.00")

        with f3:
            nueva_trm = st.number_input("TRM del mes (COP/USD)", min_value=3500.0, max_value=5500.0, value=4250.0, step=10.0)
            nuevo_precio_venta = st.number_input("Precio de venta en Colombia (COP)", min_value=5000, max_value=10000000, value=210000, step=5000)
            nuevas_imp = st.number_input("Unidades importadas", min_value=10, max_value=100000, value=400, step=10)
            nuevas_ven = st.number_input("Unidades vendidas", min_value=0, max_value=100000, value=370, step=10)
            nuevos_comp = st.number_input("Competidores activos estimados", min_value=1, max_value=500, value=22, step=1)

        enviado = st.form_submit_button("✅ Calcular Costo Aterrizado y Agregar a la Plataforma", use_container_width=True)

        if enviado:
            if not nuevo_prod.strip():
                st.error("Por favor ingresa un nombre de producto.")
            else:
                cif = nuevo_fob + nuevo_flete
                arancel_usd = cif * nuevo_arancel
                iva_usd = (cif + arancel_usd) * 0.19
                nac_usd = cif * 0.08
                costo_aterrizado = int(np.round(((cif + arancel_usd + iva_usd + nac_usd) * nueva_trm) / 100.0) * 100)
                puerto_auto = "Aéreo El Dorado" if nuevo_transp == "Aéreo" else ("Buenaventura" if nueva_ciudad in ["Bogotá", "Cali", "Pereira"] else "Cartagena")
                transito_auto = 11 if nuevo_transp == "Aéreo" else 46

                if nuevo_sku.strip():
                    sku_final = nuevo_sku.strip().upper()
                else:
                    pref = re.sub(r"[^a-z]", "", normalizar_texto(nueva_cat_custom))[:3].upper().ljust(3, "X")
                    sku_final = f"VIV-{pref}-{len(st.session_state['registros_manuales']) + 1:03d}"

                partida_final = nueva_partida.strip() or PARTIDAS_DIAN_DEFAULT.get(nueva_cat_custom.strip(), "")

                nuevo_reg = {
                    "Fecha": nueva_fecha.strftime("%Y-%m-01"),
                    "Anio": nueva_fecha.year,
                    "Mes": nueva_fecha.month,
                    "SKU": sku_final,
                    "EAN_UPC": limpiar_codigo_texto(nuevo_ean),
                    "Partida_Arancelaria": partida_final,
                    "Producto": nuevo_prod.strip(),
                    "Categoria": nueva_cat_custom.strip(),
                    "Ciudad_Destino": nueva_ciudad,
                    "Tipo_Transporte": nuevo_transp,
                    "Puerto_Entrada": puerto_auto,
                    "Tiempo_Transito_Dias": transito_auto,
                    "TRM_COP": nueva_trm,
                    "Precio_FOB_USD": nuevo_fob,
                    "Flete_Unitario_USD": nuevo_flete,
                    "Arancel_Pct": nuevo_arancel,
                    "IVA_Pct": 0.19,
                    "Costo_Aterrizado_COP": costo_aterrizado,
                    "Precio_Venta_Mercado_COP": int(nuevo_precio_venta),
                    "Unidades_Importadas": int(nuevas_imp),
                    "Unidades_Vendidas": int(min(nuevas_ven, nuevas_imp)),
                    "Competidores_Activos": int(nuevos_comp),
                    "Calificacion_Mercado": 4.6,
                    "Tasa_Devolucion_Pct": 2.4,
                }
                st.session_state["registros_manuales"].append(nuevo_reg)
                st.success(
                    f"Registro agregado: **{nuevo_reg['Producto']}** (`{sku_final}`) | Costo aterrizado calculado: "
                    f"**${costo_aterrizado:,.0f} COP**. Recargando métricas..."
                )
                st.rerun()

    if st.session_state["registros_manuales"]:
        st.markdown("#### Registros añadidos en esta sesión")
        df_ses = pd.DataFrame(st.session_state["registros_manuales"])
        st.dataframe(df_ses, use_container_width=True, hide_index=True)

        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            csv_master = df_combinado_raw.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "💾 Base Maestra Actualizada (.csv)",
                data=csv_master,
                file_name="importaciones_china_colombia_actualizada.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_act2:
            xlsx_ses = generar_excel_bytes(df_ses, nombre_hoja="Registros_En_Vivo")
            st.download_button(
                "📗 Registros de sesión (.xlsx)",
                data=xlsx_ses,
                file_name="registros_en_vivo_sinoradar.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_act3:
            if st.button("🗑️ Limpiar registros de sesión", use_container_width=True):
                st.session_state["registros_manuales"] = []
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 8: METODOLOGÍA, ARQUITECTURA PYTHON Y EQUIPO
# ------------------------------------------------------------------------------
with tab8:
    st.markdown("### ℹ️ Arquitectura Técnica, Sustentación de Datos y Equipo")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            r"""
            #### 1. Sustentación y Escalabilidad de la Base de Datos
            La base de datos inicial (`importaciones_china_colombia.csv`) contiene **14,400 registros estructurados**
            generados de forma reproducible mediante `generar_datos.py` (**120 productos reales** × 10 categorías ×
            24 meses × 5 ciudades colombianas), incorporando **código de barras (`EAN_UPC`)** y **partida arancelaria DIAN**:
            - **Fórmula aduanera real en Colombia:**
              $$\text{CIF} = \text{FOB} + \text{Flete}$$
              $$\text{Costo Aterrizado} = \left(\text{CIF} + \text{Arancel} + \text{IVA}_{19\%} + \text{Nacionalización}\right) \times \text{TRM}$$
            - **Gestión de archivos externos (Excel y CSV):** Respeta los SKUs propios de cada empresa o los crea automáticamente con `pd.factorize` si el Excel no trae esa columna, y cruza productos contra el mercado mediante **EAN/UPC**, **Partida DIAN** o **similitud de nombre**.
            - **Estacionalidad comercial:** Modela picos verificables en Colombia (Día de la Madre, prima de junio, Black Friday y Navidad).
            """
        )

    with col_m2:
        st.markdown(
            """
            #### 2. Conceptos de Python, Pandas y NumPy Aplicados
            - **Pandas + OpenPyXL:** Lectura y exportación nativa de Excel (`.xlsx`) y CSV, autogeneración determinística de SKU (`pd.factorize`), fusión dinámica (`pd.concat`), indexación booleana múltiple (`.isin()`, `.between()`), agregaciones (`groupby().agg()`), series de tiempo (`pd.to_datetime`) y matrices de correlación (`.corr()`).
            - **NumPy:** Operaciones vectorizadas sobre 14,400+ filas, control seguro de divisiones (`np.where`), normalización Min-Max, puntaje compuesto por producto punto (`np.dot`), clasificación condicional multicriterio (`np.select`), percentiles de mercado (`np.percentile`), regresión lineal de tendencia (`np.polyfit` / `np.polyval`) y análisis de sensibilidad 2D (`np.meshgrid`).
            - **Cruce de catálogos externos:** Comparación priorizada por `EAN_UPC`, `Partida_Arancelaria` DIAN y similitud textual (`difflib.SequenceMatcher` + coincidencia de palabras clave).
            """
        )

    st.divider()
    st.markdown("#### 👥 Integrantes del Proyecto")
    e1, e2, e3, e4 = st.columns(4)
    e1.info("**Isabella Prieto Morales**\n\nAnálisis de Mercado & Datos")
    e2.info("**Santiago Plazas**\n\nModelo Comercial & Negocio")
    e3.info("**Nicolás Alandete**\n\nArquitectura Python & Importaciones")
    e4.info("**Emmanuel Caballero**\n\nDesarrollo Web & Visualización")
