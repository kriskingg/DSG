"""
trade_controller.py
-------------------
Central orchestrator for DSG trading framework.

Purpose:
- Acts as the universal entry point to launch trading workflows.
- Dynamically loads a broker module (Rupeezy, Dhan, Kotak, etc.).
- Runs its main() or start_trading() function to execute strategies.
- Handles exceptions, logging, and broker selection logic.

Author: Chaitanya / DSG Project
"""

import importlib
import os
import sys
from datetime import datetime
import logging

# ============================================================
# 1️⃣ Logging setup
# ============================================================

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"trade_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# ============================================================
# 2️⃣ Configuration
# ============================================================

# Allow broker selection via environment variable or command-line arg
BROKER = os.getenv("BROKER_NAME", "Rupeezy").capitalize()

# Allow optional strategy override in the future
STRATEGY = os.getenv("STRATEGY", "auto_buy_logic").lower()

# Display header
logging.info("==============================================")
logging.info(f"🧭 DSG Trading Orchestrator | {datetime.now()}")
logging.info(f"💼 Selected Broker : {BROKER}")
logging.info(f"📊 Selected Strategy : {STRATEGY}")
logging.info("==============================================")


# ============================================================
# 3️⃣ Dynamic Broker Loading
# ============================================================

def load_broker_module(broker_name: str):
    """Dynamically import the broker module."""
    try:
        module_path = f"brokers.{broker_name.lower()}.main"
        logging.info(f"📦 Importing broker module: {module_path}")
        module = importlib.import_module(module_path)
        return module
    except ModuleNotFoundError:
        logging.error(f"❌ Broker module '{broker_name}' not found in brokers/ directory.")
        return None
    except Exception as e:
        logging.error(f"⚠️ Unexpected error importing broker '{broker_name}': {e}")
        return None


# ============================================================
# 4️⃣ Execution Flow
# ============================================================

def run_trading_flow():
    """Run the selected broker's trading logic."""
    logging.info(f"🚀 Launching trading workflow for broker: {BROKER}")

    module = load_broker_module(BROKER)
    if not module:
        logging.error("🛑 Broker module not found. Aborting execution.")
        return

    try:
        # If the broker module has a start_trading() function, run it
        if hasattr(module, "start_trading"):
            logging.info("▶️ Executing broker.start_trading()...")
            module.start_trading()
        # Else if it has a main() fallback
        elif hasattr(module, "main"):
            logging.info("▶️ Executing broker.main()...")
            module.main()
        else:
            logging.warning(f"⚠️ Broker '{BROKER}' module has no entry function defined.")
            logging.info("Expected one of: start_trading() or main().")
    except Exception as e:
        logging.error(f"💥 Error while executing {BROKER} workflow: {e}", exc_info=True)
    finally:
        logging.info("✅ Trading session finished.")
        logging.info("==============================================")


# ============================================================
# 5️⃣ CLI Entry Point
# ============================================================

if __name__ == "__main__":
    logging.info("🎯 Starting DSG Trade Orchestrator ...")
    run_trading_flow()
