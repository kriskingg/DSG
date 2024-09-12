import logging  # A Python module for logging messages during program execution
import os  # A module for interacting with the operating system, like reading environment variables
import boto3  # The AWS SDK for Python, used to interact with AWS services like DynamoDB
from vortex_api import AsthaTradeVortexAPI  # Importing custom SDK (from vortex API) to interact with the broker API
from vortex_api import Constants as Vc  # Importing constants from the vortex API to use in order placement

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
        return response['Items']  # Return the list of eligible stock items from the response
    except Exception as e:  # If any error occurs, log the error
        logging.error(f"Error fetching eligible stocks from DynamoDB: {e}")
        return []  # Return an empty list in case of failure

# Function to place an order using the SDK
def trigger_order_via_sdk(client, order_details):
    """Trigger an order using the SDK and log the response."""
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
        logging.error(f"Error during order placement: {str(e)}")
        return None

# Function to fetch the order details after placing an order
def fetch_order_details(client, order_id):
    """Fetch order details for a given order ID."""
    try:
        response = client.order_history(order_id)  # Fetch the order history based on order_id
        logging.info(f"Order Details for {order_id}: {response}")  # Log the fetched details
        return response  # Return the response for use later (e.g., for updating BaseValue)
    except Exception as e:  # Log errors if fetching details fails
        logging.error(f"Error fetching order details for {order_id}: {str(e)}")
        return None

# Function to fetch current positions (currently being fetched but not used)
def fetch_positions(client):
    """Fetch current positions."""
    try:
        response = client.positions()  # Fetch the current positions from the API
        logging.info(f"Current Positions: {response}")  # Log the current positions
    except Exception as e:  # Log errors if fetching positions fails
        logging.error(f"Error fetching positions: {str(e)}")

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
    except Exception as e:  # Log errors if the update fails
        logging.error(f"Error updating BaseValue for {instrument_name}: {str(e)}")

# The main script execution starts here
if __name__ == "__main__":
    # Fetch eligible stocks from the DynamoDB 'StockEligibility' table
    eligible_stocks = fetch_eligible_stocks_from_dynamodb()

    if not eligible_stocks:  # If no eligible stocks are found
        logging.info("No eligible stocks found.")
    else:
        # Open the file to save order IDs (artifact for tracking placed orders)
        with open("order_ids.txt", "w") as order_file:
            for stock in eligible_stocks:  # Loop through each eligible stock
                # Check if the DefaultQuantity is greater than 0 before placing an order
                default_quantity = int(stock.get('DefaultQuantity', {}).get('N', 0))
                if default_quantity == 0:  # Skip if DefaultQuantity is 0
                    logging.info(f"Skipping order placement for {stock['InstrumentName']['S']} as DefaultQuantity is 0.")
                    continue

                # Prepare the order details for placing the order
                order_details = {
                    "exchange": "NSE_EQ",  # Exchange type
                    "token": int(stock['Token']['N']),  # Stock token from DynamoDB
                    "symbol": stock['InstrumentName']['S'],  # Instrument name (stock symbol)
                    "transaction_type": "BUY",  # Always a "BUY" in this context
                    "product": "DELIVERY",  # Product type
                    "variety": "RL-MKT",  # Market order (can modify)
                    "quantity": default_quantity,  # Quantity to buy based on DynamoDB data
                    "price": 0.0,  # Market orders have 0 price
                    "trigger_price": 0.0,  # Trigger price (0 for market order)
                    "disclosed_quantity": 0,  # No disclosed quantity
                    "validity": "DAY",  # Full-day validity
                    "validity_days": 1,  # Valid for 1 day
                    "is_amo": False  # Not an after-market order
                }

                # Place the order and get the response
                response = trigger_order_via_sdk(client, order_details)
                if response:  # If the order is placed successfully
                    order_id = response['data']['orderId']  # Extract the order ID from the response
                    logging.info(f"Order placed successfully for {stock['InstrumentName']['S']}: {response}")
                    
                    # Save the order ID to the artifact file for future tracking
                    order_file.write(f"{order_id}\n")
                    
                    # Fetch the order details immediately after placing the order
                    order_details_response = fetch_order_details(client, order_id)
                    
                    # Update the BaseValue in DynamoDB with the fetched order price
                    if order_details_response and 'data' in order_details_response:
                        base_value = order_details_response['data'][0].get('order_price', 0)  # Extract the order price as the BaseValue
                        update_base_value_in_dynamodb(stock['InstrumentName']['S'], base_value)
                else:
                    logging.error(f"Order placement failed for {stock['InstrumentName']['S']}")

        # Optionally, fetch current positions after placing all orders (currently not used in logic)
        fetch_positions(client)
