# File: D:\DSG\main.py
import os
import importlib.util
def load_and_run_broker_main(broker_name):
    main_path = os.path.join("brokers", broker_name, "main.py")
    if not os.path.exists(main_path):
        print(f"❌ Could not find {main_path}")
        return
    print(f"🚀 Loading broker '{broker_name}' from {main_path}...")
    try:
        spec = importlib.util.spec_from_file_location("broker_main", main_path)
        broker_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(broker_main)
        print("✅ Broker main executed successfully.")
    except Exception as e:
        print(f"❌ Failed to run broker main: {e}")
if __name__ == "__main__":
    broker = os.getenv("BROKER")
    strategy = os.getenv("STRATEGY")
    run_broker_main = os.getenv("RUN_BROKER_MAIN", "false").lower() == "true"
    print(f"📦 Selected Broker: {broker}")
    print(f"📈 Selected Strategy: {strategy}")
    print(f"⚙️  Run Broker Main: {run_broker_main}")
    if run_broker_main and broker:
        load_and_run_broker_main(broker)
    else:
        print("❌ Environment not properly set. Please set BROKER and RUN_BROKER_MAIN=true")
