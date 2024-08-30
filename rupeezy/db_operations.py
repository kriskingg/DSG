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
