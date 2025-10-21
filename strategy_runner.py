# strategy_runner.py

import importlib
import sys
from pathlib import Path

# Add current working directory to sys.path for dynamic imports
sys.path.append(str(Path(__file__).parent.resolve()))

def load_broker(broker_name):
    try:
        module = importlib.import_module(f'brokers.{broker_name}')
        broker_class = getattr(module, broker_name.capitalize())
        return broker_class()
    except (ModuleNotFoundError, AttributeError) as e:
        print(f"❌ Failed to load broker '{broker_name}': {e}")
        sys.exit(1)

def load_strategy(strategy_name):
    try:
        module = importlib.import_module(f'strategies.{strategy_name}')
        return module
    except ModuleNotFoundError as e:
        print(f"❌ Failed to load strategy '{strategy_name}': {e}")
        sys.exit(1)

def main():
    broker_name = input("Enter broker module name (e.g., rupeezy): ").lower()
    strategy_name = input("Enter strategy module name (e.g., price_drop): ").lower()

    print(f"\n🚀 Loading broker '{broker_name}'...")
    broker = load_broker(broker_name)

    print(f"🚀 Loading strategy '{strategy_name}'...")
    strategy = load_strategy(strategy_name)

    print(f"📈 Running strategy '{strategy_name}' with broker '{broker_name}'...\n")
    strategy.run_strategy(broker)

if __name__ == "__main__":
    main()
