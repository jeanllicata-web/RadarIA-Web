import streamlit as st
import yfinance as yf
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
        return {"status": "ok", "info": info}
    except Exception as e:
        return {"status": "error"}

def modulo_1_pe_ratio():
    resultado = obtener_datos_modulo("NVDA")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        pe_ratio = info.get("trailingPE")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        pe_limpio = str(pe_ratio) if pe_ratio is not None else "No disponible"
        
        if pe_ratio is not None and pe_ratio > 100:
            en_alerta = True
        elif pe_ratio is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {
            "id": "M01", "nombre": "Múltiplos de Valoración (P/E Ratio)", "ticker": "NVDA",
            "explicacion": "Mide cuánto pagan los inversores por cada dólar de ganancia. Un valor muy alto sugiere que la acción está cara.",
            "precio_cierre": precio_limpio, "metrica_valor": pe_limpio, "en_alerta": en_alerta
        }
    return {"id": "M01", "nombre": "Múltiplos de Valoración (P/E Ratio)", "ticker": "NVDA", "explicacion": "Mide cuánto pagan los inversores por cada dólar de ganancia. Un valor muy alto sugiere que la acción está cara.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_2_crecimiento_ingresos():
    resultado = obtener_datos_modulo("MSFT")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        crecimiento = info.get("revenueGrowth")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        crecimiento_limpio = str(crecimiento * 100) + "%" if crecimiento is not None else "No disponible"
        
        if crecimiento is not None and crecimiento < 0:
            en_alerta = True
        elif crecimiento is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M02", "nombre": "Crecimiento de Ingresos vs Expectativas", "ticker": "MSFT", "explicacion": "Evalúa si los ingresos crecen al ritmo esperado. Una caída indica desaceleración del negocio.", "precio_cierre": precio_limpio, "metrica_valor": crecimiento_limpio, "en_alerta": en_alerta}
    return {"id": "M02", "nombre": "Crecimiento de Ingresos vs Expectativas", "ticker": "MSFT", "explicacion": "Evalúa si los ingresos crecen al ritmo esperado. Una caída indica desaceleración del negocio.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_3_capex_bigtech():
    resultado = obtener_datos_modulo("GOOGL")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        capex = info.get("capitalExpenditures")
        ingresos = info.get("totalRevenue")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        
        if capex is not None and ingresos is not None and ingresos != 0:
            ratio = abs(capex) / ingresos
            ratio_limpio = str(ratio * 100) + "%"
            en_alerta = ratio > 0.2
        else:
            ratio_limpio = "No disponible"
            en_alerta = True
            
        return {"id": "M03", "nombre": "Inversión en CapEx de Big Tech", "ticker": "GOOGL", "explicacion": "Analiza la inversión en infraestructura respecto a sus ingresos. Un ratio alto puede afectar la rentabilidad.", "precio_cierre": precio_limpio, "metrica_valor": ratio_limpio, "en_alerta": en_alerta}
    return {"id": "M03", "nombre": "Inversión en CapEx de Big Tech", "ticker": "GOOGL", "explicacion": "Analiza la inversión en infraestructura respecto a sus ingresos. Un ratio alto puede afectar la rentabilidad.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_4_concentracion_mercado():
    resultado = obtener_datos_modulo("AAPL")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        institucionales = info.get("heldPercentInstitutions")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        inst_limpio = str(institucionales * 100) + "%" if institucionales is not None else "No disponible"
        
        if institucionales is not None and institucionales > 0.8:
            en_alerta = True
        elif institucionales is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M04", "nombre": "Concentración de Mercado (Top 5)", "ticker": "AAPL", "explicacion": "Mide el porcentaje de acciones en manos de grandes fondos. Si es muy alto, una venta masiva causaría un colapso.", "precio_cierre": precio_limpio, "metrica_valor": inst_limpio, "en_alerta": en_alerta}
    return {"id": "M04", "nombre": "Concentración de Mercado (Top 5)", "ticker": "AAPL", "explicacion": "Mide el porcentaje de acciones en manos de grandes fondos. Si es muy alto, una venta masiva causaría un colapso.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_5_margen_beneficio():
    resultado = obtener_datos_modulo("AMZN")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        margen = info.get("operatingMargins")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        margen_limpio = str(margen * 100) + "%" if margen is not None else "No disponible"
        
        if margen is not None and margen < 0.1:
            en_alerta = True
        elif margen is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M05", "nombre": "Margen de Beneficio Operativo", "ticker": "AMZN", "explicacion": "Mide la eficiencia operativa. Un margen bajo indica que los costos se están comiendo las ganancias.", "precio_cierre": precio_limpio, "metrica_valor": margen_limpio, "en_alerta": en_alerta}
    return {"id": "M05", "nombre": "Margen de Beneficio Operativo", "ticker": "AMZN", "explicacion": "Mide la eficiencia operativa. Un margen bajo indica que los costos se están comiendo las ganancias.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_6_endeudamiento():
    resultado = obtener_datos_modulo("META")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        deuda_equity = info.get("debtToEquity")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        deuda_limpio = str(deuda_equity) if deuda_equity is not None else "No disponible"
        
        if deuda_equity is not None and deuda_equity > 2:
            en_alerta = True
        elif deuda_equity is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M06", "nombre": "Nivel de Endeudamiento Neto", "ticker": "META", "explicacion": "Compara la deuda total con el patrimonio. Un nivel alto significa que la empresa tiene un riesgo financiero peligroso.", "precio_cierre": precio_limpio, "metrica_valor": deuda_limpio, "en_alerta": en_alerta}
    return {"id": "M06", "nombre": "Nivel de Endeudamiento Neto", "ticker": "META", "explicacion": "Compara la deuda total con el patrimonio. Un nivel alto significa que la empresa tiene un riesgo financiero peligroso.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_7_volatilidad():
    resultado = obtener_datos_modulo("AMD")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        beta = info.get("beta")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        beta_limpio = str(beta) if beta is not None else "No disponible"
        
        if beta is not None and beta > 1.5:
            en_alerta = True
        elif beta is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M07", "nombre": "Volatilidad del Sector (Implied Vol)", "ticker": "AMD", "explicacion": "El Beta indica cuánto más oscila la acción respecto al mercado. Un valor alto implica riesgo extremo en caídas.", "precio_cierre": precio_limpio, "metrica_valor": beta_limpio, "en_alerta": en_alerta}
    return {"id": "M07", "nombre": "Volatilidad del Sector (Implied Vol)", "ticker": "AMD", "explicacion": "El Beta indica cuánto más oscila la acción respecto al mercado. Un valor alto implica riesgo extremo en caídas.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_8_fcf_yield():
    resultado = obtener_datos_modulo("AVGO")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        fcf = info.get("freeCashflow")
        market_cap = info.get("marketCap")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        
        if fcf is not None and market_cap is not None and market_cap != 0:
            yield_fcf = fcf / market_cap
            yield_limpio = str(yield_fcf * 100) + "%"
            en_alerta = yield_fcf < 0.02
        else:
            yield_limpio = "No disponible"
            en_alerta = True
            
        return {"id": "M08", "nombre": "Flujo de Caja Libre (FCF Yield)", "ticker": "AVGO", "explicacion": "Mide el efectivo real que genera la empresa respecto a su valor de mercado. Si es bajo, la acción está sobrevalorada.", "precio_cierre": precio_limpio, "metrica_valor": yield_limpio, "en_alerta": en_alerta}
    return {"id": "M08", "nombre": "Flujo de Caja Libre (FCF Yield)", "ticker": "AVGO", "explicacion": "Mide el efectivo real que genera la empresa respecto a su valor de mercado. Si es bajo, la acción está sobrevalorada.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_9_insiders_selling():
    resultado = obtener_datos_modulo("SMCI")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        insiders = info.get("heldPercentInsiders")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        insiders_limpio = str(insiders * 100) + "%" if insiders is not None else "No disponible"
        
        if insiders is not None and insiders < 0.01:
            en_alerta = True
        elif insiders is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M09", "nombre": "Insiders Selling (Venta de Directivos)", "ticker": "SMCI", "explicacion": "Mide si los directivos tienen acciones de su propia empresa. Si no tienen, puede ser porque saben que la acción va a caer.", "precio_cierre": precio_limpio, "metrica_valor": insiders_limpio, "en_alerta": en_alerta}
    return {"id": "M09", "nombre": "Insiders Selling (Venta de Directivos)", "ticker": "SMCI", "explicacion": "Mide si los directivos tienen acciones de su propia empresa. Si no tienen, puede ser porque saben que la acción va a caer.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_10_rd_gasto():
    resultado = obtener_datos_modulo("PLTR")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        rd = info.get("researchAndDevelopment")
        ingresos = info.get("totalRevenue")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        
        if rd is not None and ingresos is not None and ingresos != 0:
            ratio_rd = rd / ingresos
            rd_limpio = str(ratio_rd * 100) + "%"
            en_alerta = ratio_rd < 0.1
        else:
            rd_limpio = "No disponible"
            en_alerta = True
            
        return {"id": "M10", "nombre": "Gasto en I+D (R&D % Ingresos)", "ticker": "PLTR", "explicacion": "Evalúa si la empresa invierte lo suficiente en innovación. En IA, un gasto bajo significa que quedarán atrás frente a la competencia.", "precio_cierre": precio_limpio, "metrica_valor": rd_limpio, "en_alerta": en_alerta}
    return {"id": "M10", "nombre": "Gasto en I+D (R&D % Ingresos)", "ticker": "PLTR", "explicacion": "Evalúa si la empresa invierte lo suficiente en innovación. En IA, un gasto bajo significa que quedarán atrás frente a la competencia.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_11_primas_riesgo():
    resultado = obtener_datos_modulo("ASML")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        vol_impl = info.get("impliedVolatility")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        vol_limpio = str(vol_impl * 100) + "%" if vol_impl is not None else "No disponible"
        
        if vol_impl is not None and vol_impl > 0.4:
            en_alerta = True
        elif vol_impl is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M11", "nombre": "Primas de Riesgo en Opciones", "ticker": "ASML", "explicacion": "Mide el miedo o incertidumbre en el mercado a través de las opciones. Una volatilidad implícita alta presagia grandes caídas.", "precio_cierre": precio_limpio, "metrica_valor": vol_limpio, "en_alerta": en_alerta}
    return {"id": "M11", "nombre": "Primas de Riesgo en Opciones", "ticker": "ASML", "explicacion": "Mide el miedo o incertidumbre en el mercado a través de las opciones. Una volatilidad implícita alta presagia grandes caídas.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_12_apalancamiento():
    resultado = obtener_datos_modulo("TSM")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        activos = info.get("totalAssets")
        patrimonio = info.get("totalEquity")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        
        if activos is not None and patrimonio is not None and patrimonio != 0:
            apalancamiento = activos / patrimonio
            apal_limpio = str(apalancamiento) + "x"
            en_alerta = apalancamiento > 3
        else:
            apal_limpio = "No disponible"
            en_alerta = True
            
        return {"id": "M12", "nombre": "Multiplicador de Apalancamiento", "ticker": "TSM", "explicacion": "Indica cuántos dólares de activos se tienen por cada dólar de capital propio. Si es muy alto, cualquier pérdida se multiplica exponencialmente.", "precio_cierre": precio_limpio, "metrica_valor": apal_limpio, "en_alerta": en_alerta}
    return {"id": "M12", "nombre": "Multiplicador de Apalancamiento", "ticker": "TSM", "explicacion": "Indica cuántos dólares de activos se tienen por cada dólar de capital propio. Si es muy alto, cualquier pérdida se multiplica exponencialmente.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def modulo_13_sentimiento():
    resultado = obtener_datos_modulo("QCOM")
    if resultado["status"] == "ok":
        info = resultado["info"]
        precio = info.get("currentPrice") or info.get("previousClose")
        recomendacion = info.get("recommendationKey")
        
        precio_limpio = str(precio) if precio is not None else "No disponible"
        rec_limpio = str(recomendacion) if recomendacion is not None else "No disponible"
        
        if recomendacion is not None and recomendacion in ["sell", "reduce"]:
            en_alerta = True
        elif recomendacion is None:
            en_alerta = True
        else:
            en_alerta = False
            
        return {"id": "M13", "nombre": "Sentimiento del Mercado", "ticker": "QCOM", "explicacion": "Resume lo que opinan los analistas de Wall Street. Si la recomendación es vender, es una señal de alarma clara sobre la empresa.", "precio_cierre": precio_limpio, "metrica_valor": rec_limpio, "en_alerta": en_alerta}
    return {"id": "M13", "nombre": "Sentimiento del Mercado", "ticker": "QCOM", "explicacion": "Resume lo que opinan los analistas de Wall Street. Si la recomendación es vender, es una señal de alarma clara sobre la empresa.", "precio_cierre": "No disponible", "metrica_valor": "No disponible", "en_alerta": True}

def crear_grafico_riesgo(historial):
    fig = go.Figure()
    
    fig.add_shape(type="rect", x0=-0.5, y0=0, x1=3.5, y1=13.5, fillcolor="rgba(0, 255, 136, 0.05)", line_width=0)
    fig.add_shape(type="rect", x0=3.5, y0=0, x1=7.5, y1=13.5, fillcolor="rgba(255, 221, 0, 0.05)", line_width=0)
    fig.add_shape(type="rect", x0=7.5, y0=0, x1=13.5, y1=13.5, fillcolor="rgba(255, 0, 68, 0.05)", line_width=0)
    
    if len(historial) > 0:
        horas = [p["hora"] for p in historial]
        scores = [p["score"] for p in historial]
        
        fig.add_trace(go.Scatter(
            x=horas,
            y=scores,
            mode='lines+markers',
            line=dict(color='#00ff88', width=3),
            marker=dict(color='#00ff88', size=10, line=dict(color='white', width=2)),
            name='Evolución del Riesgo'
        ))
        
        fig.update_xaxes(type='category', tickangle=45)
    else:
        fig.add_trace(go.Scatter(x=["Esperando datos..."], y=[0], mode='markers', marker=dict(color='gray', size=10)))
        fig.update_xaxes(type='category')
        
    fig.add_annotation(x=1.5, y=12.5, text="ZONA VERDE\n(Riesgo Bajo)", showarrow=False, font=dict(color="rgba(0, 255, 136, 0.5)", size=12))
    fig.add_annotation(x=5.5, y=12.5, text="ZONA AMARILLA\n(Riesgo Moderado)", showarrow=False, font=dict(color="rgba(255, 221, 0, 0.5)", size=12))
    fig.add_annotation(x=10.5, y=12.5, text="ZONA ROJA\n(Riesgo Crítico)", showarrow=False, font=dict(color="rgba(255, 0, 68, 0.5)", size=12))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title=dict(text='Historial de Nivel de Riesgo del Sector IA', font=dict(size=18, color='white'), x=0.5, xanchor='center'),
        yaxis=dict(title='Número de Alertas', range=[0, 13], gridcolor='rgba(255,255,255,0.1)', tick0=0, dtick=1),
        margin=dict(l=50, r=50, t=60, b=80),
        height=400,
        showlegend=False
    )
    
    return fig

def generar_conclusion(alertas):
    if alertas == 0:
        return "El sector de la Inteligencia Artificial presenta **fundamentales sólidos y estables** en este momento. Todos los indicadores analizados se encuentran dentro de rangos saludables, lo que sugiere que las valoraciones están justificadas por el crecimiento real de los negocios. No se detectan señales de burbuja inminente."
    elif alertas <= 3:
        return f"El sector de la IA muestra **algunos puntos de atención** con {alertas} indicadores en zona de alerta. Aunque la mayoría de los fundamentales se mantienen sólidos, se recomienda monitorear de cerca estos aspectos. No hay señales claras de burbuja, pero existe cierta tensión en el mercado."
    elif alertas <= 7:
        return f"**PRECAUCIÓN:** El sector presenta {alertas} indicadores en alerta, lo que sugiere un **incremento significativo en el nivel de riesgo**. Varios fundamentales clave muestran señales de estrés. Se recomienda extremar la cautela y considerar reducir la exposición a los activos más afectados."
    else:
        return f"**ALERTA ROJA:** Con {alertas} indicadores en alerta, los datos sugieren un **sobrecalentamiento severo en el sector de la IA**. Existe un **riesgo muy elevado de corrección significativa o estallido de burbuja**. Se recomienda encarecidamente reducir la exposición al sector y considerar estrategias de protección de capital."

def main():
    if 'historial_scores' not in st.session_state:
        st.session_state.historial_scores = []

    modulos = [
        modulo_1_pe_ratio, modulo_2_crecimiento_ingresos, modulo_3_capex_bigtech,
        modulo_4_concentracion_mercado, modulo_5_margen_beneficio, modulo_6_endeudamiento,
        modulo_7_volatilidad, modulo_8_fcf_yield, modulo_9_insiders_selling,
        modulo_10_rd_gasto, modulo_11_primas_riesgo, modulo_12_apalancamiento,
        modulo_13_sentimiento
    ]
    
    resultados = [modulo() for modulo in modulos]
    
    alertas = sum(1 for resultado in resultados if resultado["en_alerta"] == True)
    
    ahora = datetime.now().strftime('%H:%M:%S')
    st.session_state.historial_scores.append({"hora": ahora, "score": alertas})
    
    if len(st.session_state.historial_scores) > 20:
        st.session_state.historial_scores = st.session_state.historial_scores[-20:]
    
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
            Última actualización: {ahora} | Módulos en alerta: {alertas}/13
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(crear_grafico_riesgo(st.session_state.historial_scores), use_container_width=True)
    
    for resultado in resultados:
        with st.expander(f"{resultado['id']} - {resultado['nombre']} ({resultado['ticker']})"):
            
            estado_texto = "✅ Normal" if not resultado["en_alerta"] else "🚨 Alerta Activada"
            
            precio_str = f"${resultado['precio_cierre']}" if resultado['precio_cierre'] != "No disponible" else "No disponible"
            
            st.markdown(f"""**Métrica analizada:** {resultado['explicacion']}

**Último Precio de Cierre:** {precio_str}

**Resultado de Wall Street ({resultado['nombre']}):** {resultado['metrica_valor']}

**Estado de Alerta:** {estado_texto}
""")
    
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
    
    st.markdown('<div class="refresh-button">', unsafe_allow_html=True)
    
    if st.button("🔄 Actualizar Datos en Tiempo Real"):
        st.rerun()
    
    st.markdown("""
    </div>
    <div class="footer">
        <p>RadarIA v2.0 | Desarrollado para monitorizar el riesgo de la burbuja de IA | Datos proporcionados por Yahoo Finance</p>
        <p>© 2023 RadarIA. Todos los derechos reservados.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
