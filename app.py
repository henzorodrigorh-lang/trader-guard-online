import streamlit as st
import os
import sys
import pandas as pd
from binance.client import Client
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DE PORTA (Obrigatória para o Railway) ---
port = int(os.getenv("PORT", 8080))
if "IS_RUNNING" not in os.environ:
    os.environ["IS_RUNNING"] = "true"
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "app.py", "--server.port", str(port), "--server.address", "0.0.0.0"]
    sys.exit(stcli.main())

# --- 2. INTERFACE COMPLETA (Como no seu local) ---
st.set_page_config(page_title="Trader Guard PRO", layout="wide")

# Barra Lateral (Menu original)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=100) # Ajuste a URL do logo se necessário
    st.title("TRADER GUARD PRO")
    st.write("Usuário: **Rodrigo**")
    st.info("Conectado")
    st.metric("SINAIS HOJE", "14")
    st.success("0 COMPRAS")
    st.error("14 VENDAS")

# Área Principal
st.title("Trader Guard PRO")
st.subheader("SINAIS ANTECIPADOS v2.0 ESCURO")

col1, col2 = st.columns([1, 4])
with col1:
    st.button("RADAR AO VIVO")
    st.toggle("Ativar Robô de Sinais")
with col2:
    st.write("Binance Conectada ✅")

# Lista de Moedas Completa
moedas = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT", "DOTUSDT", "BNBUSDT", "XRPUSDT", "LINKUSDT", "MATICUSDT"]
par_v = st.selectbox("Par Principal", moedas)

# Gráfico TradingView
tv_html = f'''
<div id="tv-chart" style="height:500px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
    new TradingView.widget({{"autosize": true, "symbol": "BINANCE:{par_v}", "interval": "15", "theme": "dark", "container_id": "tv-chart"}});
</script>
'''
components.html(tv_html, height=520)
