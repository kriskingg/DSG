import logging
from decimal import Decimal
from vortex_api import AsthaTradeVortexAPI, Constants as Vc
import os

# Set up basic logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Fetch API credentials from environment variables
api_secret = os.getenv('RUPEEZY_API_KEY')
application_id = os.getenv('RUPEEZY_APPLICATION_ID')
access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')

# Check for missing environment variables
if not api_secret or not application_id or not access_token:
    logging.error("One or more API credentials are missing. Exiting script.")
    exit(1)

# Initialize the broker API client
client = AsthaTradeVortexAPI(api_secret, application_id)
client.access_token = access_token

# Hardcoded instrument details
instrument_token = 19640  # Token for ALPHAETF

# Function to fetch the current stock price
from decimal import Decimal, ROUND_HALF_UP

def get_current_price(instrument_token):
    try:
        # Request the stock price from the broker API
        response = client.quotes([f"NSE_EQ-{instrument_token}"], mode=Vc.QuoteModes.LTP)
        
        # Log the full response for debugging
        logging.debug(f"Full response from quotes API for token {instrument_token}: {response}")
        
        # Check if 'data' exists and contains the 'NSE_EQ-{instrument_token}' key
        if 'data' not in response or f"NSE_EQ-{instrument_token}" not in response['data']:
            logging.error(f"Missing data or token key in response for token {instrument_token}: {response}")
            return None
        
        # Extract the Last Traded Price (LTP)
        ltp = response['data'][f"NSE_EQ-{instrument_token}"].get('last_trade_price', 0)
        
        if ltp == 0:
            logging.error(f"Received LTP as 0 for token {instrument_token}: {response}")
            return None
        
        # Convert to Decimal and round to two decimal places
        price = Decimal(ltp).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return price
    except Exception as e:
        logging.error(f"Error fetching current price for token {instrument_token}: {str(e)}")
        return None



# Main function to fetch and log the stock price
def main():
    try:
        # Use the hardcoded instrument token
        price = get_current_price(instrument_token)
        if price:
            logging.info(f"Current price for token {instrument_token} is {price}")
        else:
            logging.info(f"Could not fetch the current price for token {instrument_token}")
    
    except Exception as e:
        logging.error(f"Error fetching stock price: {str(e)}")

if __name__ == "__main__":
    main()
