import os
import logging
from time import sleep
from datetime import datetime
import boto3
import pytz
import requests
from bs4 import BeautifulSoup

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from .env file (if needed)
from dotenv import load_dotenv
load_dotenv()

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Constants for Chartink
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

# Fetch data from Chartink based on the given condition (minimal logging)
def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                r = s.get(Charting_Link)
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})
                response = s.post(Charting_url, data={'scan_clause': condition})
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logging.error("Exception during data fetch from Chartink: {}".format(str(e)))
        sleep(10)  # wait before retrying
    logging.error("All retries to fetch data from Chartink failed")
    return None

# Fetch all stocks from DynamoDB StockEligibility table
def fetch_all_stocks_from_dynamodb():
    try:
        response = dynamodb.scan(TableName='StockEligibility')
        return response['Items']
    except Exception as e:
        logging.error(f"Error fetching items from DynamoDB: {e}")
        return []

# Function to update stock eligibility
def update_stock_eligibility():
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Fetch data from Chartink
    chartink_data = fetch_chartink_data(condition)
    if not chartink_data:
        logging.error("No data fetched from Chartink.")
        return

    # Create a set of eligible instruments from Chartink
    eligible_instruments = {item['nsecode'] for item in chartink_data['data']}
    
    # Fetch all stocks from DynamoDB
    all_stocks = fetch_all_stocks_from_dynamodb()
    
    for stock in all_stocks:
        instrument_name = stock['InstrumentName']['S']
        is_eligible = instrument_name in eligible_instruments

        eligibility_status = 'Eligible' if is_eligible else 'Ineligible'
        current_price = stock.get('InitialPrice', {'N': '0'})['N']  # Use the existing price from DynamoDB or set default
        
        logging.info(f"Updating {instrument_name} as {eligibility_status} in DynamoDB.")
        try:
            dynamodb.update_item(
                TableName='StockEligibility',
                Key={'InstrumentName': {'S': instrument_name}},
                UpdateExpression="SET EligibilityStatus = :elig, LastUpdated = :lu",
                ExpressionAttributeValues={
                    ':elig': {'S': eligibility_status},
                    ':lu': {'S': current_time}
                }
            )
            logging.info(f"Successfully updated {instrument_name} to {eligibility_status}.")
        except Exception as e:
            logging.error(f"Error updating {instrument_name} in DynamoDB: {e}")

if __name__ == "__main__":
    logging.info("Starting stock eligibility update process...")
    update_stock_eligibility()
    logging.info("Stock eligibility update process completed.")
