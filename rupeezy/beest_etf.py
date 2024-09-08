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

import requests
import logging
from auth import get_access_token
from time import sleep  # Import the sleep function

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def trigger_order_on_rupeezy(order_details):
    """Trigger an order on Rupeezy."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = get_access_token()
    if not access_token:
        logging.error("Access token is not available.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=order_details, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        logging.debug("Order response: %s", response_json)

        if response_json.get('status') == 'success':
            logging.info(f"Market order successfully placed with price: {order_details['price']}")
            return response_json
        else:
            logging.error(f"Order placement failed: {response_json}")
            return None
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred during order placement: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred during order placement: {err}")

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
                    if status == 'EXECUTED':
                        logging.info(f"Order {order_id} has been executed.")
                        return True
                    elif status in ['REJECTED', 'ADMINREJECT']:
                        logging.error(f"Order {order_id} was rejected: {order.get('error_reason', 'Unknown reason')}")
                        return False
                    elif status == 'PENDING':
                        logging.info(f"Order {order_id} is still pending.")
                        # Explicit pending status check
                        break

            logging.info(f"Order {order_id} is still pending. Retrying in {delay} seconds...")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred while checking order status: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred while checking order status: {err}")

        sleep(delay)

    logging.error(f"Order {order_id} could not be confirmed after {retries} retries.")
    return False

def fetch_trade_details(order_id):
    """Fetch the trade details for an executed order."""
    api_url = f"https://vortex.trade.rupeezy.in/trades?limit=10&offset=1"
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
        logging.debug("Trade details response: %s", response_json)

        trades = response_json.get('trades', [])
        for trade in trades:
            if trade.get('order_id') == order_id:
                return trade

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching trade details: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred while fetching trade details: {err}")

    return None
