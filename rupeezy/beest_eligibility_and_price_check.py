# Here’s a write-up for the script you provided:

#   The script starts by setting up basic logging and loading environment variables, if needed, from a .env file.
  
#   It initializes a DynamoDB client to interact with the StockEligibility table in DynamoDB.
  
#   The script defines a function fetch_chartink_data that fetches stock data from the Chartink website using a predefined condition. It retrieves data using a session-based request and retries in case of failure.
  
#   The fetch_all_stocks_from_dynamodb function scans the StockEligibility table in DynamoDB to fetch all stock records.
  
#   The update_stock_eligibility function compares stocks retrieved from DynamoDB with the eligible instruments fetched from Chartink. For each stock, it checks whether it meets the eligibility criteria based on the Chartink data.
  
#   If a stock is eligible, its status is updated to "Eligible" in the DynamoDB table; otherwise, it is marked "Ineligible."
  
#   The script updates the EligibilityStatus and the LastUpdated timestamp for each stock in DynamoDB and logs the updates.
      
#   Finally, the script runs the entire eligibility check and update process and logs the outcome.
  
#   This script is designed to automate the process of validating stock eligibility and updating the corresponding records in DynamoDB based on data fetched from Chartink.

# Standard library imports
import os  # Library for interacting with the operating system (e.g., environment variables)
import logging  # Module for logging events and debugging messages

# Time and date-related imports
from time import sleep  # Function from time module to pause the script for a specified duration
from datetime import datetime  # Class from the datetime module to work with dates and times

# External libraries
import boto3  # AWS SDK for Python to interact with AWS services (in this case, DynamoDB)
import pytz  # Library to work with time zones in Python
import requests  # Library to make HTTP requests (used for fetching data from Chartink API)
from bs4 import BeautifulSoup  # Library for parsing HTML/XML (used to extract CSRF tokens from web pages)

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from a .env file
from dotenv import load_dotenv  # Used to load environment variables from a file
load_dotenv()  # Loads the variables from the .env file into the script's environment

# Initialize the DynamoDB client from boto3
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Constants for Chartink (URLs and API endpoints)
Charting_Link = "https://chartink.com/screener/"  # URL to Chartink's website
Charting_url = 'https://chartink.com/screener/process'  # API endpoint for Chartink data processing
# The condition defines the criteria for fetching stock data from Chartink's screener
condition = "( {166311} ( latest rsi(65) < latest ema(rsi(65),35) or weekly rsi(65) < weekly ema(rsi(65),35) ) )"

# Fetch data from Chartink based on the given condition
def fetch_chartink_data(condition):
    """Fetch data from Chartink based on the given condition."""
    retries = 3  # Number of retry attempts if the request fails
    for attempt in range(retries):  # Loop to retry fetching data
        try:
            # Using a requests.Session to maintain a session across multiple requests
            with requests.Session() as s:
                # Setting the headers for the HTTP request
                s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                
                # First, make a GET request to get the CSRF token from Chartink
                r = s.get(Charting_Link)
                soup = BeautifulSoup(r.text, "html.parser")  # Parse the HTML page using BeautifulSoup
                csrf_token = soup.select_one("[name='csrf-token']")['content']  # Extract the CSRF token
                s.headers.update({'x-csrf-token': csrf_token})  # Update session headers with the CSRF token
                
                # POST request to the Chartink API with the stock condition
                response = s.post(Charting_url, data={'scan_clause': condition})
                if response.status_code == 200:  # Check if the request was successful
                    return response.json()  # Return the response data in JSON format
        except Exception as e:
            # Log any errors that occur during the request
            logging.error("Exception during data fetch from Chartink: {}".format(str(e)))
        # Sleep for 10 seconds before retrying the request
        sleep(10)
    logging.error("All retries to fetch data from Chartink failed")
    return None  # Return None if the request fails after all retries

# Function to fetch all stock records from the DynamoDB StockEligibility table
def fetch_all_stocks_from_dynamodb():
    """Fetch all stocks from DynamoDB StockEligibility table."""
    try:
        # Scan the entire StockEligibility table to retrieve all items (this can be optimized later)
        response = dynamodb.scan(TableName='StockEligibility')
        return response['Items']  # Return the list of items (stocks) from the response
    except Exception as e:
        # Log any errors that occur when interacting with DynamoDB
        logging.error(f"Error fetching items from DynamoDB: {e}")
        return []  # Return an empty list if an error occurs

# Function to update the eligibility status of stocks based on Chartink data
def update_stock_eligibility():
    """Update stock eligibility based on Chartink data and update DynamoDB records."""
    # Get the current time in the Asia/Kolkata time zone
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    # Format the current time as a string to store in DynamoDB
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Fetch data from Chartink
    chartink_data = fetch_chartink_data(condition)
    if not chartink_data:  # If no data was fetched, exit the function
        logging.error("No data fetched from Chartink.")
        return

    # Create a set of eligible instruments based on the Chartink response
    eligible_instruments = {item['nsecode'] for item in chartink_data['data']}
    
    # Fetch all stocks from the DynamoDB StockEligibility table
    all_stocks = fetch_all_stocks_from_dynamodb()
    
    # Loop through each stock in the DynamoDB table
    for stock in all_stocks:
        instrument_name = stock['InstrumentName']['S']  # Extract the instrument name (stock ticker)
        is_eligible = instrument_name in eligible_instruments  # Check if the stock is in the eligible set

        # Set the eligibility status based on whether the stock is eligible or not
        eligibility_status = 'Eligible' if is_eligible else 'Ineligible'

        # If stock becomes Ineligible, reset BaseValue to -1
        base_value = '-1' if not is_eligible else stock.get('BaseValue', {'N': '0'})['N']  # If ineligible, reset BaseValue to -1

        # Log the update for the stock
        logging.info(f"Updating {instrument_name} as {eligibility_status} in DynamoDB.")
        
        # Update the stock's eligibility status, base value, and last updated time in DynamoDB
        try:
            dynamodb.update_item(
                TableName='StockEligibility',  # Specify the DynamoDB table to update
                Key={
                    'InstrumentName': {'S': instrument_name},  # Primary key: instrument name
                    'Eligibility': {'S': stock['Eligibility']['S']}  # Sort key: eligibility
                },
                # Update expression to set the new eligibility status, base value, and last updated timestamp
                UpdateExpression="SET EligibilityStatus = :elig, LastUpdated = :lu, BaseValue = :bv",
                ExpressionAttributeValues={
                    ':elig': {'S': eligibility_status},  # Set eligibility status
                    ':lu': {'S': current_time},  # Set the last updated timestamp
                    ':bv': {'N': base_value}  # Set BaseValue, reset to -1 if ineligible
                }
            )
            logging.info(f"Successfully updated {instrument_name} to {eligibility_status}.")
        except Exception as e:
            # Log any errors that occur during the update
            logging.error(f"Error updating {instrument_name} in DynamoDB: {e}")

# Main execution block: This runs when the script is executed directly
if __name__ == "__main__":
    logging.info("Starting stock eligibility update process...")
    update_stock_eligibility()  # Call the function to update stock eligibility
    logging.info("Stock eligibility update process completed.")
