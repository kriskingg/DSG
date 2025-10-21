"""
eligible_scrips.py
------------------
Updates eligibility status of stocks in DynamoDB based on Chartink scans.
Resets BaseValue and FirstDayProcessed for ineligible stocks.
Sets FirstDayProcessed = True for newly eligible ones.
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Chartink constants
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

def fetch_chartink_data(condition):
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0'
                r = s.get(Charting_Link)
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})

                response = s.post(Charting_url, data={'scan_clause': condition})
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logging.error("Exception during data fetch from Chartink: {}".format(str(e)))
        sleep(10)
    logging.error("All retries to fetch data from Chartink failed")
    return None

def fetch_all_stocks_from_dynamodb():
    try:
        response = dynamodb.scan(TableName='StockEligibility')
        return response['Items']
    except Exception as e:
        logging.error(f"Error fetching items from DynamoDB: {e}")
        return []

def update_stock_eligibility():
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    chartink_data = fetch_chartink_data(condition)
    if not chartink_data:
        logging.error("No data fetched from Chartink.")
        return

    eligible_instruments = {item['nsecode'] for item in chartink_data['data']}
    all_stocks = fetch_all_stocks_from_dynamodb()

    for stock in all_stocks:
        instrument_name = stock['InstrumentName']['S'].strip()
        is_eligible = instrument_name in eligible_instruments
        eligibility_status = 'Eligible' if is_eligible else 'Ineligible'
        first_day_processed = stock.get('FirstDayProcessed', {'BOOL': False})['BOOL']

        if is_eligible and not first_day_processed:
            first_day_processed = True
        elif not is_eligible:
            base_value = None
            first_day_processed = False
        else:
            base_value_attr = stock.get('BaseValue', {})
            if isinstance(base_value_attr, dict) and 'N' in base_value_attr:
                base_value = base_value_attr['N']
            else:
                logging.info(f"Skipping {instrument_name} as BaseValue is invalid or missing 'N' key.")
                continue

        logging.info(f"Updating {instrument_name} as {eligibility_status} in DynamoDB.")

        try:
            update_expression = "SET EligibilityStatus = :elig, LastUpdated = :lu, FirstDayProcessed = :fd"
            expression_attribute_values = {
                ':elig': {'S': eligibility_status.strip()},
                ':lu': {'S': current_time},
                ':fd': {'BOOL': first_day_processed}
            }

            if not is_eligible:
                update_expression += ", BaseValue = :bv"
                expression_attribute_values[':bv'] = {'NULL': True}

            dynamodb.update_item(
                TableName='StockEligibility',
                Key={
                    'InstrumentName': {'S': instrument_name},
                    'Eligibility': {'S': stock['Eligibility']['S'].strip()}
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            logging.info(f"Successfully updated {instrument_name} to {eligibility_status}.")
        except Exception as e:
            logging.error(f"Error updating {instrument_name} in DynamoDB: {e}")

# ✅ Tradetron-style runner entrypoint
def run():
    logging.info("🚀 Starting stock eligibility update process...")
    update_stock_eligibility()
    logging.info("✅ Stock eligibility update process completed.")

if __name__ == "__main__":
    run()
