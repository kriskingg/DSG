# signals/eligible_scrips.py
"""
Updates eligibility status of stocks in DynamoDB based on Chartink scans.

- Fetches Chartink scan results using a predefined RSI/EMA condition.
- Compares those results with all entries in DynamoDB 'StockEligibility' table.
- Marks stocks as 'Eligible' or 'Ineligible' accordingly.
- Resets BaseValue and FirstDayProcessed for ineligible stocks.
- Sets FirstDayProcessed = True for newly eligible ones.

Can be called directly via run() or imported as a reusable signal provider.
"""

import os
import logging
from time import sleep
from datetime import datetime

import boto3
import pytz
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --------------------------------------------------------------------------
# Setup logging and environment
# --------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
load_dotenv()

# --------------------------------------------------------------------------
# Initialize clients and constants
# --------------------------------------------------------------------------
dynamodb = boto3.client("dynamodb", region_name="ap-south-1")

CHARTINK_URL = "https://chartink.com/screener/process"
CHARTINK_LINK = "https://chartink.com/screener/"
CONDITION = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"


# --------------------------------------------------------------------------
# Chartink fetcher
# --------------------------------------------------------------------------
def fetch_chartink_data(condition: str):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers["User-Agent"] = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/58.0.3029.110 Safari/537.3"
                )

                # Fetch CSRF token
                r = s.get(CHARTINK_LINK, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")["content"]
                s.headers.update({"x-csrf-token": csrf_token})

                # Fetch scan results
                response = s.post(CHARTINK_URL, data={"scan_clause": condition}, timeout=15)
                if response.status_code == 200:
                    return response.json()
                logging.warning(f"Chartink response code {response.status_code}")
        except Exception as e:
            logging.error(f"Chartink fetch error (attempt {attempt + 1}): {e}")
        sleep(10)
    logging.error("All retries to fetch data from Chartink failed")
    return None


# --------------------------------------------------------------------------
# DynamoDB helpers
# --------------------------------------------------------------------------
def fetch_all_stocks_from_dynamodb():
    """Fetch all stocks from DynamoDB StockEligibility table."""
    try:
        response = dynamodb.scan(TableName="StockEligibility")
        return response["Items"]
    except Exception as e:
        logging.error(f"Error fetching items from DynamoDB: {e}")
        return []


def update_dynamodb_stock(stock, eligibility_status, first_day_processed, current_time, reset_base=False):
    """Helper to update individual DynamoDB items."""
    try:
        update_expression = "SET EligibilityStatus = :elig, LastUpdated = :lu, FirstDayProcessed = :fd"
        expr_values = {
            ":elig": {"S": eligibility_status},
            ":lu": {"S": current_time},
            ":fd": {"BOOL": first_day_processed},
        }
        if reset_base:
            update_expression += ", BaseValue = :bv"
            expr_values[":bv"] = {"NULL": True}

        dynamodb.update_item(
            TableName="StockEligibility",
            Key={
                "InstrumentName": {"S": stock["InstrumentName"]["S"].strip()},
                "Eligibility": {"S": stock["Eligibility"]["S"].strip()},
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expr_values,
        )
        logging.info(f"✅ Updated {stock['InstrumentName']['S']} → {eligibility_status}")
    except Exception as e:
        logging.error(f"Error updating {stock['InstrumentName']['S']}: {e}")


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------
def update_stock_eligibility():
    """Update stock eligibility based on Chartink data."""
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    chartink_data = fetch_chartink_data(CONDITION)
    if not chartink_data:
        logging.error("No data fetched from Chartink.")
        return

    eligible_instruments = {item["nsecode"] for item in chartink_data["data"]}
    all_stocks = fetch_all_stocks_from_dynamodb()

    for stock in all_stocks:
        instrument = stock["InstrumentName"]["S"].strip()
        is_eligible = instrument in eligible_instruments
        eligibility_status = "Eligible" if is_eligible else "Ineligible"
        first_day_processed = stock.get("FirstDayProcessed", {"BOOL": False})["BOOL"]

        if is_eligible and not first_day_processed:
            first_day_processed = True
            reset_base = False
        elif not is_eligible:
            first_day_processed = False
            reset_base = True
        else:
            base_attr = stock.get("BaseValue", {})
            if not isinstance(base_attr, dict) or "N" not in base_attr:
                logging.info(f"Skipping {instrument}: invalid BaseValue.")
                continue
            reset_base = False

        update_dynamodb_stock(
            stock,
            eligibility_status,
            first_day_processed,
            current_time,
            reset_base=reset_base,
        )


# --------------------------------------------------------------------------
# Tradetron-style entrypoint
# --------------------------------------------------------------------------
def run():
    logging.info("🚀 Starting stock eligibility update process...")
    update_stock_eligibility()
    logging.info("✅ Stock eligibility update process completed.")


if __name__ == "__main__":
    run()
