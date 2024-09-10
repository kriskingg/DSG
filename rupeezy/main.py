import logging
import os
import json
from time import sleep
import requests

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Version 1 - Standard request
def trigger_order_with_requests_v1(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details)}")
    try:
        response = requests.post(api_url, headers=headers, json=order_details)
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response JSON: {response.json()}")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to place order. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
    return None

# Version 2 - Use `data` instead of `json`
def trigger_order_with_requests_v2(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details)}")
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(order_details))
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response JSON: {response.json()}")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to place order. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
    return None

# Version 3 - Use URL-encoded Data
def trigger_order_with_requests_v3(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/x-www-form-urlencoded'}
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details)}")
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(order_details))
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response JSON: {response.json()}")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to place order. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
    return None

# Version 4 - Adjust `Content-Type`
def trigger_order_with_requests_v4(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/x-www-form-urlencoded'}
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details)}")
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(order_details))
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response JSON: {response.json()}")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to place order. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
    return None

# Version 5 - Simplified Headers
def trigger_order_with_requests_v5(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {'Authorization': f'Bearer {access_token}'}
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details)}")
    try:
        response = requests.post(api_url, headers=headers, json=order_details)
        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response JSON: {response.json()}")
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to place order. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
    return None

# Function to check order status (common to all versions)
def check_order_status(order_id, access_token, retries=10, delay=5):
    """Check the status of an order on Rupeezy."""
    api_url = f"https://vortex.trade.rupeezy.in/orders?limit=10&offset=1"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    for attempt in range(retries):
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
                        break
            logging.info(f"Order {order_id} is still pending. Retrying in {delay} seconds...")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred while checking order status: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred while checking order status: {err}")
        sleep(delay)
    logging.error(f"Order {order_id} could not be confirmed after {retries} retries.")
    return False

# Function to fetch trade details (common to all versions)
def fetch_trade_details(order_id, access_token):
    """Fetch the trade details for an executed order."""
    api_url = f"https://vortex.trade.rupeezy.in/trades?limit=10&offset=1"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
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

# Main Execution Logic to test all versions
if __name__ == '__main__':
    # Retrieve the access token from environment variables
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')
    logging.debug(f"Access Token: {access_token}")
    if not access_token:
        logging.error("RUPEEZY_ACCESS_TOKEN not found in environment variables. Exiting.")
        exit(1)

    # Hardcoded ALPHAETF details
    instrument_name = 'ALPHAETF'
    token = 19640  # Hardcoded token for ALPHAETF
    default_quantity = 1  # Hardcoded default quantity
    logging.info(f"Placing order for {instrument_name} with quantity {default_quantity}")
    order_details = {
        "exchange": "NSE_EQ",
        "token": token,
        "symbol": instrument_name,
        "transaction_type": "BUY",
        "product": "DELIVERY",
        "variety": "RL-MKT",
        "quantity": default_quantity,
        "price": 0.00,
        "trigger_price": 0.00,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "validity_days": 1,
        "is_amo": False
    }

    # Test each version
    for version in range(1, 6):
        logging.info(f"\n\nTesting Version {version}")
        trigger_function = globals()[f'trigger_order_with_requests_v{version}']
        response = trigger_function(order_details, access_token)
        if response and response.get('status') == 'success':
            order_id = response['data'].get('orderId')
            logging.info(f"Order placed successfully with ID: {order_id}")
            if check_order_status(order_id, access_token):
                trade_details = fetch_trade_details(order_id, access_token)
                if trade_details:
                    executed_price = trade_details.get('trade_price')
                    logging.info(f"Order executed at price: {executed_price}")
                else:
                    logging.error("Failed to fetch trade details. Exiting.")
            else:
                logging.error("Order was not executed successfully. Exiting.")
        else:
            logging.error(f"Failed to place order for {instrument_name}. Response: {response}")
