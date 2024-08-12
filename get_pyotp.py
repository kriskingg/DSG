import requests
import pyotp
import os
import time
from dotenv import load_dotenv

# Load environment variables from GitHub Secrets
load_dotenv()

def generate_totp():
    """Generate TOTP code using the secret key from an environment variable."""
    totp_secret_key = os.getenv('TOTP_SECRET_KEY')
    if not totp_secret_key:
        logging.error("TOTP_SECRET_KEY is not set.")
        raise ValueError("TOTP_SECRET_KEY is not set. Cannot generate TOTP code.")
    totp = pyotp.TOTP(totp_secret_key)
    return totp.now()

def login_and_save_token():
    try:
        # Ensure all necessary environment variables are set
        api_key = os.getenv('YOUR_API_KEY')
        client_code = os.getenv('YOUR_CLIENT_CODE')
        password = os.getenv('YOUR_PASSWORD')
        application_id = os.getenv('YOUR_APPLICATION_ID')

        if not api_key or not client_code or not password or not application_id:
            raise ValueError("One or more required environment variables are not set.")

        # Generate the TOTP
        current_totp = generate_totp()
        logging.info(f"Generated TOTP: {current_totp}")

        # Prepare the request
        url = "https://vortex.trade.rupeezy.in/user/login"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "client_code": client_code,
            "password": password,
            "totp": current_totp,
            "application_id": application_id
        }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if access_token:
            # Save the access token as a GitHub Actions output
            with open(os.getenv('GITHUB_ENV'), 'a') as file:
                file.write(f"ACCESS_TOKEN={access_token}\n")
            print("Access token saved.")
        else:
            print("Access token not found in response.")
            print("Response data:", response_data)
    else:
        print(f"Failed to login: {response.status_code} - {response.text}")

def unified_login_process():
    """Generate TOTP and perform login with it."""
    current_totp = generate_totp()
    
    # Wait 3 seconds to ensure TOTP timing is correct
    time.sleep(3)
    
    print(f"Generated TOTP: {current_totp}")
    
    # Perform login with TOTP
    login_with_totp(current_totp)

if __name__ == "__main__":
    login_and_save_token()
