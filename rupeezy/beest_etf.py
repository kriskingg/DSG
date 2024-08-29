import requests
import logging
from auth import get_access_token
from time import sleep

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
                        return True
                    elif status == 'REJECTED':
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
