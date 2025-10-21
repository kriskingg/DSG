# strategies/price_drop.py

"""
Price Drop Strategy

This strategy fetches all eligible stocks from the broker and compares their current LTP
against a defined trigger price. If the LTP drops below the trigger, a buy order is placed.

The broker object passed must implement:
- get_eligible_stocks()
- get_ltp(symbol)
- place_order(symbol, qty, order_type)
"""

def run(broker):
    print("📉 [STRATEGY] Running Price Drop Strategy...")

    try:
        eligible_stocks = broker.get_eligible_stocks()

        if not eligible_stocks:
            print("⚠️  No eligible stocks found.")
            return

        for stock in eligible_stocks:
            symbol = stock.get("symbol")
            trigger_price = stock.get("trigger_price")
            quantity = stock.get("qty", 0)

            if not symbol or not trigger_price or quantity <= 0:
                print(f"⛔ Skipping invalid stock entry: {stock}")
                continue

            ltp = broker.get_ltp(symbol)

            print(f"🔍 {symbol}: LTP = {ltp}, Trigger = {trigger_price}")
            if ltp < trigger_price:
                print(f"✅ Trigger met for {symbol}. Placing order...")
                broker.place_order(symbol, quantity, "BUY")
            else:
                print(f"❌ No action for {symbol}. LTP hasn't dropped enough.")

    except Exception as e:
        print(f"🔥 Exception in Price Drop Strategy: {e}")
