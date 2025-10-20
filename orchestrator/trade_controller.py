import importlib.util
import os
import sys
import logging
from datetime import datetime

# ============================================================
# UTF-8 Fix & Path Setup
# ============================================================
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROKER_DIR = os.path.join(ROOT_DIR, "brokers")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

for p in [ROOT_DIR, BROKER_DIR]:
    if p not in sys.path:
        sys.path.append(p)

# ============================================================
# Logging
# ============================================================
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
# Configuration
# ============================================================
BROKER = os.getenv("BROKER", "rupeezy").strip().lower()
STRATEGY = os.getenv("STRATEGY", "auto_buy_logic").strip().lower()

# ============================================================
# Broker Loader (Direct exec fallback)
# ============================================================
def load_broker_module(broker_name: str):
    """Loads or executes the broker's main.py file dynamically."""
    broker_folder = broker_name.lower()

    possible_paths = [
        os.path.join(BROKER_DIR, broker_folder, "main.py"),
        os.path.join(BROKER_DIR, broker_name, "main.py"),
        os.path.join(ROOT_DIR, "brokers", broker_folder, "main.py"),
        os.path.join(ROOT_DIR, "brokers", broker_name, "main.py"),
    ]

    logging.info(f"🔍 Checking possible paths for broker '{broker_name}':")
    for path in possible_paths:
        logging.info(f"   - {path}")

    main_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if not main_path:
        logging.error(f"❌ Broker module '{broker_name}' not found.")
        available = [d for d in os.listdir(BROKER_DIR) if os.path.isdir(os.path.join(BROKER_DIR, d))]
        logging.error(f"📁 Available brokers: {available}")
        return None

    logging.info(f"✅ Found broker module at: {main_path}")

    try:
        # 🔧 FIX: add '__name__' and '__file__' to globals so __main__ runs properly
        module_globals = {
            "__name__": "__main__",
            "__file__": main_path
        }
        with open(main_path, "r", encoding="utf-8") as f:
            code = f.read()
        exec(code, module_globals)
        logging.info(f"✅ Executed {main_path} successfully.")
        return module_globals
    except Exception as e:
        logging.exception(f"💥 Failed to execute broker module '{broker_name}': {e}")
        return None

# ============================================================
# Trading Flow
# ============================================================
def run_trading_flow():
    logging.info(f"🚀 Launching trading workflow for broker: {BROKER}")
    module = load_broker_module(BROKER)

    if not module:
        logging.error("🛑 Broker module not found. Aborting execution.")
        return

    try:
        if isinstance(module, dict) and "start_trading" in module:
            logging.info("▶️ Calling start_trading() ...")
            module["start_trading"]()
        elif hasattr(module, "start_trading"):
            logging.info("▶️ Calling start_trading() ...")
            module.start_trading()
        elif isinstance(module, dict) and "main" in module:
            logging.info("▶️ Calling main() ...")
            module["main"]()
        elif hasattr(module, "main"):
            logging.info("▶️ Calling main() ...")
            module.main()
        else:
            logging.warning("⚠️ No entry function (main/start_trading) found.")
    except Exception as e:
        logging.exception(f"💥 Trading execution failed: {e}")
    finally:
        logging.info("✅ Orchestration complete.")
        logging.info(f"🗂 Log saved to: {log_file}")

# ============================================================
# Entrypoint
# ============================================================
if __name__ == "__main__":
    logging.info("=" * 45)
    logging.info(f"🧭 DSG Trading Orchestrator | {datetime.now()}")
    logging.info(f"💼 Selected Broker : {BROKER}")
    logging.info(f"📊 Selected Strategy : {STRATEGY}")
    logging.info("=" * 45)
    logging.info("🎯 Starting DSG Trade Orchestrator ...")
    run_trading_flow()
