# brokers/rupeezy/main.py

import os
import logging
from datetime import datetime

# Fix import for same-folder login.py
from .login import rupeezy_login  # NOTE: This is a relative import for package execution

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def run_strategy(client, strategy_name):
    if strategy_name == "auto_buy_logic":
        logging.info("🚀 Executing Auto Buy Logic")
        # TODO: Import and run your strategy here
        # from strategies.auto_buy_logic import run
        # run(client)
        logging.info("✅ Auto Buy Logic completed (placeholder)")
    else:
        logging.warning(f"⚠️ Unknown strategy: {strategy_name}")

def main():
    logging.info("=============================================")
    logging.info(f"📈 Rupeezy Broker Launcher | {datetime.now()}")

    strategy = os.getenv("STRATEGY", "auto_buy_logic")
    logging.info(f"📊 Strategy to execute: {strategy}")

    logging.info("🔐 Logging in to Rupeezy ...")
    client = rupeezy_login()

    if client:
        logging.info("✅ Login successful")
        run_strategy(client, strategy)
    else:
        logging.error("❌ Login failed. Aborting strategy execution.")

    logging.info("=============================================")

if __name__ == "__main__":
    main()
