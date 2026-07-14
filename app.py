import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web
import os
from datetime import datetime, timedelta, date
from git import Repo

# Configuración de la página
st.set_page_config(
    page_title="RadarIA Cuantitativo | Burbuja de IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DISEÑO VISUAL ULTRA-CONTRASTE (FONDO 100% NEGRO)
st.markdown(
    """
    <style>
    .stApp { background-color: #000000 !important; }
    p, span, label, .stMarkdown, .stText { color: #FFFFFF !important; font-weight: 500 !important; }
    h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-weight: 700 !important; }
    div[data-testid="stBlock"], div[data-testid="element-container"] {
        background-color: #0c0c0c !important;
        border: 1px solid #262626 !important;
        border-radius: 8px !important;
    }
    .dataframe, table { background-color: #0c0c0c !important; color: #FFFFFF !important; }
    .stAlert p { color: #FFFFFF !important; font-weight: 600 !important; }
    
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: linear-gradient(180deg, #000000 0%, #0c0c0c 100%);
        border-bottom: 1px solid #262626;
        margin: -2.5rem -2rem 2rem -2rem;
        padding-top: 4rem;
    }
    
    h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #bc8cff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .module-box {
        background-color: #000000 !important;
        border-left: 4px solid #58a6ff;
        padding: 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1.5rem;
        border-top: 1px solid #262626 !important;
        border-right: 1px solid #262626 !important;
        border-bottom: 1px solid #262626 !important;
    }
    
    .alert-red { border-left-color: #da3633 !important; }
    .alert-yellow { border-left-color: #f0883e !important; }
    .alert-green { border-left-color: #238636 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# FUNCIONES AUXILIARES DE EXTRACTION Y PERSISTENCIA
# ==========================================

def render_detail(detail):
    """Convierte los textos de diagnóstico en componentes nativos de alto contraste."""
    texto_limpio = detail.replace("🟢", "").replace("🟡", "").replace("🟠", "").replace("🔴", "").replace("🚨", "").replace("⚪", "").strip()
    if "🔴" in detail or "🚨" in detail:
        st.error(f"🚨 **{texto_limpio}**")
    elif "🟠" in detail or "🟡" in detail:
        st.warning(f"⚠️ **{texto_limpio}**")
    elif "🟢" in detail or "✅" in detail:
        st.success(f"✅ **{texto_limpio}**")
    else:
        st.info(f"ℹ️ **{texto_limpio}**")

@st.cache_data(ttl=3600, show_spinner="Descargando datos de Yahoo Finance...")
def get_yfinance_data(tickers, period="1y"):
    """Descarga datos históricos con manejo robusto de errores."""
    data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            info = stock.info
            if not hist.empty:
                data[ticker] = {"hist": hist, "info": info}
            else:
                data[ticker] = None
        except Exception as e:
            data[ticker] = None
    return data

@st.cache_data(ttl=3600, show_spinner="Conectando con la FRED (Reserva Federal)...")
def get_fred_data(series_ids):
    """Descarga datos macroeconómicos de la FRED."""
    data = {}
    start = datetime.today() - timedelta(days=5*365)
    for series in series_ids:
        try:
            df = web.DataReader(series, 'fred', start)
            if not df.empty:
                data[series] = df
            else:
                data[series] = None
        except Exception as e:
            data[series] = None
    return data

def safe_get(dictionary, key, default=0.0):
    """Extrae datos de forma segura del diccionario .info de yfinance."""
    val = dictionary.get(key, default)
    if val is None: return default
    return val

def guardar_y_sincronizar_score(score_actual):
    """Gestiona el CSV local y sincroniza con GitHub para persistencia histórica."""
    archivo_csv = "historial_riesgo.csv"
    hoy = str(date.today())
    
    if os.path.exists(archivo_csv):
        df_hist = pd.read_csv(archivo_csv)
    else:
        df_hist = pd.DataFrame(columns=["Fecha", "Score_Riesgo"])
    
    if hoy not in df_hist["Fecha"].values:
        nuevo_registro = pd.DataFrame([{"Fecha": hoy, "Score_Riesgo": score_actual}])
        df_hist = pd.concat([df_hist, nuevo_registro], ignore_index=True)
        df_hist.to_csv(archivo_csv, index=False)
        
        try:
            repo = Repo(os.getcwd())
            repo.git.add(archivo_csv)
            repo.index.commit(f"Update historial riesgo: {hoy}")
            origin = repo.remote(name='origin')
            origin.push()
        except Exception as e:
            st.sidebar.error(f"Error al sincronizar con GitHub: {e}")
            
    return df_hist

# ==========================================
# LÓGICA DE LOS MÓDULOS
# ==========================================

def calcular_pe_manual(ticker_symbol, fallback_pe):
    """Calcula el Forward P/E de forma manual y homogénea para evitar errores fiscales de la API."""
    try:
        t = yf.Ticker(ticker_symbol)
        hist_1d = t.history(period="1d")
        if hist_1d.empty:
            return fallback_pe
            
        current_price = hist_1d["Close"].iloc[-1]
        info = t.info
        forward_eps = info.get("forwardEps")
        
        if forward_eps is not None and forward_eps > 0 and current_price > 0:
            pe_calculado = current_price / forward_eps
            return pe_calculado
    except Exception:
        pass
    return fallback_pe

def analizar_modulo1_valoracion(data):
    puntos = 0.0
    detalles = []
    
    # Cálculo estricto con histórico de 1d y forwardEps
    nvda_pe = calcular_pe_manual("NVDA", 23.0)
    amd_pe = calcular_pe_manual("AMD", 70.0)
    intc_pe = calcular_pe_manual("INTC", 30.0)
    
    if nvda_pe < 25: puntos += 0.0; detalles.append("🟢 NVDA P/E < 25x: Suelo conservador.")
    elif 25 <= nvda_pe < 30: puntos += 0.5; detalles.append("🟢 NVDA P/E 25-30x: Zona de confort.")
    elif 30 <= nvda_pe < 35: puntos += 1.5; detalles.append("🟡 NVDA P/E 30-35x: Sector caro.")
    elif 35 <= nvda_pe < 40: puntos += 2.0; detalles.append("🟠 NVDA P/E 35-40x: Carísima (Riesgo técnico).")
    else: puntos += 4.0; detalles.append("🔴 NVDA P/E >= 40x: Burbuja desatada.")
    
    if nvda_pe > 0:
        ratio_div = amd_pe / nvda_pe
        if nvda_pe < 40 and ratio_div > 1.5:
            puntos += 2.0; detalles.append("🔴 Alerta: Especulación extrema en rezagados (AMD) respecto al líder.")
        elif nvda_pe >= 40 and ratio_div > 1.0:
            puntos += 1.5; detalles.append("🔴 Alerta: Burbuja de arrastre colectivo extremo.")
        elif nvda_pe < 25 and ratio_div > 1.5:
            puntos += 1.5; detalles.append("🟠 Alerta: Minoristas atrapados en segundas marcas mientras NVDA capitula.")
            
    return puntos, detalles, f"**P/E NVDA:** {nvda_pe:.1f}x | **P/E AMD:** {amd_pe:.1f}x | **P/E INTC:** {intc_pe:.1f}x"

def analizar_modulo2_ciclo_fisico(data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    # Extracción estricta desde el histórico de 1 año para evitar desfases
    mu_hist = data.get("MU", {}).get("hist")
    kospi_hist = data.get("^KS11", {}).get("hist")
    
    if mu_hist is not None and not mu_hist.empty:
        precio_actual_mu = mu_hist["Close"].iloc[-1]
        ema_200_mu = mu_hist["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**MU Precio:** ${precio_actual_mu:.2f} vs **EMA 200:** ${ema_200_mu:.2f} | "
        
        if precio_actual_mu < ema_200_mu and nvda_pe >= 30:
            puntos += 2.0; detalles.append("🔴 Alerta Crítica: MU bajo EMA 200 con P/E NVDA >= 30x. Anticipa acumulación de inventarios y deflación de márgenes.")
        elif precio_actual_mu < ema_200_mu:
            detalles.append("🟡 MU debilucho, pero contexto de valoración de NVDA no es de riesgo extremo.")
        else:
            detalles.append("🟢 Ciclo físico de memorias sano (MU sobre EMA 200).")
    else: 
        detalles.append("⚪ Error al obtener datos históricos completos de Micron (MU).")

    if kospi_hist is not None and not kospi_hist.empty:
        precio_actual_kospi = kospi_hist["Close"].iloc[-1]
        ema_200_kospi = kospi_hist["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**KOSPI Precio:** {precio_actual_kospi:.2f} vs **EMA 200:** {ema_200_kospi:.2f}"
        
        if precio_actual_kospi < ema_200_kospi and nvda_pe >= 35:
            puntos += 1.5; detalles.append("🔴 Alerta: Debilidad industrial en Asia (KOSPI < EMA) mientras NVDA está en burbuja.")
    else: 
        detalles.append("⚪ Error al obtener datos históricos completos del KOSPI.")
        
    return puntos, detalles, metricas

def analizar_modulo3_motor_corporativo(data, nvda_pe):
    puntos = 0.0
    detalles = []
    tickers_hs = ['META', 'AMZN', 'GOOG', 'MSFT']
    roics = []
    
    for ticker in tickers_hs:
        try:
            t = yf.Ticker(ticker)
            financials = t.financials
            balance = t.balance_sheet
            
            ebit = financials.loc['Operating Income'].iloc[0]
            tax_provision = financials.loc['Tax Provision'].iloc[0]
            pretax_income = financials.loc['Pretax Income'].iloc[0]
            effective_tax_rate = max(0.0, min(tax_provision / pretax_income, 0.4)) if pretax_income > 0 else 0.21
            nopat = ebit * (1 - effective_tax_rate)
            
            equity = balance.loc['Stockholders Equity'].iloc[0]
            st_debt = balance.loc['Current Debt'].iloc[0] if 'Current Debt' in balance.index else 0
            lt_debt = balance.loc['Long Term Debt'].iloc[0] if 'Long Term Debt' in balance.index else 0
            total_debt = np.nan_to_num(st_debt) + np.nan_to_num(lt_debt)
            
            cash = balance.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance.index else 0
            invested_capital = equity + total_debt - cash
            
            roic = nopat / invested_capital if invested_capital > 0 else 0
            roics.append(roic)
        except Exception:
            roic = 0.22 
            roics.append(roic)
        
    avg_roic = np.mean(roics)
    metricas = f"**ROIC TTM Promedio Hyperscalers:** {avg_roic*100:.1f}%"
    
    if avg_roic > 0.15:
        puntos -= 1.5; detalles.append("🟢 Motor financiero indestructible (ROIC > 15%). Inmunidad parcial activada (-1.5 pts).")
    else:
        puntos += 1.5; detalles.append("🟠 Peligro de claudicación en CapEx de IA (ROIC < 15%). (+1.5 pts)")
        
    if nvda_pe < 25:
        puntos -= 1.0; detalles.append("🟢 Cojín CUDA activado. P/E NVDA < 25x indica zona de acumulación segura (-1.0 pts).")
        
    return puntos, detalles, metricas

def analizar_modulo4_credito_privado(data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    hyg = data.get("HYG")
    bizd = data.get("BIZD")
    apo = data.get("APO")
    bx = data.get("BX")
    kre = data.get("KRE")
    
    hyg_bizd_alert = False
    if (hyg and not hyg["hist"].empty and hyg["hist"]['Close'].iloc[-1] < hyg["hist"]['Close'].ewm(span=200, adjust=False).mean().iloc[-1]) or \
       (bizd and not bizd["hist"].empty and bizd["hist"]['Close'].iloc[-1] < bizd["hist"]['Close'].ewm(span=200, adjust=False).mean().iloc[-1]):
        hyg_bizd_alert = True
        
    if hyg_bizd_alert and nvda_pe >= 30:
        puntos += 2.0; detalles.append("🔴 Alerta: Estrés y cierre del grifo de deuda High Yield / BDCs mientras NVDA está caro.")
    elif hyg_bizd_alert:
        detalles.append("🟡 Crédito basura bajo EMA, pero el múltiplo de NVDA no está en zona de peligro.")
    else:
        detalles.append("🟢 Mercado de crédito privado (HYG/BIZD) líquido y estable.")

    private_bank_alert = False
    if nvda_pe >= 30:
        apo_bx_cond = (apo and not apo["hist"].empty and apo["hist"]['Close'].iloc[-1] < apo["hist"]['Close'].ewm(span=200, adjust=False).mean().iloc[-1]) or \
                      (bx and not bx["hist"].empty and bx["hist"]['Close'].iloc[-1] < bx["hist"]['Close'].ewm(span=200, adjust=False).mean().iloc[-1])
        kre_cond = kre and not kre["hist"].empty and kre["hist"]['Close'].iloc[-1] < kre["hist"]['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        if apo_bx_cond and kre_cond:
            private_bank_alert = True
            puntos += 2.0; detalles.append("🔴 Alerta Sistémica: Grietas en Private Equity (APO/BX) contagiando a la Banca Regional (KRE).")
            
    if not private_bank_alert and not hyg_bizd_alert: metricas = "✅ Estable"
        
    return puntos, detalles, metricas

def analizar_modulo5_startup_fed(data, fred_data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    spcx = data.get("SPCX")
    if spcx and not spcx["hist"].empty:
        spcx_price = spcx["hist"]['Close'].iloc[-1]
        ratio_inflacion = spcx_price / 80.0
        metricas += f"**SPCX:** ${spcx_price:.2f} (Ratio Inflación: {ratio_inflacion:.1f}x) | "
        if ratio_inflacion > 1.5:
            puntos += 2.0; detalles.append("🔴 Alerta: Euforia insostenible en startups privadas (SPCX > $120).")
        else:
            detalles.append("🟢 Valoración de startups privadas (SPCX) contenida.")
            
    walcl = fred_data.get("WALCL")
    wtregen = fred_data.get("WTREGEN")
    rrpontsyd = fred_data.get("RRPONTSYD")
    
    if walcl is not None and wtregen is not None and rrpontsyd is not None:
        df_liquidez = pd.concat([walcl, wtregen, rrpontsyd], axis=1).dropna()
        df_liquidez.columns = ['WALCL', 'WTREGEN', 'RRPONTSYD']
        df_liquidez['Net_Liquidity'] = df_liquidez['WALCL'] - df_liquidez['WTREGEN'] - df_liquidez['RRPONTSYD']
        
        liq_actual = df_liquidez['Net_Liquidity'].iloc[-1]
        liq_ema = df_liquidez['Net_Liquidity'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**Liquidez Neta FED:** ${liq_actual/1e6:.1f}T"
        
        if liq_ema:
            if liq_actual < liq_ema and nvda_pe >= 35:
                puntos += 2.5; detalles.append("🔴 Alerta Crítica: Estrangulamiento monetario soberano (Liquidez < EMA 200) con NVDA en burbuja.")
            elif liq_actual < liq_ema:
                detalles.append("🟡 La FRED está drenando liquidez, pero las valoraciones de IA no están en máximo extremo.")
                
        ipo = data.get("IPO")
        if ipo and not ipo["hist"].empty:
            ipo_max = ipo["hist"]['Close'].max()
            ipo_actual = ipo["hist"]['Close'].iloc[-1]
            walcl_yoy = (walcl.iloc[-1] / walcl.iloc[-52]) - 1 if len(walcl) >= 52 else 0
            
            if (ipo_actual / ipo_max) < 0.70 and walcl_yoy > 0.02:
                puntos += 1.5; detalles.append("🚨 ALERTA CRÍTICA: Capitulación del minorista (IPO -30%) rescatada por inyección de la FED (>2% YoY). Socializando pérdidas.")
    else:
        detalles.append("⚪ No se pudieron obtener los datos de la FRED para analizar liquidez.")
        
    return puntos, detalles, metricas

def generar_sintesis_global(score, raw, d1, d2, d3, d4, d5, nvda_pe):
    texto = f"**Análisis Dinámico para P/E NVDA actual: {nvda_pe:.1f}x | Puntuación Cruda: {raw:.1f}**\n\n"
    
    if score < 3.0:
        texto += "### 🟢 Diagnóstico: Ecosistema Sano y Autopropulsado\n"
        texto += "Actualmente, el complejo de Inteligencia Artificial presenta fundamentos que justifican sus valoraciones. "
        texto += "No hay señales de estrangulamiento de liquidez por parte de la FED, y el motor de capital de las Hyperscalers (ROIC > 15%) garantiza que los pedidos de infraestructura física se mantendrán sólidos. "
        texto += "El mercado está recompensando la ejecución real (liderazgo de NVDA) en lugar de comprar narrativas especulativas en competidores rezagados. "
        texto += "**Conclusión operativa:** Las correcciones en este entorno deben ser tratadas como oportunidades de acumulación institucional, no como el inicio de un crash estructural."
    elif score < 6.0:
        texto += "### 🟡 Diagnóstico: Tensión por Narrativa y Desconexiones Parciales\n"
        texto += "El sistema está mostrando fatiga microestructural. Aunque los balances corporativos grandes no han roto todavía, "
        texto += "estamos viendo anomalías preocupantes: "
        if any("rezagados" in d or "AMD" in d for d in d1): texto += "**Divergencia de valoración en semiconductores secundarios**, "
        if any("KOSPI" in d or "MU" in d for d in d2): texto += "**Debilidad en la cadena de suministro físico asiático**, "
        if any("HYG" in d or "BIZD" in d for d in d4): texto += "**Aprietes iniciales en el crédito de alto riesgo**, "
        texto += ". Esto indica que el mercado está transitando de una fase de inversión basada en crecimiento a una fase de supervivencia de narrativas. "
        texto += "**Conclusión operativa:** Reducir exposición a activos puros de narrativa (segundas marcas, startups sin cash flow) y refugiarse en el duopolio real (NVDA y las Hyperscalers). No es una burbuja generalizada todavía, pero el margen de error se ha estrechado drásticamente."
    else:
        texto += "### 🔴 Diagnóstico: Peligro Inminente de Crash Sistémico\n"
        texto += "Los indicadores cuantitativos están gritando un colapso inminente del ecosistema de IA. La transmisión del riesgo es total y letal: "
        if any("FED" in d or "Liquidez" in d or "Estrangulamiento" in d for d in d5): texto += "**La Reserva Federal ha cortado el flujo de liquidez soberana**, destruyendo el respaldo último del mercado. "
        if any("Socializando" in d or "Capitulación" in d for d in d5): texto += "**Se ha activado la trampa del Fed Put**: el minorista está siendo liquidado mientras se inyecta dinero para rescatar a los fondos privados. "
        if any("CapEx" in d or "claudicación" in d for d in d3): texto += "**El motor corporativo ha claudicado**, significando que las Big Tech ya no pueden justificar el gasto en infraestructura. "
        if any("Crédito" in d or "contagiando" in d for d in d4): texto += "**El sistema de crédito privado está contagiando a la banca tradicional**, lo que amenaza con un apalancamiento inverso masivo (margin calls). "
        if any("inventarios" in d or "deflación" in d for d in d2): texto += "**El ciclo físico ha roto su soporte**, confirmando que la demanda real de servidores ha desacelerado bruscamente frente al exceso de oferta de chips. "
        texto += "\n\n**Conclusión operativa:** Entorno de ONLY SHORTS o positions en efectivo. La probabilidad de un evento de 'Black Swan' sectorial supera el 80%. Cualquier rally debe ser utilizado para vender, no para comprar."

    return texto

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

def main():
    st.markdown("<div class='main-header'><h1>🧠 RadarIA Cuantitativo</h1><p>Sistema Institucional de Detección de Burbujas en Inteligencia Artificial</p></div>", unsafe_allow_html=True)
    
    tickers_yf = ["NVDA", "AMD", "INTC", "MU", "^KS11", "META", "AMZN", "GOOG", "MSFT", 
                  "APO", "BX", "BIZD", "HYG", "KRE", "SPCX", "IPO"]
    series_fred = ["WALCL", "WTREGEN", "RRPONTSYD"]
    
    data_yf = get_yfinance_data(tickers_yf)
    data_fred = get_fred_data(series_fred)
    
    # Extraer el P/E manual corregido para las dependencias de otros módulos
    nvda_pe = calcular_pe_manual("NVDA", 23.0)
    
    # Ejecutar análisis (Los módulos 1 y 2 usan las nuevas lógicas de ingeniería)
    p1, d1, m1 = analizar_modulo1_valoracion(data_yf)
    p2, d2, m2 = analizar_modulo2_ciclo_fisico(data_yf, nvda_pe)
    p3, d3, m3 = analizar_modulo3_motor_corporativo(data_yf, nvda_pe)
    p4, d4, m4 = analizar_modulo4_credito_privado(data_yf, nvda_pe)
    p5, d5, m5 = analizar_modulo5_startup_fed(data_yf, data_fred, nvda_pe)
    
    raw_score = p1 + p2 + p3 + p4 + p5
    final_score = max(0.0, min(10.0, raw_score))
    
    # --- PERSISTENCIA HISTÓRICA ---
    df_historial = guardar_y_sincronizar_score(round(final_score, 2))
    
    # --- CABECERA DE INDICADOR GENERAL ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Índice de Alerta General de Burbuja de IA")
        
        if final_score < 3: color_bar = "green"
        elif final_score < 6: color_bar = "orange"
        else: color_bar = "red"
        
        st.markdown(f"""
        <style>
            div[data-testid="stProgress"] > div > div > div > div {{
                background-color: {color_bar};
            }}
        </style>
        """, unsafe_allow_html=True)
        
        st.progress(final_score / 10.0)
        st.metric(label="Puntuación de Riesgo (0-10)", value=f"{final_score:.1f} pts", delta=f"Raw Score: {raw_score:.1f}")
        
        if final_score < 3: 
            st.success("✅ **Estado: SANO / RACIONAL**")
        elif final_score < 6: 
            st.warning("⚠️ **Estado: TENSIÓN POR NARRATIVA**")
        else: 
            st.error("🚨 **Estado: PELIGRO INMINENTE DE CRASH**")

    st.markdown("---")
    
    # --- MÓDULOS EXPANDIBLES ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Resumen Ejecutivo", "💸 M1: Valoración", "🏭 M2: Ciclo Físico", "🏗️ M3: Motor BigTech", "🏦 M4: Crédito Oculto", "🏦 M5: FED & Startups"])
    
    with tab1:
        st.subheader("Síntesis Global y Transmisión de Riesgos")
        st.markdown(generar_sintesis_global(final_score, raw_score, d1, d2, d3, d4, d5, nvda_pe))
        
    with tab2:
        st.markdown("<div class='module-box alert-yellow'><h3>MÓDULO 1: VALORACIÓN DE SEMICONDUCTORES</h3></div>", unsafe_allow_html=True)
        st.markdown(m1)
        st.info("💡 **Lógica Microestructural:** El hardware es cíclico. Si el dinero huye del líder rentable (NVDA) y se refugia en competidores caros (AMD), el mercado no está comprando fundamentos, está comprando pura narrativa de 'catch-up'. Una divergencia de P/E > 1.5x a favor del rezagado históricamente indica que los inversores minoristas están asumiendo riesgos asimétricos injustificables.")
        for d in d1: render_detail(d)
        st.metric("Puntos acumulados", f"{p1:.1f}")

    with tab3:
        st.markdown("<div class='module-box alert-red'><h3>MÓDULO 2: CICLO FÍSICO DE MEMORIAS Y SUMINISTRO</h3></div>", unsafe_allow_html=True)
        st.markdown(m2)
        st.info("💡 **Lógica Macroeconómica:** Las memorias RAM/HBM son el 'canario en la mina'. Al ser bienes físicos con alta elasticidad, sus precios y la salud de sus fabricantes (Micron) anticipan cambios en la demanda de servidores. Si el KOSPI (proxy del comercio exterior tecnológico de Asia) cae bajo su EMA de 200 días mientras las valoraciones de IA en EE.UU. se disparan, indica una desconexión letal entre el papel de Wall Street y la realidad de las fábricas.")
        for d in d2: render_detail(d)
        st.metric("Puntos acumulados", f"{p2:.1f}")

    with tab4:
        st.markdown("<div class='module-box alert-green'><h3>MÓDULO 3: MOTOR CORPORATIVO Y EL FOSO CUDA (ROIC)</h3></div>", unsafe_allow_html=True)
        st.markdown(m3)
        st.info("💡 **Lógica de Negocio (ROIC vs ROA/ROE):** A diferencia del ROA (que ignora la estructura de capital) o el ROE (que se infla peligrosamente con deuda), el **ROIC (Return on Invested Capital)** es la métrica definitiva institucional. Mide los rendimientos reales generados sobre todo el capital desplegado (Patrimonio + Deuda Neta). Cuando el ROIC de las Hyperscalers supera consistentemente su Costo de Capital Promedio Ponderado (WACC) —generalmente entre un 9% y un 12%—, demuestra que la brutal inversión en infraestructura de IA (servidores Nvidia) está creando valor económico real, no destruyéndolo. Si este ROIC cae por debajo del 15%, significa que el peso del CapEx está aplastando la rentabilidad corporativa.")
        for d in d3: render_detail(d)
        st.metric("Puntos acumulados", f"{p3:.1f}")

    with tab5:
        st.markdown("<div class='module-box alert-yellow'><h3>MÓDULO 4: LA FONTANERÍA DEL CRÉDITO PRIVADO</h3></div>", unsafe_allow_html=True)
        st.markdown(m4 if m4 != "" else "✅ Estable")
        st.info("💡 **Lógica de Contagio Sistémico:** Las startups de IA queman miles de millones al año y no sobreviven con ingresos operativos. Dependen del Private Equity (Apollo, Blackstone) y de los BDCs (BIZD) para refinanciarse. Si esos fondos sufren impagos, dejan de prestar. Como los fondos privados usan deuda bancaria estructurada (KRE), el impago de una startup de IA insolvente termina transmitiéndose como riesgo de crédito al balance de tu banco regional local.")
        for d in d4: render_detail(d)
        st.metric("Puntos acumulados", f"{p4:.1f}")

    with tab6:
        st.markdown("<div class='module-box alert-red'><h3>MÓDULO 5: EUFORIA STARTUPS Y EL GRIFO DE LA FED</h3></div>", unsafe_allow_html=True)
        st.markdown(m5)
        st.info("💡 **Lógica Termodinámica de Liquidez:** Las startups operan como agujeros negros que destruyen el efectivo del sistema. El ETF SPCX (SpaceX proxy) a $80 representa su valor industrial real; cualquier precio por encima es inflación especulativa pura. A nivel macro, la única forma de que una burbuja de esta magnitud no colapse es mediante la inyección de Liquidez Neta de la Reserva Federal (Balance Total - Tesoro - Repos). Si el minorista capitula (IPO -30%) y la FED inyecta dinero de emergencia (>2% expansión), estás presenciando la socialización de las pérdidas de los fondos de venture capital.")
        for d in d5: render_detail(d)
        st.metric("Puntos acumulados", f"{p5:.1f}")

    # --- GRÁFICO HISTÓRICO EN LA INTERFAZ ---
    st.markdown("---")
    st.subheader("📈 Evolución Histórica del Índice de Riesgo")
    if not df_historial.empty:
        st.line_chart(df_historial.set_index('Fecha'))
        st.caption("Registro diario almacenado de forma persistente mediante Git.")
    else:
        st.info("El historial se construirá y guardará automáticamente a partir de la ejecución de hoy.")

if __name__ == "__main__":
    main()
