# # Beest Main Flow:
# # GitHub Actions Workflow (Trade_Script_with_DB_and_S3.yml):
# # The workflow is either manually triggered or runs on a schedule.
# # Environment setup: Python and dependencies are installed.
# # Access Token Handling: The access token is downloaded and set as an environment variable without using rupeezy/auth.py.
# # Running main.py:
# # Order Placement: The script defines the order details and places an order using trigger_order_on_rupeezy.
# # Order Status Check: The script checks the order status using check_order_status.
# # Fetch Trade Details: If the order is successful, trade details are fetched using fetch_trade_details.
# # Data Storage:
# # The order details are stored in DynamoDB using insert_order_dynamodb.

import logging
import os
from beest_etf import trigger_order_on_rupeezy, check_order_status, fetch_trade_details

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    # Retrieve the access token from environment variables
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')
    
    # Logging the access token for debugging purposes (you can remove this later)
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

    # Logging the order details to verify everything is correct
    logging.debug(f"Order Details: {order_details}")

    # Place the order
    response = trigger_order_on_rupeezy(order_details)

    # Check if the response is successful
    if response:
        logging.debug(f"Order API Response: {response}")

    if response and response.get('status') == 'success':
        order_id = response['data'].get('orderId')
        logging.info(f"Order placed successfully with ID: {order_id}")

        # Check order status to ensure it's executed
        if check_order_status(order_id):
            # Fetch trade details after the order is executed
            trade_details = fetch_trade_details(order_id)
            if trade_details:
                executed_price = trade_details.get('trade_price')
                logging.info(f"Order executed at price: {executed_price}")
            else:
                logging.error("Failed to fetch trade details. Exiting.")
        else:
            logging.error("Order was not executed successfully. Exiting.")
    else:
        logging.error(f"Failed to place order for {instrument_name}. Response: {response}")
