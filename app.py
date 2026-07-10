import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="RadarIA - Monitor de Riesgo Burbuja IA",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    :root {
        --bg-color: #0e1117;
        --text-color: #fafafa;
        --green-neon: #00ff88;
        --yellow-neon: #ffdd00;
        --red-neon: #ff0044;
    }
    
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    
    .main-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00ff88, #00ccff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .main-header p {
        color: #8899aa;
        font-size: 1rem;
    }
    
    .semaforo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 25px 0;
        gap: 20px;
    }
    
    .semaforo {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
    }
    
    .semaforo.verde {
        background: radial-gradient(circle, #00ff88, #00cc66);
        color: #003311;
        box-shadow: 0 0 40px rgba(0,255,136,0.6);
    }
    
    .semaforo.amarillo {
        background: radial-gradient(circle, #ffdd00, #ffaa00);
        color: #332200;
        box-shadow: 0 0 40px rgba(255,221,0,0.6);
    }
    
    .semaforo.rojo {
        background: radial-gradient(circle, #ff0044, #cc0033);
        color: #330011;
        box-shadow: 0 0 40px rgba(255,0,68,0.6);
    }
    
    .semaforo-info {
        text-align: left;
        max-width: 400px;
    }
    
    .semaforo-info h3 {
        margin: 0 0 5px 0;
        font-size: 1.3rem;
    }
    
    .semaforo-info p {
        margin: 0;
        color: #8899aa;
        font-size: 0.9rem;
    }
    
    .module-card {
        background-color: #1a1f2e;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #00ff88;
        transition: all 0.2s ease;
    }
    
    .module-card.alerta {
        border-left-color: #ff0044;
        background-color: #1e1520;
    }
    
    .module-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .module-id {
        background-color: #2a2f3e;
        color: #8899aa;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .module-status {
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-ok {
        background-color: rgba(0,255,136,0.15);
        color: #00ff88;
    }
    
    .status-error {
        background-color: rgba(255,0,68,0.15);
        color: #ff0044;
    }
    
    .module-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 5px 0;
    }
    
    .module-ticker {
        color: #00ccff;
        font-weight: bold;
    }
    
    .module-data {
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #2a2f3e;
    }
    
    .data-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
    }
    
    .data-item {
        background-color: #12151f;
        padding: 10px;
        border-radius: 6px;
    }
    
    .data-label {
        color: #8899aa;
        font-size: 0.8rem;
        margin-bottom: 5px;
    }
    
    .data-value {
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    .refresh-button {
        display: flex;
        justify-content: center;
        padding: 30px 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #00ff88, #00ccff);
        color: #0e1117;
        font-weight: bold;
        padding: 12px 30px;
        border: none;
        border-radius: 30px;
        font-size: 1.1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,255,136,0.4);
    }
    
    .footer {
        text-align: center;
        padding: 20px 0;
        color: #556677;
        font-size: 0.8rem;
        border-top: 1px solid #1a1f2e;
        margin-top: 20px;
    }
    
    .expander-header {
        display: flex;
        align-items: center;
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)

def obtener_datos_modulo(ticker, timeout=5):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1mo", timeout=timeout)
        return {"status": "ok", "info": info, "hist": hist}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def modulo_1_pe_ratio():
    resultado = obtener_datos_modulo("NVDA")
    datos = {"id": "M01", "nombre": "Múltiplos de Valoración (P/E Ratio)", "ticker": "NVDA"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "P/E Trailing": info.get("trailingPE", "N/A"),
            "P/E Forward": info.get("forwardPE", "N/A"),
            "PEG Ratio": info.get("pegRatio", "N/A"),
            "Price/Book": info.get("priceToBook", "N/A"),
            "Price/Sales": info.get("priceToSalesTrailing12Months", "N/A")
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_2_crecimiento_ingresos():
    resultado = obtener_datos_modulo("MSFT")
    datos = {"id": "M02", "nombre": "Crecimiento de Ingresos vs Expectativas", "ticker": "MSFT"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "Crecimiento Ingresos": f"{info.get('revenueGrowth', 0) * 100:.2f}%",
            "Crecimiento Ganancias": f"{info.get('earningsGrowth', 0) * 100:.2f}%",
            "Revenue Estimate": f"${info.get('revenueEstimate', 0):.2f}B",
            "Earnings Estimate": f"${info.get('earningsEstimate', 0):.2f}",
            "Surprise %": f"{info.get('earningsSurprise', 0) * 100:.2f}%"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_3_capex_bigtech():
    resultado = obtener_datos_modulo("GOOGL")
    datos = {"id": "M03", "nombre": "Inversión en CapEx de Big Tech", "ticker": "GOOGL"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        capex = info.get("capitalExpenditures", 0)
        datos["valores"] = {
            "CapEx Total": f"${capex/1e9:.2f}B",
            "CapEx/Ingresos": f"{abs(capex)/info.get('totalRevenue', 1) * 100:.2f}%",
            "Flujo de Inversión": f"${info.get('investments', 0)/1e9:.2f}B",
            "Cash Flow Op.": f"${info.get('operatingCashflow', 0)/1e9:.2f}B",
            "Free Cash Flow": f"${info.get('freeCashflow', 0)/1e9:.2f}B"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_4_concentracion_mercado():
    resultado = obtener_datos_modulo("AAPL")
    datos = {"id": "M04", "nombre": "Concentración de Mercado (Top 5)", "ticker": "AAPL"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "Market Cap": f"${info.get('marketCap', 0)/1e12:.2f}T",
            "Share Float": f"{info.get('floatShares', 0)/1e9:.2f}B",
            "% Held by Inst.": f"{info.get('heldPercentInstitutions', 0) * 100:.2f}%",
            "% Held by Insiders": f"{info.get('heldPercentInsiders', 0) * 100:.2f}%",
            "Short Ratio": f"{info.get('shortRatio', 0):.2f}"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_5_margen_beneficio():
    resultado = obtener_datos_modulo("AMZN")
    datos = {"id": "M05", "nombre": "Margen de Beneficio Operativo", "ticker": "AMZN"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "Margen Operativo": f"{info.get('operatingMargins', 0) * 100:.2f}%",
            "Margen Beneficio": f"{info.get('profitMargins', 0) * 100:.2f}%",
            "Margen Bruto": f"{info.get('grossMargins', 0) * 100:.2f}%",
            "ROE": f"{info.get('returnOnEquity', 0) * 100:.2f}%",
            "ROA": f"{info.get('returnOnAssets', 0) * 100:.2f}%"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_6_endeudamiento():
    resultado = obtener_datos_modulo("META")
    datos = {"id": "M06", "nombre": "Nivel de Endeudamiento Neto", "ticker": "META"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "Deuda Total": f"${info.get('totalDebt', 0)/1e9:.2f}B",
            "Deuda/Equity": f"{info.get('debtToEquity', 0):.2f}",
            "Cash": f"${info.get('totalCash', 0)/1e9:.2f}B",
            "Deuda Neta": f"${(info.get('totalDebt', 0) - info.get('totalCash', 0))/1e9:.2f}B",
            "Interest Coverage": f"{info.get('interestCoverage', 0):.2f}"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_7_volatilidad():
    resultado = obtener_datos_modulo("AMD")
    datos = {"id": "M07", "nombre": "Volatilidad del Sector (Implied Vol)", "ticker": "AMD"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        hist = resultado["hist"]
        datos["estado"] = "ok"
        
        if len(hist) > 0:
            returns = hist['Close'].pct_change().dropna()
            volatilidad_historica = returns.std() * (252 ** 0.5) * 100
        else:
            volatilidad_historica = 0
        
        datos["valores"] = {
            "Beta": f"{info.get('beta', 0):.2f}",
            "Volatilidad Hist.": f"{volatilidad_historica:.2f}%",
            "52W High": f"${info.get('fiftyTwoWeekHigh', 0):.2f}",
            "52W Low": f"${info.get('fiftyTwoWeekLow', 0):.2f}",
            "Avg Volume": f"{info.get('averageVolume', 0)/1e6:.2f}M"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_8_fcf_yield():
    resultado = obtener_datos_modulo("AVGO")
    datos = {"id": "M08", "nombre": "Flujo de Caja Libre (FCF Yield)", "ticker": "AVGO"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        fcf = info.get("freeCashflow", 0)
        market_cap = info.get("marketCap", 1)
        fcf_yield = (fcf / market_cap) * 100 if market_cap > 0 else 0
        
        datos["valores"] = {
            "FCF": f"${fcf/1e9:.2f}B",
            "FCF Yield": f"{fcf_yield:.2f}%",
            "Dividend Yield": f"{info.get('dividendYield', 0) * 100:.2f}%",
            "Payout Ratio": f"{info.get('payoutRatio', 0) * 100:.2f}%",
            "Div Rate": f"${info.get('dividendRate', 0):.2f}"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_9_insiders_selling():
    resultado = obtener_datos_modulo("SMCI")
    datos = {"id": "M09", "nombre": "Insiders Selling (Venta de Directivos)", "ticker": "SMCI"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "% Held by Insiders": f"{info.get('heldPercentInsiders', 0) * 100:.2f}%",
            "% Held by Inst.": f"{info.get('heldPercentInstitutions', 0) * 100:.2f}%",
            "Short Ratio": f"{info.get('shortRatio', 0):.2f}",
            "Short % Float": f"{info.get('shortPercentOfFloat', 0) * 100:.2f}%",
            "Shares Short": f"{info.get('shortShares', 0)/1e6:.2f}M"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_10_rd_gasto():
    resultado = obtener_datos_modulo("PLTR")
    datos = {"id": "M10", "nombre": "Gasto en I+D (R&D % Ingresos)", "ticker": "PLTR"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        rd = info.get("researchAndDevelopment", 0)
        revenue = info.get("totalRevenue", 1)
        rd_percentage = (rd / revenue) * 100 if revenue > 0 else 0
        
        datos["valores"] = {
            "Gasto R&D": f"${rd/1e9:.2f}B",
            "R&D % Ingresos": f"{rd_percentage:.2f}%",
            "SGA % Ingresos": f"{info.get('sgaExpenses', 0)/revenue * 100:.2f}%",
            "OpEx Total": f"${(rd + info.get('sgaExpenses', 0))/1e9:.2f}B",
            "Ingresos Totales": f"${revenue/1e9:.2f}B"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_11_primas_riesgo():
    resultado = obtener_datos_modulo("ASML")
    datos = {"id": "M11", "nombre": "Primas de Riesgo en Opciones", "ticker": "ASML"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        datos["valores"] = {
            "Implied Volatility": f"{info.get('impliedVolatility', 0) * 100:.2f}%",
            "Put/Call Ratio": f"{info.get('putToCallRatio', 0):.2f}",
            "Open Interest": f"{info.get('openInterest', 0)/1e6:.2f}M",
            "52W High": f"${info.get('fiftyTwoWeekHigh', 0):.2f}",
            "52W Low": f"${info.get('fiftyTwoWeekLow', 0):.2f}"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_12_apalancamiento():
    resultado = obtener_datos_modulo("TSM")
    datos = {"id": "M12", "nombre": "Multiplicador de Apalancamiento", "ticker": "TSM"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        total_assets = info.get("totalAssets", 1)
        total_equity = info.get("totalEquity", 1)
        apalancamiento = total_assets / total_equity if total_equity > 0 else 0
        
        datos["valores"] = {
            "Multiplicador Apalanc.": f"{apalancamiento:.2f}x",
            "Deuda/Assets": f"{info.get('debtToEquity', 0) / (1 + info.get('debtToEquity', 0)) * 100:.2f}%",
            "Equity Multiplier": f"{total_assets / total_equity:.2f}x",
            "ROE": f"{info.get('returnOnEquity', 0) * 100:.2f}%",
            "ROA": f"{info.get('returnOnAssets', 0) * 100:.2f}%"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def modulo_13_sentimiento():
    resultado = obtener_datos_modulo("QCOM")
    datos = {"id": "M13", "nombre": "Sentimiento del Mercado", "ticker": "QCOM"}
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        datos["estado"] = "ok"
        
        recomendacion = info.get("recommendationKey", "N/A")
        target_price = info.get("targetHighPrice", 0)
        current_price = info.get("currentPrice", 1)
        upside = ((target_price / current_price) - 1) * 100 if current_price > 0 else 0
        
        datos["valores"] = {
            "Recomendación": recomendacion,
            "Target Price": f"${info.get('targetMeanPrice', 0):.2f}",
            "Upside Potencial": f"{upside:.2f}%",
            "# Analistas": f"{info.get('numberOfAnalystOpinions', 0)}",
            "Consensus Score": f"{info.get('averageAnalystRating', 0):.2f}"
        }
    else:
        datos["estado"] = "error"
        datos["valores"] = {"Error": resultado["message"]}
    
    return datos

def render_modulo(modulo_datos):
    estado = modulo_datos["estado"]
    clase_card = "module-card" if estado == "ok" else "module-card alerta"
    clase_status = "status-ok" if estado == "ok" else "status-error"
    texto_status = "Activo" if estado == "ok" else "No disponible"
    
    html = f"""
    <div class="{clase_card}">
        <div class="module-header">
            <span class="module-id">{modulo_datos["id"]}</span>
            <span class="module-status {clase_status}">{texto_status}</span>
        </div>
        <div class="module-title">{modulo_datos["nombre"]} <span class="module-ticker">({modulo_datos["ticker"]})</span></div>
        <div class="module-data">
            <div class="data-grid">
    """
    
    for etiqueta, valor in modulo_datos["valores"].items():
        html += f"""
                <div class="data-item">
                    <div class="data-label">{etiqueta}</div>
                    <div class="data-value">{valor}</div>
                </div>
        """
    
    html += """
            </div>
        </div>
    </div>
    """
    
    return html

def main():
    modulos = [
        modulo_1_pe_ratio,
        modulo_2_crecimiento_ingresos,
        modulo_3_capex_bigtech,
        modulo_4_concentracion_mercado,
        modulo_5_margen_beneficio,
        modulo_6_endeudamiento,
        modulo_7_volatilidad,
        modulo_8_fcf_yield,
        modulo_9_insiders_selling,
        modulo_10_rd_gasto,
        modulo_11_primas_riesgo,
        modulo_12_apalancamiento,
        modulo_13_sentimiento
    ]
    
    resultados = [modulo() for modulo in modulos]
    
    alertas = sum(1 for resultado in resultados if resultado["estado"] == "error")
    
    if alertas == 0:
        semaforo_clase = "verde"
        semaforo_emoji = "✅"
        semaforo_texto = "SISTEMA SEGUR"
        semaforo_desc = "Todos los módulos están operativos. No se detectan riesgos críticos en la burbuja de IA."
    elif alertas <= 3:
        semaforo_clase = "amarillo"
        semaforo_emoji = "⚠️"
        semaforo_texto = "PRECAUCIÓN"
        semaforo_desc = f"Se han detectado {alertas} alerta(s). Algunos módulos no están disponibles, lo que indica posible volatilidad sectorial."
    else:
        semaforo_clase = "rojo"
        semaforo_emoji = "🚨"
        semaforo_texto = "ALERTA ROJA"
        semaforo_desc = f"CRÍTICO: {alertas} módulos caídos. Alta probabilidad de estrés en el sector de IA. Se recomienda extrema precaución."
    
    st.markdown("""
    <div class="main-header">
        <h1>📡 RadarIA</h1>
        <p>Monitor de Riesgo de la Burbuja de Inteligencia Artificial</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="semaforo-container">
        <div class="semaforo {semaforo_clase}">{semaforo_emoji}</div>
        <div class="semaforo-info">
            <h3>{semaforo_texto}</h3>
            <p>{semaforo_desc}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="background-color: #1a1f2e; padding: 8px 15px; border-radius: 20px; font-size: 0.9rem;">
            Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Módulos activos: {13 - alertas}/13 | 
            Alertas: {alertas}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    for resultado in resultados:
        with st.expander(f"{resultado['id']} - {resultado['nombre']} ({resultado['ticker']})"):
            st.markdown(render_modulo(resultado), unsafe_allow_html=True)
    
    st.markdown("""
    <div class="refresh-button">
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Actualizar Datos en Tiempo Real"):
        st.experimental_rerun()
    
    st.markdown("""
    </div>
    <div class="footer">
        <p>RadarIA v1.0 | Desarrollado para monitorizar el riesgo de la burbuja de IA | Datos proporcionados por Yahoo Finance</p>
        <p>© 2023 RadarIA. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
