import os
import sqlite3
import boto3
import logging
from dotenv import load_dotenv
from time import sleep
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
DB_FILE = "beest-orders.db"
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

def create_connection(db_file):
    """Create a database connection to SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Connected to SQLite database: {db_file}")
    except sqlite3.Error as e:
        logging.error(f"SQLite connection error: {e}")
    return conn

def create_table(conn):
    """Create orders table if it does not exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        product TEXT NOT NULL,
        ltp REAL NOT NULL,
        executed_at TEXT NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        logging.info("Orders table created or already exists.")
    except sqlite3.Error as e:
        logging.error(f"SQLite table creation error: {e}")

def insert_order(conn, order):
    """Insert a new order into the orders table."""
    insert_order_sql = """
    INSERT INTO orders(symbol, quantity, price, transaction_type, product, ltp, executed_at)
    VALUES(?, ?, ?, ?, ?, ?, datetime('now', 'localtime', '+05:30'));
    """
    try:
        cursor = conn.cursor()
        cursor.execute(insert_order_sql, order)
        conn.commit()
        logging.info("Order inserted into the orders table.")
    except sqlite3.Error as e:
        logging.error(f"SQLite insertion error: {e}")

def upload_to_s3(db_file, bucket_name):
    """Upload the database file to S3."""
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(db_file, bucket_name, db_file)
        logging.info(f"Database {db_file} uploaded to S3 bucket {bucket_name}.")
    except Exception as e:
        logging.error(f"Failed to upload {db_file} to S3: {e}")

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

def fetch_ltp_from_rupeezy(token):
    """Fetch the LTP from Rupeezy."""
    api_url = f"https://vortex.trade.rupeezy.in/data/quote?q=NSE_EQ-{token}&mode=full"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        logging.debug(f"Rupeezy LTP response: {response_json}")

        ltp_data = response_json.get('data', {}).get(f'NSE_EQ-{token}', {})
        ltp_1 = ltp_data.get('last_trade_price')
        ltp_2 = ltp_data.get('close_price')
        ltp_3 = ltp_1 if ltp_1 else ltp_2
        logging.debug(f"LTP Possibilities: ltp_1={ltp_1}, ltp_2={ltp_2}, ltp_3={ltp_3}")
        return ltp_3
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching LTP: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred while fetching LTP: {err}")
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
        logging.debug(f"Order attempt {attempt + 1} with price: {order_details['price']}")

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

        sleep(2)  # Short delay before retrying

    logging.error("All retries for order placement failed.")
    return None

def check_order_status(order_id, retries=10, delay=5):
    """Check the status of an order on Rupeezy."""
    for attempt in range(retries):
        api_url = f"https://vortex.trade.rupeezy.in/orders?limit=10&offset=1"
        access_token = get_access_token()
        if not access_token:
            logging.error("Access token is not available.")
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            logging.debug("Order status response: %s", response_json)

            orders = response_json.get('orders', [])
            for order in orders:
                if order.get('order_id') == order_id:
                    status = order.get('status')
                    if status == 'executed':
                        return True
                    elif status == 'rejected':
                        logging.error(f"Order {order_id} was rejected: {order}")
                        return False

            logging.info(f"Order {order_id} is still pending. Retrying in {delay} seconds...")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred while checking order status: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred while checking order status: {err}")

        sleep(delay)

    logging.error(f"Order {order_id} could not be confirmed after {retries} retries.")
    return False

if __name__ == '__main__':
    # Fetch data from Chartink
    data = fetch_chartink_data(condition)

    if data:
        alpha_data = [item for item in data['data'] if item['nsecode'] == 'ALPHAETF']
        
        if alpha_data:
            logging.debug(f"Filtered ALPHAETF data: {alpha_data}")
            
            # Get the current price from Rupeezy
            current_price = fetch_ltp_from_rupeezy(19640)
            if not current_price:
                logging.error("Failed to fetch LTP from Rupeezy. Exiting.")
                exit(1)
            
            logging.debug(f"LTP from Rupeezy data for ALPHAETF: {current_price}")
            
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
                logging.info(f"Order placed successfully with ID: {order_id}")
                
                # Check order status to ensure it's executed
                if check_order_status(order_id):
                    # Store the order details in the database only if the order was executed successfully
                    conn = create_connection(DB_FILE)
                    if conn is not None:
                        create_table(conn)
                        order_entry = ("ALPHAETF", order_quantity, current_price, "BUY", "DELIVERY", current_price)
                        insert_order(conn, order_entry)
                        conn.close()

                        # Upload the database to S3
                        upload_to_s3(DB_FILE, 'my-beest-db')
                    else:
                        logging.error("Failed to create the database connection.")
                else:
                    logging.error("Order was not executed successfully. Exiting.")
            else:
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHAETF data found in Chartink results. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
                     
