# config.py

# --- Wallex API Configuration ---
API_KEY = "15933|BmSQkr4yYw6RcFDILqW5T3zsNT8b5rAfq2mmc92A"

# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = "7435237309:AAEAXXkce1VU8Wk-NqxX1v6VKnSMaydbErs"
TELEGRAM_GROUP_CHAT_ID = -1002684336789
TELEGRAM_MESSAGE_THREAD_ID = 6380

# --- TRADING MODE ---
IS_LIVE_TRADING = False
VERBOSE_MODE = True # اگر True باشد، ربات سود محاسبه شده برای تمام ارزها را چاپ میکند

# --- DB Settings ---
DB_NAME = "trades.db"

# --- Bot Timing (in seconds) ---
POST_TRADE_DELAY = 300  # زمان انتظار پس از ثبت یک معامله موفق
MAIN_LOOP_DELAY = 60    # زمان انتظار در پایان هر چرخه اصلی
SCAN_LOOP_DELAY = 2     # زمان انتظار بین بررسی هر ارز در لیست سفید

# --- Hybrid Exit Strategy Config ---
EXIT_TARGET_PROFIT_PERCENTAGE = 0.5 # هدف: کسب ۵۰٪ از شکاف سود اولیه

# --- Smart Precision Dictionary ---
MARKET_PRECISIONS = {
    "DEFAULT": 5, "TMN_PRICE_DEFAULT": 0,
    "DOTTMN": 2, "SOLTMN": 5, "ETHTMN": 5, "ATOMTMN": 2, "BNBTMN": 5
}

# --- Whitelist & Filters ---
WHITELIST = ["BTC", "ETH", "SOL", "ADA", "XRP", "DOT", "BNB", "TRX", "LTC", "BCH", "LINK", "ATOM", "AVAX", "NEAR", "FIL", "DOGE"]
ENTRY_FEE_PERCENT = 0.25  # *** این مقدار به عدد صحیح اصلاح شد ***
EXIT_FEE_PERCENT = 0.25
MIN_NET_PROFIT_PERCENT = 0.05
MIN_TRADE_SIZE_USDT = 3.5
MIN_TRADE_VALUE_TMN = 50000.0
TOMAN_SYMBOL = "TMN"
USDT_SYMBOL = "USDT"

# --- External URLs ---
WALLEX_BASE_URL = "https://wallex.ir/app/trade/"

# --- API Server Config ---
API_HOST = '0.0.0.0'  # به تمام IP های سرور گوش می دهد
API_PORT = 8889       # پورت منحصر به فرد برای این ربات