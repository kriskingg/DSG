# Beest Main Flow:
# GitHub Actions Workflow (Trade_Script_with_DB_and_S3.yml):
# The workflow is either manually triggered or runs on a schedule.
# Environment setup: Python and dependencies are installed.
# Access Token Handling: The access token is downloaded and set as an environment variable without using rupeezy/auth.py.
# Running main.py:
# Order Placement: The script defines the order details and places an order using trigger_order_on_rupeezy.
# Order Status Check: The script checks the order status using check_order_status.
# Fetch Trade Details: If the order is successful, trade details are fetched using fetch_trade_details.
# Data Storage:
# The order details are stored in DynamoDB using insert_order_dynamodb.

import boto3
import logging
from datetime import datetime
import pytz

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')

def get_ist_datetime():
    """Get the current date and time in IST."""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

def insert_order_dynamodb(user_id, instrument_id, quantity, price, transaction_type, product, ltp):
    """Insert a new order into the DynamoDB table."""
    executed_at = get_ist_datetime()  # Get current date and time in IST
    try:
        dynamodb.put_item(
            TableName='Portfolio',
            Item={
                'UserId': {'S': user_id},
                'InstrumentId': {'S': instrument_id},
                'ExecutedAt': {'S': executed_at},
                'LTP': {'N': str(ltp)},
                'Price': {'N': str(price)},
                'Product': {'S': product},
                'Quantity': {'N': str(quantity)},
                'TransactionType': {'S': transaction_type}
            }
        )
        logging.info(f"Order for {instrument_id} inserted into DynamoDB.")
    except Exception as e:
        logging.error(f"Failed to insert item into DynamoDB: {e}")

# Example usage (for testing):
if __name__ == "__main__":
    insert_order_dynamodb(
        user_id="user123",
        instrument_id="ALPHAETF",
        quantity=1,
        price=100.50,
        transaction_type="BUY",
        product="DELIVERY",
        ltp=100.50
    )
