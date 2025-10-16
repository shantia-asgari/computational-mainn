# core_engine.py
import wallex_client
import uuid
import sqlite3
import time
from time import sleep
import json
import telegram_sender
from datetime import datetime, timezone

# --- Configuration Import ---
from config import (
    API_KEY, IS_LIVE_TRADING, VERBOSE_MODE, DB_NAME,
    WHITELIST, ENTRY_FEE_PERCENT, EXIT_FEE_PERCENT, MIN_NET_PROFIT_PERCENT,
    MIN_TRADE_SIZE_USDT, MIN_TRADE_VALUE_TMN, TOMAN_SYMBOL,
    USDT_SYMBOL, MARKET_PRECISIONS, POST_TRADE_DELAY,
    MAIN_LOOP_DELAY, SCAN_LOOP_DELAY, EXIT_TARGET_PROFIT_PERCENTAGE
)

# --- Database Functions (بدون تغییر) ---
def get_open_position():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE status = 'OPEN' LIMIT 1;")
        position = cursor.fetchone()
        conn.close()
        return dict(position) if position else None
    except sqlite3.Error as e:
        print(f"DATABASE ERROR on get_open_position: {e}")
        return None

def record_entry_position(order_response):
    result = order_response.get('result', {})
    if result.get('status') == 'FILLED' and result.get('fills'):
        fill = result['fills'][0]
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            params = (
                result.get('clientOrderId'), result.get('symbol'), 'OPEN',
                float(fill.get('quantity')), float(fill.get('price')),
                int(time.time()), float(fill.get('sum')), float(fill.get('fee'))
            )
            cursor.execute("""
                INSERT INTO positions 
                (client_order_id, symbol, status, quantity, entry_price, entry_time, total_cost_tmn, entry_fee) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, params)
            conn.commit()
            conn.close()
            print(f"✅ Position for {result.get('symbol')} recorded as OPEN.")
        except sqlite3.Error as e:
            print(f"DATABASE ERROR on record_entry_position: {e}")

def update_position_to_closed(position_id, exit_price, pnl):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        params = ('CLOSED', exit_price, int(time.time()), pnl, position_id)
        cursor.execute("""
            UPDATE positions 
            SET status = ?, exit_price = ?, exit_time = ?, pnl_tmn = ? 
            WHERE id = ?;
        """, params)
        conn.commit()
        conn.close()
        print(f"✅ Position ID {position_id} marked as CLOSED.")
    except sqlite3.Error as e:
        print(f"DATABASE ERROR on update_position_to_closed: {e}")
        
def update_limit_order_id(position_id, limit_order_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE positions SET limit_sell_order_id = ? WHERE id = ?;", (limit_order_id, position_id))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"DATABASE ERROR on update_limit_order_id: {e}")


# --- Main Bot Logic (اصلاح شده برای اجرا در نخ پس زمینه) ---
def run_scanner_cycle(shared_state, lock):
    mode = "LIVE TRADING" if IS_LIVE_TRADING else "SIMULATION"
    print(f"Initializing Bot in {mode} MODE (Verbose: {VERBOSE_MODE})...")

    if IS_LIVE_TRADING and ("YOUR_API_KEY_HERE" in API_KEY or not API_KEY):
        print("FATAL ERROR: A valid API_KEY is not set in config.py.")
        return

    while True:
        open_position = get_open_position()
        if open_position:
            # --- POSITION MANAGEMENT MODE (کد کامل و دست نخورده) ---
            print(f"\n--- Managing open position for {open_position['symbol']} ---")
            symbol = open_position['symbol']
            crypto_usdt_symbol = f"{symbol.replace(TOMAN_SYMBOL, '')}{USDT_SYMBOL}"

            crypto_tmn_response = wallex_client.get_order_book(symbol)
            crypto_usdt_response = wallex_client.get_order_book(crypto_usdt_symbol)
            usdt_tmn_response = wallex_client.get_order_book(f"{USDT_SYMBOL}{TOMAN_SYMBOL}")

            if not (crypto_tmn_response and crypto_usdt_response and usdt_tmn_response):
                print("Could not fetch necessary order books for management. Retrying..."); sleep(60); continue

            usdt_tmn_ob = usdt_tmn_response.get('result', {})
            actual_usdt_price_to_buy = float(usdt_tmn_ob.get('ask', [{}])[0].get('price', 0))
            actual_usdt_price_to_sell = float(usdt_tmn_ob.get('bid', [{}])[0].get('price', 0))

            if not open_position.get('limit_sell_order_id'):
                crypto_tmn_ob = crypto_tmn_response.get('result', {})
                price_to_sell_crypto_for_tmn = float(crypto_tmn_ob.get('bid', [{}])[0].get('price', 0))
                crypto_usdt_ob = crypto_usdt_response.get('result', {})
                price_to_buy_crypto_with_usdt = float(crypto_usdt_ob.get('ask', [{}])[0].get('price', 0))

                if price_to_buy_crypto_with_usdt > 0:
                    implied_usdt_price = price_to_sell_crypto_for_tmn / price_to_buy_crypto_with_usdt
                    initial_gross_margin = ((actual_usdt_price_to_sell / implied_usdt_price) - 1) * 100
                    net_profit_margin = initial_gross_margin - ENTRY_FEE_PERCENT - EXIT_FEE_PERCENT
                    target_profit_margin = net_profit_margin * EXIT_TARGET_PROFIT_PERCENTAGE
                    
                    limit_sell_price = open_position['entry_price'] * (1 + (target_profit_margin / 100))
                    
                    if IS_LIVE_TRADING:
                        limit_client_id = f"arbbot-exit-{uuid.uuid4()}"
                        precision = MARKET_PRECISIONS.get(symbol, MARKET_PRECISIONS["DEFAULT"])
                        sell_order_result = wallex_client.place_order(API_KEY, symbol=symbol, side="sell", order_type="limit", price=limit_sell_price, quantity=open_position['quantity'], client_order_id=limit_client_id, precision=precision)
                        if sell_order_result and sell_order_result.get('success'):
                            update_limit_order_id(open_position['id'], limit_client_id)
                            print(f"🎯 Take-profit LIMIT order set for {symbol} at {limit_sell_price:,.0f} TMN.")
                    else:
                        print(f"--- SIMULATION: Would place a LIMIT sell order for {symbol} at {limit_sell_price:,.0f} TMN. ---")
            else:
                limit_order_id = open_position['limit_sell_order_id']
                order_details = wallex_client.get_order_details(API_KEY, limit_order_id) if IS_LIVE_TRADING else {'result': {'status': 'ACTIVE'}}

                if order_details and order_details.get('success'):
                    status = order_details['result']['status']
                    if status == 'FILLED':
                        print(f"💰 Take-profit for {symbol} filled!")
                        exit_price = float(order_details['result']['fills'][0]['price'])
                        pnl = (exit_price - open_position['entry_price']) * open_position['quantity']
                        update_position_to_closed(open_position['id'], exit_price, pnl)
                    elif status in ['CANCELED', 'EXPIRED']:
                        update_limit_order_id(open_position['id'], None)
                    elif status == 'ACTIVE':
                        crypto_tmn_ob = crypto_tmn_response.get('result', {})
                        price_to_sell_crypto_for_tmn = float(crypto_tmn_ob.get('bid', [{}])[0].get('price', 0))
                        crypto_usdt_ob = crypto_usdt_response.get('result', {})
                        price_to_buy_crypto_with_usdt = float(crypto_usdt_ob.get('ask', [{}])[0].get('price', 0))

                        if price_to_buy_crypto_with_usdt > 0:
                            current_implied_usdt_price = price_to_sell_crypto_for_tmn / price_to_buy_crypto_with_usdt
                            if current_implied_usdt_price >= actual_usdt_price_to_buy:
                                print(f"⚠️ STOP-LOSS TRIGGERED for {symbol}. Exiting position...")
                                if IS_LIVE_TRADING:
                                    wallex_client.cancel_order(API_KEY, limit_order_id)
                                    market_exit_client_id = f"arbbot-sl-exit-{uuid.uuid4()}"
                                    precision = MARKET_PRECISIONS.get(symbol, MARKET_PRECISIONS["DEFAULT"])
                                    exit_order_result = wallex_client.place_order(API_KEY, symbol=symbol, side="sell", quantity=open_position['quantity'], client_order_id=market_exit_client_id, precision=precision)
                                    if exit_order_result and exit_order_result.get('success'):
                                        pnl = 0 
                                        update_position_to_closed(open_position['id'], 0, pnl)
                                else:
                                    print(f"--- SIMULATION: Would cancel LIMIT order and place MARKET sell order for {symbol}. ---")
            
            sleep(MAIN_LOOP_DELAY)
            continue

        # --- SCANNING MODE (با قابلیت ذخیره در API) ---
        print("\n--- No open positions. Scanning for new entry opportunities... ---")
        usdt_tmn_symbol = f"{USDT_SYMBOL}{TOMAN_SYMBOL}"
        usdt_tmn_response = wallex_client.get_order_book(usdt_tmn_symbol)
        if usdt_tmn_response is None: sleep(MAIN_LOOP_DELAY); continue
        usdt_tmn_ob = usdt_tmn_response.get('result', {})
        if not (usdt_tmn_ob and usdt_tmn_ob.get('bid') and usdt_tmn_ob.get('ask')): sleep(MAIN_LOOP_DELAY); continue
        
        actual_usdt_price_to_buy = float(usdt_tmn_ob['ask'][0]['price'])
        print(f"Scan Cycle Started... | Live USDT Buy Price: {actual_usdt_price_to_buy:,.0f} {TOMAN_SYMBOL}")
        
        profit_threshold = ENTRY_FEE_PERCENT + EXIT_FEE_PERCENT + MIN_NET_PROFIT_PERCENT

        for crypto in WHITELIST:
            crypto_tmn_symbol = f"{crypto}{TOMAN_SYMBOL}"
            crypto_usdt_symbol = f"{crypto}{USDT_SYMBOL}"
            
            crypto_tmn_response = wallex_client.get_order_book(crypto_tmn_symbol)
            crypto_usdt_response = wallex_client.get_order_book(crypto_usdt_symbol)
            if not (crypto_tmn_response and crypto_usdt_response): continue

            crypto_tmn_ob = crypto_tmn_response.get('result', {})
            crypto_usdt_ob = crypto_usdt_response.get('result', {})
            if not (crypto_tmn_ob.get('bid') and crypto_tmn_ob.get('bid')[0] and crypto_usdt_ob.get('ask') and crypto_usdt_ob.get('ask')[0]): continue
            
            price_to_sell_crypto_for_tmn = float(crypto_tmn_ob['bid'][0]['price'])
            price_to_buy_crypto_with_usdt = float(crypto_usdt_ob['ask'][0]['price'])
            if price_to_buy_crypto_with_usdt == 0: continue

            implied_usdt_price = price_to_sell_crypto_for_tmn / price_to_buy_crypto_with_usdt
            
            gross_margin_crypto = ((actual_usdt_price_to_buy / implied_usdt_price) - 1) * 100
            gross_margin_usdt = ((implied_usdt_price / actual_usdt_price_to_buy) - 1) * 100

            if VERBOSE_MODE: 
                print(f"  - Checking {crypto.ljust(5)} | Crypto Margin: {gross_margin_crypto:+.4f}% | USDT Margin: {gross_margin_usdt:+.4f}%")
            
            if gross_margin_crypto > profit_threshold:
                price_to_buy_crypto_with_tmn = float(crypto_tmn_ob['ask'][0]['price'])
                net_profit_margin = gross_margin_crypto - ENTRY_FEE_PERCENT - EXIT_FEE_PERCENT
                target_profit_margin = net_profit_margin * EXIT_TARGET_PROFIT_PERCENTAGE
                limit_sell_price = price_to_buy_crypto_with_tmn * (1 + (target_profit_margin / 100))
                stop_loss_price = actual_usdt_price_to_buy * price_to_buy_crypto_with_usdt

                telegram_sender.notify_arbitrage_opportunity(
                    coin=crypto, entry_price=price_to_buy_crypto_with_tmn,
                    take_profit_price=limit_sell_price, stop_loss_price=stop_loss_price,
                    net_profit_percent=net_profit_margin
                )
                
                opportunity_data = {
                    "asset_name": crypto,
                    "exchange_name": "Wallex",
                    "entry_price": price_to_buy_crypto_with_tmn,
                    "stop_loss_price": stop_loss_price,
                    "take_profit_price": limit_sell_price,
                    "net_profit_percent": round(net_profit_margin, 2),
                    "strategy_name": "Computiational"
                }
                with lock:
                    shared_state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    shared_state["opportunities"] = [opportunity_data]
                
                print(f"🔥 Golden Opportunity: BUY {crypto} | Net Profit: {net_profit_margin:.2f}%")
                if not IS_LIVE_TRADING: print(f"--- SIMULATION: Would buy {crypto}. ---")
                
                print(f"Pausing for {POST_TRADE_DELAY} seconds...")
                sleep(POST_TRADE_DELAY)
                break
            
            elif gross_margin_usdt > profit_threshold:
                net_profit_margin_usdt = gross_margin_usdt - ENTRY_FEE_PERCENT - EXIT_FEE_PERCENT

                telegram_sender.notify_usdt_opportunity(
                    crypto_basis=crypto,
                    implied_price=implied_usdt_price,
                    actual_price=actual_usdt_price_to_buy,
                    net_profit_percent=net_profit_margin_usdt
                )
                
                opportunity_data = {
                    "asset_name": USDT_SYMBOL,
                    "exchange_name": "Wallex",
                    "entry_price": actual_usdt_price_to_buy,
                    "stop_loss_price": actual_usdt_price_to_buy,
                    "take_profit_price": implied_usdt_price,
                    "net_profit_percent": round(net_profit_margin_usdt, 2),
                    "strategy_name": "Computiational"
                }
                with lock:
                    shared_state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    shared_state["opportunities"] = [opportunity_data]
                    
                print(f"🔥 Golden Opportunity: BUY USDT based on {crypto} market | Net Profit: {net_profit_margin_usdt:.2f}%")
                if not IS_LIVE_TRADING: print(f"--- SIMULATION: Would buy USDT. ---")
                
                print(f"Pausing for {POST_TRADE_DELAY} seconds...")
                sleep(POST_TRADE_DELAY)
                break
            
            sleep(SCAN_LOOP_DELAY)
    
        print(f"--- Main loop cycle finished. Waiting {MAIN_LOOP_DELAY} seconds ---")
        sleep(MAIN_LOOP_DELAY)