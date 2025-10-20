# - This script performs secure login to the Rupeezy trading platform using API credentials stored in environment variables.
# - It retrieves an access token needed for making authenticated API requests to Rupeezy.
# - The script logs steps and errors for debugging and monitoring purposes.
# - If run directly, it prints the token or exits with an error if login fails.
# - Handles various errors such as missing credentials, HTTP issues, or unexpected failures.

import requests  # Importing the requests library for making HTTP requests to the Rupeezy API
import os  # Importing the os library to access environment variables (like API keys, passwords, etc.)
import logging  # Importing the logging module to log information and errors during the script execution
# Setup basic logging configuration to show info and error messages with timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
def login_and_get_token():
    try:
        # Retrieve environment variables (these are stored outside the script, typically in your system or CI/CD environment)
        totp = os.getenv('TOTP')  # Time-based One-Time Password (TOTP) fetched from environment
        api_key = os.getenv('RUPEEZY_API_KEY')  # API key for authenticating with the Rupeezy platform
        client_code = os.getenv('RUPEEZY_CLIENT_CODE')  # Client code for login
        password = os.getenv('RUPEEZY_PASSWORD')  # Password for the Rupeezy account
        application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Application ID for Rupeezy
        # Check if all required environment variables are set; raise an error if any are missing
        if not all([totp, api_key, client_code, password, application_id]):
            raise ValueError("One or more required environment variables are not set.")  # If any variable is missing, raise a ValueError
        logging.info("Using TOTP: %s", totp)  # Log the TOTP (useful for tracking/debugging)
        # Prepare the URL for the login API and set the headers for the HTTP request
        url = "https://vortex.trade.rupeezy.in/user/login"  # API endpoint for Rupeezy login
        headers = {
            "x-api-key": api_key,  # Send the API key as a header
            "Content-Type": "application/json"  # Specify that the request body is in JSON format
        }
        # Prepare the data payload for the POST request (login credentials)
        data = {
            "client_code": client_code,  # Client code to log in
            "password": password,  # Password for the account
            "totp": totp,  # Time-based One-Time Password (TOTP) for two-factor authentication
            "application_id": application_id  # Application ID for Rupeezy
        }
        # Send the POST request to the login API with headers and data
        response = requests.post(url, headers=headers, json=data)  # Sending HTTP POST request
        response.raise_for_status()  # Raise an exception if the server returns an HTTP error (e.g., 4xx or 5xx status codes)
        # Process the response JSON data to extract the access token
        response_data = response.json()  # Convert the response text to a Python dictionary (JSON)
        access_token = response_data.get('data', {}).get('access_token')  # Extract 'access_token' from the response (if available)
        
        # If the access token is successfully retrieved, log the success and return the token
        if access_token:
            logging.info("RUPEEZY_ACCESS_TOKEN retrieved successfully.")  # Log that the access token was retrieved
            return access_token  # Return the token to be used in future API calls
        else:
            logging.error("Login failed or access token not found.")  # If token is missing, log an error
            return None  # Return None to indicate failure
    # Handle different types of errors that could occur during the request
    except requests.exceptions.RequestException as e:
        logging.error("HTTP error occurred: %s", e)  # Catch and log HTTP-related errors (e.g., connection issues)
    except ValueError as ve:
        logging.error("Value error: %s", ve)  # Catch and log ValueError (e.g., missing environment variables)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)  # Catch and log any other unexpected errors
    return None  # Return None if any error occurred
# This block runs only when the script is executed directly (i.e., not imported as a module)
if __name__ == "__main__":
    token = login_and_get_token()  # Call the login function to attempt to get the access token
    if token:
        print(token)  # Print the access token if successfully retrieved
    else:
        exit(1)  # If the token is not retrieved (None), exit the script with an error code
