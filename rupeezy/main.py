import logging
from vortex_api import AsthaTradeVortexAPI
from vortex_api import Constants as Vc
import os

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def trigger_order_via_sdk(client, order_details):
    """Trigger an order using the SDK."""
    try:
        # Placing the order using the SDK's place_order method
        response = client.place_order(
            exchange=Vc.ExchangeTypes.NSE_EQUITY,
            token=order_details['token'],
            transaction_type=Vc.TransactionSides.BUY if order_details['transaction_type'] == "BUY" else Vc.TransactionSides.SELL,
            product=Vc.ProductTypes.DELIVERY,
            variety=Vc.VarietyTypes.REGULAR_LIMIT_ORDER if order_details['variety'] == "RL-MKT" else Vc.VarietyTypes.STOP_MARKET_ORDER,
            quantity=order_details['quantity'],
            price=order_details['price'],
            trigger_price=order_details['trigger_price'],
            disclosed_quantity=order_details['disclosed_quantity'],
            validity=Vc.ValidityTypes.FULL_DAY if order_details['validity'] == "DAY" else Vc.ValidityTypes.IMMEDIATE_OR_CANCEL
        )
        logging.debug(f"Order Response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
        return None

if __name__ == "__main__":
    # Retrieve necessary secrets from environment variables
    api_secret = os.getenv('RUPEEZY_API_KEY')  # API Key from GitHub Secrets
    application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Application ID from GitHub Secrets
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')  # Access token from GitHub Secrets

    # Create a client instance
    client = AsthaTradeVortexAPI(api_secret, application_id)
    client.access_token = access_token  # Set the access token directly

    # Define the order details
    order_details = {
    "exchange": "NSE_EQ",
    "token": 19640,
    "symbol": "ALPHAETF",
    "transaction_type": "BUY",
    "product": "DELIVERY",
    "variety": "RL-MKT",  # Change to RL-MKT for market order
    "quantity": 1,
    "price": 0.0,  # For market orders, price can be 0
    "trigger_price": 0.0,
    "disclosed_quantity": 0,
    "validity": "DAY",
    "validity_days": 1,
    "is_amo": False
}


    # Place the order
    response = trigger_order_via_sdk(client, order_details)
    if response:
        logging.info(f"Order placed successfully: {response}")
    else:
        logging.error("Order placement failed")
