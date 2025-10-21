import csv
import os
import logging
from datetime import datetime
from .orders import place_order
logger = logging.getLogger("AutoBuy")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "eligible_stocks.csv")
def read_eligible_stocks():
    if not os.path.exists(DATA_FILE):
        logger.error(f"CSV file not found: {DATA_FILE}")
        return []
    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)
def write_updated_stocks(rows):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
def run():
    logger.info("?? Starting Auto Buy Logic...")
    stocks = read_eligible_stocks()
    if not stocks:
        logger.warning("No eligible stocks to process.")
        return
    updated_stocks = []
    for stock in stocks:
        symbol = stock.get("InstrumentName")
        status = stock.get("EligibilityStatus", "")
        base_value = float(stock.get("BaseValue", 0) or 0)
        quantity = int(stock.get("DefaultQuantity", 0) or 0)
        processed = stock.get("FirstDayProcessed", "False").lower() == "true"
        if status != "Eligible":
            logger.info(f"? Skipping {symbol} (Status: {status})")
            updated_stocks.append(stock)
            continue
        if processed:
            logger.info(f"? Already processed: {symbol}")
            updated_stocks.append(stock)
            continue
        if quantity <= 0:
            logger.warning(f"?? Quantity 0 for {symbol}, skipping.")
            updated_stocks.append(stock)
            continue
        try:
            price = place_order(symbol, quantity)
            logger.info(f"?? Order placed: {symbol} | Qty: {quantity} | Price: {price}")
            if base_value <= 0:
                stock["BaseValue"] = price
            stock["FirstDayProcessed"] = "True"
        except Exception as e:
            logger.error(f"? Failed to place order for {symbol}: {str(e)}")
        updated_stocks.append(stock)
    write_updated_stocks(updated_stocks)
    logger.info("? Auto Buy Logic completed.")
