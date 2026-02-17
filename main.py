import requests
import pandas as pd
from datetime import datetime
import os
import time

def get_hype_data():
    # Hyperliquid 데이터 (공식 API)
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {'Content-Type': 'application/json'}
        
        # 1. 가격 및 거래량 조회 (globalStats)
        payload = {"type": "metaAndAssetCtxs"}
        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()
        
        # HYPE 토큰 찾기 (보통 인덱스 0이나 심볼로 찾음)
        # 여기서는 전체 거래소 볼륨을 가져오는 로직으로 구성
        # 2. 거래소 전체 24시간 볼륨 조회 (별도 엔드포인트가 없으면 day stats 계산)
        # 간단하게 HYPE 토큰 가격만 가져오고, 볼륨은 L1 stats에서 가져오는 방식 등 다양함.
        # 여기서는 선생님이 쓰시던 로직을 추정하여 'HYPE' 가격을 가져옵니다.
        
        hype_price = 0
        universe = data[0]['universe']
        asset_ctxs = data[1]
        
        for i, asset in enumerate(universe):
            if asset['name'] == 'HYPE':
                price = float(asset_ctxs[i]['markPx'])
                hype_price = round(price, 2)
                break
        
        # 거래소 전체 볼륨 (별도 API 필요, 여기서는 HYPE 토큰의 거래량이 아닌 거래소 전체 볼륨을 위해)
        # Hyperliquid stats API (historical)
        # 편의상 HYPE 가격만 우선 수집하고, 거래량은 User Input을 가정하거나
        # 추후 스크래핑 로직을 고도화해야 합니다. 
        # (임시로 0으로 두거나, 선생님이 수동 입력하던 값을 대체할 API를 찾아야 함)
        # 이번 예시에서는 '가격'만 자동화하고 거래량은 0으로 둡니다. 
        # (API 분석 필요: Hyperliquid는 전체 볼륨을 한 번에 주는 엔드포인트가 숨겨져 있음)
        
        return 0, hype_price  # (Volume, Price)
    except Exception as e:
        print(f"HYPE Error: {e}")
        return 0, 0

def get_competitor_data():
    # 1. Binance (Spot)
    binance_vol = 0
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        resp = requests.get(url).json()
        # 모든 쌍의 quoteVolume 합산 (USDT, BTC 등 중복 제거 로직 필요하나 단순 합산은 너무 큼)
        # 주요 페어만 합산하거나 CoinGecko 사용 추천.
        # 여기서는 CoinGecko API 사용 (간편함)
        pass 
    except: pass
    
    # 더 정확한 방법: CoinGecko API (무료) 사용
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
    # HYPE 데이터는 API가 복잡하여 우선 0으로 두고, 경쟁사 데이터만 자동화 예시
    # 선생님이 HYPE 거래량을 구하는 구체적 코드가 있다면 get_hype_data() 안에 넣으면 됩니다.
    hype_vol, hype_price = get_hype_data() 
    bin_vol, coin_vol, upbit_vol = get_competitor_data()
    
    print(f"Collected: {today} | HYPE: ${hype_price} | Bin: {bin_vol}B | Coin: {coin_vol}B | Up: {upbit_vol}B")
    
    # 4. 데이터 추가
    new_row = {
        'Date': today,
        'HYPE_Vol_B': hype_vol, # 현재는 0, 추후 로직 보완 필요
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
