import requests
import pyotp
import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables from .env file or directly from the environment
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_totp():
    """Generate TOTP code using the secret key from the environment variable."""
    totp_secret_key = os.getenv('TOTP_SECRET_KEY')
    if not totp_secret_key:
        raise ValueError("TOTP_SECRET_KEY is not set. Cannot generate TOTP code.")
    totp = pyotp.TOTP(totp_secret_key)
    return totp.now()

def login_with_totp(totp):
    """Perform login using the generated TOTP."""
    url = "https://vortex.trade.rupeezy.in/user/login"
    headers = {
        "x-api-key": os.getenv('YOUR_API_KEY'),
        "Content-Type": "application/json"
    }
    data = {
        "client_code": os.getenv('YOUR_CLIENT_CODE'),
        "password": os.getenv('YOUR_PASSWORD'),
        "totp": totp,
        "application_id": os.getenv('YOUR_APPLICATION_ID')
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if access_token:
            # Save the access token as a GitHub Actions output
            with open(os.getenv('GITHUB_ENV'), 'a') as file:
                file.write(f"ACCESS_TOKEN={access_token}\n")
            logging.info("Access token saved.")
        else:
            logging.error("Access token not found in response.")
            logging.error("Response data: %s", response_data)
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")

def unified_login_process():
    """Generate TOTP and perform login with it."""
    try:
        current_totp = generate_totp()
        logging.info(f"Generated TOTP: {current_totp}")

        # Wait 3 seconds to ensure TOTP timing is correct
        time.sleep(3)

        # Perform login with TOTP
        login_with_totp(current_totp)
    except ValueError as e:
        logging.error(f"An error occurred during TOTP generation: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    unified_login_process()
