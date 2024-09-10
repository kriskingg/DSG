import logging
import subprocess
import json
from time import sleep  # Import the sleep function

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def trigger_order_with_curl(order_details):
    """Trigger an order on Rupeezy using curl."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    access_token = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjYwMjE4MDAsImlhdCI6MTcyNTk1Mjc4OSwiaXNzIjoiQXN0aGFUcmFkZSIsInN1YiI6IkFJNjM2NyIsImRldmljZUlkIjoiYXBpLWNsaWVudCIsImFwcGxpY2F0aW9uSWQiOiJkZXZfM3NLNURaRFIiLCJpcCI6IjEzLjIwMC4xNDEuNjUiLCJzY29wZSI6InByb2ZpbGUucmVhZCxvcmRlcnMucmVhZCxvcmRlcnMud3JpdGUsaG9sZGluZ3MucmVhZCxwb3NpdGlvbnMucmVhZCxwb3NpdGlvbnMud3JpdGUsZnVuZHMucmVhZCx0cmFkZXMucmVhZCxtYXJnaW5zLnJlYWQsZGF0YS5yZWFkIiwiY2xpZW50X2NvZGUiOiJBSTYzNjciLCJzb3VyY2UiOiJhcGlfYXV0aCIsInBvYSI6dHJ1ZSwidG9rZW5fdHlwZSI6InZvcnRleF92MyIsIm9zIjoiIiwiZGV2aWNlSW5mbyI6IiJ9.BIAyTcWgkJ0rV5XHAWvIq1Rv66LTTe3UXGwUSGielHztwiGQA3aDrlT9ddbLADX4MmkdGSrPRjNZqAJhbR456GqiFC01v71DRqMYdFdYETxdYmI5GgA5ItS7qdD9KOFRtoAL68BYxolVBtGdMAHhNBefmw1qVHyowCTZqb3fLFoJliSPRzsVTSCxWBcfsFbShnFgo8ITfBEi560wTkT_qhn8hHnP2ohE80zu48SznfbDnKLzZ50F9Rdql_rsBQCMn-xmbas2Xu_riDMNKfvaR39CNS6CuOAsSz10Sn1Svk8f1BrJ-s_jd3GxkoZsol657HFfqqvqX_rYhecOp5Ha1tMbKVzwZq51zIwNaIzA7RgbWFy4oXiFlgHgfZOOO8hxxoe1xJZujdydvbziFQmTFsRwnW1nhFK5snn-s1dhuDNYEvKFFAYnrEg_Sjatbj5ruk0LhtlW557Ef4uoyqNvYhEFNGg591X45ahU06F7Us6kWXMJ08wAafI6340c7YCc"

    # Construct curl command
    curl_command = [
        'curl', '--location', api_url,
        '--header', f'Authorization: Bearer {access_token}',
        '--header', 'Content-Type: application/json',
        '--data', json.dumps(order_details)
    ]

    # Log the curl command for debugging
    logging.debug(f"Curl Command: {' '.join(curl_command)}")
    
    try:
        # Execute the curl command and capture the output
        result = subprocess.run(curl_command, capture_output=True, text=True)

        # Log the result of the curl command
        logging.debug(f"Curl Output: {result.stdout}")

        if result.returncode == 0:
            response_json = json.loads(result.stdout)
            logging.debug(f"Order Response: {response_json}")
            return response_json
        else:
            logging.error(f"Curl failed with exit code {result.returncode}. Error: {result.stderr}")
    except Exception as e:
        logging.error(f"Error during order placement with curl: {str(e)}")
    
    return None

def check_order_status(order_id, access_token, retries=10, delay=5):
    """Check the status of an order on Rupeezy."""
    for attempt in range(retries):
        api_url = f"https://vortex.trade.rupeezy.in/orders?limit=10&offset=1"
        
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
                        break

            logging.info(f"Order {order_id} is still pending. Retrying in {delay} seconds...")
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred while checking order status: {http_err}")
        except Exception as err:
            logging.error(f"Other error occurred while checking order status: {err}")

        sleep(delay)

    logging.error(f"Order {order_id} could not be confirmed after {retries} retries.")
    return False

def fetch_trade_details(order_id, access_token):
    """Fetch the trade details for an executed order."""
    api_url = f"https://vortex.trade.rupeezy.in/trades?limit=10&offset=1"
    
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

if __name__ == '__main__':
    # Hardcoded ALPHAETF details and token
    access_token = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjYwMjE4MDAsImlhdCI6MTcyNTk1Mjc4OSwiaXNzIjoiQXN0aGFUcmFkZSIsInN1YiI6IkFJNjM2NyIsImRldmljZUlkIjoiYXBpLWNsaWVudCIsImFwcGxpY2F0aW9uSWQiOiJkZXZfM3NLNURaRFIiLCJpcCI6IjEzLjIwMC4xNDEuNjUiLCJzY29wZSI6InByb2ZpbGUucmVhZCxvcmRlcnMucmVhZCxvcmRlcnMud3JpdGUsaG9sZGluZ3MucmVhZCxwb3NpdGlvbnMucmVhZCxwb3NpdGlvbnMud3JpdGUsZnVuZHMucmVhZCx0cmFkZXMucmVhZCxtYXJnaW5zLnJlYWQsZGF0YS5yZWFkIiwiY2xpZW50X2NvZGUiOiJBSTYzNjciLCJzb3VyY2UiOiJhcGlfYXV0aCIsInBvYSI6dHJ1ZSwidG9rZW5fdHlwZSI6InZvcnRleF92MyIsIm9zIjoiIiwiZGV2aWNlSW5mbyI6IiJ9.BIAyTcWgkJ0rV5XHAWvIq1Rv66LTTe3UXGwUSGielHztwiGQA3aDrlT9ddbLADX4MmkdGSrPRjNZqAJhbR456GqiFC01v71DRqMYdFdYETxdYmI5GgA5ItS7qdD9KOFRtoAL68BYxolVBtGdMAHhNBefmw1qVHyowCTZqb3fLFoJliSPRzsVTSCxWBcfsFbShnFgo8ITfBEi560wTkT_qhn8hHnP2ohE80zu48SznfbDnKLzZ50F9Rdql_rsBQCMn-xmbas2Xu_riDMNKfvaR39CNS6CuOAsSz10Sn1Svk8f1BrJ-s_jd3GxkoZsol657HFfqqvqX_rYhecOp5Ha1tMbKVzwZq51zIwNaIzA7RgbWFy4oXiFlgHgfZOOO8hxxoe1xJZujdydvbziFQmTFsRwnW1nhFK5snn-s1dhuDNYEvKFFAYnrEg_Sjatbj5ruk0LhtlW557Ef4uoyqNvYhEFNGg591X45ahU06F7Us6kWXMJ08wAafI6340c7YCc"

    instrument_name = 'ALPHAETF'
    token = 19640  # Hardcoded token for ALPHAETF
    default_quantity = 1  # Hardcoded default quantity

    logging.info(f"Placing order for {instrument_name} with quantity {default_quantity}")

    order_details = {
        "exchange": "NSE_EQ",
        "token": token,  # Hardcoded token for ALPHAETF
        "symbol": instrument_name,
        "transaction_type": "BUY",
        "product": "DELIVERY",
        "variety": "RL-MKT",  # Market Order
        "quantity": default_quantity,
        "price": 0.00,  # Price set to 0 for market order
        "trigger_price": 0.00,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "validity_days": 1,
        "is_amo": False
    }

    # Call the API using curl to place the order
    response = trigger_order_with_curl(order_details)

    if response and response.get('status') == 'success':
        order_id = response['data'].get('orderId')
        logging.info(f"Order placed successfully with ID: {order_id}")

        # Check order status to ensure it's executed
        if check_order_status(order_id, access_token):
            # Fetch trade details after the order is executed
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
