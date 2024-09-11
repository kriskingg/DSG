import logging
import os
from vortex_api import AsthaTradeVortexAPI

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_order_details(client, order_id):
    """Fetch order details using the order ID."""
    try:
        order_details = client.order_history(order_id)
        logging.info(f"Order Details for {order_id}: {order_details}")
    except Exception as e:
        logging.error(f"Error fetching order details for {order_id}: {e}")

def get_positions(client):
    """Fetch current positions."""
    try:
        positions_data = client.positions()
        logging.info(f"Current Positions: {positions_data}")
    except Exception as e:
        logging.error(f"Error fetching positions: {e}")

if __name__ == "__main__":
    # Retrieve necessary secrets from environment variables
    api_secret = os.getenv('RUPEEZY_API_KEY')  # API Key from GitHub Secrets
    application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Application ID from GitHub Secrets
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')  # Access token from GitHub Secrets

    # Create a client instance
    client = AsthaTradeVortexAPI(api_secret, application_id)
    client.access_token = access_token  # Set the access token directly

    # You can pass the order IDs directly or get them from a file/log if `main.py` stores them.
    # Here, we'll assume the order ID is passed from environment variables or hardcoded for simplicity
    order_ids = ["OFIQV00001;9"]  # Example order ID. Replace with dynamic IDs from `main.py`

    # Fetch order details for each order ID
    for order_id in order_ids:
        get_order_details(client, order_id)

    # Fetch current positions
    get_positions(client)
