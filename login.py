# Authentication & TOTP Flow (login_with_generated_totp.yml):
# Manually Trigger or Schedule:

# The workflow can be manually triggered or scheduled (cron job).
# Checkout & Environment Setup:

# The repository is checked out, and Python (version 3.8) is set up using GitHub Actions.
# Dependencies installed: pyotp and other necessary libraries.
# Generate TOTP:

# TOTP generation using pyotp based on TOTP_SECRET_KEY.
# The generated TOTP is saved as an environment variable.
# Run login.py:

# The login script uses the generated TOTP and environment variables (API key, client code, password, and application ID) to log in to Rupeezy.
# Retrieves the access token.
# Store the Access Token:

# The access token is saved as an artifact (access_token.txt) and uploaded as a GitHub secret for future use.



import requests
import os
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def login_and_save_token():
    try:
        # Retrieve environment variables
        totp = os.getenv('TOTP')
        api_key = os.getenv('RUPEEZY_API_KEY')
        client_code = os.getenv('RUPEEZY_CLIENT_CODE')
        password = os.getenv('RUPEEZY_PASSWORD')
        application_id = os.getenv('RUPEEZY_APPLICATION_ID')

        # Check if all environment variables are set
        if not all([totp, api_key, client_code, password, application_id]):
            raise ValueError("One or more required environment variables are not set.")

        logging.info("Using TOTP: %s", totp)

        # Prepare and perform the request
        url = "https://vortex.trade.rupeezy.in/user/login"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "client_code": client_code,
            "password": password,
            "totp": totp,
            "application_id": application_id
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Process the response
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if access_token:
            logging.info("ACCESS_TOKEN=%s", access_token)
            # Save the access token to an environment variable
            with open(os.getenv('GITHUB_ENV'), 'a') as env_file:
                env_file.write(f"ACCESS_TOKEN={access_token}\n")
            # Save the access token to a file for artifact storage
            with open('access_token.txt', 'w') as token_file:
                token_file.write(access_token)
        else:
            logging.error("Login failed or access token not found.")
            logging.error("Response data: %s", response_data)

    except requests.exceptions.RequestException as e:
        logging.error("HTTP error occurred: %s", e)
    except ValueError as ve:
        logging.error("Value error: %s", ve)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    login_and_save_token()
