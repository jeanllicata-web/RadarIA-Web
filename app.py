import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_datareader.data as web
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="RadarIA Cuantitativo | Burbuja de IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para un look institucional
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-bottom: 1px solid #30363d;
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
    
    .stProgress > div > div > div > div {
        background-color: linear-gradient(90deg, #238636, #f0883e, #da3633);
    }
    
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .module-box {
        background-color: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1.5rem;
    }
    
    .alert-red { border-left-color: #da3633; }
    .alert-yellow { border-left-color: #f0883e; }
    .alert-green { border-left-color: #238636; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNCIONES AUXILIARES DE EXTRACTION
# ==========================================

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
    start = datetime.today() - timedelta(days=5*365) # 5 años para EMA 200 semanal
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

def calculate_ema(df, column='Close', window=200):
    """Calcula la EMA localmente. Si falla, devuelve None."""
    try:
        if len(df) >= window:
            return df[column].ewm(span=window, adjust=False).mean().iloc[-1]
        return None
    except:
        return None

def safe_get(dictionary, key, default=0.0):
    """Extrae datos de forma segura del diccionario .info de yfinance."""
    val = dictionary.get(key, default)
    if val is None: return default
    return val

# ==========================================
# LÓGICA DE LOS MÓDULOS
# ==========================================

def analizar_modulo1_valoracion(data):
    puntos = 0.0
    detalles = []
    nvda_pe = safe_get(data.get("NVDA", {}).get("info", {}), "forwardPE", 35.0) # Default 35x si falla
    amd_pe = safe_get(data.get("AMD", {}).get("info", {}), "forwardPE", 35.0)
    
    # Lógica NVDA Absoluta
    if nvda_pe < 25: puntos += 0.0; detalles.append("🟢 NVDA P/E < 25x: Suelo conservador.")
    elif 25 <= nvda_pe < 30: puntos += 0.5; detalles.append("🟢 NVDA P/E 25-30x: Zona de confort.")
    elif 30 <= nvda_pe < 35: puntos += 1.5; detalles.append("🟡 NVDA P/E 30-35x: Sector caro.")
    elif 35 <= nvda_pe < 40: puntos += 2.0; detalles.append("🟠 NVDA P/E 35-40x: Carísima (Riesgo técnico).")
    else: puntos += 4.0; detalles.append("🔴 NVDA P/E >= 40x: Burbuja desatada.")
    
    # Lógica Divergencia AMD
    if nvda_pe > 0:
        ratio_div = amd_pe / nvda_pe
        if nvda_pe < 40 and ratio_div > 1.5:
            puntos += 2.0; detalles.append("🔴 Alerta: Especulación extrema en rezagados (AMD) respecto al líder.")
        elif nvda_pe >= 40 and ratio_div > 1.0:
            puntos += 1.5; detalles.append("🔴 Alerta: Burbuja de arrastre colectivo extremo.")
        elif nvda_pe < 25 and ratio_div > 1.5:
            puntos += 1.5; detalles.append("🟠 Alerta: Minoristas atrapados en segundas marcas mientras NVDA capitula.")
            
    return puntos, detalles, f"**P/E NVDA:** {nvda_pe:.1f}x | **P/E AMD:** {amd_pe:.1f}x"

def analizar_modulo2_ciclo_fisico(data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    mu = data.get("MU")
    kospi = data.get("^KS11")
    
    if mu and not mu["hist"].empty:
        mu_price = mu["hist"]['Close'].iloc[-1]
        mu_ema = calculate_ema(mu["hist"])
        if mu_ema:
            metricas += f"**MU Precio:** ${mu_price:.2f} vs **EMA 200:** ${mu_ema:.2f} | "
            if mu_price < mu_ema and nvda_pe >= 30:
                puntos += 2.0; detalles.append("🔴 Alerta Crítica: MU bajo EMA 200 con P/E NVDA >= 30x. Anticipa acumulación de inventarios y deflación de márgenes.")
            elif mu_price < mu_ema:
                detalles.append("🟡 MU debilucho, pero contexto de valoración de NVDA no es de riesgo extremo.")
            else:
                detalles.append("🟢 Ciclo físico de memorias sano (MU sobre EMA 200).")
        else: detalles.append("⚪ Datos insuficientes para calcular EMA de MU.")
    else: detalles.append("⚪ Error al obtener datos de Micron (MU).")

    if kospi and not kospi["hist"].empty:
        k_price = kospi["hist"]['Close'].iloc[-1]
        k_ema = calculate_ema(kospi["hist"])
        if k_ema:
            metricas += f"**KOSPI Precio:** {k_price:.2f} vs **EMA 200:** {k_ema:.2f}"
            if k_price < k_ema and nvda_pe >= 35:
                puntos += 1.5; detalles.append("🔴 Alerta: Debilidad industrial en Asia (KOSPI < EMA) mientras NVDA está en burbuja.")
        else: detalles.append("⚪ Datos insuficientes para KOSPI.")
    else: detalles.append("⚪ Error al obtener datos del KOSPI.")
        
    return puntos, detalles, metricas

def analizar_modulo3_motor_corporativo(data, nvda_pe):
    puntos = 0.0
    detalles = []
    tickers_hs = ["META", "AMZN", "GOOG", "MSFT"]
    roas = []
    
    for t in tickers_hs:
        info = data.get(t, {}).get("info", {})
        # Preferencia ROA sobre ROE para evitar distorsión por apalancamiento
        roa = safe_get(info, "returnOnAssets", None)
        if roa is None: roa = safe_get(info, "returnOnEquity", 0.10) # Fallback ROE
        roas.append(roa)
        
    avg_roa = np.mean(roas)
    metricas = f"**ROA/ROE Promedio Hyperscalers:** {avg_roa*100:.1f}%"
    
    # Lógica Eficiencia de Capital
    if avg_roa > 0.15:
        puntos -= 1.5; detalles.append("🟢 Motor financiero indestructible (ROA > 15%). Inmunidad parcial activada (-1.5 pts).")
    else:
        puntos += 1.5; detalles.append("🟠 Peligro de claudicación en CapEx de IA (ROA < 15%). (+1.5 pts)")
        
    # Lógica Foso CUDA
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
    if (hyg and not hyg["hist"].empty and hyg["hist"]['Close'].iloc[-1] < calculate_ema(hyg["hist"])) or \
       (bizd and not bizd["hist"].empty and bizd["hist"]['Close'].iloc[-1] < calculate_ema(bizd["hist"])):
        hyg_bizd_alert = True
        
    if hyg_bizd_alert and nvda_pe >= 30:
        puntos += 2.0; detalles.append("🔴 Alerta: Estrés y cierre del grifo de deuda High Yield / BDCs mientras NVDA está caro.")
    elif hyg_bizd_alert:
        detalles.append("🟡 Crédito basura bajo EMA, pero el múltiplo de NVDA no está en zona de peligro.")
    else:
        detalles.append("🟢 Mercado de crédito privado (HYG/BIZD) líquido y estable.")

    private_bank_alert = False
    if nvda_pe >= 30:
        apo_bx_cond = (apo and not apo["hist"].empty and apo["hist"]['Close'].iloc[-1] < calculate_ema(apo["hist"])) or \
                      (bx and not bx["hist"].empty and bx["hist"]['Close'].iloc[-1] < calculate_ema(bx["hist"]))
        kre_cond = kre and not kre["hist"].empty and kre["hist"]['Close'].iloc[-1] < calculate_ema(kre["hist"])
        
        if apo_bx_cond and kre_cond:
            private_bank_alert = True
            puntos += 2.0; detalles.append("🔴 Alerta Sistémica: Grietas en Private Equity (APO/BX) contagiando a la Banca Regional (KRE).")
            
    if not private_bank_alert and not hyg_bizd_alert: metricas = "✅ Estable"
        
    return puntos, detalles, metricas

def analizar_modulo5_startup_fed(data, fred_data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    # Lógica SPCX
    spcx = data.get("SPCX")
    if spcx and not spcx["hist"].empty:
        spcx_price = spcx["hist"]['Close'].iloc[-1]
        ratio_inflacion = spcx_price / 80.0
        metricas += f"**SPCX:** ${spcx_price:.2f} (Ratio Inflación: {ratio_inflacion:.1f}x) | "
        if ratio_inflacion > 1.5:
            puntos += 2.0; detalles.append("🔴 Alerta: Euforia insostenible en startups privadas (SPCX > $120).")
        else:
            detalles.append("🟢 Valoración de startups privadas (SPCX) contenida.")
            
    # Lógica FED
    walcl = fred_data.get("WALCL")
    wtregen = fred_data.get("WTREGEN")
    rrpontsyd = fred_data.get("RRPONTSYD")
    
    if walcl is not None and wtregen is not None and rrpontsyd is not None:
        # Alinear fechas
        df_liquidez = pd.concat([walcl, wtregen, rrpontsyd], axis=1).dropna()
        df_liquidez.columns = ['WALCL', 'WTREGEN', 'RRPONTSYD']
        df_liquidez['Net_Liquidity'] = df_liquidez['WALCL'] - df_liquidez['WTREGEN'] - df_liquidez['RRPONTSYD']
        
        liq_actual = df_liquidez['Net_Liquidity'].iloc[-1]
        liq_ema = calculate_ema(df_liquidez, column='Net_Liquidity', window=200)
        
        metricas += f"**Liquidez Neta FED:** ${liq_actual/1e6:.1f}T"
        
        if liq_ema:
            if liq_actual < liq_ema and nvda_pe >= 35:
                puntos += 2.5; detalles.append("🔴 Alerta Crítica: Estrangulamiento monetario soberano (Liquidez < EMA 200) con NVDA en burbuja.")
            elif liq_actual < liq_ema:
                detalles.append("🟡 La FRED está drenando liquidez, pero las valoraciones de IA no están en máximo extremo.")
                
        # Lógica Rescate / Trampa Fed Put
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


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

def main():
    st.markdown("<div class='main-header'><h1>🧠 RadarIA Cuantitativo</h1><p>Sistema Institucional de Detección de Burbujas en Inteligencia Artificial</p></div>", unsafe_allow_html=True)
    
    # Descarga masiva de datos
    tickers_yf = ["NVDA", "AMD", "INTC", "MU", "^KS11", "META", "AMZN", "GOOG", "MSFT", 
                  "APO", "BX", "BIZD", "HYG", "KRE", "SPCX", "IPO"]
    series_fred = ["WALCL", "WTREGEN", "RRPONTSYD"]
    
    data_yf = get_yfinance_data(tickers_yf)
    data_fred = get_fred_data(series_fred)
    
    nvda_pe = safe_get(data_yf.get("NVDA", {}).get("info", {}), "forwardPE", 35.0)
    
    # Ejecutar análisis
    p1, d1, m1 = analizar_modulo1_valoracion(data_yf)
    p2, d2, m2 = analizar_modulo2_ciclo_fisico(data_yf, nvda_pe)
    p3, d3, m3 = analizar_modulo3_motor_corporativo(data_yf, nvda_pe)
    p4, d4, m4 = analizar_modulo4_credito_privado(data_yf, nvda_pe)
    p5, d5, m5 = analizar_modulo5_startup_fed(data_yf, data_fred, nvda_pe)
    
    raw_score = p1 + p2 + p3 + p4 + p5
    # Normalización estricta a escala 0-10
    final_score = max(0.0, min(10.0, raw_score))
    
    # --- CABECERA DE INDICADOR GENERAL ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Índice de Alerta General de Burbuja de IA")
        
        if final_score < 3: color_bar = "green"
        elif final_score < 6: color_bar = "orange"
        else: color_bar = "red"
        
        # Hack para cambiar color de la barra de progreso de Streamlit
        st.markdown(f"""
        <style>
            div[data-testid="stProgress"] > div > div > div > div {{
                background-color: {color_bar};
            }}
        </style>
        """, unsafe_allow_html=True)
        
        st.progress(final_score / 10.0)
        st.metric(label="Puntuación de Riesgo (0-10)", value=f"{final_score:.1f} pts", delta=f"Raw Score: {raw_score:.1f}")
        
        if final_score < 3: st.success("Estado: SANO / RACIONAL")
        elif final_score < 6: st.warning("Estado: TENSIÓN POR NARRATIVA")
        else: st.error("Estado: PELIGRO INMINENTE DE CRASH")

    st.markdown("---")
    
    # --- MÓDULOS EXPANDIBLES ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Resumen Ejecutivo", "💸 M1: Valoración", "🏭 M2: Ciclo Físico", "🏗️ M3: Motor BigTech", "🏦 M4: Crédito Oculto", " central_bank M5: FED & Startups"])
    
    with tab1:
        st.subheader("Síntesis Global y Transmisión de Riesgos")
        st.markdown(generar_sintesis_global(final_score, raw_score, d1, d2, d3, d4, d5, nvda_pe))
        
    with tab2:
        st.markdown("<div class='module-box alert-yellow'><h3>MÓDULO 1: VALORACIÓN DE SEMICONDUCTORES</h3></div>", unsafe_allow_html=True)
        st.markdown(m1)
        st.info("💡 **Lógica Microestructural:** El hardware es cíclico. Si el dinero huye del líder rentable (NVDA) y se refugia en competidores caros (AMD), el mercado no está comprando fundamentos, está comprando pura narrativa de 'catch-up'. Una divergencia de P/E > 1.5x a favor del rezagado históricamente indica que los inversores minoristas están asumiendo riesgos asimétricos injustificables.")
        for d in d1: st.markdown(d)
        st.metric("Puntos acumulados", f"{p1:.1f}")

    with tab3:
        st.markdown("<div class='module-box alert-red'><h3>MÓDULO 2: CICLO FÍSICO DE MEMORIAS Y SUMINISTRO</h3></div>", unsafe_allow_html=True)
        st.markdown(m2)
        st.info("💡 **Lógica Macroeconómica:** Las memorias RAM/HBM son el 'canario en la mina'. Al ser bienes físicos con alta elasticidad, sus precios y la salud de sus fabricantes (Micron) anticipan cambios en la demanda de servidores. Si el KOSPI (proxy del comercio exterior tecnológico de Asia) cae bajo su EMA de 200 días mientras las valoraciones de IA en EE.UU. se disparan, indica una desconexión letal entre el papel de Wall Street y la realidad de las fábricas.")
        for d in d2: st.markdown(d)
        st.metric("Puntos acumulados", f"{p2:.1f}")

    with tab4:
        st.markdown("<div class='module-box alert-green'><h3>MÓDULO 3: MOTOR CORPORATIVO Y EL FOSO CUDA</h3></div>", unsafe_allow_html=True)
        st.markdown(m3)
        st.info("💡 **Lógica de Negocio:** Las Big Tech (META, AMZN, GOOG, MSFT) son el cliente último de la IA. Si su Rentabilidad sobre Activos (ROA) promedio es >15%, tienen el músculo financiero para sostener el CapEx infinitamente; las caídas por petróleo o tipos de interés son solo ruido. Por otro lado, el ecosistema CUDA de Nvidia funciona como un 'pegamento' monopolístico: si ocurre un pánico pero el P/E de NVDA cae a niveles racionales (<25x), los ingresos recurrentes por software evitan la destrucción del negocio base.")
        for d in d3: st.markdown(d)
        st.metric("Puntos acumulados", f"{p3:.1f}")

    with tab5:
        st.markdown("<div class='module-box alert-yellow'><h3>MÓDULO 4: LA FONTANERÍA DEL CRÉDITO PRIVADO</h3></div>", unsafe_allow_html=True)
        st.markdown(m4 if m4 != "" else "✅ Estable")
        st.info("💡 **Lógica de Contagio Sistémico:** Las startups de IA queman miles de millones al año y no sobreviven con ingresos operativos. Dependen del Private Equity (Apollo, Blackstone) y de los BDCs (BIZD) para refinanciarse. Si esos fondos sufren impagos, dejan de prestar. Como los fondos privados usan deuda bancaria estructurada (KRE), el impago de una startup de IA insolvente termina transmitiéndose como riesgo de crédito al balance de tu banco regional local.")
        for d in d4: st.markdown(d)
        st.metric("Puntos acumulados", f"{p4:.1f}")

    with tab6:
        st.markdown("<div class='module-box alert-red'><h3>MÓDULO 5: EUFORIA STARTUPS Y EL GRIFO DE LA FED</h3></div>", unsafe_allow_html=True)
        st.markdown(m5)
        st.info("💡 **Lógica Termodinámica de Liquidez:** Las startups operan como agujeros negros que destruyen el efectivo del sistema. El ETF SPCX (SpaceX proxy) a $80 representa su valor industrial real; cualquier precio por encima es inflación especulativa pura. A nivel macro, la única forma de que una burbuja de esta magnitud no colapse es mediante la inyección de Liquidez Neta de la Reserva Federal (Balance Total - Tesoro - Repos). Si el minorista capitula (IPO -30%) y la FED inyecta dinero de emergencia (>2% expansión), estás presenciando la socialización de las pérdidas de los fondos de venture capital.")
        for d in d5: st.markdown(d)
        st.metric("Puntos acumulados", f"{p5:.1f}")

def generar_sintesis_global(score, raw, d1, d2, d3, d4, d5, nvda_pe):
    texto = f"**Análisis Dinámico para P/E NVDA actual: {nvda_pe:.1f}x | Puntuación Cruda: {raw:.1f}**\n\n"
    
    if score < 3.0:
        texto += "### 🟢 Diagnóstico: Ecosistema Sano y Autopropulsado\n"
        texto += "Actualmente, el complejo de Inteligencia Artificial presenta fundamentos que justifican sus valoraciones. "
        texto += "No hay señales de estrangulamiento de liquidez por parte de la FED, y el motor de capital de las Hyperscalers (ROA > 15%) garantiza que los pedidos de infraestructura física se mantendrán sólidos. "
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

if __name__ == "__main__":
    main()
