```python
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
            "P/E Trailing": str(info.get("trailingPE", "No disponible")),
            "P/E Forward": str(info.get("forwardPE", "No disponible")),
            "PEG Ratio": str(info.get("pegRatio", "No disponible")),
            "Price/Book": str(info.get("priceToBook", "No disponible")),
            "Price/Sales": str(info.get("priceToSalesTrailing12Months", "No disponible"))
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
        
        revenue_growth = info.get("revenueGrowth", None)
        earnings_growth = info.get("earningsGrowth", None)
        revenue_estimate = info.get("revenueEstimate", None)
        earnings_estimate = info.get("earningsEstimate", None)
        earnings_surprise = info.get("earningsSurprise", None)
        
        datos["valores"] = {
            "Crecimiento Ingresos": str(revenue_growth * 100) + "%" if revenue_growth else "No disponible",
            "Crecimiento Ganancias": str(earnings_growth * 100) + "%" if earnings_growth else "No disponible",
            "Revenue Estimate": "$" + str(revenue_estimate) + "B" if revenue_estimate else "No disponible",
            "Earnings Estimate": "$" + str(earnings_estimate) if earnings_estimate else "No disponible",
            "Surprise %": str(earnings_surprise * 100) + "%" if earnings_surprise else "No disponible"
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
        
        capex = info.get("capitalExpenditures", None)
        total_revenue = info.get("totalRevenue", None)
        investments = info.get("investments", None)
        operating_cashflow = info.get("operatingCashflow", None)
        free_cashflow = info.get("freeCashflow", None)
        
        capex_revenue = str(abs(capex) / total_revenue * 100) + "%" if capex and total_revenue else "No disponible"
        
        datos["valores"] = {
            "CapEx Total": "$" + str(capex / 1e9) + "B" if capex else "No disponible",
            "CapEx/Ingresos": capex_revenue,
            "Flujo de Inversión": "$" + str(investments / 1e9) + "B" if investments else "No disponible",
            "Cash Flow Op.": "$" + str(operating_cashflow / 1e9) + "B" if operating_cashflow else "No disponible",
            "Free Cash Flow": "$" + str(free_cashflow / 1e9) + "B" if free_cashflow else "No disponible"
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
        
        market_cap = info.get("marketCap", None)
        float_shares = info.get("floatShares", None)
        held_percent_institutions = info.get("heldPercentInstitutions", None)
        held_percent_insiders = info.get("heldPercentInsiders", None)
        short_ratio = info.get("shortRatio", None)
        
        datos["valores"] = {
            "Market Cap": "$" + str(market_cap / 1e12) + "T" if market_cap else "No disponible",
            "Share Float": str(float_shares / 1e9) + "B" if float_shares else "No disponible",
            "% Held by Inst.": str(held_percent_institutions * 100) + "%" if held_percent_institutions else "No disponible",
            "% Held by Insiders": str(held_percent_insiders * 100) + "%" if held_percent_insiders else "No disponible",
            "Short Ratio": str(short_ratio) if short_ratio else "No disponible"
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
        
        operating_margins = info.get("operatingMargins", None)
        profit_margins = info.get("profitMargins", None)
        gross_margins = info.get("grossMargins", None)
        return_on_equity = info.get("returnOnEquity", None)
        return_on_assets = info.get("returnOnAssets", None)
        
        datos["valores"] = {
            "Margen Operativo": str(operating_margins * 100) + "%" if operating_margins else "No disponible",
            "Margen Beneficio": str(profit_margins * 100) + "%" if profit_margins else "No disponible",
            "Margen Bruto": str(gross_margins * 100) + "%" if gross_margins else "No disponible",
            "ROE": str(return_on_equity * 100) + "%" if return_on_equity else "No disponible",
            "ROA": str(return_on_assets * 100) + "%" if return_on_assets else "No disponible"
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
        
        total_debt = info.get("totalDebt", None)
        debt_to_equity = info.get("debtToEquity", None)
        total_cash = info.get("totalCash", None)
        interest_coverage = info.get("interestCoverage", None)
        
        net_debt = (total_debt - total_cash) / 1e9 if total_debt and total_cash else None
        
        datos["valores"] = {
            "Deuda Total": "$" + str(total_debt / 1e9) + "B" if total_debt else "No disponible",
            "Deuda/Equity": str(debt_to_equity) if debt_to_equity else "No disponible",
            "Cash": "$" + str(total_cash / 1e9) + "B" if total_cash else "No disponible",
            "Deuda Neta": "$" + str(net_debt) + "B" if net_debt else "No disponible",
            "Interest Coverage": str(interest_coverage) if interest_coverage else "No disponible"
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
        
        beta = info.get("beta", None)
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", None)
        fifty_two_week_low = info.get("fiftyTwoWeekLow", None)
        average_volume = info.get("averageVolume", None)
        
        volatilidad_historica = "No disponible"
        if len(hist) > 0:
            returns = hist['Close'].pct_change().dropna()
            vol = returns.std() * (252 ** 0.5) * 100
            if vol:
                volatilidad_historica = str(vol) + "%"
        
        datos["valores"] = {
            "Beta": str(beta) if beta else "No disponible",
            "Volatilidad Hist.": volatilidad_historica,
            "52W High": "$" + str(fifty_two_week_high) if fifty_two_week_high else "No disponible",
            "52W Low": "$" + str(fifty_two_week_low) if fifty_two_week_low else "No disponible",
            "Avg Volume": str(average_volume / 1e6) + "M" if average_volume else "No disponible"
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
        
        fcf = info.get("freeCashflow", None)
        market_cap = info.get("marketCap", None)
        dividend_yield = info.get("dividendYield", None)
        payout_ratio = info.get("payoutRatio", None)
        dividend_rate = info.get("dividendRate", None)
        
        fcf_yield = str(fcf / market_cap * 100) + "%" if fcf and market_cap else "No disponible"
        
        datos["valores"] = {
            "FCF": "$" + str(fcf / 1e9) + "B" if fcf else "No disponible",
            "FCF Yield": fcf_yield,
            "Dividend Yield": str(dividend_yield * 100) + "%" if dividend_yield else "No disponible",
            "Payout Ratio": str(payout_ratio * 100) + "%" if payout_ratio else "No disponible",
            "Div Rate": "$" + str(dividend_rate) if dividend_rate else "No disponible"
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
        
        held_percent_insiders = info.get("heldPercentInsiders", None)
        held_percent_institutions = info.get("heldPercentInstitutions", None)
        short_ratio = info.get("shortRatio", None)
        short_percent_of_float = info.get("shortPercentOfFloat", None)
        short_shares = info.get("shortShares", None)
        
        datos["valores"] = {
            "% Held by Insiders": str(held_percent_insiders * 100) + "%" if held_percent_insiders else "No disponible",
            "% Held by Inst.": str(held_percent_institutions * 100) + "%" if held_percent_institutions else "No disponible",
            "Short Ratio": str(short_ratio) if short_ratio else "No disponible",
            "Short % Float": str(short_percent_of_float * 100) + "%" if short_percent_of_float else "No disponible",
            "Shares Short": str(short_shares / 1e6) + "M" if short_shares else "No disponible"
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
        
        rd = info.get("researchAndDevelopment", None)
        total_revenue = info.get("totalRevenue", None)
        sga_expenses = info.get("sgaExpenses", None)
        
        rd_percentage = str(rd / total_revenue * 100) + "%" if rd and total_revenue else "No disponible"
        sga_percentage = str(sga_expenses / total_revenue * 100) + "%" if sga_expenses and total_revenue else "No disponible"
        opex_total = (rd + sga_expenses) / 1e9 if rd and sga_expenses else None
        
        datos["valores"] = {
            "Gasto R&D": "$" + str(rd / 1e9) + "B" if rd else "No disponible",
            "R&D % Ingresos": rd_percentage,
            "SGA % Ingresos": sga_percentage,
            "OpEx Total": "$" + str(opex_total) + "B" if opex_total else "No disponible",
            "Ingresos Totales": "$" + str(total_revenue / 1e9) + "B" if total_revenue else "No disponible"
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
        
        implied_volatility = info.get("impliedVolatility", None)
        put_to_call_ratio = info.get("putToCallRatio", None)
        open_interest = info.get("openInterest", None)
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", None)
        fifty_two_week_low = info.get("fiftyTwoWeekLow", None)
        
        datos["valores"] = {
            "Implied Volatility": str(implied_volatility * 100) + "%" if implied_volatility else "No disponible",
            "Put/Call Ratio": str(put_to_call_ratio) if put_to_call_ratio else "No disponible",
            "Open Interest": str(open_interest / 1e6) + "M" if open_interest else "No disponible",
            "52W High": "$" + str(fifty_two_week_high) if fifty_two_week_high else "No disponible",
            "52W Low": "$" + str(fifty_two_week_low) if fifty_two_week_low else "No disponible"
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
        
        total_assets = info.get("totalAssets", None)
        total_equity = info.get("totalEquity", None)
        debt_to_equity = info.get("debtToEquity", None)
        return_on_equity = info.get("returnOnEquity", None)
        return_on_assets = info.get("returnOnAssets", None)
        
        apalancamiento = str(total_assets / total_equity) + "x" if total_assets and total_equity else "No disponible"
        equity_multiplier = str(total_assets / total_equity) + "x" if total_assets and total_equity else "No disponible"
        debt_assets = str(debt_to_equity / (1 + debt_to_equity) * 100) + "%" if debt_to_equity else "No disponible"
        
        datos["valores"] = {
            "Multiplicador Apalanc.": apalancamiento,
            "Deuda/Assets": debt_assets,
            "Equity Multiplier": equity_multiplier,
            "ROE": str(return_on_equity * 100) + "%" if return_on_equity else "No disponible",
            "ROA": str(return_on_assets * 100) + "%" if return_on_assets else "No disponible"
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
        
        recommendation_key = info.get("recommendationKey", None)
        target_high_price = info.get("targetHighPrice", None)
        current_price = info.get("currentPrice", None)
        number_of_analyst_opinions = info.get("numberOfAnalystOpinions", None)
        average_analyst_rating = info.get("averageAnalystRating", None)
        
        upside = str((target_high_price / current_price - 1) * 100) + "%" if target_high_price and current_price else "No disponible"
        
        datos["valores"] = {
            "Recomendación": str(recommendation_key) if recommendation_key else "No disponible",
            "Target Price": "$" + str(target_high_price) if target_high_price else "No disponible",
            "Upside Potencial": upside,
            "# Analistas": str(number_of_analyst_opinions) if number_of_analyst_opinions else "No disponible",
            "Consensus Score": str(average_analyst_rating) if average_analyst_rating else "No disponible"
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
```
