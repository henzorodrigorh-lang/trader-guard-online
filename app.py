# ================= IMPORTS =================
import streamlit as st
from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import hashlib
import os # Importante para ler as variáveis do Railway
import time
import streamlit.components.v1 as components

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(page_title="Trader Guard PRO", layout="wide")

# ================= API & TELEGRAM (LENDO DO RAILWAY) =================
# Agora o robô busca as chaves que você configurou no painel "Variables" do Railway
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

try:
    client = Client(api_key, api_secret)
except:
    client = None

def enviar_telegram(mensagem):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

# ================= ESTADO DA SESSÃO & LOGIN =================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"admin": hash_senha("admin")} 
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'sinais_enviados' not in st.session_state:
    st.session_state['sinais_enviados'] = [] 

def autenticar(usuario, senha):
    return st.session_state['usuarios_db'].get(usuario) == hash_senha(senha)

# ================= FUNÇÕES TÉCNICAS =================
def ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

def atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift())
    low_close = abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def get_candles(symbol, interval, limit=205):
    if not client: return None
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=["open_time","open","high","low","close","volume","close_time","qav","trades","tb_base","tb_quote","ignore"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df
    except:
        return None

def check_tendencia_4h(symbol):
    df_4h = get_candles(symbol, "4h", limit=201)
    if df_4h is not None:
        ma_4h = ema(df_4h["close"]).iloc[-1]
        preco_4h = df_4h["close"].iloc[-1]
        return "ALTA" if preco_4h > ma_4h else "BAIXA"
    return "INDEFINIDA"

def checklist(df, symbol):
    df["EMA200"] = ema(df["close"])
    df["ATR"] = atr(df)
    ultimo = df.iloc[-1] 
    
    topo = df["high"].iloc[-11:-2].max()
    fundo = df["low"].iloc[-11:-2].min()

    if df["ATR"].iloc[-1] < df["ATR"].mean() * 0.5: return None

    if ultimo["close"] > ultimo["EMA200"] and ultimo["low"] <= ultimo["EMA200"]:
        return {"par": symbol, "direcao": "COMPRA", "prob": 96, "risco": "MUITO BAIXO", "msg": "Pullback na EMA200"}
    if ultimo["close"] < ultimo["EMA200"] and ultimo["high"] >= ultimo["EMA200"]:
        return {"par": symbol, "direcao": "VENDA", "prob": 96, "risco": "MUITO BAIXO", "msg": "Pullback na EMA200"}

    if ultimo["low"] < fundo and ultimo["close"] > fundo:
        return {"par": symbol, "direcao": "COMPRA", "prob": 95, "risco": "BAIXO", "msg": "Armadilha de Fundo"}
    if ultimo["high"] > topo and ultimo["close"] < topo:
        return {"par": symbol, "direcao": "VENDA", "prob": 95, "risco": "BAIXO", "msg": "Armadilha de Topo"}

    return None

# ================= INTERFACE PRINCIPAL =================
st.title("📊 Trader Guard - Sinais Antecipados")

if not st.session_state['logado']:
    menu = st.sidebar.selectbox("Menu", ["Fazer Login"])
    if menu == "Fazer Login":
        with st.sidebar.form(key="login_f"):
            u_input = st.text_input("Usuário")
            p_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if autenticar(u_input, p_input):
                    st.session_state['logado'] = True
                    st.rerun()
else:
    col_monitor, col_grafico = st.columns([1, 3])
    with col_monitor:
        robo_ligado = st.toggle("🤖 Ligar Robô")
        placeholder_alertas = st.container()

    with col_grafico:
        par_v = st.selectbox("Par Principal", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        tv_html = f'<div id="tv-chart" style="height:600px;"></div><script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({{"autosize": true, "symbol": "BINANCE:{par_v}", "interval": "15", "theme": "dark", "container_id": "tv-chart"}});</script>'
        components.html(tv_html, height=620)

    if robo_ligado:
        pares = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        intervalos = ["15m"]
        for par in pares:
            tendencia_mestra = check_tendencia_4h(par)
            for tempo in intervalos:
                df = get_candles(par, tempo)
                if df is not None:
                    sinal = checklist(df, par)
                    if sinal:
                        if (sinal["direcao"] == "COMPRA" and tendencia_mestra == "BAIXA") or (sinal["direcao"] == "VENDA" and tendencia_mestra == "ALTA"):
                            continue
                        
                        id_sinal = f"{par}_{tempo}_{sinal['direcao']}_{datetime.now().minute // 15}"
                        if id_sinal not in st.session_state['sinais_enviados']:
                            st.session_state['sinais_enviados'].append(id_sinal)
                            emoji = "🟢" if sinal['direcao'] == "COMPRA" else "🔴"
                            enviar_telegram(f"🚀 *{emoji} {sinal['direcao']}* | {par}")
                            with placeholder_alertas:
                                st.markdown(f"**{par}**: {emoji}")
        time.sleep(15)
        st.rerun()
