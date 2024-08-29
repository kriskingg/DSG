import logging
import requests
from beest_etf import trigger_order_on_rupeezy, check_order_status, fetch_trade_details
from db_operations import insert_order_dynamodb

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

API_BASE_URL = "https://vortex.trade.rupeezy.in"

def place_order(symbol, token):
    """Place an order and update DynamoDB with the order details."""
    order_details = {
        "exchange": "NSE_EQ",
        "token": token,
        "symbol": symbol,
        "transaction_type": "BUY",
        "product": "DELIVERY",
        "variety": "RL-MKT",  # Market Order
        "quantity": 1,  # Default quantity
        "price": 0.00,  # Price set to 0 for market order
        "trigger_price": 0.00,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "validity_days": 1,
        "is_amo": False
    }

    try:
        response = trigger_order_on_rupeezy(order_details)
        if response and response.get('status') == 'success':
            order_id = response['data'].get('orderId')
            logging.info(f"Order placed successfully with ID: {order_id}")

            # Check order status to ensure it's executed
            if check_order_status(order_id):
                logging.info("Order executed successfully. Fetching trade details.")
                # Fetch trade details after the order is executed
                trade_details = fetch_trade_details(order_id)
                if trade_details:
                    executed_price = trade_details.get('trade_price')
                    logging.info(f"Order executed at price: {executed_price}")

                    # Store the order details in DynamoDB
                    insert_order_dynamodb(
                        user_id="user123",  # Replace with actual user ID
                        instrument_id=symbol,
                        quantity=1,  # Default quantity
                        price=executed_price,
                        transaction_type="BUY",
                        product="DELIVERY",
                        ltp=executed_price
                    )
                    return True
                else:
                    logging.error("Failed to fetch trade details. Exiting.")
                    return False
            else:
                logging.error("Order was not executed successfully. Exiting.")
                return False
        else:
            logging.error(f"Failed to place order. Response: {response}")
            return False
    except Exception as e:
        logging.error(f"An error occurred while placing the order: {e}")
        return False

def check_order_status(order_id):
    """Check the status of an order."""
    try:
        response = requests.get(f"{API_BASE_URL}/orders/{order_id}")
        response.raise_for_status()
        status = response.json()
        logging.info(f"Order status fetched: {status}")
        return status.get('status') == 'completed'
    except requests.RequestException as e:
        logging.error(f"Error fetching order status: {e}")
        return False

def fetch_trade_details(order_id):
    """Fetch trade details for an order."""
    try:
        response = requests.get(f"{API_BASE_URL}/trades?order_id={order_id}")
        response.raise_for_status()
        trades = response.json()
        logging.info(f"Trade details fetched: {trades}")
        return trades
    except requests.RequestException as e:
        logging.error(f"Error fetching trade details: {e}")
        return None

if __name__ == '__main__':
    # Tokens and symbols
    symbol_token_mapping = {
        "ALPHA": 7412,
        "ALPHAETF": 19640
    }

    # Try placing order for ALPHA
    success = place_order("ALPHA", symbol_token_mapping["ALPHA"])
    
    # If order for ALPHA failed, try placing order for ALPHAETF
    if not success:
        logging.info("Retrying with ALPHAETF")
        place_order("ALPHAETF", symbol_token_mapping["ALPHAETF"])
