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
from beest_strategy_logic import fetch_chartink_data  # Importing from beest_strategy_logic

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    # Retrieve the access token from environment variables
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')
    if not access_token:
        logging.error("RUPEEZY_ACCESS_TOKEN not found in environment variables. Exiting.")
        exit(1)

    # Fetch data from Chartink using the logic from beest_strategy_logic
    data = fetch_chartink_data("( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )")

    if data:
        # Filter for ALPHAETF
        alpha_etf_data = [item for item in data['data'] if item['nsecode'] == 'ALPHAETF']
        
        if alpha_etf_data:
            logging.debug(f"Filtered ALPHAETF data: {alpha_etf_data}")
            # Extracting current price of ALPHAETF
            current_price = alpha_etf_data[0]['close']
            logging.info(f"Current price of ALPHAETF: {current_price}")

            # Example data for the order
            token = 19640  # Token for ALPHAETF
            order_quantity = 1  # Default quantity

            order_details = {
                "exchange": "NSE_EQ",
                "token": token,
                "symbol": "ALPHAETF",
                "transaction_type": "BUY",
                "product": "DELIVERY",
                "variety": "RL-MKT",  # Market Order
                "quantity": order_quantity,
                "price": 0.00,  # Price set to 0 for market order
                "trigger_price": 0.00,
                "disclosed_quantity": 0,
                "validity": "DAY",
                "validity_days": 1,
                "is_amo": False,
                "access_token": access_token  # Pass the access token with the order details
            }

            # Place the order
            response = trigger_order_on_rupeezy(order_details)
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
                logging.error(f"Failed to place order. Response: {response}")
        else:
            logging.info("No ALPHAETF data found. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
