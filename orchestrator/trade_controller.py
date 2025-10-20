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
BROKER = os.getenv("BROKER", "Rupezy")
STRATEGY = os.getenv("STRATEGY", "auto_buy_logic")

# ============================================================
# Broker Loader (Absolute Path + Case Handling)
# ============================================================
def load_broker_module(broker_name: str):
    """Robust loader for brokers/<broker_name>/main.py (case-insensitive)."""
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

    # Pick the first valid file
    main_path = next((p for p in possible_paths if os.path.exists(p)), None)

    if not main_path:
        logging.error(f"❌ Broker module '{broker_name}' not found in brokers/ directory.")
        available = [d for d in os.listdir(BROKER_DIR) if os.path.isdir(os.path.join(BROKER_DIR, d))]
        logging.error(f"📁 Available brokers: {available}")
        return None

    logging.info(f"✅ Found broker module at: {main_path}")

    try:
        spec = importlib.util.spec_from_file_location(f"brokers.{broker_folder}.main", main_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        logging.info(f"✅ Broker '{broker_name}' loaded successfully.")
        return module
    except Exception as e:
        logging.exception(f"💥 Failed to load broker module '{broker_name}': {e}")
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
        if hasattr(module, "start_trading"):
            logging.info("▶️ Calling start_trading() ...")
            module.start_trading()
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
