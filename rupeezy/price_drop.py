# Key Points:
# EligibilityStatus = "Eligible": Only stocks marked as eligible are processed for additional orders.
# FirstDayProcessed = True: The stock must have passed the first-day order condition before considering additional purchases.
# BaseValue > 0: Ensures the stock has a valid base price to calculate the percentage drop for subsequent buys.
# AdditionalQuantity > 0: This check skips any stock that does not require additional quantities, preventing orders where the extra purchase count is set to zero.
# This ensures there are no contradictions or unnecessary actions taken. Only eligible stocks with valid BaseValue, having passed the first-day order, and with a non-zero AdditionalQuantity, are considered for further orders based on price drops.

import logging
import boto3
from decimal import Decimal, ROUND_HALF_UP
from vortex_api import AsthaTradeVortexAPI, Constants as Vc
import os
from botocore.exceptions import ClientError
import time

# Set up basic logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize a connection to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('StockEligibility')

# Initialize the broker API client
api_secret = os.getenv('RUPEEZY_API_KEY')
application_id = os.getenv('RUPEEZY_APPLICATION_ID')
access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')

if not api_secret or not application_id or not access_token:
    logging.error("API credentials are missing. Exiting script.")
    exit(1)

client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token

# Function to fetch the current stock price
def get_current_price(instrument_token):
    retries = 3
    delay = 5
    for attempt in range(retries):
        try:
            response = client.quotes([f"NSE_EQ-{instrument_token}"], mode=Vc.QuoteModes.LTP)
            logging.debug(f"Full response from quotes API for token {instrument_token}: {response}")
            if 'data' not in response or f"NSE_EQ-{instrument_token}" not in response['data']:
                logging.error(f"Missing data or token key in response for token {instrument_token}: {response}")
                return None
            ltp = response['data'][f"NSE_EQ-{instrument_token}"].get('last_trade_price', 0)
            if ltp == 0:
                logging.error(f"Received LTP as 0 for token {instrument_token}: {response}")
                return None
            price = Decimal(ltp).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return price
        except Exception as e:
            logging.error(f"Error fetching current price for token {instrument_token}: {str(e)}. Attempt {attempt + 1} of {retries}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None

# Function to check available funds
def check_available_funds():
    try:
        response = client.funds()
        logging.debug(f"Full response from funds API: {response}")
        available_funds = Decimal(response.get('nse', {}).get('net_available', 0))
        return available_funds
    except Exception as e:
        logging.error(f"Error fetching available funds: {str(e)}")
        return None

# Function to calculate percentage drop
def calculate_percentage_drop(base_value, current_price):
    return ((base_value - current_price) / base_value) * 100

# Function to fetch order details with retry logic
def fetch_order_details_with_retry(client, order_id):
    retries = 3
    delay = 5
    for attempt in range(retries):
        try:
            response = client.order_history(order_id)
            logging.info(f"Order Details for {order_id}: {response}")
            return response
        except Exception as e:
            logging.error(f"Error fetching order details for {order_id}: {str(e)}. Attempt {attempt + 1} of {retries}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None

# Function to update BaseValue in DynamoDB
def update_base_value_in_dynamodb(instrument_name, base_value):
    try:
        table.update_item(
            Key={'InstrumentName': instrument_name},
            UpdateExpression="SET BaseValue = :bv",
            ExpressionAttributeValues={':bv': Decimal(base_value)}
        )
        logging.info(f"Updated BaseValue for {instrument_name} to {base_value}.")
    except Exception as e:
        logging.error(f"Error updating BaseValue for {instrument_name}: {str(e)}")

# Main function to process additional quantity logic
def process_additional_quantity():
    available_funds = check_available_funds()
    if available_funds is None:
        logging.error("Unable to retrieve available funds. Skipping all orders.")
        return

    with open("order_ids.txt", "w") as order_file:
        try:
            response = table.scan(
                FilterExpression="EligibilityStatus = :status AND AdditionalQuantity > :qty",
                ExpressionAttributeValues={':status': 'Eligible', ':qty': Decimal('0')}
            )
            items = response.get('Items', [])
        except ClientError as e:
            logging.error(f"Error scanning DynamoDB table: {e}")
            return

        for item in items:
            instrument = item.get('InstrumentName', '')
            instrument_token = int(item.get('Token', 0))
            additional_quantity = int(item.get('AdditionalQuantity', 0))
            first_day_processed = item.get('FirstDayProcessed', False)
            base_value = item.get('BaseValue', None)

            if not first_day_processed:
                logging.info(f"Skipping {instrument} - FirstDayProcessed is False.")
                continue
            if base_value is None or Decimal(base_value) <= 0:
                logging.info(f"Skipping {instrument} - BaseValue is invalid or not greater than 0.")
                continue
            if additional_quantity == 0:
                logging.info(f"Skipping {instrument} - AdditionalQuantity is 0.")
                continue

            base_value = Decimal(base_value)
            current_price = get_current_price(instrument_token)
            if current_price is None:
                logging.info(f"Could not fetch the current price for {instrument}. Skipping.")
                continue

            percentage_drop = calculate_percentage_drop(base_value, current_price)
            total_cost = current_price * additional_quantity

            if percentage_drop >= 3:
                total_cost = current_price * 3 * additional_quantity
                if total_cost <= available_funds:
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying 3x AdditionalQuantity ({3 * additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, 3 * additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        order_details_response = fetch_order_details_with_retry(client, order_id)
                        if order_details_response:
                            executed_price = order_details_response['data'][0].get('order_price', None)
                            if executed_price:
                                update_base_value_in_dynamodb(instrument, executed_price)
                    available_funds -= total_cost

            elif percentage_drop >= 2:
                total_cost = current_price * 2 * additional_quantity
                if total_cost <= available_funds:
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying 2x AdditionalQuantity ({2 * additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, 2 * additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        order_details_response = fetch_order_details_with_retry(client, order_id)
                        if order_details_response:
                            executed_price = order_details_response['data'][0].get('order_price', None)
                            if executed_price:
                                update_base_value_in_dynamodb(instrument, executed_price)
                    available_funds -= total_cost

            elif percentage_drop >= 1:
                if total_cost <= available_funds:
                    logging.info(f"{instrument} is down by {percentage_drop:.2f}% - Buying AdditionalQuantity ({additional_quantity} units)")
                    response = trigger_order_via_sdk(client, prepare_order_details(instrument_token, additional_quantity))
                    if response:
                        order_id = response['data']['orderId']
                        order_file.write(f"{order_id}\n")
                        time.sleep(5)
                        order_details_response = fetch_order_details_with_retry(client, order_id)
                        if order_details_response:
                            executed_price = order_details_response['data'][0].get('order_price', None)
                            if executed_price:
                                update_base_value_in_dynamodb(instrument, executed_price)
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
        response = client.place_order(**order_details)
        logging.info(f"Order placed successfully: {response}")
        return response
    except Exception as e:
        logging.error(f"Error placing order: {str(e)}")
        return None

# Main function to run when the script is executed
if __name__ == "__main__":
    process_additional_quantity()
