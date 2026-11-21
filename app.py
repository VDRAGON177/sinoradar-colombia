"""
SinoRadar Colombia v2.0 - Plataforma de Inteligencia Comercial para Importaciones China -> Colombia
Desarrollado en Python con Pandas, NumPy, Plotly y Streamlit.

Características principales:
  - Base de datos inicial de 14,400 registros (120 productos reales x 24 meses x 5 ciudades x 10 categorías)
  - Carga masiva de nuevos datos vía CSV (modo Combinar con pd.concat o Reemplazar)
  - Formulario en vivo para registrar nuevas importaciones y ver su impacto inmediato en KPIs y Semáforo
  - Motor analítico vectorizado en NumPy y Pandas

Equipo del proyecto:
  - Isabella Prieto Morales
  - Santiago Plazas
  - Nicolás Alandete
  - Emmanuel Caballero
"""

import datetime
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
        font-size: 0.90rem !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

COLUMNAS_REQUERIDAS = [
    "Fecha", "Anio", "Mes", "SKU", "Producto", "Categoria", "Ciudad_Destino",
    "Tipo_Transporte", "Puerto_Entrada", "Tiempo_Transito_Dias", "TRM_COP",
    "Precio_FOB_USD", "Flete_Unitario_USD", "Arancel_Pct", "IVA_Pct",
    "Costo_Aterrizado_COP", "Precio_Venta_Mercado_COP", "Unidades_Importadas",
    "Unidades_Vendidas", "Competidores_Activos", "Calificacion_Mercado",
    "Tasa_Devolucion_Pct"
]

NOMBRES_MESES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}

if "registros_manuales" not in st.session_state:
    st.session_state["registros_manuales"] = []


# ==============================================================================
# 2. MOTOR DE DATOS Y CÁLCULO ANALÍTICO (PANDAS + NUMPY)
# ==============================================================================
@st.cache_data
def cargar_csv_base(ruta: str = "importaciones_china_colombia.csv") -> pd.DataFrame:
    return pd.read_csv(ruta)


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

with st.sidebar:
    st.markdown("## 🚢 SinoRadar Colombia")
    st.caption("Inteligencia Comercial China → Colombia")
    st.divider()

    st.markdown("### 📂 Expansión de Base de Datos")
    modo_carga = st.radio(
        "Modo al subir archivo CSV:",
        options=["Sumar a la base actual (pd.concat)", "Reemplazar toda la base"],
        index=0,
    )
    archivo_subido = st.file_uploader(
        "Subir CSV adicional o propio",
        type=["csv"],
        help="Sube registros adicionales para ampliar el análisis en tiempo real.",
    )

    df_combinado_raw = df_raw_base.copy()
    if archivo_subido is not None:
        try:
            df_extra_csv = pd.read_csv(archivo_subido)
            faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df_extra_csv.columns]
            if faltantes:
                st.error(f"Faltan columnas: {', '.join(faltantes)}")
            else:
                if modo_carga.startswith("Sumar"):
                    df_combinado_raw = pd.concat([df_combinado_raw, df_extra_csv[COLUMNAS_REQUERIDAS]], ignore_index=True)
                    st.success(f"+{len(df_extra_csv):,} filas añadidas.")
                else:
                    df_combinado_raw = df_extra_csv[COLUMNAS_REQUERIDAS].copy()
                    st.success(f"Base reemplazada: {len(df_combinado_raw):,} filas.")
        except Exception as exc:
            st.error(f"Error leyendo el CSV: {exc}")

    # Combinar registros añadidos manualmente en el formulario de la pestaña "➕ Agregar Datos"
    if st.session_state["registros_manuales"]:
        df_manual = pd.DataFrame(st.session_state["registros_manuales"])
        df_combinado_raw = pd.concat([df_combinado_raw, df_manual[COLUMNAS_REQUERIDAS]], ignore_index=True)
        st.info(f"Registros añadidos en vivo: **+{len(df_manual)}**")

    df_base = enriquecer_dataframe(df_combinado_raw)

    # Plantilla vacía/ejemplo para que cualquier usuario pueda crear su CSV
    plantilla_csv = df_raw_base.head(3).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📄 Descargar plantilla CSV (3 filas ejemplo)",
        data=plantilla_csv,
        file_name="plantilla_importaciones_sinoradar.csv",
        mime="text/csv",
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Radar Ejecutivo",
    "🚦 Semáforo de Inventario",
    "🧮 Simulador de Importación",
    "📈 Estacionalidad y Pronóstico",
    "🔎 Datos y Correlaciones",
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
            title="Ventas y Margen por Categoría (10 Rubros)",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            margin=dict(l=10, r=55, t=40, b=10),
            coloraxis_colorbar=dict(title="Margen %"),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("### 🏆 Ranking Comercial de Productos Importados")
    col_rk1, col_rk2 = st.columns([2, 1])
    with col_rk1:
        buscar_rk = st.text_input("Filtrar ranking por producto o SKU:", placeholder="Ej: Proyector, Cafetera, SR-TEC...")
    with col_rk2:
        top_n = st.selectbox("Cantidad a mostrar:", options=[15, 30, 50, len(radar_df)], index=0, format_func=lambda n: f"Todos ({n})" if n == len(radar_df) else f"Top {n}")

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
            "Precio_FOB_Prom_USD", "Precio_Venta_Prom", "Competidores_Prom"
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
            "Competidores_Prom", "Accion_Recomendada"
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
        "Selecciona cualquiera de los productos de la base para precargar sus referencias reales del mercado colombiano "
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
        trm_sim = st.slider("TRM proyectada (COP / USD)", min_value=3600, max_value=5000, value=int(round(trm_actual_prom, -1)), step=20)
        arancel_sim = st.slider("Arancel de importación (%)", min_value=0, max_value=25, value=int(round(fila_prod["Arancel_Prom"] * 100)), step=1) / 100.0
        gastos_nac_sim = st.slider("Nacionalización y logística local (% sobre CIF)", min_value=3, max_value=20, value=8, step=1) / 100.0
        tasa_venta_esp = st.slider("Rotación esperada del lote (%)", min_value=50, max_value=100, value=int(round(min(98, fila_prod["Tasa_Rotacion_Pct"]))), step=1) / 100.0

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
            title="Demanda Regional en Colombia (5 Ciudades)",
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
            "Competidores_Activos", "Tasa_Devolucion_Pct"
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
            "Unidades_Vendidas", "Tasa_Rotacion_Pct", "Competidores_Activos"
        ]].describe().T[["mean", "std", "min", "50%", "max"]]
        desc.columns = ["Promedio", "Desv. Est.", "Mínimo", "Mediana", "Máximo"]
        st.dataframe(desc.style.format("{:,.2f}"), use_container_width=True, height=370)

    st.markdown("#### Buscador de Registros Históricos")
    busqueda = st.text_input("Buscar por nombre de producto, SKU, ciudad o puerto:", placeholder="Ej: Cafetera, SR-GAM-01, Bucaramanga...")
    df_tabla = df.copy()
    if busqueda.strip():
        q = busqueda.strip().lower()
        df_tabla = df_tabla[
            df_tabla["Producto"].str.lower().str.contains(q)
            | df_tabla["SKU"].str.lower().str.contains(q)
            | df_tabla["Ciudad_Destino"].str.lower().str.contains(q)
            | df_tabla["Puerto_Entrada"].str.lower().str.contains(q)
        ]

    st.dataframe(
        df_tabla[[
            "Fecha", "SKU", "Producto", "Categoria", "Ciudad_Destino", "Tipo_Transporte",
            "Precio_FOB_USD", "Costo_Aterrizado_COP", "Precio_Venta_Mercado_COP",
            "Unidades_Importadas", "Unidades_Vendidas", "Tasa_Rotacion_Pct",
            "Margen_Bruto_Pct", "Competidores_Activos"
        ]].head(500),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando hasta 500 de {len(df_tabla):,} registros filtrados.")

    csv_export = df_tabla.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ Descargar registros filtrados (.csv)",
        data=csv_export,
        file_name="sinoradar_datos_filtrados.csv",
        mime="text/csv",
    )

# ------------------------------------------------------------------------------
# TAB 6: AGREGAR NUEVOS PRODUCTOS / IMPORTACIONES EN VIVO
# ------------------------------------------------------------------------------
with tab6:
    st.markdown("### ➕ Registrar Nuevos Productos e Importaciones en Vivo")
    st.caption(
        "Añade nuevos productos o embarques directamente desde la web. El sistema calcula automáticamente "
        "el costo aterrizado en Colombia (CIF + Arancel + IVA 19% + Nacionalización × TRM), concatena el registro "
        "mediante `pd.concat` y actualiza al instante todos los gráficos y el Semáforo de Riesgo."
    )

    with st.form("form_nuevo_registro", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            nuevo_sku = st.text_input("SKU del producto", value="SR-NEW-01")
            nuevo_prod = st.text_input("Nombre del producto", placeholder="Ej: Aspiradora Robot Láser LiDAR")
            nueva_cat = st.selectbox("Categoría", options=sorted(df_base["Categoria"].unique().tolist()) + ["Nueva Categoría"])
            if nueva_cat == "Nueva Categoría":
                nueva_cat_custom = st.text_input("Escribe el nombre de la nueva categoría", value="Electrónica Industrial")
            else:
                nueva_cat_custom = nueva_cat
            nueva_ciudad = st.selectbox("Ciudad destino", options=["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Cartagena", "Pereira"])

        with f2:
            nueva_fecha = st.date_input("Fecha del embarque / mes", value=datetime.date(2026, 11, 1))
            nuevo_transp = st.selectbox("Tipo de transporte", options=["Marítimo", "Aéreo"])
            nuevo_fob = st.number_input("Precio FOB en China (USD)", min_value=0.5, max_value=2000.0, value=14.5, step=0.5)
            nuevo_flete = st.number_input("Flete unitario (USD)", min_value=0.2, max_value=300.0, value=2.4, step=0.2)
            nuevo_arancel = st.slider("Arancel (%)", min_value=0, max_value=25, value=10, step=1) / 100.0

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

                nuevo_reg = {
                    "Fecha": nueva_fecha.strftime("%Y-%m-01"),
                    "Anio": nueva_fecha.year,
                    "Mes": nueva_fecha.month,
                    "SKU": nuevo_sku.strip().upper(),
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
                    f"Registro agregado: **{nuevo_reg['Producto']}** | Costo aterrizado calculado: "
                    f"**${costo_aterrizado:,.0f} COP**. Recargando métricas..."
                )
                st.rerun()

    if st.session_state["registros_manuales"]:
        st.markdown("#### Registros añadidos en esta sesión")
        df_ses = pd.DataFrame(st.session_state["registros_manuales"])
        st.dataframe(df_ses, use_container_width=True, hide_index=True)

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            csv_master = df_combinado_raw.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "💾 Descargar Base Maestra Actualizada (.csv)",
                data=csv_master,
                file_name="importaciones_china_colombia_actualizada.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_act2:
            if st.button("🗑️ Limpiar registros añadidos en sesión", use_container_width=True):
                st.session_state["registros_manuales"] = []
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 7: METODOLOGÍA, ARQUITECTURA PYTHON Y EQUIPO
# ------------------------------------------------------------------------------
with tab7:
    st.markdown("### ℹ️ Arquitectura Técnica, Sustentación de Datos y Equipo")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            r"""
            #### 1. Sustentación y Escalabilidad de la Base de Datos
            La base de datos inicial (`importaciones_china_colombia.csv`) contiene **14,400 registros estructurados**
            generados de forma reproducible mediante `generar_datos.py` (**120 productos reales** × 10 categorías ×
            24 meses × 5 ciudades colombianas):
            - **Fórmula aduanera real en Colombia:**
              $$\text{CIF} = \text{FOB} + \text{Flete}$$
              $$\text{Costo Aterrizado} = \left(\text{CIF} + \text{Arancel} + \text{IVA}_{19\%} + \text{Nacionalización}\right) \times \text{TRM}$$
            - **Estacionalidad comercial:** Modela picos verificables en Colombia (Día de la Madre, prima de junio, Black Friday y Navidad).
            - **Tres formas de crecer la base:** (1) Subir archivos `.csv` adicionales en la barra lateral para fusionarlos con `pd.concat`, (2) registrar embarques en vivo desde la pestaña *Agregar Datos*, o (3) ampliar el catálogo en `generar_datos.py`.
            """
        )

    with col_m2:
        st.markdown(
            """
            #### 2. Conceptos de Python, Pandas y NumPy Aplicados
            - **Pandas:** Lectura/exportación CSV, fusión dinámica (`pd.concat`), indexación booleana múltiple
              (`.isin()`, `.between()`), agregaciones avanzadas (`groupby().agg()`), series de tiempo
              (`pd.to_datetime`) y matrices de correlación (`.corr()`).
            - **NumPy:** Operaciones vectorizadas sobre 14,400+ filas, control seguro de divisiones (`np.where`),
              normalización Min-Max, puntaje compuesto por producto punto (`np.dot`), clasificación condicional
              multicriterio (`np.select`), percentiles de mercado (`np.percentile`), regresión lineal de tendencia
              (`np.polyfit` / `np.polyval`) y análisis de sensibilidad 2D (`np.meshgrid`).
            """
        )

    st.divider()
    st.markdown("#### 👥 Integrantes del Proyecto")
    e1, e2, e3, e4 = st.columns(4)
    e1.info("**Isabella Prieto Morales**\n\nAnálisis de Mercado & Datos")
    e2.info("**Santiago Plazas**\n\nModelo Comercial & Negocio")
    e3.info("**Nicolás Alandete**\n\nArquitectura Python & Importaciones")
    e4.info("**Emmanuel Caballero**\n\nDesarrollo Web & Visualización")
