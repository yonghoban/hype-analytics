import requests
import pandas as pd
from datetime import datetime
import os
import time

def get_hype_data():
    try:
        # 1. HYPE 토큰 가격 가져오기 (Hyperliquid 공식 API)
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "metaAndAssetCtxs"}
        resp = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        
        hype_price = 0
        for i, asset in enumerate(resp[0]['universe']):
            if asset['name'] == 'HYPE':
                hype_price = round(float(resp[1][i]['markPx']), 2)
                break
        
        # 2. Hyperliquid 파생상품 거래소 전체 거래량 가져오기 (CoinGecko API)
        cg_url = "https://api.coingecko.com/api/v3/derivatives/exchanges/hyperliquid"
        cg_resp = requests.get(cg_url).json()
        vol_btc = float(cg_resp.get('trade_volume_24h_btc', 0))
        
        # 3. BTC -> USD 환산을 위한 비트코인 가격 조회
        btc_price_data = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()
        btc_price = btc_price_data['bitcoin']['usd']
        
        # 4. Billion($B) 단위로 환산
        hype_vol_b = round((vol_btc * btc_price) / 1e9, 2)
        
        return hype_vol_b, hype_price
    except Exception as e:
        print(f"HYPE Error: {e}")
        return 0, 0

def get_competitor_data():
    try:
        cg_url = "https://api.coingecko.com/api/v3/exchanges"
        
        # Binance
        bin_data = requests.get(f"{cg_url}/binance").json()
        binance_vol_btc = float(bin_data['trade_volume_24h_btc'])
        
        # Coinbase
        coin_data = requests.get(f"{cg_url}/gdax").json() # Coinbase Pro = gdax
        coinbase_vol_btc = float(coin_data['trade_volume_24h_btc'])
        
        # Upbit
        upbit_data = requests.get(f"{cg_url}/upbit").json()
        upbit_vol_btc = float(upbit_data['trade_volume_24h_btc'])
        
        # BTC Price for conversion
        btc_price_data = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()
        btc_price = btc_price_data['bitcoin']['usd']
        
        return (
            round(binance_vol_btc * btc_price / 1e9, 2), # Billions
            round(coinbase_vol_btc * btc_price / 1e9, 2),
            round(upbit_vol_btc * btc_price / 1e9, 2)
        )
    except Exception as e:
        print(f"Competitor Error: {e}")
        return 0, 0, 0

def main():
    # 파일명
    file_name = 'data.csv'
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. 기존 데이터 로드
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
    else:
        df = pd.DataFrame(columns=['Date', 'HYPE_Vol_B', 'HYPE_Price', 'Binance_Vol_B', 'Coinbase_Vol_B', 'Upbit_Vol_B'])
    
    # 2. 중복 실행 방지 (오늘 날짜가 이미 있으면 스킵)
    if today in df['Date'].values:
        print(f"Data for {today} already exists.")
        return

    # 3. 데이터 수집
    hype_vol, hype_price = get_hype_data() 
    bin_vol, coin_vol, upbit_vol = get_competitor_data()
    
    print(f"Collected: {today} | HYPE: ${hype_price} (Vol: {hype_vol}B) | Bin: {bin_vol}B | Coin: {coin_vol}B | Up: {upbit_vol}B")
    
    # 4. 데이터 추가
    new_row = {
        'Date': today,
        'HYPE_Vol_B': hype_vol,
        'HYPE_Price': hype_price,
        'Binance_Vol_B': bin_vol,
        'Coinbase_Vol_B': coin_vol,
        'Upbit_Vol_B': upbit_vol
    }
    
    new_df = pd.DataFrame([new_row])
    df = pd.concat([df, new_df], ignore_index=True)
    
    # 5. 저장
    df.to_csv(file_name, index=False)
    print("CSV Saved successfully.")

if __name__ == "__main__":
    main()
