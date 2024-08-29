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

def insert_order_dynamodb(user_id, symbol, quantity, price, transaction_type, product, ltp):
    """Insert a new order into the DynamoDB table."""
    executed_at = get_ist_datetime()  # Get current date and time in IST
    try:
        dynamodb.put_item(
            TableName='Portfolio',
            Item={
                'UserId': {'S': user_id},
                'InstrumentId': {'S': symbol},
                'Quantity': {'N': str(quantity)},
                'Price': {'N': str(price)},
                'TransactionType': {'S': transaction_type},
                'Product': {'S': product},
                'LTP': {'N': str(ltp)},
                'ExecutedAt': {'S': executed_at}
            }
        )
        logging.info(f"Order for {symbol} inserted into DynamoDB.")
    except Exception as e:
        logging.error(f"Failed to insert item into DynamoDB: {e}")
