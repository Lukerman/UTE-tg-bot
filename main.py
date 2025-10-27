import os
import threading
from dotenv import load_dotenv

load_dotenv()

def run_web():
    from web import app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    from bot import run_bot
    run_bot()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting File Monetization System")
    print("=" * 50)
    
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("✅ Flask Web Server started on port 5000")
    
    print("✅ Starting Telegram Bot...")
    run_bot()
