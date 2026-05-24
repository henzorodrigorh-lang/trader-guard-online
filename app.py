import streamlit as st
import os
import sys
import pandas as pd
from binance.client import Client
import streamlit.components.v1 as components
from datetime import datetime
import requests
import hashlib

# --- FORÇAR PORTA PARA O RAILWAY (MANTÉM O SITE NO AR) ---
port = int(os.getenv("PORT", 8080))
if "IS_RUNNING" not in os.environ:
    os.environ["IS_RUNNING"] = "true"
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "app.py", "--server.port", str(port), "--server.address", "0.0.0.0"]
    sys.exit(stcli.main())

# --- SEU CÓDIGO ORIGINAL COMPLETO ---
st.set_page_config(page_title="Trader Guard PRO", layout="wide")

# Configuração de API
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
client = Client(api_key, api_secret) if api_key and api_secret else None

if 'logado' not in st.session_state: st.session_state['logado'] = False

st.title("📊 Trader Guard - Sinais Antecipados")

if not st.session_state['logado']:
    if st.sidebar.button("Entrar como Admin"): st.session_state['logado'] = True
else:
    col_monitor, col_grafico = st.columns([1, 3])
    with col_monitor:
        robo_ligado = st.toggle("🤖 Ligar Robô")
        st.write("Status: " + ("Ativo" if robo_ligado else "Desligado"))

    with col_grafico:
        par_v = st.selectbox("Par Principal", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        tv_html = f'''
        <div id="tv-chart" style="height:500px;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
            new TradingView.widget({{"autosize": true, "symbol": "BINANCE:{par_v}", "interval": "15", "theme": "dark", "container_id": "tv-chart"}});
        </script>
        '''
        components.html(tv_html, height=520)

    if robo_ligado:
        st.success(f"Monitorando {par_v}...")
