
import ccxt
import pandas as pd
import ta
import time
import requests
import os

# ====== CONFIG ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "x")
CHAT_ID = os.getenv("CHAT_ID", "891612789")
SYMBOL = 'ETH/USDT'
TIMEFRAME = '5m'
LIMIT = 200
SLEEP_SECONDS = 5 * 60
# =====================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Eroare la trimitere Telegram:", e)

def get_eth_data():
    exchange = ccxt.gateio()
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    stoch = ta.momentum.StochRSIIndicator(df['close'])
    df['stoch_k'] = stoch.stochrsi_k()
    df['stoch_d'] = stoch.stochrsi_d()

    sar = ta.trend.PSARIndicator(df['high'], df['low'], df['close'])
    df['sar'] = sar.psar()

    return df

def generate_signal(row):
    macd_buy = row['macd'] > row['macd_signal']
    stoch_buy = row['stoch_k'] < 20 and row['stoch_k'] > row['stoch_d']
    sar_buy = row['close'] > row['sar']

    macd_sell = row['macd'] < row['macd_signal']
    stoch_sell = row['stoch_k'] > 80 and row['stoch_k'] < row['stoch_d']
    sar_sell = row['close'] < row['sar']

    if macd_buy and stoch_buy and sar_buy:
        return 'BUY'
    elif macd_sell and stoch_sell and sar_sell:
        return 'SELL'
    else:
        return 'HOLD'

def main():
    print("📡 Bot de semnale ETH/USDT [5m] pornit...")
    ultima_actiune = ""
    while True:
        try:
            df = get_eth_data()
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            signal = generate_signal(last_row)

            timestamp = last_row['timestamp']
            price = last_row['close']

            if signal != ultima_actiune:
                mesaj = f"📊 ETH/USDT [5m]\nSemnal: {signal}\nPreț: {price:.2f}\nTimp: {timestamp}"
                print(mesaj)
                send_telegram_message(mesaj)
                ultima_actiune = signal
            else:
                print(f"[{timestamp}] Fără schimbare ({signal})")

        except Exception as e:
            print("Eroare:", e)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()
