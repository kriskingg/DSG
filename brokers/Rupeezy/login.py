# File: brokers/rupeezy/login.py
import os
import requests
import pyotp
import logging

def rupeezy_login():
    creds = {
        "client_code": os.getenv("RUPEEZY_CLIENT_CODE"),
        "password": os.getenv("RUPEEZY_PASSWORD"),
        "api_key": os.getenv("RUPEEZY_API_KEY"),
        "app_id": os.getenv("RUPEEZY_APPLICATION_ID"),
        "totp_secret": os.getenv("RUPEEZY_TOTP_SECRET"),
    }

    # Generate TOTP
    totp = pyotp.TOTP(creds["totp_secret"])
    otp = totp.now()

    payload = {
        "clientcode": creds["client_code"],
        "password": creds["password"],
        "totp": otp
    }

    headers = {
        "x-api-key": creds["api_key"],
        "x-appid": creds["app_id"]
    }

    try:
        response = requests.post(
            "https://vortex.trade.rupeezy.in/user/login",
            json=payload,
            headers=headers
        )

        if response.status_code == 200 and "data" in response.json():
            session_data = response.json()["data"]
            logging.info("✅ Rupeezy login successful.")
            return session_data  # Token, Client Code, etc.
        else:
            logging.error(f"❌ Login failed: {response.text}")
            return None

    except Exception as e:
        logging.exception(f"💥 Exception during Rupeezy login: {e}")
        return None
