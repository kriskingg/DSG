import requests
import pyotp
import os
import time
import subprocess
from dotenv import load_dotenv

# Load environment variables from variables.txt
load_dotenv('variables.txt')

def generate_totp():
    """Generate TOTP code using the secret key from the environment variable."""
    totp_secret_key = os.getenv('TOTP_SECRET_KEY')
    if not totp_secret_key:
        raise ValueError("TOTP_SECRET_KEY is not set. Cannot generate TOTP code.")
    totp = pyotp.TOTP(totp_secret_key)
    return totp.now()

def run_login_with_totp(totp):
    """Run the login.py script and input the TOTP when prompted."""
    print("Running login.py and inputting TOTP...")

    # Use subprocess to run login.py and input the TOTP
    process = subprocess.Popen(['C:\\Users\\Lenovo\\miniconda3\\python.exe', 'D:\\Beest\\ChartinkScanner\\login.py'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Wait for the script to ask for the TOTP
    stdout, stderr = process.communicate(input=f'{totp}\n')

    # Print the output of login.py
    print(stdout)
    print(stderr)

def unified_login_process():
    """Generate TOTP and run login.py with it."""
    
    # Generate TOTP
    current_totp = generate_totp()
    
    # Wait 3 seconds to ensure TOTP timing is correct
    time.sleep(3)
    
    # Debug: Print the generated TOTP
    print(f"Generated TOTP: {current_totp}")
    
    # Run login.py and input the TOTP
    run_login_with_totp(current_totp)

if __name__ == "__main__":
    unified_login_process()
