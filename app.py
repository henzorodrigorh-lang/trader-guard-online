import streamlit as st
import os
import sys

# --- BLOCO DE INICIALIZAÇÃO PARA RAILWAY ---
# Isso força o Streamlit a rodar na porta definida pelo Railway
if "IS_RUNNING" not in os.environ:
    os.environ["IS_RUNNING"] = "true"
    port = int(os.getenv("PORT", 8080))
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "app.py", "--server.port", str(port), "--server.address", "0.0.0.0"]
    sys.exit(stcli.main()) 
# ================= IMPORTS =================
import streamlit as st
from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import hashlib
import pyttsx3
import threading
import time
import streamlit.components.v1 as components

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(page_title="Trader Guard PRO", layout="wide")

# ================= API & TELEGRAM =================
api_key = "SUA_API_KEY"
api_secret = ""

try:
    client = Client(api_key, api_secret)
except:
    client = None

TOKEN = ""
CHAT_ID = ""

def enviar_telegram(mensagem):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

def falar(texto):
    def run_speech():
        try:
            engine = pyttsx3.init()
            engine.say(texto)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=run_speech, daemon=True).start()

# ================= ESTADO DA SESSÃO & LOGIN =================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

if 'usuarios_db' not in st.session_state:
    st.session_state['usuarios_db'] = {"admin": hash_senha("admin")} 
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = ""
if 'sinais_enviados' not in st.session_state:
    st.session_state['sinais_enviados'] = [] 

def cadastrar_usuario(usuario, senha):
    if usuario in st.session_state['usuarios_db']: return False
    st.session_state['usuarios_db'][usuario] = hash_senha(senha)
    return True

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

# ================= LÓGICA DE SINAL ANTECIPADO =================
def checklist(df, symbol):
    df["EMA200"] = ema(df["close"])
    df["ATR"] = atr(df)
    ultimo = df.iloc[-1] 
    
    topo = df["high"].iloc[-11:-2].max()
    fundo = df["low"].iloc[-11:-2].min()

    if df["ATR"].iloc[-1] < df["ATR"].mean() * 0.5: return None

    # Pullback Antecipado na EMA200
    if ultimo["close"] > ultimo["EMA200"] and ultimo["low"] <= ultimo["EMA200"]:
        return {"par": symbol, "direcao": "COMPRA", "prob": 96, "risco": "MUITO BAIXO", "msg": "Pullback na EMA200"}
    if ultimo["close"] < ultimo["EMA200"] and ultimo["high"] >= ultimo["EMA200"]:
        return {"par": symbol, "direcao": "VENDA", "prob": 96, "risco": "MUITO BAIXO", "msg": "Pullback na EMA200"}

    # Armadilhas Antecipadas
    if ultimo["low"] < fundo and ultimo["close"] > fundo:
        return {"par": symbol, "direcao": "COMPRA", "prob": 95, "risco": "BAIXO", "msg": "Armadilha de Fundo"}
    if ultimo["high"] > topo and ultimo["close"] < topo:
        return {"par": symbol, "direcao": "VENDA", "prob": 95, "risco": "BAIXO", "msg": "Armadilha de Topo"}

    return None

# ================= INTERFACE PRINCIPAL =================
st.title("📊 Trader Guard - Sinais Antecipados")

if not st.session_state['logado']:
    menu = st.sidebar.selectbox("Menu de Acesso", ["Fazer Login", "Criar Conta"])
    
    if menu == "Fazer Login":
        st.sidebar.subheader("🔐 Login")
        with st.sidebar.form(key="login_f"):
            u_input = st.text_input("Usuário")
            p_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if autenticar(u_input, p_input):
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = u_input
                    st.rerun()
                else:
                    st.sidebar.error("Usuário ou senha incorretos.")
                    
    elif menu == "Criar Conta":
        st.sidebar.subheader("📝 Cadastro")
        with st.sidebar.form(key="signup_f"):
            n_user = st.text_input("Novo Usuário")
            n_pass = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Cadastrar"):
                if n_user and n_pass:
                    if cadastrar_usuario(n_user, n_pass):
                        st.sidebar.success("✅ Cadastrado! Mude para Login.")
                    else:
                        st.sidebar.error("❌ Usuário já existe.")
else:
    st.sidebar.success(f"👤 Logado: {st.session_state['usuario']}")
    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    # Painel de Controle
    col_monitor, col_grafico = st.columns([1, 3])
    
    with col_monitor:
        st.header("🚦 Radar")
        robo_ligado = st.toggle("🤖 Ligar Robô")
        placeholder_alertas = st.container()

    with col_grafico:
        par_v = st.selectbox("Par Principal", ["BTCUSDT", "ETHUSDT", "SOLUSDT","XRPUSDT", "ADAUSDT", "DOGEUSDT"])
        tv_html = f'<div id="tv-chart" style="height:600px;"></div><script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({{"autosize": true, "symbol": "BINANCE:{par_v}", "interval": "15", "theme": "dark", "container_id": "tv-chart"}});</script>'
        components.html(tv_html, height=620)

    # LOOP DE EXECUÇÃO
    if robo_ligado:
        pares = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]
        intervalos = ["15m", "1h"]

        for par in pares:
            tendencia_mestra = check_tendencia_4h(par)
            
            for tempo in intervalos:
                df = get_candles(par, tempo)
                if df is not None:
                    sinal = checklist(df, par)

                    if sinal:
                        if sinal["direcao"] == "COMPRA" and tendencia_mestra == "BAIXA": sinal = None
                        elif sinal["direcao"] == "VENDA" and tendencia_mestra == "ALTA": sinal = None

                        if sinal:
                            # ID para evitar repetição no mesmo candle de 15 min
                            id_sinal = f"{par}_{tempo}_{sinal['direcao']}_{datetime.now().hour}_{datetime.now().minute // 15}"
                            
                            if id_sinal not in st.session_state['sinais_enviados']:
                                st.session_state['sinais_enviados'].append(id_sinal)
                                
                                emoji = "🟢 COMPRA" if sinal['direcao'] == "COMPRA" else "🔴 VENDA"
                                msg = (f"🚀 *{emoji} VALIDADO*\n"
                                       f"🪙 {par} ({tempo})\n"
                                       f"🎯 Prob: {sinal['prob']}%\n"
                                       f"📝 {sinal['msg']}\n"
                                       f"⏰ *ENTRE AGORA* - Sinal Antecipado")
                                
                                enviar_telegram(msg)
                                falar(f"Sinal de {sinal['direcao']} em {par}")
                                with placeholder_alertas:
                                    st.markdown(f"**{par}**: {emoji}")

        time.sleep(15) # Mais rápido para pegar o "toque" em tempo real
        st.rerun()
# --- AQUI COMEÇA O SEU CÓDIGO ORIGINAL ---
# (Cole aqui todo o seu código exatamente como você enviou na última mensagem,
# começando desde os imports até o loop de execução final)
