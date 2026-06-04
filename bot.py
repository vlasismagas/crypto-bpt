import requests
import time

NEWS_API_KEY = "4d344f55049c4ad982ef3497ef5b4326"
TELEGRAM_TOKEN = "8603161941:AAG-6q6zrPAxVVbccAOByTAZWowdu_gSdvQ"
TELEGRAM_CHAT_ID = "5942217222"

balance_usd = 10000.0
balance_btc = 0.0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

send_telegram("🤖 Bot ξεκίνησε!")

def get_bitcoin_price():
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    response = requests.get(url)
    data = response.json()
    return float(data["data"]["amount"])

def get_news_sentiment():
    url = f"https://newsapi.org/v2/everything?q=bitcoin&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    articles = requests.get(url).json().get("articles", [])
    positive = ["surge", "bull", "rise", "gain", "rally"]
    negative = ["crash", "bear", "drop", "fall", "decline"]
    score = 0
    for article in articles:
        title = article["title"].lower()
        for w in positive:
            if w in title: score += 1
        for w in negative:
            if w in title: score -= 1
    if score > 0: return "BUY"
    elif score < 0: return "SELL"
    else: return "HOLD"

counter = 0
while True:
    price = get_bitcoin_price()
    signal = get_news_sentiment()
    
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
        print(f"⏸️ HOLD | BTC: ${price:,.2f} | Αξία: ${total:,.2f}")
    
    counter += 1
    if counter >= 60:
        total = balance_usd + (balance_btc * price)
        send_telegram(f"📊 Update\nBTC: ${price:,.2f}\nΑξία: ${total:,.2f}")
        counter = 0
    
    time.sleep(3)