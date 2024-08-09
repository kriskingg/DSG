import requests
import pyotp
import os

def generate_totp():
    """Generate TOTP code using the secret key from the environment variable."""
    totp_secret_key = os.getenv('TOTP_SECRET_KEY')
    if not totp_secret_key:
        raise ValueError("TOTP_SECRET_KEY is not set. Cannot generate TOTP code.")
    totp = pyotp.TOTP(totp_secret_key)
    return totp.now()

def login_and_save_token():
    current_totp = generate_totp()

    url = "https://vortex.trade.rupeezy.in/user/login"
    headers = {
        "x-api-key": os.getenv('YOUR_API_KEY'),
        "Content-Type": "application/json"
    }
    data = {
        "client_code": os.getenv('YOUR_CLIENT_CODE'),
        "password": os.getenv('YOUR_PASSWORD'),
        "totp": current_totp,
        "application_id": os.getenv('YOUR_APPLICATION_ID')
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if access_token:
            # Store access token in GitHub Actions environment
            with open(os.getenv('GITHUB_ENV'), 'a') as file:
                file.write(f"ACCESS_TOKEN={access_token}\n")
            print("Access token saved as a GitHub environment variable.")
        else:
            print("Access token not found in response.")
            print("Response data:", response_data)
    else:
        print(f"Failed to login: {response.status_code} - {response.text}")

if __name__ == "__main__":
    login_and_save_token()
