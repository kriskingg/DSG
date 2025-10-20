import json, struct, logging, sys, time, requests, pyotp, websocket, os

# ===========================================================
# CONFIGURATION
# ===========================================================
CONFIG = {
    "CLIENT_CODE": os.getenv("RUPEEZY_CLIENT_CODE"),
    "PASSWORD": os.getenv("RUPEEZY_PASSWORD"),
    "TOTP_SECRET": os.getenv("RUPEEZY_TOTP_SECRET"),
    "API_KEY": os.getenv("RUPEEZY_API_KEY"),
    "APP_ID": os.getenv("RUPEEZY_APPLICATION_ID"),
}

# ===========================================================
# LOGGING
# ===========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)

# ===========================================================
# LOGIN FUNCTION
# ===========================================================
def login_and_get_token(retry=False):
    """Authenticate with Rupeezy using TOTP and return access token."""
    try:
        totp = pyotp.TOTP(CONFIG["TOTP_SECRET"]).now()
        logging.info(f"🔢 Generated TOTP: {totp}")

        url = "https://vortex.trade.rupeezy.in/user/login"
        headers = {
            "x-api-key": CONFIG["API_KEY"],
            "Content-Type": "application/json"
        }
        data = {
            "client_code": CONFIG["CLIENT_CODE"],
            "password": CONFIG["PASSWORD"],
            "totp": totp,
            "application_id": CONFIG["APP_ID"]
        }

        logging.info("🔐 Logging into Rupeezy...")
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        logging.info(f"Status Code: {resp.status_code}")

        resp_json = resp.json()
        access_token = resp_json.get("data", {}).get("access_token")

        if not access_token:
            logging.warning(f"⚠️ Login failed: {resp_json}")

            # Retry once if first TOTP might have expired
            if not retry:
                logging.warning("⏳ Retrying login with fresh TOTP...")
                time.sleep(3)
                return login_and_get_token(retry=True)

            sys.exit("❌ Login failed after retry. Exiting.")

        with open("access_token.txt", "w") as f:
            f.write(access_token)
        logging.info("✅ Login successful. Token saved to access_token.txt.")
        return access_token

    except Exception as e:
        logging.error(f"❌ Login error: {e}")
        sys.exit(1)

# ===========================================================
# BINARY PACKET DECODER
# ===========================================================
def decode_ltp_packet(packet_bytes):
    """Decode a binary LTP packet correctly (little-endian, Rupeezy spec)."""
    try:
        token = struct.unpack("<i", packet_bytes[0:4])[0]
        ltp = struct.unpack("<d", packet_bytes[4:12])[0]
        return {"token": token, "ltp": round(ltp, 2)}
    except Exception as e:
        logging.error(f"⚠️ Binary decode error: {e}")
        return None

# ===========================================================
# WEBSOCKET HANDLER
# ===========================================================
def connect_ws(token):
    """Connect to Rupeezy WebSocket feed and stream market data."""
    ws_url = f"wss://wire.rupeezy.in/ws?auth_token={token}"
    logging.info(f"🌐 Connecting to WebSocket...\n→ {ws_url}")

    def on_open(ws):
        logging.info("✅ WebSocket connected. Subscribing to NIFTY (26000)...")
        sub_msg = {
            "exchange": "NSE_EQ",
            "token": 26000,   # NIFTY 50 token ID
            "mode": "ltp",
            "message_type": "subscribe"
        }
        ws.send(json.dumps(sub_msg))

    def on_message(ws, message):
        if isinstance(message, bytes):
            tick = decode_ltp_packet(message[2:])  # Skip 2-byte header
            if tick:
                logging.info(f"📈 {tick}")
        else:
            logging.info(f"📩 Text message (server response): {message}")

    def on_error(ws, error):
        logging.error(f"❌ WebSocket error: {error}")

    def on_close(ws, code, reason):
        logging.warning(f"🔚 WebSocket closed: {code} – {reason}")

    # Auto-reconnect loop
    while True:
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        try:
            ws.run_forever(ping_interval=25, ping_timeout=10)
        except KeyboardInterrupt:
            logging.info("🛑 Interrupted by user. Exiting gracefully.")
            break
        except Exception as e:
            logging.error(f"⚠️ WebSocket crash: {e}")
            logging.info("🔁 Reconnecting in 5 seconds...")
            time.sleep(5)
            continue

# ===========================================================
# MAIN
# ===========================================================
if __name__ == "__main__":
    token = login_and_get_token()
    if not token:
        sys.exit("❌ No access token retrieved. Exiting.")
    connect_ws(token)
