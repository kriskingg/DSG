import os
import requests
import sqlite3
import logging
from time import sleep
from datetime import datetime
import pytz
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
S3_BUCKET_NAME = 'my-beest-db'
DB_FILE_NAME = 'beest-orders.db'

# AWS credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def validate_s3_access():
    """Validate access to the S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' in response:
            logging.info(f"Successfully accessed S3 bucket {S3_BUCKET_NAME}.")
        else:
            logging.warning(f"S3 bucket {S3_BUCKET_NAME} is empty or not accessible.")
    except ClientError as e:
        logging.error(f"Failed to access S3 bucket {S3_BUCKET_NAME}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error occurred while accessing S3 bucket: {e}")

def init_db():
    """Initialize SQLite database and validate S3 access."""
    try:
        validate_s3_access()
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS orders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      symbol TEXT,
                      quantity INTEGER,
                      price REAL,
                      order_type TEXT,
                      product TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                      status TEXT)''')
        conn.commit()
        conn.close()
        logging.debug("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred during initialization: {e}")

def store_order(order_details, status):
    """Store order details in SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        ist = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

        c.execute("""
            INSERT INTO orders (symbol, quantity, price, order_type, product, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_details['symbol'],
            order_details['quantity'],
            order_details['price'],
            order_details['transaction_type'],  # Make sure this matches the key in your order details
            order_details['product'],
            ist_time,
            status
        ))
        conn.commit()
        conn.close()
        logging.debug("Order stored successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred while storing order: {e}")

def upload_db_to_s3():
    """Upload the SQLite database to S3."""
    try:
        logging.debug("Starting upload of the database to S3...")
        s3_client.upload_file(DB_FILE_NAME, S3_BUCKET_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} uploaded to S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 upload: {e}")
    except ClientError as e:
        logging.error(f"Failed to upload {DB_FILE_NAME} to S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {e}")

def download_db_from_s3():
    """Download the SQLite database from S3."""
    try:
        logging.debug("Starting download of the database from S3...")
        s3_client.download_file(S3_BUCKET_NAME, DB_FILE_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} downloaded from S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 download: {e}")
    except ClientError as e:
        logging.error(f"Failed to download {DB_FILE_NAME} from S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 download: {e}")

def fetch_latest_ltp(symbol_token):
    """Fetch the latest LTP for the given symbol token."""
    api_url = f"https://vortex.trade.rupeezy.in/data/quote?q=NSE_EQ-{symbol_token}&mode=full"
    access_token = os.getenv('ACCESS_TOKEN')
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        ltp = response_json['data'][0]['ltp']
        logging.debug(f"Fetched LTP for token {symbol_token}: {ltp}")
        return ltp
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching LTP: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred while fetching LTP: {err}")
    return None

def trigger_order_on_rupeezy(order_details, retries=10):
    """Trigger an order on Rupeezy with retry logic."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = os.getenv('ACCESS_TOKEN')
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries):
        ltp = fetch_latest_ltp(order_details['token'])
        if ltp and ltp <= order_details['price']:
            order_details['price'] = ltp
            logging.debug(f"Order attempt {attempt + 1} with LTP: {ltp}")

            try:
                response = requests.post(api_url, json=order_details, headers=headers)
                response.raise_for_status()
                response_json = response.json()
                logging.debug("Order response: %s", response_json)

                if response_json.get('status') == 'success':
                    return response_json
                else:
                    logging.error(f"Order failed on attempt {attempt + 1}: {response_json}")
            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred during order attempt {attempt + 1}: {http_err}")
            except Exception as err:
                logging.error(f"Other error occurred during order attempt {attempt + 1}: {err}")
        else:
            logging.info(f"LTP {ltp} is higher than order price. Retrying...")
        sleep(2)  # Short delay before retrying

    logging.error("All retries for order placement failed.")
    return None

if __name__ == '__main__':
    # Validate S3 access before starting
    validate_s3_access()

    # Download the database from S3 before starting
    download_db_from_s3()

    # Initialize the database
    init_db()

    # Fetch data from Chartink
    data = fetch_chartink_data(condition)

    if data:
        alpha_etf_data = [item for item in data['data'] if item['nsecode'] == 'ALPHAETF']
        
        if alpha_etf_data:
            logging.debug(f"Filtered ALPHAETF data: {alpha_etf_data}")
            
            # Get the current price from the data
            current_price = alpha_etf_data[0]['close']
            
            order_quantity = 1  # Default quantity
            
            order_details = {
                "exchange": "NSE_EQ",
                "token": 19640,  # Token number for ALPHAETF.
                "symbol": "ALPHAETF",
                "transaction_type": "BUY",
                "product": "DELIVERY",
                "variety": "RL",
                "quantity": order_quantity,
                "price": current_price,
                "trigger_price": 0.00,
                "disclosed_quantity": 0,
                "validity": "DAY",
                "validity_days": 1,
                "is_amo": False
            }
            
            response = trigger_order_on_rupeezy(order_details)
            if response and response.get('status') == 'success':
                order_details['price'] = response['data'].get('price', current_price)  # Update with the actual price from response
                store_order(order_details, status="SUCCESS")
                logging.info(f"Order placed successfully. Response: {response}")
                # Upload the updated database back to S3
                upload_db_to_s3()
            else:
                store_order(order_details, status="FAILED")
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHAETF data found. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
