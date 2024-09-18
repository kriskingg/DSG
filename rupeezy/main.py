# InstrumentName: It identifies the stock by InstrumentName and uses this key to update DynamoDB when necessary.
# EligibilityStatus: This script only processes stocks with EligibilityStatus = Eligible. It fetches eligible stocks from DynamoDB.
# BaseValue:
# If BaseValue is less than or equal to 0 (or null), after the first successful order, the script updates the BaseValue to the order price.
# If BaseValue is already set (greater than 0), it does not update the BaseValue.
# DefaultQuantity: The script places an order only if the stock has a DefaultQuantity greater than 0. If DefaultQuantity is 0, the order is skipped.
# FirstDayProcessed: If FirstDayProcessed is False, the script updates it to True after setting the BaseValue for the first time.

import logging  # A Python module for logging messages during program execution
import os  # A module for interacting with the operating system, like reading environment variables
import boto3  # The AWS SDK for Python, used to interact with AWS services like DynamoDB
from vortex_api import AsthaTradeVortexAPI  # Importing custom SDK (from vortex API) to interact with the broker API
from vortex_api import Constants as Vc  # Importing constants from the vortex API to use in order placement
from decimal import Decimal
import time  # Import time to use sleep for retry logic

# Setup basic logging. This logs debug-level information in a formatted manner
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize a DynamoDB client using boto3 to interact with the DynamoDB service in the 'ap-south-1' region
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Retrieve secrets like API keys and access tokens from environment variables (set in the system or in a .env file)
api_secret = os.getenv('RUPEEZY_API_KEY')  # Fetch API key from environment
application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Fetch Application ID
access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')  # Fetch Access token

# Create an instance of the AsthaTradeVortexAPI client, passing in the required API keys and tokens
client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token  # Set the access token to authenticate requests

# Function to fetch eligible stocks from the DynamoDB 'StockEligibility' table
def fetch_eligible_stocks_from_dynamodb():
    """Fetch all eligible stocks from DynamoDB."""
    try:
        response = dynamodb.scan(
            TableName='StockEligibility',  # The name of the DynamoDB table
            FilterExpression="EligibilityStatus = :status",  # A filter to only fetch stocks that are eligible
            ExpressionAttributeValues={':status': {'S': 'Eligible'}}  # AttributeValue to match "Eligible" stocks
        )
        
        # Inspect the EligibilityStatus for each stock
        for stock in response['Items']:
            logging.debug(f"EligibilityStatus for {stock['InstrumentName']['S']}: {repr(stock['EligibilityStatus']['S'])}")
        
        return response['Items']  # Return the list of eligible stock items from the response
    except Exception as e:  # If any error occurs, log the error
        logging.error(f"Error fetching eligible stocks from DynamoDB: {e}")
        return []  # Return an empty list in case of failure

# Function to place an order using the SDK with retry logic
def trigger_order_via_sdk(client, order_details):
    """Trigger an order using the SDK and log the response."""
    retries = 3  # Number of retry attempts
    delay = 5  # Delay in seconds between retries

    for attempt in range(retries):
        try:
            # Choose the correct order type (market or limit) based on the variety specified in 'order_details'
            variety = Vc.VarietyTypes.REGULAR_MARKET_ORDER if order_details['variety'] == "RL-MKT" else Vc.VarietyTypes.REGULAR_LIMIT_ORDER

            # Place the order using the broker's API, providing all necessary parameters
            response = client.place_order(
                exchange=Vc.ExchangeTypes.NSE_EQUITY,  # The exchange (NSE Equity in this case)
                token=order_details['token'],  # Stock token (unique identifier for the stock)
                transaction_type=Vc.TransactionSides.BUY if order_details['transaction_type'] == "BUY" else Vc.TransactionSides.SELL,  # Buy or Sell
                product=Vc.ProductTypes.DELIVERY,  # Product type (e.g., delivery)
                variety=variety,  # Order variety (market or limit)
                quantity=order_details['quantity'],  # Quantity of stocks to buy
                price=order_details['price'],  # Order price (if a limit order)
                trigger_price=order_details['trigger_price'],  # Trigger price (if applicable)
                disclosed_quantity=order_details['disclosed_quantity'],  # Disclosed quantity
                validity=Vc.ValidityTypes.FULL_DAY if order_details['validity'] == "DAY" else Vc.ValidityTypes.IMMEDIATE_OR_CANCEL  # Order validity
            )
            logging.info(f"Order placed. Full response: {response}")  # Log the full response from the API
            return response  # Return the response for further processing
        except Exception as e:  # Log errors if the order fails
            logging.error(f"Error during order placement: {str(e)}. Attempt {attempt + 1} of {retries}")
            if attempt < retries - 1:  # If it's not the last attempt, wait before retrying
                time.sleep(delay)
            else:
                return None  # Return None if all retries fail

# Function to fetch the order details with retry logic
def fetch_order_details(client, order_id):
    """Fetch order details for a given order ID."""
    retries = 3  # Number of retry attempts
    delay = 5  # Delay in seconds between retries

    for attempt in range(retries):
        try:
            response = client.order_history(order_id)  # Fetch the order history based on order_id
            logging.info(f"Order Details for {order_id}: {response}")  # Log the fetched details
            return response  # Return the response for use later (e.g., for updating BaseValue)
        except Exception as e:
            logging.error(f"Error fetching order details for {order_id}: {str(e)}. Attempt {attempt + 1} of {retries}")
            if attempt < retries - 1:  # If it's not the last attempt, wait before retrying
                time.sleep(delay)
            else:
                return None  # Return None if all retries fail

# Function to fetch current positions with retry logic
def fetch_positions(client):
    """Fetch current positions with retry logic."""
    retries = 3  # Number of retry attempts
    delay = 5  # Delay in seconds between retries

    for attempt in range(retries):
        try:
            response = client.positions()  # Fetch the current positions from the API
            logging.info(f"Current Positions: {response}")  # Log the current positions
            return response
        except Exception as e:  # Log errors if fetching positions fails
            logging.error(f"Error fetching positions: {str(e)}. Attempt {attempt + 1} of {retries}")
            if attempt < retries - 1:  # If it's not the last attempt, wait before retrying
                time.sleep(delay)
            else:
                return None  # Return None if all retries fail

# Function to update the BaseValue for a stock in DynamoDB
def update_base_value_in_dynamodb(instrument_name, base_value):
    """Update the BaseValue in DynamoDB for a given instrument."""
    try:
        # Update the BaseValue field in DynamoDB for the stock
        dynamodb.update_item(
            TableName='StockEligibility',  # The name of the DynamoDB table
            Key={
                'InstrumentName': {'S': instrument_name},  # The partition key (instrument name)
                'Eligibility': {'S': 'Eligible'}  # The sort key (eligibility status)
            },
            UpdateExpression="SET BaseValue = :bv",  # The update expression to set the BaseValue
            ExpressionAttributeValues={
                ':bv': {'N': str(base_value)}  # The value to set for BaseValue (must be a stringified number)
            }
        )
        logging.info(f"Updated BaseValue for {instrument_name} to {base_value}.")  # Log the update
    except Exception as e:
        logging.error(f"Error updating BaseValue for {instrument_name}: {str(e)}")

# Function to update the FirstDayProcessed flag in DynamoDB
def update_first_day_processed_flag(instrument_name):
    """Update the FirstDayProcessed flag to True in DynamoDB for a given instrument."""
    try:
        # Update the FirstDayProcessed field in DynamoDB to True
        dynamodb.update_item(
            TableName='StockEligibility',
            Key={
                'InstrumentName': {'S': instrument_name},
                'Eligibility': {'S': 'Eligible'}
            },
            UpdateExpression="SET FirstDayProcessed = :fdp",
            ExpressionAttributeValues={
                ':fdp': {'BOOL': True}
            }
        )
        logging.info(f"Updated FirstDayProcessed flag to True for {instrument_name}.")
    except Exception as e:
        logging.error(f"Error updating FirstDayProcessed for {instrument_name}: {str(e)}")

# The main script execution starts here
if __name__ == "__main__":
    eligible_stocks = fetch_eligible_stocks_from_dynamodb()

    if not eligible_stocks:  # If no eligible stocks are found
        logging.info("No eligible stocks found.")
    else:
        with open("order_ids.txt", "w") as order_file:
            for stock in eligible_stocks:
                default_quantity = int(stock.get('DefaultQuantity', {}).get('N', 0))
                base_value = Decimal(stock.get('BaseValue', {}).get('N', -1))  # Get BaseValue, default to -1
                first_day_processed = stock.get('FirstDayProcessed', {}).get('BOOL', False)

                if default_quantity == 0:
                    logging.info(f"Skipping order placement for {stock['InstrumentName']['S']} as DefaultQuantity is 0.")
                    continue

                order_details = {
                    "exchange": "NSE_EQ",
                    "token": int(stock['Token']['N']),
                    "symbol": stock['InstrumentName']['S'],
                    "transaction_type": "BUY",
                    "product": "DELIVERY",
                    "variety": "RL-MKT",
                    "quantity": default_quantity,
                    "price": 0.0,
                    "trigger_price": 0.0,
                    "disclosed_quantity": 0,
                    "validity": "DAY",
                    "validity_days": 1,
                    "is_amo": False
                }

                # Place the order and get the response
                response = trigger_order_via_sdk(client, order_details)
                if response:
                    order_id = response['data']['orderId']  # Extract the order ID from the response
                    logging.info(f"Order placed successfully for {stock['InstrumentName']['S']}: {response}")
                    order_file.write(f"{order_id}\n")
                    
                    # Add a sleep to wait before fetching order details
                    time.sleep(10)  # Wait 10 seconds before fetching order details
                    
                    order_details_response = fetch_order_details(client, order_id)

                    # Only update BaseValue if it's less than or equal to 0 or missing (null)
                    if base_value <= 0:
                        if order_details_response and 'data' in order_details_response:
                            base_value = order_details_response['data'][0].get('order_price', 0)  # Extract the order price as the BaseValue
                            update_base_value_in_dynamodb(stock['InstrumentName']['S'], base_value)
                            update_first_day_processed_flag(stock['InstrumentName']['S'])  # Set the FirstDayProcessed flag to True
                            logging.info(f"BaseValue for {stock['InstrumentName']['S']} updated to {base_value}")
                    else:
                        logging.info(f"BaseValue and FirstDayProcessed are already set for {stock['InstrumentName']['S']}. Skipping BaseValue update.")
                else:
                    logging.error(f"Order placement failed for {stock['InstrumentName']['S']}")
        
        fetch_positions(client)
