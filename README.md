# 🧠 AI Bubble Monitor - Dashboard Analítico Personalizado

Este es un cuadro de mando privado e independiente desarrollado en **Streamlit** y desplegado en **Streamlit Community Cloud**. El objetivo del proyecto es monitorizar la salud financiera del ecosistema de la Inteligencia Artificial (IA) y calcular un **Índice de Alerta de Burbuja (0 a 10 puntos)** basándose en lógicas macroeconómicas, microestructurales y de crédito cruzadas.

La aplicación es completamente autónoma y se alimenta de datos en tiempo real mediante fuentes 100% gratuitas (`yfinance` y la base de datos `FRED` de la Reserva Federal), garantizando inmunidad a bloqueos de API o costes de suscripción.

---

## 📊 Matriz de Lógica Analítica e Indicadores

El algoritmo evalúa el riesgo sistémico dividiendo el mercado en 5 bloques fundamentales, cada uno documentado internamente en el cuadro de mando:

### 1. Valoración de Semiconductores (Múltiplos Absolutos y Relativos)
*   **Filtro Absoluto (`NVDA`):** Evaluación del *Forward P/E* bajo umbrales estrictos de control: <25x (Barato), 25x-30x (Confort), 30x-35x (Caro), 35x-40x (Carísimo con riesgo de corrección), y >=40x (Locura/Burbuja absoluta).
*   **Filtro Relativo Continuo (`AMD`/`INTC`):** Monitorización del ratio de divergencia frente al líder. Detecta si el mercado compra "humo por narrativa" en segundas marcas en cualquier tramo del ciclo.

### 2. Ciclo Físico de Suministro (El Canario en la Mina)
*   **Termómetros (`MU` y `KOSPI`):** Rastreo de las Medias Móviles Exponenciales (`EMA_200`) en Micron y el índice de Corea del Sur para anticipar el fin de la escasez física de memoria HBM, la acumulación silenciosa de inventario y la devaluación destructiva de márgenes operativos antes de que se refleje en Wall Street.

### 3. Motor Corporativo y Foso de Software
*   **Eficiencia de Capital (Hiperscalers):** Monitoreo de la rentabilidad interna (`ROIC`/`ROA`) de `META`, `AMZN`, `GOOG` y `MSFT`. Si su rentabilidad media supera el **15%**, el CapEx es indestructible a medio plazo y el script reduce el riesgo del indicador.
*   **El Amortiguador CUDA:** El software y servicios recurrentes de `NVDA` estabilizan sus ingresos. Si el PER baja de 25x por pánico macro, el script identifica la zona como acumulación segura mitigando el riesgo.

### 4. Fontanería del Crédito Privado y Riesgo Bancario
*   **Transmisión de Insolvencias:** Rastreo de vehículos de deuda alternativa corporativa y Private Equity (`BX`, `APO`, `BIZD`, `HYG`) junto a la banca regional (`KRE`). Detecta grietas de liquidez causadas por el apalancamiento oculto que financia a startups de IA insolventes.

### 5. Euforia de Startups Privadas y Grifo de la FED
*   **Proxy de Startups (`SPCX`):** Compresión de múltiplos de SpaceX fijando un suelo racional de $80 frente al precio inflado de la IPO para medir la euforia de xAI, OpenAI o Anthropic.
*   **Liquidez Neta FED (FRED):** Extracción del balance neto del sistema (Balance - TGA - Reverse Repos). Evalúa el riesgo de estrangulamiento monetario o el escenario de rescate (socialización de pérdidas) tras una capitulación del 30% del inversor minorista (`IPO`).

---

## 🛠️ Instalación y Despliegue

Si deseas clonar este repositorio de forma local, asegúrate de tener Python instalado y ejecuta:

```bash
# Clonar el repositorio
git clone <URL_DE_TU_REPOSITORIO>

# Instalar dependencias necesarias
pip install -r requirements.txt

# Ejecutar la aplicación de Streamlit localmente
streamlit run app.py
```

## 🌐 Despliegue en la Nube
Este repositorio está estructurado para conectarse directamente a [Streamlit Community Cloud](https://streamlit.io). El despliegue leerá automáticamente el archivo `requirements.txt` e iniciará el archivo `app.py`.
# RadarIA-Web
