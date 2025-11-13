# wallex_client.py
import requests
import json
import math  # <-- این ماژول اضافه شد
from config import MARKET_PRECISIONS

API_BASE_URL = "https://api.wallex.ir/v1"

def _floor_truncate(quantity, precision):
    """
    مقدار را به جای گرد کردن، به سمت پایین کوچک می کند.
    مثال: (1.127, 2) -> 1.12
    """
    if precision == 0:
        return math.floor(quantity)
    factor = 10 ** precision
    return math.floor(quantity * factor) / factor

def place_order(api_key, symbol, side, quantity, client_order_id, precision, order_type="market", price=None):
    url = f"{API_BASE_URL}/account/orders"
    headers = {'Content-Type': 'application/json', 'x-api-key': api_key}
    
    # --- *** این بخش حیاتی اصلاح شد *** ---
    # به جای گرد کردن (round)، مقدار را به پایین کوچک می کنیم
    # این کار از خطای "موجودی ناکافی" در هنگام فروش جلوگیری می کند
    final_quantity = _floor_truncate(quantity, precision)
    
    payload = {"symbol": symbol, "side": side.upper(), "type": order_type.upper(), "quantity": str(final_quantity), "client_order_id": client_order_id}
    if order_type.upper() == "LIMIT":
        if price is None:
            print("❌ Error: Price is required for LIMIT orders.")
            return None
        price_precision = MARKET_PRECISIONS.get("TMN_PRICE_DEFAULT", 0)
        payload['price'] = str(round(price, price_precision))
    
    # --- *** این خط اصلاح شد (UPPER به upper) *** ---
    print(f"\nPlacing {order_type.upper()} {side.upper()} order for {final_quantity} of {symbol}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response_data = response.json()
        print(f"Server Response: {json.dumps(response_data, ensure_ascii=False)}")
        if response.status_code in [200, 201]:
            print(f"✅ Order for {symbol} was accepted by the server.")
            return response_data
        else:
            print(f"❌ Order placement failed: Status {response.status_code}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Order placement failed: A network error occurred: {e}")
        return None

def cancel_order(api_key, client_order_id):
    url = f"{API_BASE_URL}/account/orders/{client_order_id}"
    headers = {'x-api-key': api_key}
    print(f"\nAttempting to cancel order with ID: {client_order_id}...")
    try:
        response = requests.delete(url, headers=headers, timeout=15)
        response_data = response.json()
        if response.status_code in [200, 201] and response_data.get('success'):
            print(f"✅ Order {client_order_id} cancelled successfully.")
            return response_data
        else:
            print(f"❌ Failed to cancel order {client_order_id}. Response: {response_data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error while cancelling order {client_order_id}: {e}")
        return None

def get_all_markets():
    try:
        response = requests.get(f"{API_BASE_URL}/markets", timeout=10); response.raise_for_status()
        return response.json().get("result", {}).get("symbols", {})
    except requests.exceptions.RequestException as e:
        print(f"-> API Error (get_all_markets): {e}"); return None
def get_order_book(symbol):
    try:
        response = requests.get(f"{API_BASE_URL}/depth?symbol={symbol}", timeout=10); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"-> API Error for '{symbol}': {e}"); return None
def get_order_details(api_key, client_order_id):
    url = f"{API_BASE_URL}/account/orders/{client_order_id}"
    try:
        response = requests.get(url, headers={'x-api-key': api_key}, timeout=10); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"-> API Error getting order details for '{client_order_id}': {e}"); return None
def get_balances(api_key):
    try:
        response = requests.get(f"{API_BASE_URL}/account/balances", headers={'x-api-key': api_key}, timeout=10); response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"-> API Error trying to get balances: {e}"); return None
