"""
trade_controller.py
-------------------
Central orchestrator for DSG trading framework.

Purpose:
- Universal entry point for trading workflows.
- Dynamically loads broker module (Rupeezy, Dhan, Kotak, etc.).
- Executes broker's main/start_trading function.
- Handles logging, UTF-8, and case-insensitive broker resolution.

Author: Chaitanya / DSG Project
"""

import importlib
import os
import sys
from datetime import datetime
import logging

# ============================================================
# 0️⃣ System Path & Encoding Fixes
# ============================================================
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROKER_DIR = os.path.join(ROOT_DIR, "brokers")

for path in [ROOT_DIR, BROKER_DIR]:
    if path not in sys.path:
        sys.path.append(path)

# ============================================================
# 1️⃣ Logging Setup
# ============================================================
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"trade_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ============================================================
# 2️⃣ Configuration (Dynamic Environment Variables)
# ============================================================
BROKER = os.getenv("BROKER", "Rupezy")
STRATEGY = os.getenv("STRATEGY", "auto_buy_logic")

# ============================================================
# 3️⃣ Helper: Load Broker Module (Case-insensitive)
# ============================================================
def load_broker_module(broker_name: str):
    """Dynamically import the selected broker module (case-insensitive)."""
    broker_folder = broker_name.lower()
    module_path = f"brokers.{broker_folder}.main"

    logging.info(f"📦 Importing broker module: {module_path}")
    try:
        module = importlib.import_module(module_path)
        logging.info(f"✅ Broker module '{broker_name}' loaded successfully.")
        return module
    except ModuleNotFoundError:
        logging.error(f"❌ Broker module '{broker_name}' not found in brokers/ directory.")
        available = [d for d in os.listdir(BROKER_DIR) if os.path.isdir(os.path.join(BROKER_DIR, d))]
        logging.error(f"📁 Available brokers: {available}")
        return None
    except Exception as e:
        logging.error(f"⚠️ Error loading broker module '{broker_name}': {e}")
        return None

# ============================================================
# 4️⃣ Main Trading Flow
# ============================================================
def run_trading_flow():
    """Run the complete trading orchestration flow."""
    logging.info(f"🚀 Launching trading workflow for broker: {BROKER}")
    module = load_broker_module(BROKER)

    if not module:
        logging.error("🛑 Broker module not found. Aborting execution.")
        return

    try:
        if hasattr(module, "start_trading"):
            logging.info("▶️ Calling start_trading() ...")
            module.start_trading()
        elif hasattr(module, "main"):
            logging.info("▶️ Calling main() ...")
            module.main()
        else:
            logging.warning("⚠️ No entry function (main/start_trading) found in broker module.")
    except Exception as e:
        logging.exception(f"💥 Trading execution failed: {e}")
    finally:
        logging.info("✅ Orchestration complete.")
        logging.info(f"🗂 Log saved to: {log_file}")

# ============================================================
# 5️⃣ Entrypoint
# ============================================================
if __name__ == "__main__":
    logging.info("=" * 45)
    logging.info(f"🧭 DSG Trading Orchestrator | {datetime.now()}")
    logging.info(f"💼 Selected Broker : {BROKER}")
    logging.info(f"📊 Selected Strategy : {STRATEGY}")
    logging.info("=" * 45)
    logging.info("🎯 Starting DSG Trade Orchestrator ...")
    run_trading_flow()
