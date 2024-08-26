import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
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
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

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
                        logging.info(f"Order {order_id} status is {status}.")
                        return order
                    break
            else:
                logging.info(f"Order {order_id} is still pending. Retrying...")

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

if __name__ == '__main__':
    # Fetch data from Chartink
    data = fetch_chartink_data(condition)

    if data:
        alpha_data = [item for item in data['data'] if item['nsecode'] == 'ALPHA']
        
        if alpha_data:
            logging.debug(f"Filtered ALPHA data: {alpha_data}")
            
            # Get the current price from the Chartink data directly
            current_price = alpha_data[0]['close']
            logging.debug(f"LTP from Chartink data for ALPHA: {current_price}")
            
            order_quantity = 1  # Default quantity
            
            order_details = {
                "exchange": "NSE_EQ",
                "token": 7412,  # Token number for ALPHA.
                "symbol": "ALPHA",
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
                    logging.info(f"Order executed successfully. Response: {order_status_response}")
                else:
                    logging.error(f"Order {order_id} did not execute successfully. Final status: {order_status_response}")
            else:
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHA data found in Chartink results. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
