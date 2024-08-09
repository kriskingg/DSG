import requests

def read_variables():
    variables = {}
    with open('variables.txt', 'r') as file:
        for line in file:
            name, value = line.strip().split('=', 1)
            variables[name] = value
    return variables

def login_and_save_token():
    variables = read_variables()

    # Input TOTP from the user
    current_totp = input("Enter your TOTP: ")

    # Debug: Print the loaded variables (mask sensitive data)
    print(f"TOTP_SECRET_KEY: {variables.get('TOTP_SECRET_KEY')}")
    print(f"YOUR_API_KEY: {variables.get('YOUR_API_KEY')[:4]}****")
    print(f"YOUR_CLIENT_CODE: {variables.get('YOUR_CLIENT_CODE')}")
    print(f"YOUR_PASSWORD: {'*' * len(variables.get('YOUR_PASSWORD'))}")  # Mask the password
    print(f"YOUR_APPLICATION_ID: {variables.get('YOUR_APPLICATION_ID')}")

    url = "https://vortex.trade.rupeezy.in/user/login"
    headers = {
        "x-api-key": variables['YOUR_API_KEY'],
        "Content-Type": "application/json"
    }
    data = {
        "client_code": variables['YOUR_CLIENT_CODE'],
        "password": variables['YOUR_PASSWORD'],
        "totp": current_totp,
        "application_id": variables['YOUR_APPLICATION_ID']
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_data = response.json()
        access_token = response_data.get('data', {}).get('access_token')
        if access_token:
            with open('access_token.txt', 'w') as file:
                file.write(access_token)
            print("Access token saved.")
        else:
            print("Access token not found in response.")
            print("Response data:", response_data)  # Log the full response data for troubleshooting
    else:
        print(f"Failed to login: {response.status_code} - {response.text}")

if __name__ == "__main__":
    login_and_save_token()
