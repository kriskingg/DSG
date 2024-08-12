import requests
import pyotp
import os
import time
from dotenv import load_dotenv

# Load environment variables from GitHub Secrets
load_dotenv()

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
    unified_login_process()
