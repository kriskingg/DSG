"""
main.py
---------
Rupeezy broker main workflow.
Handles login, live feed, and strategy orchestration.
"""

import logging
from brokers.Rupeezy.login import login_and_get_token
from core_logic.auto_buy_logic import run_auto_buy_flow
from datetime import datetime

def start_trading():
    print(f"[{datetime.now()}] 🚀 Starting Rupeezy trading workflow...")

    token = login_and_get_token()
    if not token:
        print("❌ Login failed. Exiting.")
        return

    print("✅ Login successful. Token acquired.")
    run_auto_buy_flow()
    print(f"[{datetime.now()}] 🏁 Trading workflow completed.")

if __name__ == "__main__":
    start_trading()
