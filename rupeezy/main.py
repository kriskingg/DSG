import logging
import os
from beest_etf import trigger_order_on_rupeezy

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

    # Call the API to place the order
    response = trigger_order_on_rupeezy(order_details, access_token)

    if response and response.get('status') == 'success':
        order_id = response['data'].get('orderId')
        logging.info(f"Order placed successfully with ID: {order_id}")
    else:
        logging.error(f"Failed to place order for {instrument_name}. Response: {response}")
