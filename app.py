import streamlit as st
import asyncio
import pandas as pd
import pandas_ta as ta
from deriv_api import DerivAPI
import requests

# --- Configuration de la page ---
st.set_page_config(page_title="Deriv 6$ Micro-Bot", layout="wide")

# --- Fonctions Utilitaires ---
def send_telegram(message):
    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

async def get_data_and_trade():
    api = DerivAPI(app_id=st.secrets["APP_ID"])
    # Connexion avec le compte réel
    authorize = await api.authorize(st.secrets["DERIV_TOKEN"])
    
    st.success(f"Connecté au compte : {authorize['authorize']['loginid']}")
    
    # Paramètres de l'indice (V75)
    symbol = "R_75"
    
    # Conteneurs Streamlit pour affichage dynamique
    price_display = st.empty()
    rsi_display = st.empty()
    
    # On récupère les dernières bougies
    while True:
        try:
            # Récupération de l'historique pour le calcul du RSI
            candles = await api.candles({"ticks_history": symbol, "count": 50, "end": "latest", "style": "candles"})
            df = pd.DataFrame(candles['candles'])
            df['close'] = df['close'].astype(float)
            
            # Calcul du RSI avec pandas_ta
            df['RSI'] = ta.rsi(df['close'], length=14)
            current_rsi = df['RSI'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Affichage
            price_display.metric("Prix V75", f"{current_price:.2f}")
            rsi_display.metric("RSI (14)", f"{current_rsi:.2f}")
            
            # --- LOGIQUE DE SIGNAL (Pour tes 6$) ---
            # Achat si RSI < 25 (Survendu)
            if current_rsi < 25:
                msg = f"🟢 SIGNAL ACHAT V75\nRSI: {current_rsi:.2f}\nAction: Lancement de 5 micro-trades (Lot min)"
                send_telegram(msg)
                st.warning("Signal d'achat envoyé sur Telegram !")
                # Ici on pourrait ajouter la boucle pour passer les 5 ordres
                await asyncio.sleep(60) # Pause pour éviter de spammer le même signal

            # Vente si RSI > 75 (Sur-acheté)
            elif current_rsi > 75:
                msg = f"🔴 SIGNAL VENTE V75\nRSI: {current_rsi:.2f}\nAction: Lancement de 5 micro-trades (Lot min)"
                send_telegram(msg)
                st.warning("Signal de vente envoyé sur Telegram !")
                await asyncio.sleep(60)

        except Exception as e:
            st.error(f"Erreur de flux : {e}")
            break
            
        await asyncio.sleep(2) # Rafraîchissement toutes les 2 secondes

# --- Interface Utilisateur ---
st.sidebar.header("Paramètres")
target_indice = st.sidebar.selectbox("Choisir l'indice", ["R_75", "R_10", "1HZ10V"])

if st.button("Démarrer le Bot"):
    asyncio.run(get_data_and_trade())
