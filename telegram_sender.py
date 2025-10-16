# telegram_sender.py 
import requests
import json
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_CHAT_ID, 
    TELEGRAM_MESSAGE_THREAD_ID, TOMAN_SYMBOL, USDT_SYMBOL,
    WALLEX_BASE_URL
)

def send_message(message, keyboard=None):
    """پیام را با فرمت مشخص شده (HTML) به تلگرام ارسال می کند."""
    if "YOUR_TOKEN" in TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_CHAT_ID == 0:
        print("Telegram credentials are not set. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': str(TELEGRAM_GROUP_CHAT_ID),
        'message_thread_id': TELEGRAM_MESSAGE_THREAD_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    if keyboard:
        payload['reply_markup'] = json.dumps(keyboard)

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram signal notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Telegram notification: {e}")


def notify_arbitrage_opportunity(coin, entry_price, take_profit_price, stop_loss_price, net_profit_percent):
    """یک اعلان برای فرصت خرید ارز دیجیتال با فرمت HTML ارسال می کند."""
    market_symbol = f"{coin}{TOMAN_SYMBOL}"
    hashtag_symbol = f"{coin}{TOMAN_SYMBOL}"
    market_url = f"{WALLEX_BASE_URL}{market_symbol}"
    
    message = (
        f"💲 #{hashtag_symbol}\n"
        f"<b>Entry Price:</b> <code>{entry_price:,.0f} {TOMAN_SYMBOL}</code>\n"
        f"<b>Take Profit:</b> <code>{take_profit_price:,.0f} {TOMAN_SYMBOL}</code>\n"
        f"<b>Stop Loss:</b> <code>{stop_loss_price:,.0f} {TOMAN_SYMBOL}</code>\n\n"
        f"<b>Net Profit:</b> <code>{net_profit_percent:.2f}%</code>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                # --- اموجی اینجا تغییر کرد ---
                {"text": "💸 Go To Market", "url": market_url}
            ]
        ]
    }
    
    send_message(message, keyboard)

def notify_usdt_opportunity(crypto_basis, implied_price, actual_price, net_profit_percent):
    """یک اعلان برای فرصت خرید تتر با فرمت HTML ارسال می کند."""
    market_symbol = f"{USDT_SYMBOL}{TOMAN_SYMBOL}"
    hashtag_symbol = f"{USDT_SYMBOL}{TOMAN_SYMBOL}"
    market_url = f"{WALLEX_BASE_URL}{market_symbol}"

    message = (
        f"💲 #{hashtag_symbol}\n"
        f"<b>Entry Price:</b> <code>{actual_price:,.0f} {TOMAN_SYMBOL}</code>\n"
        f"<b>Take Profit:</b> <code>{implied_price:,.0f} {TOMAN_SYMBOL}</code>\n"
        f"<b>Stop Loss:</b> <code>{actual_price:,.0f} {TOMAN_SYMBOL}</code>\n\n"
        f"<b>Net Profit:</b> <code>{net_profit_percent:.2f}%</code>"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                # --- اموجی اینجا تغییر کرد ---
                {"text": "💸 Go To Market", "url": market_url}
            ]
        ]
    }

    send_message(message, keyboard)