import requests
import time 
import random 
from bs4 import BeautifulSoup 
# ========================= 
# # LINE Notify #
#  ========================= 
import os

LINE_TOKEN = os.environ.get("LINE_TOKEN", "")
USER_ID = os.environ.get("USER_ID", "")

def send_line_notify(msg):
    if not LINE_TOKEN or not USER_ID:
        raise RuntimeError(
            "LINE_TOKEN と USER_ID を環境変数に設定してください。"
        )
 
    headers = { "Content-Type": "application/json", 
               "Authorization": f"Bearer {LINE_TOKEN}" } 
    data = { "to": USER_ID, 
            "messages": [{"type": "text", "text": msg}] } 
    requests.post( "https://api.line.me/v2/bot/message/push", 
                  headers=headers, json=data ) 
# ========================= #
#  楽天監視設定 # 
# ========================= 
headers = {
    "User-Agent": "Mozilla/5.0"
}
##JadeForestの場合は45827698。
RAKUTEN_URL = "https://item.rakuten.co.jp/netbaby/4582769806223/"
#RAKUTEN_URL = "https://item.rakuten.co.jp/netbaby/406495/"
def is_rakuten_stock():

    try:
        res = requests.get(RAKUTEN_URL, headers=headers, timeout=20)
        html = res.text

        # schema.org 在庫判定
        if "schema.org/InStock" in html:
            print("楽天: 在庫あり")
            return True

        if "schema.org/LimitedAvailability" in html:
            print("楽天: 在庫わずか（争奪戦）")
            return True

        if "schema.org/PreOrder" in html:
            print("楽天: 予約開始")
            return True

        print("楽天: 売り切れ")
        return False

    except Exception as e:
        print("楽天通信エラー:", e)
        return False

# ========================= 
# # Amazon監視設定 # 
# ========================= 
AMAZON_ASINS = [ "B0G2RSS3HV", 
                 "B0G2RQL3RG", 
                 "B0G2RQ7QBP", 
                 "B0G2RTFMMH", 
                 "B0G2RPXXY8", 
                 "B0F4CWWMTM", 
                 "B0F4CZTGD9", 
                 "B0F4CZNHWC",
                 "B0F132JP2F",
                 "B0F131B391",
                 "B0F136VSTJ"
                 #"B0FQNN2V9B" 
               ] 
from bs4 import BeautifulSoup 

def is_amazon_stock(asin): 
    url = f"https://www.amazon.co.jp/dp/{asin}" 
    try: 
        res = requests.get(url, headers=headers, timeout=20) 
        soup = BeautifulSoup(res.text, "html.parser") 
        page_text = soup.get_text() 
        # 在庫チェック 
        if not ("カートに入れる" in page_text or "今すぐ買う" in page_text):
            return False 
        # ---- 出荷元 / 販売元取得 ---- 
        merchant = soup.select_one( '[offer-display-feature-name="desktop-merchant-info"] .offer-display-feature-text-message' ) 
        if merchant is None: 
            return False 
        merchant_text = merchant.get_text(strip=True) 
        print("販売者:", merchant_text) 
        # Amazon公式のみ許可 
        return merchant_text == "Amazon.co.jp" 
    except Exception as e: 
        print("Amazon通信エラー:", e) 
        return False 
# ========================= 
# # 重複通知防止 # 
# ========================= 
notified_amazon = set() 
rakuten_notified = False 

# ========================= 
# # メイン監視ループ # 
# ========================= 
print("監視Botスタート") 
while True: 
    try: 
        # -------- 楽天 -------- 
        rakuten_stock = is_rakuten_stock() 
        if rakuten_stock and not rakuten_notified: 
            send_line_notify(f"楽天在庫復活！\n{RAKUTEN_URL}") 
            print("楽天通知送信") 
            rakuten_notified = True 
            
        if not rakuten_stock: 
            rakuten_notified = False 

        # -------- Amazon -------- 
        for asin in AMAZON_ASINS: 
            stock = is_amazon_stock(asin)
            if stock and asin not in notified_amazon: 
                url = f"https://www.amazon.co.jp/dp/{asin}" 
                send_line_notify(f"Amazon在庫復活！\n{url}") 
                print(f"Amazon通知送信 {asin}") 
                notified_amazon.add(asin) 
            if not stock and asin in notified_amazon: 
                notified_amazon.remove(asin) 
            
    except Exception as e: 
        print("想定外エラー:", e) 
        
    wait = random.randint(12, 15) 
    print(f"{wait}秒待機") 
    time.sleep(wait)