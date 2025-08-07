import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import os


st.set_page_config(page_title="Tablero HTS_TST ", layout="wide")
st.markdown("""
<style>
h1 {
    text-shadow: 2px 2px 4px rgba(0, 0.1, 0.2, 0.5);
}
</style>
""", unsafe_allow_html=True)

st.title("📋TABLERO HTS_TST FY25")

@st.cache_data
def cargar_datos(file):
    df_tst = pd.read_excel(file, sheet_name="HTS_TST")
    df_metas = pd.read_excel(file, sheet_name="METAS_SITIOS")
    df_tst.columns = df_tst.columns.str.strip().str.lower()
    df_metas.columns = df_metas.columns.str.strip().str.lower()
    df_tst['país'] = df_tst['país'].astype(str).str.strip().str.title()
    df_tst['departamento'] = df_tst['departamento'].astype(str).str.strip().str.title()
    df_tst['servicio de salud'] = df_tst['servicio de salud'].astype(str).str.strip()
    df_metas['país'] = df_metas['país'].astype(str).str.strip().str.title()
    df_metas['sitio'] = df_metas['sitio'].astype(str).str.strip()
    return df_tst, df_metas

# --- Cargar archivo pidiendo el archivo

#uploaded_file = st.sidebar.file_uploader("📂 Cargar archivo Excel", type=["xlsx"])
#if not uploaded_file:
#    st.warning("Por favor, carga el archivo Excel con las hojas HTS_TST y METAS_SITIOS.")
#    st.stop()

#df_tst, df_metas = cargar_datos(uploaded_file)

#Carga de el archivo desde la carpeta raís
archivo_nombre="Prueba Tablero Python.xlsx"
archivo_path=os.path.join(os.path.dirname(__file__), archivo_nombre)

if not os.path.exists(archivo_path):
    st.error(f"❌ No se se encontro el archivo '{archivo_nombre}' en la misma carpeta script. ")
    st.stop()

df_tst, df_metas =cargar_datos(archivo_path)
st.success(f"✅ Archivo cargado correctamente : {archivo_nombre}")

# --- Filtros jerárquicos
paises = sorted(df_tst['país'].dropna().unique())
pais_sel = st.sidebar.selectbox("🌍 País", ["Todos"] + paises)

df_filt = df_tst.copy()
if pais_sel != "Todos":
    df_filt = df_filt[df_filt['país'] == pais_sel]

departamentos = sorted(df_filt['departamento'].dropna().unique())
depto_sel = st.sidebar.selectbox("🏩 Departamento", ["Todos"] + departamentos)
if depto_sel != "Todos":
    df_filt = df_filt[df_filt['departamento'] == depto_sel]

sitios = sorted(df_filt['servicio de salud'].dropna().unique())
sitio_sel = st.sidebar.selectbox("🏥 Unidad de salud", ["Todos"] + sitios)
if sitio_sel != "Todos":
    df_filt = df_filt[df_filt['servicio de salud'] == sitio_sel]

# --- Tabla resumen por sitio
df_resumen = (
    df_filt.groupby('servicio de salud')
    .agg(
        Total_Pruebas=('resultado de la prueba de vih', 'count'),
        Positivos=('resultado de la prueba de vih', lambda x: (x == 'POSITIVO').sum())
    )
    .reset_index()
)

df_resumen = df_resumen.merge(
    df_metas[['sitio', 'hts_pos fy25']],
    left_on='servicio de salud',
    right_on='sitio',
    how='left'
).drop(columns='sitio')

df_resumen['hts_pos fy25'] = df_resumen['hts_pos fy25'].fillna(0).astype(int)
df_resumen['% Positividad'] = (df_resumen['Positivos'] / df_resumen['Total_Pruebas'] * 100).round(1)
df_resumen['% Alcance Meta'] = (
    (df_resumen['Positivos'] / df_resumen['hts_pos fy25']) * 100
).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)

# --- Tarjetas estilo Power BI con estilo
st.subheader("📊 Resúmen de metas")
total_pruebas = df_resumen['Total_Pruebas'].sum()
total_positivos = df_resumen['Positivos'].sum()
meta_total = df_resumen['hts_pos fy25'].sum()
positividad = (total_positivos / total_pruebas * 100) if total_pruebas > 0 else 0
alcance_meta = (total_positivos / meta_total * 100) if meta_total > 0 else 0

st.markdown(f"""
<style>
.card-container {{
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
}}
.card {{
    background-color: #f0f2f6;
    padding: 20px 25px;
    border-radius: 12px;
    text-align: center;
    width: 22%;
    box-shadow: 0 2px 6px rgba(0,0,0.2,0.2);
}}
.card h2 {{
    margin: 0;
    font-size: 30px;
    color: #2c3e50;
}}
.card p {{
    margin: 5px 0 0;
    font-size: 16px;
    color: #7f8c8d;
}}
</style>
<div class="card-container">
    <div class="card">
        <h2>{total_pruebas:,}</h2>
        <p>Total de Pruebas</p>
    </div>
    <div class="card">
        <h2>{total_positivos:,}</h2>
        <p>Positivos</p>
    </div>
    <div class="card">
        <h2>{positividad:.1f}%</h2>
        <p>Positividad</p>
    </div>
    <div class="card">
        <h2>{alcance_meta:.1f}%</h2>
        <p>Alcance Meta</p>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Mostrar tabla con formato condicional
st.subheader("📌 Resumen por unidad de salud")
def formato_color(val):
    if isinstance(val, (int, float)):
        if val >= 85:
            return 'background-color: #4CAF50; color: white'
        elif val >= 60:
            return 'background-color: #FF9800; color: black'
        else:
            return 'background-color: #F44336; color: white'
    return ''

styled_df = df_resumen.rename(columns={
    'servicio de salud': 'Sitio',
    'Total_Pruebas': 'Total de pruebas',
    'Positivos': 'Positivos',
    'hts_pos fy25': 'Meta HTS_POS FY25',
    '% Positividad': '% Positividad',
    '% Alcance Meta': '% Alcance de Meta'
}).style.format({
    '% Positividad': '{:.1f}%',
    '% Alcance de Meta': '{:.1f}%'
}).applymap(formato_color, subset=['% Alcance de Meta']).set_properties(**{'text-align': 'center'})

st.dataframe(styled_df, use_container_width=True)

# === Gráficas mensuales
if 'fecha del diagnóstico' in df_filt.columns:
    st.subheader("📆 Tendencias mensuales separadas")

    df_filt['fecha del diagnóstico'] = pd.to_datetime(df_filt['fecha del diagnóstico'], errors='coerce')
    df_filt['mes'] = df_filt['fecha del diagnóstico'].dt.to_period('M').astype(str)
    df_filt['mes_dt'] = df_filt['fecha del diagnóstico'].dt.to_period('M').dt.to_timestamp()

    df_linea = df_filt.groupby('mes_dt').agg(
        Total_Pruebas=('resultado de la prueba de vih', 'count'),
        Total_Positivos=('resultado de la prueba de vih', lambda x: (x == 'POSITIVO').sum())
    ).reset_index().sort_values('mes_dt')

    # --- Gráfica mensual de pruebas con línea de tendencia
    fig_pruebas = px.line(df_linea, x='mes_dt', y='Total_Pruebas',
        title="📈 Total de Pruebas por Mes", markers=True, text='Total_Pruebas')
    fig_pruebas.update_traces(textposition="top center")
    fig_pruebas.add_traces(go.Scatter(
        x=df_linea['mes_dt'],
        y=np.poly1d(np.polyfit(range(len(df_linea)), df_linea['Total_Pruebas'], 1))(range(len(df_linea))),
        mode='lines', name='Tendencia', line=dict(dash='dot')
    ))
    fig_pruebas.update_layout(xaxis_title="Mes", yaxis_title="Total de pruebas", template="plotly_white")
    st.plotly_chart(fig_pruebas, use_container_width=True)

    # --- Gráfica mensual de positivos con línea de tendencia
    fig_positivos = px.line(df_linea, x='mes_dt', y='Total_Positivos',
        title="📈 Total de Positivos por Mes", markers=True, text='Total_Positivos')
    fig_positivos.update_traces(textposition="top center")
    fig_positivos.add_traces(go.Scatter(
        x=df_linea['mes_dt'],
        y=np.poly1d(np.polyfit(range(len(df_linea)), df_linea['Total_Positivos'], 1))(range(len(df_linea))),
        mode='lines', name='Tendencia', line=dict(dash='dot')
    ))
    fig_positivos.update_layout(xaxis_title="Mes", yaxis_title="Total positivos", template="plotly_white")
    st.plotly_chart(fig_positivos, use_container_width=True)

    # === Proyección acumulada a septiembre
    st.subheader("📈 Proyección acumulada de positivos hasta septiembre")
    df_acum = df_linea[['mes_dt', 'Total_Positivos']].copy()
    df_acum['Acumulado'] = df_acum['Total_Positivos'].cumsum()
    ultimo_mes = df_acum['mes_dt'].max()
    septiembre = pd.Timestamp(year=ultimo_mes.year, month=9, day=1)
    if septiembre < ultimo_mes:
        septiembre += relativedelta(years=1)

    meses_restantes = (septiembre.year - ultimo_mes.year) * 12 + (septiembre.month - ultimo_mes.month)
    promedio_mensual = df_linea['Total_Positivos'].mean()
    acumulado_actual = df_acum['Acumulado'].iloc[-1]
    estimado_final = int(acumulado_actual + promedio_mensual * meses_restantes)

    fechas_proj = pd.date_range(start=ultimo_mes + relativedelta(months=1), end=septiembre, freq='MS')
    valores_proj = [int(promedio_mensual * (i+1) + acumulado_actual) for i in range(len(fechas_proj))]

    df_proj = pd.DataFrame({'mes_dt': fechas_proj, 'Acumulado': valores_proj, 'Tipo': 'Proyección'})
    df_real = df_acum[['mes_dt', 'Acumulado']].copy()
    df_real['Tipo'] = 'Real'
    df_final = pd.concat([df_real, df_proj], ignore_index=True)

    fig_acum = px.line(df_final, x='mes_dt', y='Acumulado', color='Tipo',
        title="📈 Positivos Acumulados por Mes con Proyección", markers=True, text='Acumulado')
    fig_acum.update_traces(textposition="top center")
    fig_acum.update_layout(xaxis_title="Mes", yaxis_title="Positivos acumulados", template="plotly_white", hovermode="x unified")
    fig_acum.add_trace(go.Scatter(
        x=[septiembre], y=[estimado_final], mode='text',
        text=[f"Total estimado: {estimado_final}"], textposition="top right", showlegend=False
    ))
    st.plotly_chart(fig_acum, use_container_width=True)

    # === %CD4 <200 entre positivos
    if 'cd4 basal' in df_filt.columns:
        st.subheader("📉 Porcentaje de CD4<200 entre positivos por mes")
        df_cd4 = df_filt[df_filt['resultado de la prueba de vih'] == 'POSITIVO'].copy()
        df_cd4['cd4 basal'] = pd.to_numeric(df_cd4['cd4 basal'], errors='coerce')
        df_cd4['CD4<200'] = df_cd4['cd4 basal'] < 200

        df_cd4_mensual = df_cd4.groupby('mes_dt').agg(
            Total_Positivos=('cd4 basal', 'count'),
            CD4_Menor_200=('CD4<200', 'sum')
        ).reset_index()
        df_cd4_mensual['%CD4<200'] = (df_cd4_mensual['CD4_Menor_200'] / df_cd4_mensual['Total_Positivos'] * 100).round(1)
        df_cd4_mensual['label_text'] = df_cd4_mensual['%CD4<200'].apply(lambda x: f"{x:.1f}%")

        fig_cd4 = px.line(df_cd4_mensual, x='mes_dt', y='%CD4<200',
                          title='% de CD4<200 entre Positivos por Mes', markers=True, text='label_text')
        fig_cd4.update_traces(textposition="top center")
        fig_cd4.add_traces(go.Scatter(
            x=df_cd4_mensual['mes_dt'],
            y=np.poly1d(np.polyfit(range(len(df_cd4_mensual)), df_cd4_mensual['%CD4<200'], 1))(range(len(df_cd4_mensual))),
            mode='lines', name='Tendencia', line=dict(dash='dot')
        ))
        fig_cd4.update_layout(xaxis_title="Mes", yaxis_title="% CD4<200", template="plotly_white")
        st.plotly_chart(fig_cd4, use_container_width=True)
else:
    st.warning("La columna 'fecha del diagnóstico' no está disponible.")