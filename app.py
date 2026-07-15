import streamlit as st
import pandas as pd
import yfinance as yf
from github import Github
import io
from datetime import datetime

# ==========================================
# REGISTRO METROLÓGICO GLOBAL
# ==========================================
registro_metrológico = []

# ==========================================
# DISEÑO E INFRAESTRUCTURA (Ultra-Contraste)
# ==========================================
def inyectar_css():
    css = """
    <style>
        .stApp {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, div, li, label {
            color: #FFFFFF !important;
        }
        .stAlert {
            background-color: #111111 !important;
            color: #FFFFFF !important;
            border-left: 4px solid #00FF66 !important;
        }
        .stDataframe {
            background-color: #000000 !important;
            color: #00FF66 !important;
        }
        th {
            background-color: #000000 !important;
            color: #00FF66 !important;
        }
        td {
            background-color: #0A0A0A !important;
            color: #FFFFFF !important;
        }
        [data-testid="stMetricValue"] {
            color: #00FF66 !important;
            font-size: 3rem !important;
            font-weight: bold !important;
        }
        [data-testid="stMetricLabel"] {
            color: #FFFFFF !important;
            font-size: 1.2rem !important;
        }
        .peligro [data-testid="stMetricValue"] {
            color: #FF3333 !important;
        }
        .tension [data-testid="stMetricValue"] {
            color: #FFFF33 !important;
        }
        .streamlit-expanderHeader {
            background-color: #111111 !important;
            color: #00FF66 !important;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ==========================================
# MÓDULO DE DESCARGA FRED (CORREGIDO Y BLINDADO CONTRA KEYERROR)
# ==========================================
def descargar_datos_fred():
    series_ids = ["WALCL", "WTREGEN", "RRPONTSYD"]
    dfs = {}
    
    for s_id in series_ids:
        try:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s_id}"
            df = pd.read_csv(url, parse_dates=["DATE"], index_col="DATE")
            df[s_id] = pd.to_numeric(df[s_id], errors='coerce')
            dfs[s_id] = df
            if not df.empty:
                registro_metrológico.append({"Fuente": "FRED (CSV Directo)", "Ticker": s_id, "Estado": "Éxito", "Valor Crudo": df[s_id].iloc[-1]})
        except Exception as e:
            dfs[s_id] = pd.DataFrame(columns=[s_id])
            registro_metrológico.append({"Fuente": "FRED (CSV Directo)", "Ticker": s_id, "Estado": f"Error: {str(e)[:50]}", "Valor Crudo": None})
            
    # Unificación explícita usando el primer DataFrame como base real
    df_unificado = dfs["WALCL"].join(dfs["WTREGEN"], how='outer').join(dfs["RRPONTSYD"], how='outer')
    
    # Relleno de datos vacíos por desfase de días
    df_unificado = df_unificado.ffill().bfill().dropna()
    
    # Inyección matemática 100% segura
    if not df_unificado.empty and all(k in df_unificado.columns for k in series_ids):
        df_unificado['Liquidez_Neta'] = df_unificado['WALCL'] - df_unificado['WTREGEN'] - df_unificado['RRPONTSYD']
    else:
        # Fallback maestro si la FRED está caída por completo en el servidor de la nube
        df_unificado['Liquidez_Neta'] = 6000000.0  # Nivel proxy base de 6.0T
        registro_metrológico.append({"Fuente": "FRED (Fallback Maestro)", "Ticker": "Liquidez_Neta", "Estado": "Proxy Inyectado", "Valor Crudo": 6000000.0})
        
    return df_unificado

# ==========================================
# FUNCIONES AUXILIARES DE DATOS (CON FALLBACKS)
# ==========================================
def obtener_datos_yfinance(ticker, periodo="3y"):
    try:
        df = yf.Ticker(ticker).history(period=periodo)
        if not df.empty:
            df['Close'] = df['Close'].ffill().bfill()
            df = df.dropna(subset=['Close'])
            
            if not df.empty:
                valor = df['Close'].iloc[-1]
                registro_metrológico.append({"Fuente": "Yahoo Finance", "Ticker": ticker, "Estado": "Éxito", "Valor Crudo": round(valor, 2)})
                return df
            else:
                registro_metrológico.append({"Fuente": "Yahoo Finance", "Ticker": ticker, "Estado": "Vacío tras limpiar NaN", "Valor Crudo": None})
                return pd.DataFrame()
        else:
            registro_metrológico.append({"Fuente": "Yahoo Finance", "Ticker": ticker, "Estado": "Vacío", "Valor Crudo": None})
            return pd.DataFrame()
    except Exception as e:
        registro_metrológico.append({"Fuente": "Yahoo Finance", "Ticker": ticker, "Estado": f"Error: {str(e)}", "Valor Crudo": None})
        return pd.DataFrame()

def obtener_pe(ticker):
    try:
        tk = yf.Ticker(ticker)
        pe = tk.info.get("trailingPE")
        
        if pe is None or pe <= 0 or pe != pe:
            precio = tk.info.get("currentPrice") or tk.info.get("previousClose")
            eps = tk.info.get("forwardEps") or tk.info.get("trailingEps")
            
            if precio and eps and eps > 0:
                pe = precio / eps
                registro_metrológico.append({"Fuente": "Yahoo Finance (Implícito)", "Ticker": ticker, "Estado": "Éxito (Calculado)", "Valor Crudo": round(pe, 2)})
                return pe
            
            valores_base = {"NVDA": 30.0, "AMD": 100.0}
            pe = valores_base.get(ticker, 35.0)
            registro_metrológico.append({"Fuente": "Yahoo Finance (Fallback)", "Ticker": ticker, "Estado": "Éxito (Valor Base)", "Valor Crudo": pe})
            return pe
        else:
            registro_metrológico.append({"Fuente": "Yahoo Finance (Info)", "Ticker": ticker, "Estado": "Éxito", "Valor Crudo": round(pe, 2)})
            return pe
            
    except Exception as e:
        valores_base = {"NVDA": 30.0, "AMD": 100.0}
        pe = valores_base.get(ticker, 35.0)
        registro_metrológico.append({"Fuente": "Yahoo Finance (Excepción)", "Ticker": ticker, "Estado": f"Fallback por Error: {str(e)[:30]}", "Valor Crudo": pe})
        return pe

def obtener_roic_ttm(ticker):
    try:
        tk = yf.Ticker(ticker)
        fin = tk.quarterly_financials
        bal = tk.quarterly_balance_sheet
        
        if fin.empty or bal.empty:
            raise ValueError("Estados financieros vacíos o bloqueados")
            
        ebit = fin.loc[fin.index.str.contains("Operating Income", case=False, na=False)].iloc[:, :4].sum(axis=1).iloc[0]
        tax = fin.loc[fin.index.str.contains("Income Tax Expense", case=False, na=False)].iloc[:, :4].sum(axis=1).iloc[0]
        nopat = ebit - tax
        
        deuda = bal.loc[bal.index.str.contains("Total Debt", case=False, na=False)].iloc[:, 0].iloc[0]
        equity = bal.loc[bal.index.str.contains("Stockholders Equity", case=False, na=False)].iloc[:, 0].iloc[0]
        cash = bal.loc[bal.index.str.contains("Cash And Cash Equivalents", case=False, na=False)].iloc[:, 0].iloc[0]
        
        capital_invertido = deuda + equity - cash
        if capital_invertido == 0 or capital_invertido != capital_invertido: 
            raise ValueError("Capital invertido inválido (0 o NaN)")
            
        roic = (nopat / capital_invertido) * 100
        registro_metrológico.append({"Fuente": "Yahoo Finance (Estados)", "Ticker": ticker, "Estado": "Éxito", "Valor Crudo": round(roic, 2)})
        return roic
        
    except Exception as e:
        roics_institucionales = {"META": 26.0, "AMZN": 18.0, "GOOG": 24.0, "MSFT": 27.0}
        roic_fallback = roics_institucionales.get(ticker)
        
        if roic_fallback is not None:
            registro_metrológico.append({"Fuente": "Fallback Institucional", "Ticker": ticker, "Estado": f"Inyectado: {str(e)[:30]}", "Valor Crudo": roic_fallback})
            return roic_fallback
        else:
            registro_metrológico.append({"Fuente": "Fallback Institucional", "Ticker": ticker, "Estado": f"Sin dato: {str(e)[:30]}", "Valor Crudo": None})
            return None

def calcular_ema_200(df):
    if df.empty:
        return None
    return df['Close'].ewm(span=200, adjust=False).mean().iloc[-1]

# ==========================================
# MÓDULOS DE RIESGO
# ==========================================
def modulo_1_semiconductores(pe_nvda, pe_amd):
    puntos = 0.0
    detalle = []
    
    if pe_nvda is None: pe_nvda = 999.0
        
    if pe_nvda < 25:
        puntos += 0.0; detalle.append(f"PE NVDA {pe_nvda:.1f}x (<25x): +0.0 pt")
    elif 25 <= pe_nvda < 30:
        puntos += 0.5; detalle.append(f"PE NVDA {pe_nvda:.1f}x (25-30x): +0.5 pt")
    elif 30 <= pe_nvda < 35:
        puntos += 1.5; detalle.append(f"PE NVDA {pe_nvda:.1f}x (30-35x): +1.5 pt")
    elif 35 <= pe_nvda < 40:
        puntos += 2.0; detalle.append(f"PE NVDA {pe_nvda:.1f}x (35-40x): +2.0 pt")
    else:
        puntos += 4.0; detalle.append(f"PE NVDA {pe_nvda:.1f}x (>=40x): +4.0 pt")

    if pe_amd and pe_amd > 0 and pe_nvda > 0:
        ratio = pe_amd / pe_nvda
        if pe_nvda < 40 and ratio > 1.5:
            puntos += 2.0; detalle.append(f"Divergencia (Ratio {ratio:.2f} > 1.5x y NVDA <40x): +2.0 pt")
        elif pe_nvda >= 40 and ratio > 1.0:
            puntos += 1.5; detalle.append(f"Divergencia (Ratio {ratio:.2f} > 1.0x y NVDA >=40x): +1.5 pt")
        elif pe_nvda < 25 and ratio > 1.5:
            puntos += 1.5; detalle.append(f"Divergencia Extrema (Ratio {ratio:.2f} > 1.5x y NVDA <25x): +1.5 pt")
        else:
            detalle.append(f"Divergencia controlada (Ratio {ratio:.2f}): +0.0 pt")
    else:
        detalle.append("PE AMD no disponible para Ratio: +0.0 pt")

    return puntos, detalle

def modulo_2_ciclo_fisico(pe_nvda, df_ks11, df_mu):
    puntos = 0.0
    detalle = []
    if pe_nvda is None: pe_nvda = 0.0
    
    ema_ks11 = calcular_ema_200(df_ks11)
    if ema_ks11 is not None and not df_ks11.empty:
        precio_ks11 = df_ks11['Close'].iloc[-1]
        if precio_ks11 < ema_ks11 and pe_nvda >= 35:
            puntos += 1.5; detalle.append(f"KOSPI ({precio_ks11:.0f}) < EMA200 ({ema_ks11:.0f}) y PE NVDA >=35x: +1.5 pt")
        else:
            detalle.append("KOSPI por encima de EMA200 o PE NVDA < 35x: +0.0 pt")
    else:
        detalle.append("Datos KOSPI insuficientes para EMA200: +0.0 pt")

    ema_mu = calcular_ema_200(df_mu)
    if ema_mu is not None and not df_mu.empty:
        precio_mu = df_mu['Close'].iloc[-1]
        if precio_mu < ema_mu and pe_nvda >= 30:
            puntos += 2.0; detalle.append(f"MICRON ({precio_mu:.2f}) < EMA200 ({ema_mu:.2f}) y PE NVDA >=30x: +2.0 pt")
        else:
            detalle.append("MICRON por encima de EMA200 o PE NVDA < 30x: +0.0 pt")
    else:
        detalle.append("Datos MICRON insuficientes para EMA200: +0.0 pt")

    return puntos, detalle

def modulo_3_motor_corporativo(pe_nvda, diccio_roics):
    puntos = 0.0
    detalle = []
    if pe_nvda is None: pe_nvda = 999.0
    
    roics_validos = [v for v in diccio_roics.values() if v is not None]
    if roics_validos:
        promedio_roic = sum(roics_validos) / len(roics_validos)
        if promedio_roic > 15:
            puntos -= 1.5; detalle.append(f"ROIC Promedio Magistral ({promedio_roic:.1f}% > 15%): -1.5 pt")
        else:
            puntos += 1.5; detalle.append(f"ROIC Promedio Débil ({promedio_roic:.1f}% <= 15%): +1.5 pt")
    else:
        detalle.append("ROICs no calculables (se suma riesgo neutral): +0.0 pt")

    if pe_nvda < 25:
        puntos -= 1.0; detalle.append(f"Amortiguador CUDA activado (PE NVDA {pe_nvda:.1f}x < 25x): -1.0 pt")
    else:
        detalle.append("Amortiguador CUDA desactivado: +0.0 pt")

    return puntos, detalle

def modulo_4_credito_privado(pe_nvda, df_hyg, df_bizd, df_apo, df_bx, df_kre):
    puntos = 0.0
    detalle = []
    if pe_nvda is None: pe_nvda = 0.0
    
    ema_hyg = calcular_ema_200(df_hyg)
    ema_bizd = calcular_ema_200(df_bizd)
    
    condicion_hyg_bizd = False
    if ema_hyg is not None and not df_hyg.empty and df_hyg['Close'].iloc[-1] < ema_hyg: condicion_hyg_bizd = True
    if ema_bizd is not None and not df_bizd.empty and df_bizd['Close'].iloc[-1] < ema_bizd: condicion_hyg_bizd = True

    if condicion_hyg_bizd and pe_nvda >= 30:
        puntos += 2.0; detalle.append("Crédito Privado (HYG o BIZD < EMA200) y PE NVDA >=30x: +2.0 pt")
    else:
        detalle.append("Crédito Privado Sano o PE NVDA < 30x: +0.0 pt")

    ema_apo = calcular_ema_200(df_apo)
    ema_bx = calcular_ema_200(df_bx)
    ema_kre = calcular_ema_200(df_kre)
    
    condicion_apo_bx = False
    if ema_apo is not None and not df_apo.empty and df_apo['Close'].iloc[-1] < ema_apo: condicion_apo_bx = True
    if ema_bx is not None and not df_bx.empty and df_bx['Close'].iloc[-1] < ema_bx: condicion_apo_bx = True
        
    condicion_kre = False
    if ema_kre is not None and not df_kre.empty and df_kre['Close'].iloc[-1] < ema_kre: condicion_kre = True

    if condicion_apo_bx and condicion_kre and pe_nvda >= 30:
        puntos += 2.0; detalle.append("Stress Regional/APE (APO/BX y KRE < EMA200) y PE NVDA >=30x: +2.0 pt")
    else:
        detalle.append("Stress Regional/APE controlado o PE NVDA < 30x: +0.0 pt")

    return puntos, detalle

def modulo_5_startups_fed(pe_nvda, df_spcx, df_ipo, df_fred):
    puntos = 0.0
    detalle = []
    if pe_nvda is None: pe_nvda = 0.0
    
    if not df_spcx.empty:
        precio_spcx = df_spcx['Close'].iloc[-1]
        ratio_spcx = precio_spcx / 80.0
        if ratio_spcx > 1.5:
            puntos += 2.0; detalle.append(f"Burbuja Startups (SPCX {precio_spcx:.2f}/80 = {ratio_spcx:.2f}x > 1.5x): +2.0 pt")
        else:
            detalle.append(f"Startups Contenidas (Ratio {ratio_spcx:.2f}x): +0.0 pt")
    else:
        detalle.append("SPCX sin datos: +0.0 pt")

    if not df_fred.empty:
        try:
            # El nuevo módulo asegura que existe 'Liquidez_Neta' y las columnas base
            df_fred = df_fred.fillna(method='ffill').fillna(0)
            df_fred['Liquidez_Neta'] = df_fred.get('WALCL', 0) - df_fred.get('WTREGEN', 0) - df_fred.get('RRPONTSYD', 0)
            
            if not df_fred.empty and 'Liquidez_Neta' in df_fred.columns:
                ema_liq = df_fred['Liquidez_Neta'].ewm(span=200, adjust=False).mean()
                if not ema_liq.empty:
                    ultima_liq = df_fred['Liquidez_Neta'].iloc[-1]
                    ultima_ema_liq = ema_liq.iloc[-1]
                    
                    if ultima_liq < ultima_ema_liq and pe_nvda >= 35:
                        puntos += 2.5; detalle.append(f"Liquidez FED Contrayéndose ({ultima_liq:.0f} < EMA {ultima_ema_liq:.0f}) y PE NVDA >=35x: +2.5 pt")
                    else:
                        detalle.append("Liquidez FED Sana o PE NVDA < 35x: +0.0 pt")
                else:
                    detalle.append("Serie EMA Liquidez vacía: +0.0 pt")
                    
                if not df_ipo.empty:
                    max_ipo = df_ipo['Close'].max()
                    precio_ipo = df_ipo['Close'].iloc[-1]
                    caida_ipo = ((max_ipo - precio_ipo) / max_ipo) * 100 if max_ipo > 0 else 0
                    
                    df_walcl_w = df_fred.get('WALCL', pd.Series()).resample('W').last().dropna()
                    if not df_walcl_w.empty:
                        incr_walcl = df_walcl_w.pct_change().iloc[-1]
                        
                        if caida_ipo > 30 and incr_walcl > 0.02:
                            puntos += 1.5; detalle.append(f"Fed Put Activado (IPO -{caida_ipo:.1f}% y WALCL semanal +{incr_walcl*100:.1f}%): +1.5 pt")
                        else:
                            detalle.append(f"Sín Fed Put (IPO -{caida_ipo:.1f}%, WALCL +{incr_walcl*100:.1f}%): +0.0 pt")
                    else:
                        detalle.append("WALCL sin datos semanales para Fed Put: +0.0 pt")
                else:
                    detalle.append("ETF IPO sin datos: +0.0 pt")
            else:
                detalle.append("Liquidez Neta vacía tras cálculo: +0.0 pt")
                
        except Exception as e:
            registro_metrológico.append({"Fuente": "FRED (Cálculo)", "Ticker": "Liquidez_Neta", "Estado": f"Errorinterno: {str(e)}", "Valor Crudo": None})
            detalle.append("Error calculando métricas FRED: +0.0 pt")
    else:
        detalle.append("Datos FRED completamente vacíos: +0.0 pt")

    return puntos, detalle

# ==========================================
# GESTIÓN DE HISTORIAL (GitHub)
# ==========================================
def guardar_historial_github(puntuacion):
    try:
        token = st.secrets.get("GH_PAT")
        repo_nombre = st.secrets.get("GH_REPO")
        
        if not token or not repo_nombre:
            return False
            
        g = Github(token)
        repo = g.get_repo(repo_nombre)
        archivo_nombre = "historial_riesgo.csv"
        sha = None
        df_hist = pd.DataFrame(columns=["Fecha", "Puntuacion_Riesgo"])
        
        try:
            contenido = repo.get_contents(archivo_nombre)
            datos_csv = contenido.decoded_content.decode('utf-8')
            df_hist = pd.read_csv(io.StringIO(datos_csv))
            sha = contenido.sha
        except Exception:
            pass
            
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nueva_fila = pd.DataFrame({"Fecha": [fecha_actual], "Puntuacion_Riesgo": [puntuacion]})
        df_hist = pd.concat([df_hist, nueva_fila], ignore_index=True)
        
        csv_actualizado = df_hist.to_csv(index=False)
        
        if sha:
            repo.update_file(archivo_nombre, f"Actualización riesgo IA {fecha_actual}", csv_actualizado, sha)
        else:
            repo.create_file(archivo_nombre, "Creación historial riesgo IA", csv_actualizado)
            
        return True
    except Exception as e:
        st.error(f"Error Git: {e}")
        return False

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================
def main():
    st.set_page_config(page_title="Indicador Burbuja IA", page_icon="🚨", layout="wide")
    inyectar_css()
    
    st.title("🚨 INDICADOR PERSONALIZADO BURBUJA IA")
    st.markdown("**Sistema de Medición de Riesgo de Crash (Escala 0 - 10)**")
    st.markdown("---")

    with st.spinner("🛰️ Extrayendo datos con tolerancia a fallos (Yahoo Finance / FRED)..."):
        df_ks11 = obtener_datos_yfinance("^KS11")
        df_mu = obtener_datos_yfinance("MU")
        df_hyg = obtener_datos_yfinance("HYG")
        df_bizd = obtener_datos_yfinance("BIZD")
        df_apo = obtener_datos_yfinance("APO")
        df_bx = obtener_datos_yfinance("BX")
        df_kre = obtener_datos_yfinance("KRE")
        df_spcx = obtener_datos_yfinance("SPCX", "1y")
        df_ipo = obtener_datos_yfinance("IPO", "1y")
        
        pe_nvda = obtener_pe("NVDA")
        pe_amd = obtener_pe("AMD")
        
        roic_meta = obtener_roic_ttm("META")
        roic_amzn = obtener_roic_ttm("AMZN")
        roic_goog = obtener_roic_ttm("GOOG")
        roic_msft = obtener_roic_ttm("MSFT")
        diccio_roics = {"META": roic_meta, "AMZN": roic_amzn, "GOOG": roic_goog, "MSFT": roic_msft}
        
        df_fred = descargar_datos_fred()

    ptos_m1, det_m1 = modulo_1_semiconductores(pe_nvda, pe_amd)
    ptos_m2, det_m2 = modulo_2_ciclo_fisico(pe_nvda, df_ks11, df_mu)
    ptos_m3, det_m3 = modulo_3_motor_corporativo(pe_nvda, diccio_roics)
    ptos_m4, det_m4 = modulo_4_credito_privado(pe_nvda, df_hyg, df_bizd, df_apo, df_bx, df_kre)
    ptos_m5, det_m5 = modulo_5_startups_fed(pe_nvda, df_spcx, df_ipo, df_fred)
    
    puntuacion_total = ptos_m1 + ptos_m2 + ptos_m3 + ptos_m4 + ptos_m5
    puntuacion_normalizada = min(max(puntuacion_total, 0.0), 10.0)

    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        color_clase = "sano"
        texto_estado = "SANO 🟢"
        if puntuacion_normalizada >= 3.0 and puntuacion_normalizada <= 6.0:
            color_clase = "tension"
            texto_estado = "TENSIÓN 🟡"
        elif puntuacion_normalizada > 6.0:
            color_clase = "peligro"
            texto_estado = "PELIGRO DE CRASH 🔴"
            
        st.markdown(f"<div class='{color_clase}' style='text-align:center; padding:20px; border: 2px solid #FFFFFF; border-radius:10px; background-color:#0A0A0A;'>", unsafe_allow_html=True)
        st.metric(label="NIVEL DE RIESGO", value=f"{puntuacion_normalizada:.1f} / 10.0")
        st.markdown(f"<h2 style='text-align:center; color:#FFFFFF;'>{texto_estado}</h2>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_der:
        with st.expander("📖 Desglose Técnico por Módulos", expanded=True):
            st.subheader("Módulo 1: Semiconductores")
            for d in det_m1: st.markdown(f"- {d}")
            st.markdown(f"**Subtotal M1: {ptos_m1:.1f} pts**")
            
            st.subheader("Módulo 2: Ciclo Físico")
            for d in det_m2: st.markdown(f"- {d}")
            st.markdown(f"**Subtotal M2: {ptos_m2:.1f} pts**")
            
            st.subheader("Módulo 3: Motor Corporativo")
            for d in det_m3: st.markdown(f"- {d}")
            st.markdown(f"**Subtotal M3: {ptos_m3:.1f} pts**")
            
            st.subheader("Módulo 4: Crédito Privado")
            for d in det_m4: st.markdown(f"- {d}")
            st.markdown(f"**Subtotal M4: {ptos_m4:.1f} pts**")
            
            st.subheader("Módulo 5: Startups y FED")
            for d in det_m5: st.markdown(f"- {d}")
            st.markdown(f"**Subtotal M5: {ptos_m5:.1f} pts**")
            
            st.markdown("---")
            st.markdown(f"**PUNTUACIÓN BRUTA ACUMULADA: {puntuacion_total:.1f} pts** (Normalizada al tope de 10.0)")

    with st.expander("🔬 MÓDULO 6: METROLOGÍA Y TRAZABILIDAD DE ORIGEN", expanded=False):
        df_metrolgia = pd.DataFrame(registro_metrológico)
        if not df_metrolgia.empty:
            st.dataframe(df_metrolgia, use_container_width=True, hide_index=True)
        else:
            st.warning("No se registraron trazas metrológicas.")

    if st.button("💾 Guardar Trazabilidad y Puntaje en GitHub"):
        with st.spinner("Conectando con GitHub..."):
            exito = guardar_historial_github(puntuacion_normalizada)
            if exito:
                st.success("✅ Historial actualizado y subido con éxito al repositorio.")
            else:
                st.error("❌ Fallo al subir. Revisa los secretos (GH_PAT, GH_REPO) en Streamlit.")

# ==========================================
# CIERRE EXACTO
# ==========================================
if __name__ == "__main__": main()
