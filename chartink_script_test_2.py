import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
from datetime import datetime
import pytz
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants for Chartink
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

# Load API Key from environment variables
RUPEEZY_API_KEY = os.getenv('RUPEEZY_API_KEY')

if RUPEEZY_API_KEY:
    logging.debug("RUPEEZY_API_KEY is set.")
else:
    logging.error("RUPEEZY_API_KEY is not set.")

def get_access_token():
    """Read access token from the file."""
    try:
        with open('access_token.txt', 'r') as file:
            return file.read().strip()
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

def trigger_order_on_rupeezy(order_details):
    """Trigger an order on Rupeezy."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {order_details}")

    try:
        response = requests.post(api_url, json=order_details, headers=headers)
        response.raise_for_status()
        logging.debug("Order response: %s", response.json())
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")

def init_db():
    """Initialize SQLite database."""
    try:
        conn = sqlite3.connect('orders.db')
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
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")

def store_order(order_details):
    """Store order details in SQLite database."""
    retries = 5
    while retries > 0:
        try:
            conn = sqlite3.connect('orders.db')
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
        conn = sqlite3.connect('orders.db')
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
        conn = sqlite3.connect('orders.db')
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
    init_db()  # Initialize the database

    data = fetch_chartink_data(condition)

    if data:
        alpha_etf_data = [item for item in data['data'] if item['nsecode'] == 'ALPHAETF']
        
        if alpha_etf_data:
            logging.debug(f"Filtered ALPHAETF data: {alpha_etf_data}")
            
            # Get the first day's order price
            first_day_price = get_first_day_price()
            last_order_quantity = get_last_order_quantity()
            current_price = alpha_etf_data[0]['close']
            
            order_quantity = 1  # Default quantity
            
            if first_day_price and current_price <= first_day_price * 0.99:
                order_quantity = last_order_quantity * 2  # Double the quantity

            # Place the order
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
                store_order(order_details)
                logging.info(f"Order placed successfully. Response: {response}")
            else:
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHAETF data found. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
