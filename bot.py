import requests
import time
import pandas as pd
import pandas_ta as ta
from collections import deque

NEWS_API_KEY = "4d344f55049c4ad982ef3497ef5b4326"
TELEGRAM_TOKEN = "8603161941:AAG-6q6zrPAxVVbccAOByTAZWowdu_gSdvQ"
TELEGRAM_CHAT_ID = "5942217222"

balance_usd = 1000.0
balance_btc = 0.0
buy_price = 0.0
prices = deque(maxlen=100)
volumes = deque(maxlen=100)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def get_bitcoin_data():
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    price = float(requests.get(url).json()["data"]["amount"])
    vol_url = "https://api.binance.us/api/v3/ticker/24hr?symbol=BTCUSDT"
    vol_data = requests.get(vol_url).json()
    volume = float(vol_data.get("volume", 0))
    return price, volume

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1")
        return int(r.json()["data"][0]["value"])
    except:
        return 50

def get_news_sentiment():
    try:
        url = f"https://newsapi.org/v2/everything?q=bitcoin&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        articles = requests.get(url).json().get("articles", [])
        positive = ["surge", "bull", "rise", "gain", "rally", "high", "up"]
        negative = ["crash", "bear", "drop", "fall", "decline", "low", "down"]
        score = 0
        for article in articles:
            title = article["title"].lower()
            for w in positive:
                if w in title: score += 1
            for w in negative:
                if w in title: score -= 1
        return score
    except:
        return 0

def get_signal():
    if len(prices) < 50:
        return "HOLD", {}
    
    df = pd.DataFrame({"close": list(prices), "volume": list(volumes)})
    
    # RSI
    df["rsi"] = ta.rsi(df["close"], length=14)
    rsi = df["rsi"].iloc[-1]
    
    # MACD
    macd = ta.macd(df["close"])
    macd_val = macd["MACD_12_26_9"].iloc[-1]
    macd_signal = macd["MACDs_12_26_9"].iloc[-1]
    
    # Moving Averages
    ma20 = df["close"].rolling(20).mean().iloc[-1]
    ma50 = df["close"].rolling(50).mean().iloc[-1]
    
    # Fear & Greed
    fg = get_fear_greed()
    
    # News
    news = get_news_sentiment()
    
    price = df["close"].iloc[-1]
    
    # Scoring
    score = 0
    if rsi < 35: score += 2
    elif rsi > 65: score -= 2
    if macd_val > macd_signal: score += 1
    else: score -= 1
    if price > ma20: score += 1
    if price > ma50: score += 1
    if fg < 30: score += 1
    elif fg > 70: score -= 1
    if news > 0: score += 1
    elif news < 0: score -= 1
    
    info = {
        "RSI": round(rsi, 1),
        "MACD": "↑" if macd_val > macd_signal else "↓",
        "MA": "↑" if price > ma50 else "↓",
        "F&G": fg,
        "News": news,
        "Score": score
    }
    
    if score >= 3:
        return "BUY", info
    elif score <= -2:
        return "SELL", info
    else:
        return "HOLD", info

send_telegram("🤖 Bot ξεκίνησε!\n💰 Πορτοφόλι: €1,000\n⏳ Συλλέγω δεδομένα...")

counter = 0
while True:
    try:
        price, volume = get_bitcoin_data()
        prices.append(price)
        volumes.append(volume)
        
        signal, info = get_signal()
        
        # Stop Loss / Take Profit
        if balance_btc > 0 and buy_price > 0:
            change_pct = (price - buy_price) / buy_price * 100
            if change_pct <= -2:
                balance_usd = balance_btc * price
                balance_btc = 0
                msg = f"🛑 STOP LOSS!\n@ ${price:,.2f}\nΖημιά: {change_pct:.2f}%\nΑξία: ${balance_usd:,.2f}"
                print(msg)
                send_telegram(msg)
                buy_price = 0
            elif change_pct >= 3:
                balance_usd = balance_btc * price
                balance_btc = 0
                msg = f"✅ TAKE PROFIT!\n@ ${price:,.2f}\nΚέρδος: {change_pct:.2f}%\nΑξία: ${balance_usd:,.2f}"
                print(msg)
                send_telegram(msg)
                buy_price = 0
        
        elif signal == "BUY" and balance_usd > 0:
            balance_btc = balance_usd / price
            buy_price = price
            balance_usd = 0
            msg = f"📈 ΑΓΟΡΑ!\n{balance_btc:.6f} BTC @ ${price:,.2f}\nRSI: {info['RSI']} | Score: {info['Score']}"
            print(msg)
            send_telegram(msg)
        
        elif signal == "SELL" and balance_btc > 0:
            balance_usd = balance_btc * price
            balance_btc = 0
            buy_price = 0
            msg = f"📉 ΠΩΛΗΣΗ!\n${balance_usd:,.2f} @ ${price:,.2f}\nRSI: {info['RSI']} | Score: {info['Score']}"
            print(msg)
            send_telegram(msg)
        
        else:
            total = balance_usd + (balance_btc * price)
            print(f"⏸️ {signal} | BTC: ${price:,.2f} | RSI: {info.get('RSI','...')} | Score: {info.get('Score','...')} | Αξία: ${total:,.2f}")
        
        counter += 1
        if counter >= 100:
            total = balance_usd + (balance_btc * price)
            fg = get_fear_greed()
            send_telegram(f"📊 Update\nBTC: ${price:,.2f}\nRSI: {info.get('RSI','...')}\nF&G: {fg}\nScore: {info.get('Score','...')}\nΑξία: ${total:,.2f}")
            counter = 0
        
        time.sleep(3)
    
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)