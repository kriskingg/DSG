# Key Points:
# EligibilityStatus = "Eligible": Only stocks marked as eligible are processed for additional orders.
# FirstDayProcessed = True: The stock must have passed the first-day order condition before considering additional purchases.
# BaseValue > 0: Ensures the stock has a valid base price to calculate the percentage drop for subsequent buys.
# AdditionalQuantity > 0: This check skips any stock that does not require additional quantities, preventing orders where the extra purchase count is set to zero.
# This ensures there are no contradictions or unnecessary actions taken. Only eligible stocks with valid BaseValue, having passed the first-day order, and with a non-zero AdditionalQuantity, are considered for further orders based on price drops.

import logging  # Python's built-in module for logging events and debugging messages
import boto3  # AWS SDK for Python to interact with AWS services (in this case, DynamoDB)
from decimal import Decimal  # Module to handle decimal numbers for accuracy in currency values
from vortex_api import AsthaTradeVortexAPI, Constants as Vc  # Broker API SDK and constants
import os  # Required for fetching environment variables
from botocore.exceptions import ClientError  # Import ClientError for DynamoDB exceptions
from decimal import Decimal, ROUND_HALF_UP  # Ensure ROUND_HALF_UP is imported
import time  # Add the time module at the top for using sleep

# Set up basic logging configuration to capture and display log messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize a connection to the DynamoDB table using boto3
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
# Reference to the DynamoDB table where stock eligibility data is stored
table = dynamodb.Table('StockEligibility')

# Initialize the broker API client using the credentials from environment variables
api_secret = os.getenv('RUPEEZY_API_KEY')  # Fetch the API key from environment variables
application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Fetch the Application ID
access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')  # Fetch the access token

# Ensure the environment variables are properly set and log detailed errors if they are missing
if not api_secret:
    logging.error("RUPEEZY_API_KEY environment variable is missing.")
if not application_id:
    logging.error("RUPEEZY_APPLICATION_ID environment variable is missing.")
if not access_token:
    logging.error("RUPEEZY_ACCESS_TOKEN environment variable is missing.")

# Exit if any of the environment variables are missing
if not api_secret or not application_id or not access_token:
    logging.error("One or more API credentials are missing. Exiting script.")
    exit(1)

# Create an instance of the AsthaTradeVortexAPI client with the fetched credentials
client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token  # Set the access token for making authenticated API requests

# Function to fetch the current stock price using the instrument token via the broker's API
def get_current_price(instrument_token):
    try:
        # Call the broker's API to get the Last Traded Price (LTP) for the given stock token
        response = client.quotes([f"NSE_EQ-{instrument_token}"], mode=Vc.QuoteModes.LTP)
        
        # Log the full response from the quotes API, including the structure
        logging.debug(f"Full response from quotes API for token {instrument_token}: {response}")
        
        # Check if 'data' and 'NSE_EQ-{instrument_token}' are present in the response
        if 'data' not in response or f"NSE_EQ-{instrument_token}" not in response['data']:
            logging.error(f"Missing data or token key in response for token {instrument_token}: {response}")
            return None
        
        # Extract the Last Traded Price (LTP)
        ltp = response['data'][f"NSE_EQ-{instrument_token}"].get('last_trade_price', 0)
        
        if ltp == 0:
            logging.error(f"Received LTP as 0 for token {instrument_token}: {response}")
            return None
        
        # Convert to Decimal and round to two decimal places
        price = Decimal(ltp).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return price
    except Exception as e:
        logging.error(f"Error fetching current price for token {instrument_token}: {str(e)}")
        return None


# Function to check the user's available funds via the broker's API
def check_available_funds():
    try:
        response = client.funds()  # Call the SDK method to get funds
        logging.debug(f"Full response from funds API: {response}")  # Log the full API response
        # Attempt to extract available funds only if 'data' exists in response
        available_funds = Decimal(response.get('nse', {}).get('net_available', 0))
        return available_funds
    except Exception as e:
        logging.error(f"Error fetching available funds: {str(e)}")
        return None

# Function to calculate the percentage drop between the base value (buy price) and current stock price
def calculate_percentage_drop(base_value, current_price):
    # Formula to calculate percentage drop: (BaseValue - CurrentPrice) / BaseValue * 100
    return ((base_value - current_price) / base_value) * 100

# Function to fetch the order details after placing an order
def fetch_order_details(client, order_id):
    """Fetch order details for a given order ID."""
    try:
        response = client.order_history(order_id)  # Fetch the order history based on order_id
        logging.info(f"Order Details for {order_id}: {response}")  # Log the fetched details
        return response  # Return the response for use later
    except Exception as e:
        logging.error(f"Error fetching order details for {order_id}: {str(e)}")
        return None

# Main function to process stocks for additional quantity logic based on percentage drop
def process_additional_quantity():
    # Fetch available funds first by calling the broker API
    available_funds = check_available_funds()
    if available_funds is None:  # If available funds could not be retrieved, skip further processing
        logging.error("Unable to retrieve available funds. Skipping all orders.")
        return

    # Open the file to save order IDs (artifact for tracking placed orders)
    with open("order_ids.txt", "w") as order_file:
        # Scan the DynamoDB table for stocks that are eligible, have a valid BaseValue, and FirstDayProcessed is True
        try:
            response = table.scan(
                FilterExpression="EligibilityStatus = :status AND AdditionalQuantity > :qty",
                ExpressionAttributeValues={':status': 'Eligible', ':qty': Decimal('0')}
            )
            items = response.get('Items', [])
        except ClientError as e:
            logging.error(f"Error scanning DynamoDB table: {e}")
            return

        # Loop through each eligible stock in the DynamoDB table
        for item in items:
            instrument = item.get('InstrumentName', '')  # Fetch the stock symbol (InstrumentName)
            instrument_token = int(item.get('Token', 0))  # Fetch the stock's token for API requests
            additional_quantity = int(item.get('AdditionalQuantity', 0))  # Fetch the additional quantity
            first_day_processed = item.get('FirstDayProcessed', False)  # Check the FirstDayProcessed flag
            base_value = item.get('BaseValue', None)

            # Ensure stock is eligible, has a valid BaseValue, FirstDayProcessed is True, and AdditionalQuantity > 0
            if not first_day_processed:
                logging.info(f"Skipping {instrument} - FirstDayProcessed is False.")
                continue
            if base_value is None or Decimal(base_value) <= 0:
                logging.info(f"Skipping {instrument} - BaseValue is invalid or not greater than 0.")
                continue
            if additional_quantity == 0:
                logging.info(f"Skipping {instrument} - AdditionalQuantity is 0.")
                continue

            # Convert BaseValue to a Decimal for accurate calculations
            base_value = Decimal(base_value)

            # Fetch the current stock price from the broker's API
            current_price = get_current_price(instrument_token)
            if current_price is None:  # If the current price could not be retrieved, skip this stock
                logging.info(f"Could not fetch the current price for {instrument}. Skipping.")
                continue

            # Calculate the percentage drop between the BaseValue and the current price
            percentage_drop = calculate_percentage_drop(base_value, current_price)

            # Calculate the total cost of buying additional stocks based on the current price and quantity
            total_cost = current_price * additional_quantity

            # Handle higher percentage drops (3%, 5%, etc.)
            if percentage_drop >= 3:  # 3% drop or more
                total_cost = current_price * 3 * additional_quantity  # Update to 3x the AdditionalQuantity
                if total_cost <= available_funds:  # Check if funds are sufficient
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying 3x AdditionalQuantity ({3 * additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, 3 * additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        fetch_order_details(client, order_id)
                    available_funds -= total_cost

            elif percentage_drop >= 2:  # 2% drop or more
                total_cost = current_price * 2 * additional_quantity  # Update to 2x the AdditionalQuantity
                if total_cost <= available_funds:
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying 2x AdditionalQuantity ({2 * additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, 2 * additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        fetch_order_details(client, order_id)
                    available_funds -= total_cost

            elif percentage_drop >= 1:  # 1% drop or more
                if total_cost <= available_funds:
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying AdditionalQuantity ({additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        fetch_order_details(client, order_id)
                    available_funds -= total_cost

            else:
                logging.info(f"{instrument} is down by {percentage_drop:.2f}% - No action taken")

# Function to prepare the order details for placing an order via the broker's API
def prepare_order_details(instrument_token, quantity):
    return {
        "exchange": Vc.ExchangeTypes.NSE_EQUITY,
        "token": instrument_token,
        "transaction_type": Vc.TransactionSides.BUY,
        "product": Vc.ProductTypes.DELIVERY,
        "variety": Vc.VarietyTypes.REGULAR_MARKET_ORDER,
        "quantity": quantity,
        "price": 0.0,
        "trigger_price": 0.0,
        "disclosed_quantity": 0,
        "validity": Vc.ValidityTypes.FULL_DAY
    }

# Function to place an order via the broker's API using the prepared order details
def trigger_order_via_sdk(client, order_details):
    try:
        response = client.place_order(**order_details)  # Place order using SDK method
        logging.info(f"Order placed successfully: {response}")
        return response
    except Exception as e:
        logging.error(f"Error placing order: {str(e)}")
        return None

# Main function to run when the script is executed
if __name__ == "__main__":
    process_additional_quantity()  # Call the function to process the additional quantity logic
