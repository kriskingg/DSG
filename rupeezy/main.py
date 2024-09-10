import logging
import os
import json
import requests

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def trigger_order(order_details, access_token):
    """Trigger an order on Rupeezy using requests."""
    api_url = "https://vortex.trade.rupeezy.in/orders/regular"
    headers = {
        'Authorization': f'Bearer {access_token}', 
        'Content-Type': 'application/json'
    }
    
    logging.debug(f"API URL: {api_url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Order Details: {json.dumps(order_details, indent=4)}")
    
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

if __name__ == "__main__":
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')
    
    if not access_token:
        logging.error("Access token is not available.")
    else:
        logging.debug(f"Access Token (last 4 characters): {access_token[-4:]}")
        order_details = {
            "exchange": "NSE_EQ",
            "token": 19640,
            "symbol": "ALPHAETF",
            "transaction_type": "BUY",
            "product": "DELIVERY",
            "variety": "RL-MKT",
            "quantity": 1,
            "price": 0.0,
            "trigger_price": 0.0,
            "disclosed_quantity": 0,
            "validity": "DAY",
            "validity_days": 1,
            "is_amo": False
        }
        trigger_order(order_details, access_token)
