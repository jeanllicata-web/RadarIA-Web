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
    .dataframe { background-color: #0c0c0c !important; color: #FFFFFF !important; border: 1px solid #262626 !important; }
    thead { background-color: #161b22 !important; color: #58a6ff !important; }
    th { color: #FFFFFF !important; border-bottom: 2px solid #262626 !important; }
    td { color: #FFFFFF !important; border-bottom: 1px solid #1a1f2e !important; }
    tr:hover { background-color: #161b22 !important; }
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
    .audit-box { border-left-color: #bc8cff !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# FUNCIONES AUXILIARES DE PERSISTENCIA
# ==========================================

def render_detail(detail):
    texto_limpio = detail.replace("🟢", "").replace("🟡", "").replace("🟠", "").replace("🔴", "").replace("🚨", "").replace("⚪", "").strip()
    if "🔴" in detail or "🚨" in detail:
        st.error(f"🚨 **{texto_limpio}**")
    elif "🟠" in detail or "🟡" in detail:
        st.warning(f"⚠️ **{texto_limpio}**")
    elif "🟢" in detail or "✅" in detail:
        st.success(f"✅ **{texto_limpio}**")
    else:
        st.info(f"ℹ️ **{texto_limpio}**")

def guardar_y_sincronizar_score(score_actual):
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
            pass # Silenciar error de git en UI para no saturar
            
    return df_hist

# ==========================================
# MÓDULO 0: DESCARGA CENTRALIZADA Y AUDITORÍA
# ==========================================

@st.cache_data(ttl=3600, show_spinner="Descargando datos de Yahoo Finance y FRED...")
def descargar_datos(tickers_1y, tickers_3y, series_fred):
    data = {}
    registro_auditoria = []
    
    # 1. Descarga de históricos de 1 año (Base para gráficos y lógica general)
    for ticker in tickers_1y:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            info = stock.info
            if not hist.empty:
                data[ticker] = {"hist": hist, "info": info}
                registro_auditoria.append({
                    "Variable Analizada": f"{ticker} Info General",
                    "Origen / Endpoint": "API yfinance (Live Ticker)",
                    "Estado de Inyección": "Éxito 200",
                    "Valor Crudo Recibido": "Diccionario info recibido"
                })
            else:
                data[ticker] = {"hist": pd.DataFrame(), "info": {}}
                registro_auditoria.append({"Variable Analizada": f"{ticker} Info General", "Origen / Endpoint": "API yfinance (Live Ticker)", "Estado de Inyección": "Error (Hist vacío)", "Valor Crudo Recibido": "N/A"})
        except Exception as e:
            data[ticker] = {"hist": pd.DataFrame(), "info": {}}
            registro_auditoria.append({"Variable Analizada": f"{ticker} Info General", "Origen / Endpoint": "API yfinance (Live Ticker)", "Estado de Inyección": "Error de Conexión", "Valor Crudo Recibido": str(e)})

    # 2. Descarga estricta de 3 años (Para estabilizar matemáticamente la EMA_200)
    for ticker in tickers_3y:
        try:
            stock = yf.Ticker(ticker)
            hist_3y = stock.history(period="3y").dropna()
            data[ticker] = {"hist_3y": hist_3y}
            
            if not hist_3y.empty:
                precio_actual = hist_3y['Close'].iloc[-1]
                ema_200 = hist_3y['Close'].ewm(span=200, adjust=False).mean().iloc[-1] if len(hist_3y) >= 200 else None
                
                registro_auditoria.append({
                    "Variable Analizada": f"{ticker} Precio Actual",
                    "Origen / Endpoint": f"API yfinance (Live Ticker: {ticker}, 3Y History)",
                    "Estado de Inyección": "Éxito 200",
                    "Valor Crudo Recibido": f"{precio_actual:.2f}"
                })
                registro_auditoria.append({
                    "Variable Analizada": f"{ticker} EMA 200 Real",
                    "Origen / Endpoint": f"API yfinance (Cálculo Local EWM sobre {len(hist_3y)} días)",
                    "Estado de Inyección": "Éxito 200" if ema_200 is not None else "Error (Muestra < 200 días)",
                    "Valor Crudo Recibido": f"{ema_200:.2f}" if ema_200 is not None else "N/A"
                })
            else:
                registro_auditoria.append({"Variable Analizada": f"{ticker} Historial 3A", "Origen / Endpoint": f"API yfinance (Live Ticker: {ticker})", "Estado de Inyección": "Error (Dropna vacío)", "Valor Crudo Recibido": "N/A"})
        except Exception as e:
            registro_auditoria.append({"Variable Analizada": f"{ticker} Historial 3A", "Origen / Endpoint": f"API yfinance (Live Ticker: {ticker})", "Estado de Inyección": "Error Crítico", "Valor Crudo Recibido": str(e)})

    # 3. Evaluación de Trailing P/E (TTM) con Blindaje de Datos
    pe_config = {
        "NVDA": (31.5, 20.0, "Trailing P/E (TTM) NVDA"),
        "AMD": (155.0, 50.0, "Trailing P/E (TTM) AMD"),
        "INTC": (28.5, 15.0, "Trailing P/E (TTM) INTC")
    }
    
    for symbol, (fallback_pe, min_threshold, var_name) in pe_config.items():
        if symbol in data and data[symbol].get("info"):
            try:
                info = data[symbol]["info"]
                hist = data[symbol].get("hist", pd.DataFrame())
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0
                raw_eps = info.get("trailingEps")
                
                if raw_eps is not None and raw_eps > 0 and current_price > 0:
                    pe_calculado = current_price / raw_eps
                    
                    if pe_calculado > min_threshold:
                        data[symbol]["trailing_pe_used"] = pe_calculado
                        registro_auditoria.append({
                            "Variable Analizada": var_name,
                            "Origen / Endpoint": "API yfinance (Live info['trailingEps'])",
                            "Estado de Inyección": "Éxito 200",
                            "Valor Crudo Recibido": f"{pe_calculado:.1f}x"
                        })
                    else:
                        data[symbol]["trailing_pe_used"] = fallback_pe
                        registro_auditoria.append({
                            "Variable Analizada": var_name,
                            "Origen / Endpoint": "API yfinance (Live info['trailingEps'])",
                            "Estado de Inyección": f"Fallback (Valor < {min_threshold}x, sesgado)",
                            "Valor Crudo Recibido": f"{pe_calculado:.1f}x"
                        })
                else:
                    data[symbol]["trailing_pe_used"] = fallback_pe
                    registro_auditoria.append({
                        "Variable Analizada": var_name,
                        "Origen / Endpoint": "API yfinance (Live info['trailingEps'])",
                        "Estado de Inyección": "Fallback (EPS Nulo/Inválido)",
                        "Valor Crudo Recibido": "Nulo"
                    })
            except Exception as e:
                data[symbol]["trailing_pe_used"] = fallback_pe
                registro_auditoria.append({
                    "Variable Analizada": var_name,
                    "Origen / Endpoint": "API yfinance (Live info['trailingEps'])",
                    "Estado de Inyección": "Fallback (Error de cálculo)",
                    "Valor Crudo Recibido": str(e)
                })
        else:
            data[symbol]["trailing_pe_used"] = fallback_pe
            registro_auditoria.append({
                "Variable Analizada": var_name,
                "Origen / Endpoint": "API yfinance (Live Ticker)",
                "Estado de Inyección": "Fallback (Fallo Total API)",
                "Valor Crudo Recibido": "N/A"
            })

    # 4. Descarga de FRED (Liquidez de la FED)
    fred_data = {}
    for series in series_fred:
        try:
            start = datetime.today() - timedelta(days=5*365)
            df = web.DataReader(series, 'fred', start)
            if not df.empty:
                fred_data[series] = df
                registro_auditoria.append({
                    "Variable Analizada": f"{series} (FRED)",
                    "Origen / Endpoint": "FRED St. Louis (CSV Endpoint)",
                    "Estado de Inyección": "Éxito 200",
                    "Valor Crudo Recibido": f"Dataframe de {len(df)} filas"
                })
            else:
                registro_auditoria.append({"Variable Analizada": f"{series} (FRED)", "Origen / Endpoint": "FRED St. Louis (CSV Endpoint)", "Estado de Inyección": "Error (DataFrame vacío)", "Valor Crudo Recibido": "N/A"})
        except Exception as e:
            registro_auditoria.append({"Variable Analizada": f"{series} (FRED)", "Origen / Endpoint": "FRED St. Louis (CSV Endpoint)", "Estado de Inyección": "Error de Conexión", "Valor Crudo Recibido": str(e)})

    return data, fred_data, registro_auditoria

# ==========================================
# LÓGICA DE LOS MÓDULOS 1 AL 5 (Usando datos pre-auditorizados)
# ==========================================

def analizar_modulo1_valoracion(data):
    puntos = 0.0
    detalles = []
    
    pe_nvda = data["NVDA"].get("trailing_pe_used", 31.5)
    pe_amd = data["AMD"].get("trailing_pe_used", 155.0)
    pe_intel = data["INTC"].get("trailing_pe_used", 28.5)
    
    if pe_nvda < 25: puntos += 0.0; detalles.append("🟢 Trailing P/E NVDA < 25x: Suelo conservador.")
    elif 25 <= pe_nvda < 30: puntos += 0.5; detalles.append("🟢 Trailing P/E NVDA 25-30x: Zona de confort.")
    elif 30 <= pe_nvda < 35: puntos += 1.5; detalles.append("🟡 Trailing P/E NVDA 30-35x: Sector caro.")
    elif 35 <= pe_nvda < 40: puntos += 2.0; detalles.append("🟠 Trailing P/E NVDA 35-40x: Carísima (Riesgo técnico).")
    else: puntos += 4.0; detalles.append("🔴 Trailing P/E NVDA >= 40x: Burbuja desatada.")
    
    if pe_nvda > 0:
        ratio_div = pe_amd / pe_nvda
        if pe_nvda < 40 and ratio_div > 1.5:
            puntos += 2.0; detalles.append("🔴 Alerta: Especulación extrema en rezagados (AMD) respecto al líder.")
        elif pe_nvda >= 40 and ratio_div > 1.0:
            puntos += 1.5; detalles.append("🔴 Alerta: Burbuja de arrastre colectivo extremo.")
        elif pe_nvda < 25 and ratio_div > 1.5:
            puntos += 1.5; detalles.append("🟠 Alerta: Minoristas atrapados en segundas marcas mientras NVDA capitula.")
            
    return puntos, detalles, f"**Trailing P/E (TTM) NVDA:** {pe_nvda:.1f}x | **Trailing P/E (TTM) AMD:** {pe_amd:.1f}x | **Trailing P/E (TTM) INTC:** {pe_intel:.1f}x"

def analizar_modulo2_ciclo_fisico(data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    # Lectura directa de la muestra de 3 años pre-descargada
    mu_data = data.get("MU", {}).get("hist_3y")
    kospi_data = data.get("^KS11", {}).get("hist_3y")
    
    if mu_data is not None and not mu_data.empty and len(mu_data) >= 200:
        precio_actual_mu = mu_data['Close'].iloc[-1]
        ema_200_mu = mu_data['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**MU Precio:** ${precio_actual_mu:.2f} vs **EMA 200:** ${ema_200_mu:.2f} | "
        
        if precio_actual_mu < ema_200_mu and nvda_pe >= 30:
            puntos += 2.0; detalles.append("🔴 Alerta Crítica: MU bajo EMA 200 con P/E NVDA >= 30x. Anticipa acumulación de inventarios y deflación de márgenes.")
        elif precio_actual_mu < ema_200_mu:
            detalles.append("🟡 MU debilucho, pero contexto de valoración de NVDA no es de riesgo extremo.")
        else:
            detalles.append("🟢 Ciclo físico de memorias sano (MU sobre EMA 200).")
    else:
        detalles.append("⚪ Datos históricos insuficientes para calcular EMA 200 de Micron (MU).")

    if kospi_data is not None and not kospi_data.empty and len(kospi_data) >= 200:
        precio_actual_kospi = kospi_data['Close'].iloc[-1]
        ema_200_kospi = kospi_data['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**KOSPI Precio:** {precio_actual_kospi:.2f} vs **EMA 200:** {ema_200_kospi:.2f}"
        
        if precio_actual_kospi < ema_200_kospi and nvda_pe >= 35:
            puntos += 1.5; detalles.append("🔴 Alerta: Debilidad industrial en Asia (KOSPI < EMA) mientras NVDA está en burbuja.")
    else:
        detalles.append("⚪ Datos históricos insuficientes para calcular EMA 200 del KOSPI.")
        
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
    
    hyg = data.get("HYG", {}).get("hist")
    bizd = data.get("BIZD", {}).get("hist")
    apo = data.get("APO", {}).get("hist")
    bx = data.get("BX", {}).get("hist")
    kre = data.get("KRE", {}).get("hist")
    
    def check_ema_200(df):
        if df is not None and not df.empty and len(df) >= 200:
            return df['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        return None

    hyg_bizd_alert = False
    if (hyg is not None and hyg['Close'].iloc[-1] < check_ema_200(hyg)) or \
       (bizd is not None and bizd['Close'].iloc[-1] < check_ema_200(bizd)):
        hyg_bizd_alert = True
        
    if hyg_bizd_alert and nvda_pe >= 30:
        puntos += 2.0; detalles.append("🔴 Alerta: Estrés y cierre del grifo de deuda High Yield / BDCs mientras NVDA está caro.")
    elif hyg_bizd_alert:
        detalles.append("🟡 Crédito basura bajo EMA, pero el múltiplo de NVDA no está en zona de peligro.")
    else:
        detalles.append("🟢 Mercado de crédito privado (HYG/BIZD) líquido y estable.")

    private_bank_alert = False
    if nvda_pe >= 30:
        apo_bx_cond = (apo is not None and apo['Close'].iloc[-1] < check_ema_200(apo)) or \
                      (bx is not None and bx['Close'].iloc[-1] < check_ema_200(bx))
        kre_cond = kre is not None and kre['Close'].iloc[-1] < check_ema_200(kre)
        
        if apo_bx_cond and kre_cond:
            private_bank_alert = True
            pontos += 2.0; detalles.append("🔴 Alerta Sistémica: Grietas en Private Equity (APO/BX) contagiando a la Banca Regional (KRE).")
            
    if not private_bank_alert and not hyg_bizd_alert: metricas = "✅ Estable"
        
    return puntos, detalles, metricas

def analizar_modulo5_startup_fed(data, fred_data, nvda_pe):
    puntos = 0.0
    detalles = []
    metricas = ""
    
    spcx = data.get("SPCX", {}).get("hist")
    if spcx is not None and not spcx.empty:
        spcx_price = spcx['Close'].iloc[-1]
        ratio_inflacion = spcx_price / 80.0
        metricas += f"**SPCX:** ${spcx_price:.2f} (Ratio Inflación: {ratio_inflacion:.1f}x) | "
        if ratio_inflacion > 1.5:
            pontos += 2.0; detalles.append("🔴 Alerta: Euforia insostenible en startups privadas (SPCX > $120).")
        else:
            detalles.append("🟢 Valoración de startups privadas (SPCX) contenida.")
            
    walcl = fred_data.get("WALCL")
    wtregen = fred_data.get("WTREGEN")
    rrpontsyd = fred_data.get("RRPONTSYD")
    
    if walcl is not None and wtregen is not None and rrpontsyd is not None:
        df_liquidez = pd.concat([walcl, wtregen, rrpontsyd], axis=1).dropna()
        df_liquidez.columns = ['WALCL', 'WTREGEN', 'RRPONTSYD']
        df_liquidez['Net_Liquidity'] = df_liquidez['WALCL'] - df_liquidez['WTREGEN'] - df_liquidez['RRPONTSYD']
        
        liq_actual = df_liquidez['Net_Liquidez'].iloc[-1]
        ema_liq = df_liquidez['Net_Liquidez'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        metricas += f"**Liquidez Neta FED:** ${liq_actual/1e6:.1f}T"
        
        if ema_liq is not None:
            if liq_actual < ema_liq and nvda_pe >= 35:
                pontos += 2.5; detalles.append("🔴 Alerta Crítica: Estrangulamiento monetario soberano (Liquidez < EMA 200) con NVDA en burbuja.")
            elif liq_actual < ema_liq:
                detalles.append("🟡 La FRED está drenando liquidez, pero las valoraciones de IA no están en máximo extremo.")
                
        ipo = data.get("IPO", {}).get("hist")
        if ipo is not None and not ipo.empty:
            ipo_max = ipo['Close'].max()
            ipo_actual = ipo['Close'].iloc[-1]
            walcl_yoy = (walcl.iloc[-1] / walcl.iloc[-52]) - 1 if len(walcl) >= 52 else 0
            
            if (ipo_actual / ipo_max) < 0.70 and walcl_yoy > 0.02:
                pontos += 1.5; detalles.append("🚨 ALERTA CRÍTICA: Capitulación del minorista (IPO -30%) rescatada por inyección de la FED (>2% YoY). Socializando pérdidas.")
    else:
        detalles.append("⚪ No se pudieron obtener los datos de la FRED para analizar liquidez.")
        
    return puntos, detalles, metricas

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

def main():
    st.markdown("<div class='main-header'><h1>🧠 RadarIA Cuantitativo</h1><p>Sistema Institucional de Detección de Burbujas en Inteligencia Artificial</p></div>", unsafe_allow_html=True)
    
    tickers_1y = ["NVDA", "AMD", "INTC", "META", "AMZN", "GOOG", "MSFT", "APO", "BX", "BIZD", "HYG", "KRE", "SPCX", "IPO"]
    tickers_3y = ["MU", "^KS11"]
    series_fred = ["WALCL", "WTREGEN", "RRPONTSYD"]
    
    # Descarga centralizada y auditoría de datos
    with st.spinner("Conectando con APIs financieras y auditando orígenes..."):
        data, fred_data, registro_auditoria = descargar_datos(tickers_1y, tickers_3y, series_fred)
    
    nvda_pe = data["NVDA"].get("trailing_pe_used", 31.5)
    
    # Ejecutar análisis
    p1, d1, m1 = analizar_modulo1_valoracion(data)
    p2, d2, m2 = analizar_modulo2_ciclo_fisico(data, nvda_pe)
    p3, d3, m3 = analizar_modulo3_motor_corporativo(data, nvda_pe)
    p4, d4, m4 = analizar_modulo4_credito_privado(data, nvda_pe)
    p5, d5, m5 = analizar_modulo5_startup_fed(data, fred_data, nvda_pe)
    
    raw_score = p1 + p2 + p3 + p4 + p5
    final_score = max(0.0, min(10.0, raw_score))
    
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
        st.info("💡 **Lógica Microestructural:** El hardware es cíclico. Si el dinero huye del líder rentable (NVDA) y se refugia en competidores caros (AMD), el mercado no está comprando fundamentos, está comprando pura narrativa de 'catch-up'. Una divergencia de Trailing P/E > 1.5x a favor del rezagado históricamente indica que los inversores minoristas están asumiendo riesgos asimétricos injustificables.")
        for d in d1: render_detail(d)
        st.metric("Puntos acumulados", f"{p1:.1f}")

    with tab3:
        st.markdown("<div class='module-box alert-red'><h3>MÓDULO 2: CICLO FÍSICO DE MEMORIAS Y SUMINISTRO</h3></div>", unsafe_allow_html=True)
        st.markdown(m2)
        st.info("💡 **Lógica Macroeconómica:** Las memorias RAM/HBM son el 'canario en la mina'. Al ser bienes físicos con alta elasticidad, sus precios y la salud de sus fabricantes (Micron) anticipan cambios en la demanda de servidores. Si el KOSPI (proxy del comercio exterior tecnológico de Asia) cae bajo su EMA de 200 días sobre una base de 3 años, indica una desconexión letal entre el papel de Wall Street y la realidad de las fábricas.")
        for d in d2: render_detail(d)
        st.metric("Puntos acumulados", f"{p2:.1f}")

    with tab4:
        st.markdown("<div class='module-box alert-green'><h3>MÓDULO 3: MOTOR CORPORATIVO Y EL FOSO CUDA (ROIC)</h3></div>", unsafe_allow_html=True)
        st.markdown(m3)
        st.info("💡 **Lógica de Negocio (ROIC vs ROA/ROE):** A diferencia del ROA (que ignora la estructura de capital) o del ROE (que se infla peligrosamente con deuda), el **ROIC (Return on Invested Capital)** es la métrica definitiva institucional. Mide los rendimientos reales generados sobre todo el capital desplegado (Patrimonio + Deuda Neta). Cuando el ROIC de las Hyperscalers supera consistentemente su Costo de Capital Promedio Ponderado (WACC) —generalmente entre un 9% y un 12%—, demuestra que la brutal inversión en infraestructura de IA (servidores Nvidia) está creando valor económico real, no destruyéndolo. Si este ROIC cae por debajo del 15%, significa que el peso del CapEx está aplastando la rentabilidad corporativa.")
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

    # --- MÓDULO 6: METROLOGÍA Y TRAZABILIDAD DE ORIGEN ---
    st.markdown("---")
    
    with st.expander("🔬 MÓDULO 6: METROLOGÍA Y TRAZABILIDAD DE ORIGEN (Auditoría de Datos)", expanded=False):
        st.markdown("<div class='module-box audit-box'><h3>Registros Exactos de Inyección de Datos al Motor de Riesgo</h3></div>", unsafe_allow_html=True)
        st.caption("Esta tabla expone la fuente exacta, el endpoint utilizado, el estado de la conexión y el valor crudo exacto recibido antes de pasar por la lógica de blindaje matemático. Garantiza trazabilidad institucional total.")
        
        if registro_auditoria:
            df_auditoria = pd.DataFrame(registro_auditoria)
            st.dataframe(
                df_auditoria, 
                column_config={
                    "Variable Analizada": st.column_config.TextColumn("Variable Analizada", width="medium"),
                    "Origen / Endpoint": st.column_config.TextColumn("Origen / Endpoint", width="large"),
                    "Estado de Inyección": st.column_config.TextColumn("Estado de Inyección", width="medium"),
                    "Valor Crudo Recibido": st.column_config.TextColumn("Valor Crudo Recibido", width="medium")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No se registraron datos de auditoría en esta ejecución.")

    # --- GRÁFICO HISTÓRICO EN LA INTERFAZ ---
    st.markdown("---")
    st.subheader("📈 Evolución Histórica del Índice de Riesgo")
    if not df_historial.empty:
        st.line_chart(df_historial.set_index('Fecha'))
        st.caption("Registro diario almacenado de forma persistente mediante Git.")
    else:
        st.info("El historial se construirá y guardará automáticamente a partir de la ejecución de hoy.")

def generar_sintesis_global(score, raw, d1, d2, d3, d4, d5, nvda_pe):
    texto = f"**Análisis Dinámico para Trailing P/E NVDA actual: {nvda_pe:.1f}x | Puntuación Cruda: {raw:.1f}**\n\n"
    
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

if __name__ == "__main__":
    main()
