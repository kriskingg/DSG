"""
auto_buy_logic.py
-----------------
Automated first-day order placement logic for eligible stocks.
Fetches stock data from DynamoDB, places MTF buy orders via Rupeezy (Vortex API),
and updates BaseValue and FirstDayProcessed flags.

Author: Chaitanya / DSG Project
"""

import logging
import os
import boto3
from vortex_api import AsthaTradeVortexAPI, Constants as Vc
from decimal import Decimal
import time
from botocore.exceptions import ClientError

# ============================================================
# 1️⃣ Logging Setup
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============================================================
# 2️⃣ DynamoDB Client
# ============================================================

dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# ============================================================
# 3️⃣ API Client Setup
# ============================================================

api_secret = os.getenv("RUPEEZY_API_KEY")
application_id = os.getenv("RUPEEZY_APPLICATION_ID")
access_token = os.getenv("RUPEEZY_ACCESS_TOKEN")

client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token

# ============================================================
# 4️⃣ DynamoDB Helpers
# ============================================================

def fetch_eligible_stocks():
    """Fetch all eligible stocks from DynamoDB."""
    try:
        response = dynamodb.scan(
            TableName="StockEligibility",
            FilterExpression="EligibilityStatus = :status",
            ExpressionAttributeValues={":status": {"S": "Eligible"}}
        )
        items = response.get("Items", [])
        logging.info(f"Fetched {len(items)} eligible stocks from DynamoDB.")
        return items
    except ClientError as e:
        logging.error(f"❌ DynamoDB error: {e}")
        return []
    except Exception as e:
        logging.error(f"⚠️ Error fetching eligible stocks: {e}")
        return []


def update_base_value(instrument_name, base_value):
    """Update the BaseValue for a given instrument."""
    try:
        dynamodb.update_item(
            TableName="StockEligibility",
            Key={
                "InstrumentName": {"S": instrument_name},
                "Eligibility": {"S": "Eligible"}
            },
            UpdateExpression="SET BaseValue = :bv",
            ExpressionAttributeValues={":bv": {"N": str(base_value)}}
        )
        logging.info(f"✅ BaseValue updated for {instrument_name}: {base_value}")
    except Exception as e:
        logging.error(f"Error updating BaseValue for {instrument_name}: {e}")


def update_first_day_processed(instrument_name):
    """Set FirstDayProcessed = True for the given instrument."""
    try:
        dynamodb.update_item(
            TableName="StockEligibility",
            Key={
                "InstrumentName": {"S": instrument_name},
                "Eligibility": {"S": "Eligible"}
            },
            UpdateExpression="SET FirstDayProcessed = :flag",
            ExpressionAttributeValues={":flag": {"BOOL": True}}
        )
        logging.info(f"✅ FirstDayProcessed flag set for {instrument_name}")
    except Exception as e:
        logging.error(f"Error updating FirstDayProcessed for {instrument_name}: {e}")

# ============================================================
# 5️⃣ Broker API Helpers
# ============================================================

def place_order(order_details):
    """Place a market or limit order with retry logic."""
    retries, delay = 3, 5
    for attempt in range(retries):
        try:
            variety = (
                Vc.VarietyTypes.REGULAR_MARKET_ORDER
                if order_details["variety"] == "RL-MKT"
                else Vc.VarietyTypes.REGULAR_LIMIT_ORDER
            )

            response = client.place_order(
                exchange=Vc.ExchangeTypes.NSE_EQUITY,
                token=order_details["token"],
                transaction_type=Vc.TransactionSides.BUY
                if order_details["transaction_type"] == "BUY"
                else Vc.TransactionSides.SELL,
                product=Vc.ProductTypes.MTF,
                variety=variety,
                quantity=order_details["quantity"],
                price=order_details["price"],
                trigger_price=order_details["trigger_price"],
                disclosed_quantity=order_details["disclosed_quantity"],
                validity=Vc.ValidityTypes.FULL_DAY,
            )

            logging.info(f"✅ Order placed for {order_details['symbol']}: {response}")
            return response
        except Exception as e:
            logging.error(f"Order failed (attempt {attempt+1}/3): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None


def fetch_order_details(order_id):
    """Fetch details for a given order ID."""
    retries, delay = 3, 5
    for attempt in range(retries):
        try:
            response = client.order_history(order_id)
            logging.debug(f"Order details: {response}")
            return response
        except Exception as e:
            logging.error(f"Error fetching order details: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None


def fetch_positions():
    """Fetch current positions from Rupeezy."""
    try:
        positions = client.positions()
        logging.info(f"📊 Current Positions: {positions}")
        return positions
    except Exception as e:
        logging.error(f"Error fetching positions: {e}")
        return None

# ============================================================
# 6️⃣ Core Execution Logic
# ============================================================

def run(broker=None):
    """Entry point for orchestrator-compatible execution."""
    run_auto_buy_flow()

def run_auto_buy_flow():
    """Main function to fetch eligible stocks and place first-day buy orders."""
    eligible_stocks = fetch_eligible_stocks()

    if not eligible_stocks:
        logging.info("⚠️ No eligible stocks found in DynamoDB.")
        return

    with open("order_ids.txt", "w") as order_file:
        for stock in eligible_stocks:
            instrument_name = stock["InstrumentName"]["S"]
            default_qty = int(stock.get("DefaultQuantity", {}).get("N", 0))
            base_value = Decimal(stock.get("BaseValue", {}).get("N", "-1"))
            first_day = stock.get("FirstDayProcessed", {}).get("BOOL", False)

            if default_qty == 0:
                logging.info(f"⏭ Skipping {instrument_name} (DefaultQuantity=0)")
                continue

            order = {
                "symbol": instrument_name,
                "token": int(stock["Token"]["N"]),
                "transaction_type": "BUY",
                "variety": "RL-MKT",
                "quantity": default_qty,
                "price": 0.0,
                "trigger_price": 0.0,
                "disclosed_quantity": 0,
            }

            response = place_order(order)
            if not response:
                logging.error(f"❌ Failed to place order for {instrument_name}")
                continue

            order_id = response.get("data", {}).get("orderId")
            if order_id:
                order_file.write(f"{order_id}\n")
                logging.info(f"🆔 Order ID logged: {order_id}")
            else:
                logging.warning(f"⚠️ No orderId found for {instrument_name}")
                continue

            # Wait and fetch order details
            time.sleep(10)
            order_info = fetch_order_details(order_id)

            # Update BaseValue if not set yet
            if base_value <= 0:
                try:
                    price = order_info["data"][0].get("order_price", 0)
                    update_base_value(instrument_name, price)
                    update_first_day_processed(instrument_name)
                except Exception as e:
                    logging.error(f"⚠️ Error updating base for {instrument_name}: {e}")

    fetch_positions()
    logging.info("🏁 Auto-buy flow complete.")

# ============================================================
# 7️⃣ CLI Entrypoint
# ============================================================

if __name__ == "__main__":
    run()
