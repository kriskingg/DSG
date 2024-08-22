import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
from datetime import datetime
import pytz
import sqlite3
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants for Chartink
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

# Load API Key and AWS credentials from environment variables
YOUR_API_KEY = os.getenv('YOUR_API_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

# S3 Bucket configuration
S3_BUCKET_NAME = 'my-beest-db'
DB_FILE_NAME = 'beest-orders.db'

# Initialize the S3 client
logging.debug(f"Using AWS region: {AWS_DEFAULT_REGION}")

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

def init_db():
    """Initialize SQLite database."""
    try:
        if not os.path.exists(DB_FILE_NAME):
            logging.debug("Database file does not exist. Creating a new one.")
            conn = sqlite3.connect(DB_FILE_NAME)
            c = conn.cursor()
            # Create orders table if it does not exist
            c.execute('''CREATE TABLE IF NOT EXISTS orders
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          symbol TEXT,
                          quantity INTEGER,
                          price REAL,
                          order_type TEXT,
                          product TEXT,
                          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
            conn.close()
            logging.debug("Database initialized successfully.")
        else:
            logging.debug("Database file already exists.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred during initialization: {e}")

def get_access_token():
    """Read access token from the file."""
    try:
        with open('./token/access_token.txt', 'r') as file:
            token = file.read().strip()
            if token:
                logging.debug(f"Access token retrieved: '{token}'")
            else:
                logging.error("Access token is empty.")
            return token
    except FileNotFoundError:
        logging.error("access_token.txt file not found.")
        return None
    except Exception as e:
        logging.error(f"Error reading access token: {e}")
        return None

def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                logging.debug("Headers: {}".format(s.headers))
                r = s.get(Charting_Link)
                logging.debug("GET request to Charting_Link status code: {}".format(r.status_code))
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})
                logging.debug("CSRF Token: {}".format(csrf_token))
                logging.debug("Scan Condition: {}".format(condition))
                response = s.post(Charting_url, data={'scan_clause': condition})
                logging.debug("POST request to Charting_url status code: {}".format(response.status_code))
                logging.debug("Request Data: {}".format({'scan_clause': condition}))
                response_json = response.json()
                logging.debug("Response JSON: {}".format(response_json))
                if response.status_code == 200:
                    return response_json
                else:
                    logging.error("Failed to fetch data with status code: {}".format(response.status_code))
        except Exception as e:
            logging.error("Exception during data fetch: {}".format(str(e)))
        sleep(10)  # wait before retrying
    logging.error("All retries failed")
    return None

def fetch_latest_ltp(symbol_token):
    """Fetch the latest LTP for the given symbol token."""
    api_url = f"https://vortex.trade.rupeezy.in/data/quote?q=NSE_EQ-{symbol_token}&mode=full"
    access_token = get_access_token()
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

def check_order_status(order_id, retries=20, delay=10):
    """Check the status of an order by fetching the order book until it is no longer pending."""
    api_url = "https://vortex.trade.rupeezy.in/orders"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries):
        try:
            response = requests.get(api_url, headers=headers, params={"limit": 10, "offset": 1})
            response.raise_for_status()
            response_json = response.json()
            logging.debug("Order book response: %s", response_json)

            # Look for the specific order by order_id in the order book
            orders = response_json.get('data', [])
            for order in orders:
                if order.get('orderId') == order_id:
                    status = order.get('status')
                    logging.debug(f"Found order {order_id} with status: {status}")
                    if status != 'pending':
                        return order
                    break
            else:
                logging.info(f"Order {order_id} is not in the order book or still pending. Retrying...")

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred while checking order status: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred while checking order status: {err}")

        sleep(delay)

    logging.error(f"Order {order_id} did not complete after {retries} attempts.")
    return None

def trigger_order_on_rupeezy(order_details, retries=10):
    """Trigger an order on Rupeezy with retry logic."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = get_access_token()
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

def store_order(order_details):
    """Store order details in SQLite database."""
    retries = 5
    while retries > 0:
        try:
            conn = sqlite3.connect(DB_FILE_NAME)
            c = conn.cursor()
            logging.debug(f"Storing order: {order_details}")
            
            # Convert current time to IST
            ist = pytz.timezone('Asia/Kolkata')
            ist_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

            # Insert order details into the orders table
            c.execute("""
                INSERT INTO orders (symbol, quantity, price, order_type, product, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_details['symbol'],
                order_details['quantity'],
                order_details['price'],
                order_details['transaction_type'],  # Ensure this matches the correct key
                order_details['product'],
                ist_time
            ))
            conn.commit()
            conn.close()
            logging.debug("Order stored successfully.")
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                retries -= 1
                sleep(1)
                logging.warning(f"Database is locked, retrying {retries} more times")
            else:
                logging.error(f"SQLite error occurred: {e}")
                break
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            break

def get_first_day_price():
    """Get the first day order price from the database."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        c.execute("SELECT price FROM orders WHERE symbol = 'ALPHAETF' ORDER BY timestamp ASC LIMIT 1")
        result = c.fetchone()
        conn.close()
        if result:
            return result[0]
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")
    return None

def get_last_order_quantity():
    """Get the quantity of the last order placed for ALPHAETF."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        c.execute("SELECT quantity FROM orders WHERE symbol = 'ALPHAETF' ORDER BY timestamp DESC LIMIT 1")
        result = c.fetchone()
        conn.close()
        if result:
            return result[0]
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")
    return 1

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
                order_id = response['data'].get('orderId')
                order_status_response = check_order_status(order_id)
                if order_status_response and order_status_response.get('status') != 'pending':
                    order_details['price'] = order_status_response.get('price', current_price)  # Update with the actual price from response
                    store_order(order_details)
                    logging.info(f"Order executed successfully. Response: {order_status_response}")
                    # Upload the updated database back to S3
                    upload_db_to_s3()
                else:
                    logging.error(f"Order {order_id} did not execute successfully. Final status: {order_status_response}")
            else:
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHAETF data found. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
