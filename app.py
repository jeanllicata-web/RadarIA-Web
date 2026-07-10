import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
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
    
    .module-container {
        margin-bottom: 10px;
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
    
    .status-ok {
        color: #00ff88;
        font-weight: bold;
    }
    
    .status-error {
        color: #ff0044;
        font-weight: bold;
    }
    
    .metric-section {
        margin-bottom: 15px;
    }
    
    .metric-label {
        color: #8899aa;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .metric-description {
        color: #aab5c3;
        font-size: 0.9rem;
        margin-bottom: 15px;
        line-height: 1.4;
    }
    
    .conclusion-container {
        background-color: #1a1f2e;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        border-left: 4px solid #00ff88;
    }
    
    .conclusion-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    .conclusion-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #ccd6e0;
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

def determinar_alerta_pe_ratio(info):
    pe_ratio = info.get("trailingPE", None)
    if pe_ratio is None:
        return True, "No disponible"
    
    # Consideramos alerta si el P/E es muy alto (mayor a 100)
    if pe_ratio > 100:
        return True, f"{pe_ratio}"
    else:
        return False, f"{pe_ratio}"

def determinar_alerta_crecimiento(info):
    revenue_growth = info.get("revenueGrowth", None)
    if revenue_growth is None:
        return True, "No disponible"
    
    # Consideramos alerta si el crecimiento es negativo
    if revenue_growth < 0:
        return True, f"{revenue_growth * 100}%"
    else:
        return False, f"{revenue_growth * 100}%"

def determinar_alerta_capex(info):
    capex = info.get("capitalExpenditures", None)
    total_revenue = info.get("totalRevenue", None)
    
    if capex is None or total_revenue is None:
        return True, "No disponible"
    
    capex_ratio = abs(capex) / total_revenue
    
    # Consideramos alerta si CapEx es más del 20% de los ingresos
    if capex_ratio > 0.2:
        return True, f"{capex_ratio * 100}%"
    else:
        return False, f"{capex_ratio * 100}%"

def determinar_alerta_concentracion(info):
    held_percent_institutions = info.get("heldPercentInstitutions", None)
    
    if held_percent_institutions is None:
        return True, "No disponible"
    
    # Consideramos alerta si más del 80% está en manos de instituciones
    if held_percent_institutions > 0.8:
        return True, f"{held_percent_institutions * 100}%"
    else:
        return False, f"{held_percent_institutions * 100}%"

def determinar_alerta_margen(info):
    operating_margins = info.get("operatingMargins", None)
    
    if operating_margins is None:
        return True, "No disponible"
    
    # Consideramos alerta si el margen operativo es menor al 10%
    if operating_margins < 0.1:
        return True, f"{operating_margins * 100}%"
    else:
        return False, f"{operating_margins * 100}%"

def determinar_alerta_endeudamiento(info):
    debt_to_equity = info.get("debtToEquity", None)
    
    if debt_to_equity is None:
        return True, "No disponible"
    
    # Consideramos alerta si la deuda es más de 2 veces el equity
    if debt_to_equity > 2:
        return True, f"{debt_to_equity}"
    else:
        return False, f"{debt_to_equity}"

def determinar_alerta_volatilidad(info, hist):
    beta = info.get("beta", None)
    
    if beta is None:
        return True, "No disponible"
    
    # Consideramos alerta si el beta es mayor a 1.5
    if beta > 1.5:
        return True, f"{beta}"
    else:
        return False, f"{beta}"

def determinar_alerta_fcf_yield(info):
    fcf = info.get("freeCashflow", None)
    market_cap = info.get("marketCap", None)
    
    if fcf is None or market_cap is None or market_cap == 0:
        return True, "No disponible"
    
    fcf_yield = fcf / market_cap
    
    # Consideramos alerta si el FCF Yield es menor al 2%
    if fcf_yield < 0.02:
        return True, f"{fcf_yield * 100}%"
    else:
        return False, f"{fcf_yield * 100}%"

def determinar_alerta_insiders(info):
    held_percent_insiders = info.get("heldPercentInsiders", None)
    
    if held_percent_insiders is None:
        return True, "No disponible"
    
    # Consideramos alerta si los insiders tienen menos del 1%
    if held_percent_insiders < 0.01:
        return True, f"{held_percent_insiders * 100}%"
    else:
        return False, f"{held_percent_insiders * 100}%"

def determinar_alerta_rd(info):
    rd = info.get("researchAndDevelopment", None)
    total_revenue = info.get("totalRevenue", None)
    
    if rd is None or total_revenue is None or total_revenue == 0:
        return True, "No disponible"
    
    rd_percentage = rd / total_revenue
    
    # Consideramos alerta si el gasto en R&D es menos del 10% de los ingresos
    if rd_percentage < 0.1:
        return True, f"{rd_percentage * 100}%"
    else:
        return False, f"{rd_percentage * 100}%"

def determinar_alerta_primas(info):
    implied_volatility = info.get("impliedVolatility", None)
    
    if implied_volatility is None:
        return True, "No disponible"
    
    # Consideramos alerta si la volatilidad implícita es mayor al 40%
    if implied_volatility > 0.4:
        return True, f"{implied_volatility * 100}%"
    else:
        return False, f"{implied_volatility * 100}%"

def determinar_alerta_apalancamiento(info):
    total_assets = info.get("totalAssets", None)
    total_equity = info.get("totalEquity", None)
    
    if total_assets is None or total_equity is None or total_equity == 0:
        return True, "No disponible"
    
    equity_multiplier = total_assets / total_equity
    
    # Consideramos alerta si el multiplicador es mayor a 3
    if equity_multiplier > 3:
        return True, f"{equity_multiplier}x"
    else:
        return False, f"{equity_multiplier}x"

def determinar_alerta_sentimiento(info):
    recommendation_key = info.get("recommendationKey", None)
    
    if recommendation_key is None:
        return True, "No disponible"
    
    # Consideramos alerta si la recomendación es vender o reducir
    if recommendation_key in ["sell", "reduce"]:
        return True, f"{recommendation_key}"
    else:
        return False, f"{recommendation_key}"

def modulo_1_pe_ratio():
    resultado = obtener_datos_modulo("NVDA")
    datos = {
        "id": "M01", 
        "nombre": "Múltiplos de Valoración (P/E Ratio)", 
        "ticker": "NVDA",
        "explicacion": "El ratio P/E (Precio/Beneficio) mide cuánto están dispuestos a pagar los inversores por cada dólar de ganancias de la empresa. Un P/E muy alto puede indicar que las acciones están sobrevaloradas y existe riesgo de corrección.",
        "metrica": "P/E Trailing"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_pe_ratio(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_2_crecimiento_ingresos():
    resultado = obtener_datos_modulo("MSFT")
    datos = {
        "id": "M02", 
        "nombre": "Crecimiento de Ingresos vs Expectativas", 
        "ticker": "MSFT",
        "explicacion": "Mide si los ingresos de la empresa están creciendo al ritmo esperado por los analistas. Un crecimiento inferior a las expectativas puede señalizar que el negocio se está desacelerando.",
        "metrica": "Crecimiento de Ingresos"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_crecimiento(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_3_capex_bigtech():
    resultado = obtener_datos_modulo("GOOGL")
    datos = {
        "id": "M03", 
        "nombre": "Inversión en CapEx de Big Tech", 
        "ticker": "GOOGL",
        "explicacion": "Analiza cuánto invierte la empresa en infraestructura y equipos (CapEx) en relación con sus ingresos. Una inversión excesiva podría generar problemas de rentabilidad si no se traduce en crecimiento futuro.",
        "metrica": "CapEx / Ingresos"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_capex(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_4_concentracion_mercado():
    resultado = obtener_datos_modulo("AAPL")
    datos = {
        "id": "M04", 
        "nombre": "Concentración de Mercado (Top 5)", 
        "ticker": "AAPL",
        "explicacion": "Evalúa qué porcentaje de las acciones está en manos de grandes instituciones financieras. Una concentración excesiva puede hacer que el mercado sea más volátil si estas instituciones deciden vender masivamente.",
        "metrica": "% en manos de Instituciones"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_concentracion(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_5_margen_beneficio():
    resultado = obtener_datos_modulo("AMZN")
    datos = {
        "id": "M05", 
        "nombre": "Margen de Beneficio Operativo", 
        "ticker": "AMZN",
        "explicacion": "Mide la eficiencia operativa de la empresa calculando qué porcentaje de cada dólar de ingresos queda como beneficio después de cubrir los costos operativos. Un margen bajo puede indicar problemas de eficiencia o competitividad.",
        "metrica": "Margen Operativo"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_margen(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_6_endeudamiento():
    resultado = obtener_datos_modulo("META")
    datos = {
        "id": "M06", 
        "nombre": "Nivel de Endeudamiento Neto", 
        "ticker": "META",
        "explicacion": "Analiza la relación entre la deuda total de la empresa y su valor patrimonial (equity). Un nivel de deuda elevado respecto al patrimonio puede aumentar significativamente el riesgo financiero.",
        "metrica": "Deuda / Equity"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_endeudamiento(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_7_volatilidad():
    resultado = obtener_datos_modulo("AMD")
    datos = {
        "id": "M07", 
        "nombre": "Volatilidad del Sector (Implied Vol)", 
        "ticker": "AMD",
        "explicacion": "El Beta mide cómo se mueve la acción en relación con el mercado general. Un Beta mayor a 1 indica que la acción es más volátil que el mercado, lo que implica mayor riesgo en periodos de turbulencia.",
        "metrica": "Beta"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        hist = resultado["hist"]
        alerta, valor = determinar_alerta_volatilidad(info, hist)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_8_fcf_yield():
    resultado = obtener_datos_modulo("AVGO")
    datos = {
        "id": "M08", 
        "nombre": "Flujo de Caja Libre (FCF Yield)", 
        "ticker": "AVGO",
        "explicacion": "El FCF Yield mide el flujo de caja libre generado por la empresa en relación con su valor de mercado. Un yield bajo puede indicar que la acción está cara respecto al efectivo real que genera.",
        "metrica": "FCF Yield"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_fcf_yield(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_9_insiders_selling():
    resultado = obtener_datos_modulo("SMCI")
    datos = {
        "id": "M09", 
        "nombre": "Insiders Selling (Venta de Directivos)", 
        "ticker": "SMCI",
        "explicacion": "Analiza el porcentaje de acciones en manos de directivos y empleados de la empresa. Una participación muy baja de los insiders puede ser señal de que los que mejor conocen la empresa no confían en su futuro.",
        "metrica": "% en manos de Insiders"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_insiders(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_10_rd_gasto():
    resultado = obtener_datos_modulo("PLTR")
    datos = {
        "id": "M10", 
        "nombre": "Gasto en I+D (R&D % Ingresos)", 
        "ticker": "PLTR",
        "explicacion": "Mide qué porcentaje de los ingresos se invierte en investigación y desarrollo. Para empresas tecnológicas, un gasto en I+D bajo puede indicar falta de innovación futura, especialmente en el competitivo sector de la IA.",
        "metrica": "R&D / Ingresos"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_rd(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_11_primas_riesgo():
    resultado = obtener_datos_modulo("ASML")
    datos = {
        "id": "M11", 
        "nombre": "Primas de Riesgo en Opciones", 
        "ticker": "ASML",
        "explicacion": "La volatilidad implícita refleja las expectativas del mercado sobre futuros movimientos del precio. Una volatilidad implícita alta indica que los inversores esperan grandes oscilaciones, señal de incertidumbre y riesgo.",
        "metrica": "Volatilidad Implícita"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_primas(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_12_apalancamiento():
    resultado = obtener_datos_modulo("TSM")
    datos = {
        "id": "M12", 
        "nombre": "Multiplicador de Apalancamiento", 
        "ticker": "TSM",
        "explicacion": "El multiplicador de apalancamiento mide cuántos dólares de activos tiene la empresa por cada dólar de patrimonio. Un multiplicador alto indica que la empresa está muy apalancada, lo que amplifica tanto las ganancias como las pérdidas.",
        "metrica": "Multiplicador de Apalancamiento"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_apalancamiento(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def modulo_13_sentimiento():
    resultado = obtener_datos_modulo("QCOM")
    datos = {
        "id": "M13", 
        "nombre": "Sentimiento del Mercado", 
        "ticker": "QCOM",
        "explicacion": "Analiza la recomendación general de los analistas de Wall Street sobre la acción. Una recomendación de venta o reducción de posición puede ser una señal de alarma sobre las perspectivas de la empresa.",
        "metrica": "Recomendación de Analistas"
    }
    
    if resultado["status"] == "ok":
        info = resultado["info"]
        alerta, valor = determinar_alerta_sentimiento(info)
        datos["estado"] = "alerta" if alerta else "ok"
        datos["valor"] = valor
    else:
        datos["estado"] = "error"
        datos["valor"] = "No disponible"
    
    return datos

def crear_grafico_riesgo(nivel_riesgo):
    # Crear datos para el gráfico de líneas
    x = list(range(0, 14))
    y = [nivel_riesgo] * 14
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir zonas de colores
    fig.add_shape(type="rect", x0=0, y0=0, x1=3, y1=14, 
                  fillcolor="rgba(0, 255, 136, 0.1)", line_width=0)
    fig.add_shape(type="rect", x0=4, y0=0, x1=7, y1=14, 
                  fillcolor="rgba(255, 221, 0, 0.1)", line_width=0)
    fig.add_shape(type="rect", x0=8, y0=0, x1=13, y1=14, 
                  fillcolor="rgba(255, 0, 68, 0.1)", line_width=0)
    
    # Añadir línea de riesgo
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        line=dict(color='#00ff88', width=3),
        name='Nivel de Riesgo'
    ))
    
    # Añadir punto indicador
    fig.add_trace(go.Scatter(
        x=[nivel_riesgo],
        y=[nivel_riesgo],
        mode='markers',
        marker=dict(color='#00ff88', size=15, line=dict(color='white', width=2)),
        name='Riesgo Actual'
    ))
    
    # Configurar layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(
            text='Termómetro de Riesgo del Sector IA',
            font=dict(size=18, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Módulos',
            range=[0, 13],
            gridcolor='rgba(255,255,255,0.1)',
            tick0=0,
            dtick=1
        ),
        yaxis=dict(
            title='Nivel de Riesgo',
            range=[0, 13],
            gridcolor='rgba(255,255,255,0.1)',
            tick0=0,
            dtick=1
        ),
        margin=dict(l=50, r=50, t=50, b=50),
        height=400,
        showlegend=False
    )
    
    # Añadir anotaciones para las zonas
    fig.add_annotation(x=1.5, y=12, text="Zona Verde\n(Riesgo Bajo)", 
                       showarrow=False, font=dict(color="rgba(0, 255, 136, 0.7)"))
    fig.add_annotation(x=5.5, y=12, text="Zona Amarilla\n(Riesgo Moderado)", 
                       showarrow=False, font=dict(color="rgba(255, 221, 0, 0.7)"))
    fig.add_annotation(x=10.5, y=12, text="Zona Roja\n(Riesgo Crítico)", 
                       showarrow=False, font=dict(color="rgba(255, 0, 68, 0.7)"))
    
    return fig

def generar_conclusion(alertas):
    if alertas == 0:
        return """
        El sector de la Inteligencia Artificial presenta **fundamentales sólidos y estables** en este momento. 
        Todos los indicadores analizados se encuentran dentro de rangos saludables, lo que sugiere que 
        las valoraciones están justificadas por el crecimiento real de los negocios y no por especulación excesiva. 
        No se detectan señales de burbuja inminente, y las empresas del sector muestran un equilibrio 
        adecuado entre crecimiento, rentabilidad y riesgo financiero.
        """
    elif alertas <= 3:
        return f"""
        El sector de la Inteligencia Artificial muestra **algunos puntos de atención** con {alertas} indicadores 
        en zona de alerta. Aunque la mayoría de los fundamentales se mantienen sólidos, es recomendable 
        monitorear de cerca estos aspectos que podrían convertirse en problemas más significativos si 
        la tendencia continúa. No hay señales claras de burbuja, pero se advierte cierta tensión 
        en aspectos específicos que merecen vigilancia.
        """
    elif alertas <= 7:
        return f"""
        **PRECAUCIÓN:** El sector de la IA presenta {alertas} indicadores en zona de alerta, lo que sugiere 
        un **incremento significativo en el nivel de riesgo**. Varios fundamentales clave están mostrando 
        señales de estrés, lo que podría indicar un sobrecalentamiento parcial del sector. Se recomienda 
        extremar la cautela y considerar reducir la exposición a los activos más afectados. 
        Aunque no podemos confirmar una burbuja generalizada, los signos de exceso son cada vez más evidentes.
        """
    else:
        return f"""
        **ALERTA ROJA:** Con {alertas} indicadores en zona de alerta, los datos sugieren un **sobrecalentamiento 
        severo en el sector de la IA**. Múltiples fundamentales están en niveles preocupantes, 
        con señales claras de sobrevaloración, apalancamiento excesivo y cambio en el sentimiento del mercado. 
        Existe un **riesgo muy elevado de corrección significativa o estallido de burbuja** en el corto/medio plazo. 
        Se recomienda encarecidamente reducir la exposición al sector y considerar estrategias de protección 
        de capital. Esta situación requiere máxima precaución y monitorización constante.
        """

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
    
    # Contar alertas (estado "alerta" o "error")
    alertas = sum(1 for resultado in resultados if resultado["estado"] in ["alerta", "error"])
    
    # Determinar clase del semáforo
    if alertas == 0:
        semaforo_clase = "verde"
        semaforo_emoji = "✅"
        semaforo_texto = "SISTEMA SEGURO"
        semaforo_desc = "Todos los módulos están operativos. No se detectan riesgos críticos en la burbuja de IA."
    elif alertas <= 3:
        semaforo_clase = "amarillo"
        semaforo_emoji = "⚠️"
        semaforo_texto = "PRECAUCIÓN"
        semaforo_desc = f"Se han detectado {alertas} alerta(s). Algunos módulos muestran señales de riesgo."
    else:
        semaforo_clase = "rojo"
        semaforo_emoji = "🚨"
        semaforo_texto = "ALERTA ROJA"
        semaforo_desc = f"CRÍTICO: {alertas} módulos en alerta. Alto riesgo de burbuja en el sector IA."
    
    # Encabezado
    st.markdown("""
    <div class="main-header">
        <h1>📡 RadarIA</h1>
        <p>Monitor de Riesgo de la Burbuja de Inteligencia Artificial</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Semáforo
    st.markdown(f"""
    <div class="semaforo-container">
        <div class="semaforo {semaforo_clase}">{semaforo_emoji}</div>
        <div class="semaforo-info">
            <h3>{semaforo_texto}</h3>
            <p>{semaforo_desc}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Información de actualización
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="background-color: #1a1f2e; padding: 8px 15px; border-radius: 20px; font-size: 0.9rem;">
            Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            Módulos en alerta: {alertas}/13
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Gráfico de termómetro de riesgo
    st.plotly_chart(crear_grafico_riesgo(alertas), use_container_width=True)
    
    # Módulos con expanders
    for resultado in resultados:
        estado = resultado["estado"]
        clase_status = "status-ok" if estado == "ok" else "status-error"
        texto_status = "✅ Normal" if estado == "ok" else "🚨 Alerta"
        
        with st.expander(f"{resultado['id']} - {resultado['nombre']} ({resultado['ticker']})"):
            st.markdown(f"""
            <div class="module-container">
                <div class="metric-section">
                    <div class="metric-label">Métrica analizada</div>
                    <div class="metric-description">{resultado['explicacion']}</div>
                </div>
                
                <div class="metric-section">
                    <div class="metric-label">Resultado de Wall Street ({resultado['metrica']})</div>
                    <div class="metric-value">{resultado['valor']}</div>
                </div>
                
                <div class="metric-section">
                    <div class="metric-label">Estado de Alerta</div>
                    <div class="{clase_status}">{texto_status}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Conclusión ejecutiva
    st.markdown("""
    <div class="conclusion-container">
        <div class="conclusion-title">🔍 CONCLUSIÓN EJECUTIVA DEL RADAR</div>
        <div class="conclusion-text">
    """, unsafe_allow_html=True)
    
    st.markdown(generar_conclusion(alertas))
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de actualización
    st.markdown("""
    <div class="refresh-button">
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Actualizar Datos en Tiempo Real"):
        st.experimental_rerun()
    
    st.markdown("""
    </div>
    <div class="footer">
        <p>RadarIA v2.0 | Desarrollado para monitorizar el riesgo de la burbuja de IA | Datos proporcionados por Yahoo Finance</p>
        <p>© 2023 RadarIA. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
