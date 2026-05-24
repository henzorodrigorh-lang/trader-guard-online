import streamlit as st
import os
import sys
import pandas as pd
from binance.client import Client
import requests

# 1. Configuração de Porta para o Railway (ESSENCIAL)
port = int(os.getenv("PORT", 8080))

# 2. Se for a execução principal, rodar o Streamlit
if __name__ == "__main__":
    if "IS_RUNNING" not in os.environ:
        os.environ["IS_RUNNING"] = "true"
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", "app.py", "--server.port", str(port), "--server.address", "0.0.0.0"]
        sys.exit(stcli.main())

# 3. Restante do seu código (Apenas após o Streamlit ter iniciado)
st.set_page_config(page_title="Trader Guard PRO", layout="wide")

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
client = Client(api_key, api_secret) if api_key and api_secret else None

st.title("📊 Trader Guard - Online")

if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    if st.sidebar.button("Entrar como Admin"): st.session_state['logado'] = True
else:
    robo_ligado = st.sidebar.toggle("Ligar Robô")
    if robo_ligado:
        st.success("Robô Ativo")
        st.write("Monitorando mercado...")
    else:
        st.warning("Robô Desligado")
