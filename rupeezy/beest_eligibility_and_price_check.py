import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
from datetime import datetime
import boto3
import pytz

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

# Fetch data from Chartink based on the given condition
def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                logging.debug("Headers: {}".format(s.headers))
                r = s.get(Charting_Link)
                logging.debug("GET request to Charting_Link status code: {}".format(r.status_code))
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})
                logging.debug("CSRF Token: {}".format(csrf_token))
                logging.debug("Scan Condition: {}".format(condition))
                response = s.post(Charting_url, data={'scan_clause': condition})
                logging.debug("POST request to Charting_url status code: {}".format(response.status_code))
                response_json = response.json()
                logging.debug("Response JSON: {}".format(response_json))
                if response.status_code == 200:
                    return response_json
                else:
                    logging.error("Failed to fetch data with status code: {}".format(response.status_code))
        except Exception as e:
            logging.error("Exception during data fetch: {}".format(str(e)))
        sleep(10)  # wait before retrying
    logging.error("All retries failed")
    return None

# Function to update stock eligibility and reset ineligible stocks
def update_stock_eligibility():
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Fetch data from Chartink
    data = fetch_chartink_data(condition)
    
    if not data:
        logging.error("No data fetched from Chartink.")
        return

    for item in data['data']:
        instrument_name = item['nsecode']
        current_price = float(item['close'])
        eligibility = 'Eligible' if item['nsecode'] == 'ALPHAETF' else 'Ineligible'

        # Fetch current entry from DynamoDB
        response = dynamodb.get_item(
            TableName='StockEligibility',
            Key={
                'InstrumentName': {'S': instrument_name},
                'Eligibility': {'S': eligibility}  # Adding Eligibility key
            }
        )

        item_in_db = response.get('Item')

        if eligibility == 'Eligible':
            if item_in_db:
                # Update the current price and time
                initial_price = float(item_in_db['InitialPrice']['N'])
                logging.info(f"Stock {instrument_name} is still eligible with price {current_price}.")
            else:
                # Insert new entry if stock is eligible for the first time
                dynamodb.put_item(
                    TableName='StockEligibility',
                    Item={
                        'InstrumentName': {'S': instrument_name},
                        'Eligibility': {'S': 'Eligible'},
                        'InitialPrice': {'N': str(current_price)},
                        'DateRegistered': {'S': current_time},
                        'LastUpdated': {'S': current_time}
                    }
                )
                logging.info(f"Stock {instrument_name} added with initial price {current_price}.")

        elif eligibility == 'Ineligible':
            # Reset the stock details in DynamoDB if ineligible
            if item_in_db:
                dynamodb.update_item(
                    TableName='StockEligibility',
                    Key={
                        'InstrumentName': {'S': instrument_name},
                        'Eligibility': {'S': 'Ineligible'}  # Adding Eligibility key for updating
                    },
                    UpdateExpression="SET InitialPrice = :none, EligibilityStatus = :ineligible, LastUpdated = :lu",
                    ExpressionAttributeValues={
                        ':none': {'N': '0'},
                        ':ineligible': {'S': 'Ineligible'},
                        ':lu': {'S': current_time}
                    }
                )
                logging.info(f"Stock {instrument_name} is ineligible. Resetting initial price and status.")

if __name__ == "__main__":
    update_stock_eligibility()
