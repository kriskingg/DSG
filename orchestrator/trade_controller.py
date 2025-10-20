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
# 0️⃣ System Path + Encoding Fixes (for Windows compatibility)
# ============================================================

# Ensure UTF-8 output on Windows (fixes emoji logging)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure the project root (D:\DSG) is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ============================================================
# 1️⃣ Logging setup
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
# 2️⃣ Configuration (you can make these dynamic later)
# ============================================================

BROKER = os.getenv("BROKER", "Rupeezy")
STRATEGY = os.getenv("STRATEGY", "auto_buy_logic")

# ============================================================
# 3️⃣ Helper: Broker module loader
# ============================================================

def load_broker_module(broker_name: str):
    """Dynamically import the selected broker module."""
    module_path = f"brokers.{broker_name.lower()}.main"
    logging.info(f"📦 Importing broker module: {module_path}")
    try:
        module = importlib.import_module(module_path)
        return module
    except ModuleNotFoundError:
        logging.error(f"❌ Broker module '{broker_name}' not found in brokers/ directory.")
        return None
    except Exception as e:
        logging.error(f"⚠️ Error loading broker module '{broker_name}': {e}")
        return None

# ============================================================
# 4️⃣ Main trading flow
# ============================================================

def run_trading_flow():
    """Run the complete trading orchestration flow."""
    logging.info(f"🚀 Launching trading workflow for broker: {BROKER}")

    module = load_broker_module(BROKER)
    if not module:
        logging.error("🛑 Broker module not found. Aborting execution.")
        return

    try:
        # Detect if module has main or start_trading
        if hasattr(module, "start_trading"):
            logging.info("▶️ Calling start_trading() ...")
            module.start_trading()
        elif hasattr(module, "main"):
            logging.info("▶️ Calling main() ...")
            module.main()
        else:
            logging.warning("⚠️ No entry function (main/start_trading) found in module.")
    except Exception as e:
        logging.exception(f"💥 Trading execution failed: {e}")
    finally:
        logging.info("✅ Orchestration complete.")
        logging.info(f"📄 Log saved to: {log_file}")

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
