import requests
import pandas as pd
from datetime import datetime
import os
import time

def fetch_with_retry(url, retries=3, delay=3):
    """API 호출 제한을 우회하기 위한 지수 백오프 및 재시도 함수"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    for i in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429: # Rate Limit Error
                time.sleep(delay * (i + 2))
            else:
                time.sleep(delay)
        except Exception:
            time.sleep(delay)
    return None

def get_hype_data():
    hype_price, hype_vol_b = 0, 0
    
    # 1. HYPE Price (Hyperliquid L1 API)
    try:
        url_info = "https://api.hyperliquid.xyz/info"
        payload = {"type": "metaAndAssetCtxs"}
        resp_info = requests.post(url_info, json=payload, headers={'Content-Type': 'application/json'}).json()
        for i, asset in enumerate(resp_info[0]['universe']):
            if asset['name'] == 'HYPE':
                hype_price = round(float(resp_info[1][i]['markPx']), 2)
                break
    except Exception as e:
        print(f"HYPE Price Error: {e}")

    # 2. HYPE Volume (CoinGecko API)
    try:
        cg_resp = fetch_with_retry("https://api.coingecko.com/api/v3/derivatives/exchanges/hyperliquid")
        btc_data = fetch_with_retry("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        
        if cg_resp and btc_data:
            vol_btc = float(cg_resp.get('trade_volume_24h_btc', 0))
            btc_price = btc_data['bitcoin']['usd']
            hype_vol_b = round((vol_btc * btc_price) / 1e9, 2)
    except Exception as e:
        print(f"HYPE Vol Error: {e}")
        
    return hype_vol_b, hype_price

def get_competitor_data():
    bin_vol, coin_vol, upbit_vol = 0, 0, 0
    
    # 공통 BTC 가격 선 조회
    btc_data = fetch_with_retry("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    if not btc_data:
        print("Competitor Error: Failed to fetch BTC price.")
        return 0, 0, 0
    btc_price = btc_data['bitcoin']['usd']

    # 각각 개별 블록으로 분리하여 하나가 실패해도 나머지는 보존
    bin_data = fetch_with_retry("https://api.coingecko.com/api/v3/exchanges/binance")
    if bin_data: 
        bin_vol = round(float(bin_data.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
        
    coin_data = fetch_with_retry("https://api.coingecko.com/api/v3/exchanges/gdax")
    if coin_data: 
        coin_vol = round(float(coin_data.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
        
    upbit_data = fetch_with_retry("https://api.coingecko.com/api/v3/exchanges/upbit")
    if upbit_data: 
        upbit_vol = round(float(upbit_data.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
        
    return bin_vol, coin_vol, upbit_vol

def main():
    file_name = 'data.csv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
    else:
        df = pd.DataFrame(columns=['Date', 'HYPE_Vol_B', 'HYPE_Price', 'Binance_Vol_B', 'Coinbase_Vol_B', 'Upbit_Vol_B'])
    
# 오늘 날짜의 데이터가 이미 존재할 경우, 해당 행을 삭제하여 덮어쓰기 준비
    if today in df['Date'].values:
        df = df[df['Date'] != today]
        print(f"Existing data for {today} removed. Will be overwritten with latest data.")

    hype_vol, hype_price = get_hype_data() 
    bin_vol, coin_vol, upbit_vol = get_competitor_data()
    
    print(f"Collected: {today} | HYPE: ${hype_price}({hype_vol}B) | Bin: {bin_vol}B | Coin: {coin_vol}B | Up: {upbit_vol}B")
    
    new_row = {
        'Date': today,
        'HYPE_Vol_B': hype_vol,
        'HYPE_Price': hype_price,
        'Binance_Vol_B': bin_vol,
        'Coinbase_Vol_B': coin_vol,
        'Upbit_Vol_B': upbit_vol
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(file_name, index=False)
    print("CSV Saved successfully.")

if __name__ == "__main__":
    main()
