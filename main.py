def get_competitor_data():
    bin_vol, coin_vol, upbit_vol = 0, 0, 0
    
    # 1. 공통 BTC 가격 선 조회
    btc_data = fetch_with_retry("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
    if not btc_data:
        print("Competitor Error: Failed to fetch BTC price.")
        return 0, 0, 0
    btc_price = btc_data['bitcoin']['usd']

    # 2. 거래소 '전체 목록'을 한 번만 호출 (API 과부하 방지)
    # per_page=100을 주면 전 세계 100대 거래소가 한 번에 딸려옵니다.
    # per_page를 100에서 250으로 변경합니다.
    exchanges_data = fetch_with_retry("https://api.coingecko.com/api/v3/exchanges?per_page=250")
    
    if exchanges_data:
        # 데이터 목록을 돌면서 필요한 거래소 3개만 쏙쏙 뽑아냅니다.
        for ex in exchanges_data:
            ex_id = ex.get('id')
            if ex_id == 'binance':
                bin_vol = round(float(ex.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
            elif ex_id == 'gdax': # Coinbase Pro의 API ID는 gdax입니다.
                coin_vol = round(float(ex.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
            elif ex_id == 'upbit':
                upbit_vol = round(float(ex.get('trade_volume_24h_btc', 0)) * btc_price / 1e9, 2)
                
    else:
        print("Competitor Error: Failed to fetch exchanges list.")
        
    return bin_vol, coin_vol, upbit_vol
