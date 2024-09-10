# # # Beest Main Flow:
# # # GitHub Actions Workflow (Trade_Script_with_DB_and_S3.yml):
# # # The workflow is either manually triggered or runs on a schedule.
# # # Environment setup: Python and dependencies are installed.
# # # Access Token Handling: The access token is downloaded and set as an environment variable without using rupeezy/auth.py.
# # # Running main.py:
# # # Order Placement: The script defines the order details and places an order using trigger_order_on_rupeezy.
# # # Order Status Check: The script checks the order status using check_order_status.
# # # Fetch Trade Details: If the order is successful, trade details are fetched using fetch_trade_details.
# # # Data Storage:
# # # The order details are stored in DynamoDB using insert_order_dynamodb.

# import requests
# import logging
# import os

# # Setup basic logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def trigger_order_on_rupeezy(order_details, access_token):
#     """Trigger an order on Rupeezy."""
#     api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    
#     # Construct headers with explicit Authorization token
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     # Log the headers and order details before making the request
#     logging.debug(f"Headers: {headers}")
#     logging.debug(f"Order Details: {order_details}")

#     try:
#         # Make the POST request to place the order
#         response = requests.post(api_url, json=order_details, headers=headers)
#         response.raise_for_status()
        
#         # Log and return the response JSON
#         response_json = response.json()
#         logging.debug(f"Order Response: {response_json}")
#         return response_json
#     except requests.exceptions.HTTPError as http_err:
#         logging.error(f"HTTP error occurred during order placement: {http_err}")
#     except Exception as err:
#         logging.error(f"Other error occurred during order placement: {err}")
    
#     return None

# if __name__ == '__main__':
#     # Retrieve the access token from environment variables
#     access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')
#     logging.debug(f"Access Token: {access_token}")

#     if not access_token:
#         logging.error("RUPEEZY_ACCESS_TOKEN not found in environment variables. Exiting.")
#         exit(1)

#     # Hardcoded ALPHAETF details
#     instrument_name = 'ALPHAETF'
#     token = 19640  # Hardcoded token for ALPHAETF
#     default_quantity = 1  # Hardcoded default quantity

#     logging.info(f"Placing order for {instrument_name} with quantity {default_quantity}")

#     order_details = {
#         "exchange": "NSE_EQ",
#         "token": token,  # Hardcoded token for ALPHAETF
#         "symbol": instrument_name,
#         "transaction_type": "BUY",
#         "product": "DELIVERY",
#         "variety": "RL-MKT",  # Market Order
#         "quantity": default_quantity,
#         "price": 0.00,  # Price set to 0 for market order
#         "trigger_price": 0.00,
#         "disclosed_quantity": 0,
#         "validity": "DAY",
#         "validity_days": 1,
#         "is_amo": False
#     }

#     # Call the API to place the order
#     response = trigger_order_on_rupeezy(order_details, access_token)

#     if response and response.get('status') == 'success':
#         order_id = response['data'].get('orderId')
#         logging.info(f"Order placed successfully with ID: {order_id}")
#     else:
#         logging.error(f"Failed to place order for {instrument_name}. Response: {response}")
