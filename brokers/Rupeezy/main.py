import os
import importlib
import logging
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# =============================================
# 🚀 Orchestrator Entry Point
# =============================================

def load_broker_module(broker_name):
    logging.info(f"🚀 Launching trading workflow for broker: {broker_name}")
    possible_paths = [
        f"D:/DSG/brokers/{broker_name}/main.py",
        f"./brokers/{broker_name}/main.py",
        f"brokers/{broker_name}/main.py",
        os.path.join(os.getcwd(), "brokers", broker_name, "main.py")
    ]

    logging.info(f"🔍 Checking possible paths for broker '{broker_name}':")
    for path in possible_paths:
        logging.info(f"   - {path}")

    main_path = None
    for path in possible_paths:
        if os.path.exists(path):
            main_path = path
            break

    if main_path is None:
        logging.error(f"❌ Could not find broker module for '{broker_name}'")
        return

    logging.info(f"✅ Found broker module at: {main_path}")
    try:
        # Set up globals to allow relative imports
        module_globals = {
            "__file__": main_path,
            "__name__": "__main__",
            "__package__": f"brokers.{broker_name}"
        }

        with open(main_path, "r", encoding="utf-8") as f:
            code = f.read()

        exec(code, module_globals)

    except Exception as e:
        logging.error(f"💥 Failed to execute broker module '{broker_name}': {e}")
        logging.exception(e)
        logging.error("🛑 Broker module not found. Aborting execution.")

def main():
    logging.info("=============================================")
    logging.info(f"🧭 DSG Trading Orchestrator | {datetime.now()}")
    broker = os.getenv("BROKER", "rupeezy")
    strategy = os.getenv("STRATEGY", "auto_buy_logic")
    logging.info(f"💼 Selected Broker : {broker}")
    logging.info(f"📊 Selected Strategy : {strategy}")
    logging.info("=============================================")
    logging.info("🎯 Starting DSG Trade Orchestrator ...")
    load_broker_module(broker)

if __name__ == "__main__":
    main()
