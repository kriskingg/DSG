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

        # AWS-related logging starts here
        logging.info(f"Checking if {instrument_name} exists in the StockEligibility table with Eligibility = {eligibility}.")
        try:
            response = dynamodb.get_item(
                TableName='StockEligibility',
                Key={
                    'InstrumentName': {'S': instrument_name},
                    'Eligibility': {'S': eligibility}
                }
            )
            logging.info(f"Successfully fetched item for {instrument_name} from DynamoDB.")
        except Exception as e:
            logging.error(f"Error fetching item from DynamoDB: {e}")
            continue

        item_in_db = response.get('Item')

        if eligibility == 'Eligible':
            if item_in_db:
                initial_price = float(item_in_db['InitialPrice']['N'])
                logging.info(f"Stock {instrument_name} already exists in the table.")
                logging.info(f"Old Price: {initial_price}, New Price: {current_price}")
                
                if initial_price != current_price:
                    logging.info(f"Updating price for {instrument_name} in StockEligibility table.")
                    try:
                        dynamodb.update_item(
                            TableName='StockEligibility',
                            Key={
                                'InstrumentName': {'S': instrument_name},
                                'Eligibility': {'S': 'Eligible'}
                            },
                            UpdateExpression="SET InitialPrice = :new_price, LastUpdated = :lu",
                            ExpressionAttributeValues={
                                ':new_price': {'N': str(current_price)},
                                ':lu': {'S': current_time}
                            }
                        )
                        logging.info(f"Successfully updated price for {instrument_name} to {current_price}.")
                    except Exception as e:
                        logging.error(f"Error updating item in DynamoDB: {e}")
                else:
                    logging.info(f"Price for {instrument_name} is unchanged. No update needed.")
            else:
                logging.info(f"Stock {instrument_name} not found in the table. Adding it now.")
                try:
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
                    logging.info(f"Successfully added {instrument_name} with price {current_price}.")
                except Exception as e:
                    logging.error(f"Error adding item to DynamoDB: {e}")

        elif eligibility == 'Ineligible':
            if item_in_db:
                logging.info(f"Stock {instrument_name} is ineligible. Resetting initial price and status.")
                try:
                    dynamodb.update_item(
                        TableName='StockEligibility',
                        Key={
                            'InstrumentName': {'S': instrument_name},
                            'Eligibility': {'S': 'Ineligible'}
                        },
                        UpdateExpression="SET InitialPrice = :none, EligibilityStatus = :ineligible, LastUpdated = :lu",
                        ExpressionAttributeValues={
                            ':none': {'N': '0'},
                            ':ineligible': {'S': 'Ineligible'},
                            ':lu': {'S': current_time}
                        }
                    )
                    logging.info(f"Successfully reset stock {instrument_name} as ineligible.")
                except Exception as e:
                    logging.error(f"Error resetting ineligible stock in DynamoDB: {e}")
            else:
                logging.info(f"Stock {instrument_name} is not present in the table for reset.")

if __name__ == "__main__":
    logging.info("Starting stock eligibility update process...")
    update_stock_eligibility()
    logging.info("Stock eligibility update process completed.")
