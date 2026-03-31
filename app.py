import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Mi Portafolio de Dividendos", layout="wide")

# Archivo para guardar posiciones
DB_FILE = "portfolio.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# Inicializar datos
portfolio = load_data()

st.title("📈 Monitor de Portafolio - Jesús Brenel")

# --- Sidebar: Gestión de Posiciones ---
st.sidebar.header("Gestionar Posiciones")
ticker = st.sidebar.text_input("Ticker (ej: FMTY14.MX, ARA.MX)").upper()
shares = st.sidebar.number_input("Cantidad de títulos", min_value=0, step=1)
price_avg = st.sidebar.number_input("Precio promedio de compra", min_value=0.0)

if st.sidebar.button("Actualizar / Agregar"):
    portfolio[ticker] = {"shares": shares, "price_avg": price_avg}
    save_data(portfolio)
    st.sidebar.success(f"Actualizado: {ticker}")

if st.sidebar.button("Eliminar Ticker"):
    if ticker in portfolio:
        del portfolio[ticker]
        save_data(portfolio)
        st.sidebar.warning(f"Eliminado: {ticker}")

# --- Cuerpo Principal: Análisis ---
if portfolio:
    data_list = []
    total_invested = 0
    total_current_value = 0

    for t, info in portfolio.items():
        # Obtener precio actual de Yahoo Finance
        try:
            stock = yf.Ticker(t)
            # Pedimos el último mes para asegurar que haya datos, pero tomamos solo el último registro
            hist = stock.history(period="1mo")
        
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
            else:
                # Si sigue vacío, intentamos una última vez sin el sufijo o marcamos error
                st.error(f"No se encontraron datos para {t}. Revisa si tiene el formato TICKER.MX")
                current_price = info["price_avg"] # Usamos el precio de compra como respaldo
            
        except Exception as e:
            st.warning(f"Error al obtener {t}: {e}")
            current_price = info["price_avg"]
        
        invested = info["shares"] * info["price_avg"]
        current_value = info["shares"] * current_price
        profit_loss = current_value - invested
        
        total_invested += invested
        total_current_value += current_value
        
        data_list.append({
            "Ticker": t,
            "Títulos": info["shares"],
            "Costo Promedio": f"${info['price_avg']:.2f}",
            "Precio Actual": f"${current_price:.2f}",
            "Invertido": invested,
            "Valor Actual": current_value,
            "G/P (%)": f"{(profit_loss/invested*100 if invested > 0 else 0):.2f}%"
        })

    df = pd.DataFrame(data_list)
    
    # Métricas clave
    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Total", f"${total_invested:,.2f} MXN")
    col2.metric("Valor Actual", f"${total_current_value:,.2f} MXN", 
                delta=f"${(total_current_value - total_invested):,.2f}")
    col3.metric("Títulos Totales", sum(p["shares"] for p in portfolio.values()))

    st.dataframe(df, use_container_width=True)

    # Gráfico de pastel (Distribución)
    st.subheader("Distribución del Portafolio")

# Preparamos los datos para el gráfico
chart_data = []
for t, info in portfolio.items():
    current_price = yf.Ticker(t).history(period="1d")["Close"].iloc[-1]
    chart_data.append({
        "Ticker": t,
        "Valor": info["shares"] * current_price
    })

df_chart = pd.DataFrame(chart_data)

if not df_chart.empty:
    # Creamos el gráfico con Plotly
    fig = px.pie(
        df_chart, 
        values='Valor', 
        names='Ticker', 
        hole=0.4, # Lo hace tipo "dona" para que se vea más moderno
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Ajustes estéticos
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)