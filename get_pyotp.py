import requests
import pyotp
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_totp():
    """Generate TOTP code using the hardcoded secret key."""
    totp_secret_key = "KUGBEDKB2BCGGRNKVJIP3Q64BQROAPO7"  # Hardcoded TOTP secret key
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

        # Perform the login request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Process the response
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if response.status_code == 200 and access_token:
            # Print the access token (or save it as needed)
            logging.info(f"ACCESS_TOKEN={access_token}")
        else:
            logging.error("Login failed or access token not found.")
            logging.error("Response data: %s", response_data)

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error occurred: {e}")
    except ValueError as ve:
        logging.error(f"Value error: {ve}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    login_and_save_token()
