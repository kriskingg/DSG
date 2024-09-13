import logging  # Python's built-in module for logging events and debugging messages
import boto3  # AWS SDK for Python to interact with AWS services (in this case, DynamoDB)
from decimal import Decimal  # Module to handle decimal numbers for accuracy in currency values
from vortex_api import AsthaTradeVortexAPI, Constants as Vc  # Broker API SDK and constants
import os  # Required for fetching environment variables
from botocore.exceptions import ClientError  # Import ClientError for DynamoDB exceptions

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

# Ensure the environment variables are properly set
if not api_secret or not application_id or not access_token:
    logging.error("API credentials not properly set in environment variables")
    exit(1)

# Create an instance of the AsthaTradeVortexAPI client with the fetched credentials
client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token  # Set the access token for making authenticated API requests

# Function to fetch the current stock price using the instrument token via the broker's API
# Function to fetch the current stock price using the instrument token via the broker's API
def get_current_price(instrument_token):
    try:
        # Call the broker's API to get the Last Traded Price (LTP) for the given stock token
        response = client.quotes([f"NSE_EQ-{instrument_token}"], mode=Vc.QuoteModes.LTP)
        
        # Log the full response from the quotes API, including the structure
        logging.debug(f"Full response from quotes API for token {instrument_token}: {response}")
        
        # Check if 'data' and 'ltp' are present in the response, log any missing keys
        if 'data' not in response or not response['data']:
            logging.error(f"Missing 'data' in response for token {instrument_token}: {response}")
            return None
        
        # Fetch the LTP (Last Traded Price) from the response
        ltp = response['data'][0].get('ltp', 0)
        
        # If LTP is 0, log it and return None
        if ltp == 0:
            logging.error(f"Received LTP as 0 for token {instrument_token}: {response}")
            return None
        
        return Decimal(ltp)  # Return the LTP as a Decimal
    except Exception as e:  # Handle and log any errors encountered during the API call
        logging.error(f"Error fetching current price for token {instrument_token}: {str(e)}")
        return None  # Return None if the API call fails

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

# Main function to process stocks for additional quantity logic based on percentage drop
def process_additional_quantity():
    # Fetch available funds first by calling the broker API
    available_funds = check_available_funds()
    if available_funds is None:  # If available funds could not be retrieved, skip further processing
        logging.error("Unable to retrieve available funds. Skipping all orders.")
        return

    # Scan the DynamoDB table for stocks that are eligible and have AdditionalQuantity > 0
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

        # Check if the stock has a valid BaseValue (initial purchase price), and skip if not
        base_value = item.get('BaseValue', None)
        if base_value is None or Decimal(base_value) <= 0:
            logging.info(f"{instrument} does not have a valid BaseValue. Skipping.")
            continue  # Skip this stock if there's no valid BaseValue

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

        # Check if the available funds are sufficient for the calculated total cost
        if percentage_drop >= 2:  # If the price has dropped by 2% or more
            total_cost = current_price * 2 * additional_quantity  # Update the total cost for 2x additional quantity
            if total_cost <= available_funds:  # If funds are sufficient, place the order
                logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying twice the AdditionalQuantity ({2 * additional_quantity} units)")
                trigger_order_via_sdk(client, prepare_order_details(instrument_token, 2 * additional_quantity))
                available_funds -= total_cost  # Deduct the cost from available funds after placing the order
            else:
                # Log a warning if there are not enough funds to place the order
                logging.warning(f"Not enough funds to buy twice the AdditionalQuantity for {instrument}. Available: {available_funds}, Required: {total_cost}")

        elif percentage_drop >= 1:  # If the price has dropped by 1% or more
            if total_cost <= available_funds:  # If funds are sufficient, place the order
                logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying the AdditionalQuantity ({additional_quantity} units)")
                trigger_order_via_sdk(client, prepare_order_details(instrument_token, additional_quantity))
                available_funds -= total_cost  # Deduct the cost from available funds after placing the order
            else:
                # Log a warning if there are not enough funds to place the order
                logging.warning(f"Not enough funds to buy the AdditionalQuantity for {instrument}. Available: {available_funds}, Required: {total_cost}")
        else:
            # If the percentage drop is less than 1%, log a message and take no action
            logging.info(f"{instrument} is down by {percentage_drop:.2f}% - No action taken")

# Function to prepare the order details for placing an order via the broker's API
def prepare_order_details(instrument_token, quantity):
    # Return a dictionary containing all the necessary details for placing a market order
    return {
        "exchange": "NSE_EQ",  # Specify the exchange (NSE Equity)
        "token": instrument_token,  # Stock token for identifying the stock
        "transaction_type": "BUY",  # Specify the transaction type (Buy order)
        "product": "DELIVERY",  # Specify the product type (Delivery)
        "variety": "RL-MKT",  # Specify the order variety (Market order)
        "quantity": quantity,  # The number of stocks to buy
        "price": 0.0,  # Set the price to 0 for market orders
        "trigger_price": 0.0,  # No trigger price needed for market orders
        "disclosed_quantity": 0,  # No disclosed quantity
        "validity": "DAY",  # Specify that the order is valid for the day
        "validity_days": 1,  # The order is valid for 1 day
        "is_amo": False  # The order is not an after-market order
    }

# Function to place an order via the broker's API using the prepared order details
def trigger_order_via_sdk(client, order_details):
    try:
        # Place the order via the broker's API
        response = client.place_order(**order_details)
        logging.info(f"Order placed successfully: {response}")  # Log the response from the API
    except Exception as e:  # Handle and log any errors encountered during the order placement
        logging.error(f"Error placing order: {str(e)}")

# Main function to run when the script is executed
if __name__ == "__main__":
    process_additional_quantity()  # Call the function to process the additional quantity logic
