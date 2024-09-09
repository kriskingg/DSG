# This chartink_script_test_2.py script is performing the following tasks:

# Load environment variables:

# The script uses dotenv to load environment variables, including your API key.
# Fetch data from Chartink:

# The script defines a condition to query Chartink for stock data using a POST request.
# It retrieves the data, filters it for ALPHAETF, and logs the filtered data.
# Place an order on Rupeezy:

# If the ALPHAETF data is found, it extracts the current price.
# It creates an order for ALPHAETF and places a BUY order on Rupeezy using the trigger_order_on_rupeezy function, which calls Rupeezy's API with the appropriate headers and token
# Logging and error handling:

# It logs each step, including any HTTP or API errors, and provides retry logic for fetching data from Chartink.
# In short, this script:

# Fetches data from Chartink based on a condition.
# Places a buy order on Rupeezy if the ALPHAETF data matches the condition.

import os
import requests
from bs4 import BeautifulSoup
import logging
from time import sleep
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants for Chartink
Charting_Link = "https://chartink.com/screener/"
Charting_url = 'https://chartink.com/screener/process'
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

RUPEEZY_API_KEY = os.getenv('RUPEEZY_API_KEY')

if RUPEEZY_API_KEY:
    logging.debug("RUPEEZY_API_KEY is set.")
else:
    logging.error("RUPEEZY_API_KEY is not set.")


# Fetch data from Chartink based on the given condition
def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3
    for attempt in range(retries):
        try:
            with requests.Session() as s:
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                logging.debug("Headers: {}".format(s.headers))
                r = s.get(Charting_Link)
                logging.debug("GET request to Charting_Link status code: {}".format(r.status_code))
                soup = BeautifulSoup(r.text, "html.parser")
                csrf_token = soup.select_one("[name='csrf-token']")['content']
                s.headers.update({'x-csrf-token': csrf_token})
                logging.debug("CSRF Token: {}".format(csrf_token))
                logging.debug("Scan Condition: {}".format(condition))
                response = s.post(Charting_url, data={'scan_clause': condition})
                logging.debug("POST request to Charting_url status code: {}".format(response.status_code))
                logging.debug("Request Data: {}".format({'scan_clause': condition}))
                response_json = response.json()
                logging.debug("Response JSON: {}".format(response_json))
                if response.status_code == 200:
                    return response_json
                else:
                    logging.error("Failed to fetch data with status code: {}".format(response.status_code))
        except Exception as e:
            logging.error("Exception during data fetch: {}".format(str(e)))
        sleep(10)  # wait before retrying
    logging.error("All retries failed")
    return None

# Commented out order placement logic since you don't need it here
# def trigger_order_on_rupeezy(order_details):
#     """Trigger an order on Rupeezy."""
#     api_url = "https://vortex.trade.rupeezy.in/orders/regular"
#     access_token = get_access_token()
#     if not access_token:
#         logging.error("Access token is not available.")
#         return

#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json"
#     }

#     logging.debug(f"API URL: {api_url}")
#     logging.debug(f"Headers: {headers}")
#     logging.debug(f"Order Details: {order_details}")

#     try:
#         response = requests.post(api_url, json=order_details, headers=headers)
#         response.raise_for_status()
#         logging.debug("Order response: %s", response.json())
#         return response.json()
#     except requests.exceptions.HTTPError as http_err:
#         logging.error(f"HTTP error occurred: {http_err}")
#     except Exception as err:
#         logging.error(f"Other error occurred: {err}")

if __name__ == '__main__':
    # Fetch data from Chartink
    data = fetch_chartink_data(condition)

    if data:
        alpha_etf_data = [item for item in data['data'] if item['nsecode'] == 'ALPHAETF']
        
        if alpha_etf_data:
            logging.debug(f"Filtered ALPHAETF data: {alpha_etf_data}")
            # Removed order placement logic
        else:
            logging.info("No ALPHAETF data found. No action taken.")
    else:
        logging.error("Failed to fetch data from Chartink.")
