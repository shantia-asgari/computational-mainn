# api_server.py
from flask import Flask, jsonify
from threading import Thread, Lock
import core_engine
from config import API_HOST, API_PORT

# ۱. راه اندازی وب سرور Flask
app = Flask(__name__)

# ۲. ایجاد حافظه مشترک برای نگهداری آخرین سیگنال
shared_state = {
    "last_updated": None,
    "opportunities": []
}
# ایجاد یک قفل برای جلوگیری از تداخل در دسترسی به متغیر مشترک
lock = Lock()

# ۳. تعریف اندپوینت (مسیر) API
@app.route('/computational/signals', methods=['GET'])
def get_signals():
    """این تابع آخرین سیگنال ذخیره شده را در فرمت JSON برمی گرداند."""
    with lock:
        response_data = shared_state.copy()
    return jsonify(response_data)

# ۴. تعریف تابعی که قرار است در نخ پس زمینه اجرا شود
def background_scanner():
    """این تابع، موتور اسکنر ربات را به صورت بی نهایت اجرا می کند."""
    print("Starting background scanner thread...")
    core_engine.run_scanner_cycle(shared_state, lock)

# ۵. نقطه شروع اصلی برنامه
if __name__ == '__main__':
    # ایجاد و اجرای نخ اسکنر در پس زمینه
    scanner_thread = Thread(target=background_scanner, daemon=True)
    scanner_thread.start()

    # اجرای وب سرور در نخ اصلی
    print(f"API server starting on http://{API_HOST}:{API_PORT}")
    
    # --- خط جدید اضافه شده ---
    print(f"✅ Access API at: http://103.75.198.172:{API_PORT}/computational/signals")
    
    app.run(host=API_HOST, port=API_PORT)