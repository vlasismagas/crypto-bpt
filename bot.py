import requests
import time
from collections import deque

NEWS_API_KEY = "4d344f55049c4ad982ef3497ef5b4326"
TELEGRAM_TOKEN = "8603161941:AAG-6q6zrPAxVVbccAOByTAZWowdu_gSdvQ"
TELEGRAM_CHAT_ID = "5942217222"

balance_usd = 10000.0
balance_btc = 0.0
prices = deque(maxlen=20)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def get_bitcoin_price():
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    response = requests.get(url)
    return float(response.json()["data"]["amount"])

def get_signal(price):
    prices.append(price)
    if len(prices) < 20:
        return "HOLD"
    
    avg = sum(prices) / len(prices)
    change = (price - prices[0]) / prices[0] * 100
    
    if price > avg and change > 0.3:
        return "BUY"
    elif price < avg and change < -0.3:
        return "SELL"
    else:
        return "HOLD"

send_telegram("🤖 Bot ξεκίνησε!")

counter = 0
while True:
    try:
        price = get_bitcoin_price()
        signal = get_signal(price)
        
        if signal == "BUY" and balance_usd > 0:
            balance_btc = balance_usd / price
            balance_usd = 0
            msg = f"✅ ΑΓΟΡΑ!\n{balance_btc:.6f} BTC @ ${price:,.2f}"
            print(msg)
            send_telegram(msg)
        
        elif signal == "SELL" and balance_btc > 0:
            balance_usd = balance_btc * price
            balance_btc = 0
            msg = f"💰 ΠΩΛΗΣΗ!\n${balance_usd:,.2f} @ ${price:,.2f}"
            print(msg)
            send_telegram(msg)
        
        else:
            total = balance_usd + (balance_btc * price)
            print(f"⏸️ {signal} | BTC: ${price:,.2f} | Αξία: ${total:,.2f}")
        
        counter += 1
        if counter >= 100:
            total = balance_usd + (balance_btc * price)
            send_telegram(f"📊 Update\nBTC: ${price:,.2f}\nΑξία: ${total:,.2f}")
            counter = 0
        
        time.sleep(3)
    
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)