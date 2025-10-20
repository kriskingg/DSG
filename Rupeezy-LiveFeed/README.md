# Rupeezy Live Feed

## Overview
Rupeezy Live Feed is a Python WebSocket client for connecting to Rupeezy's market data feed. This script provides real-time market data streaming with automatic authentication, TOTP-based login, and robust error handling with automatic reconnection capabilities.

## Features
- 🔐 **Secure Authentication**: TOTP-based two-factor authentication
- 📈 **Real-time Market Data**: Live streaming of NIFTY 50 prices via WebSocket
- 🔄 **Auto-reconnection**: Automatic reconnection on connection failures
- 📊 **Binary Packet Decoding**: Efficient decoding of Rupeezy's binary market data packets
- 🛡️ **Error Handling**: Comprehensive error handling and logging
- 🌍 **Environment Variables**: Secure credential management via environment variables

## Requirements
- Python 3.6+
- Required packages:
  ```
  requests
  websocket-client
  pyotp
  ```

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/kriskingg/Rupeezy-LiveFeed.git
   cd Rupeezy-LiveFeed
   ```

2. Install required dependencies:
   ```bash
   pip install requests websocket-client pyotp
   ```

3. Set up environment variables (create a `.env` file or set system variables):
   ```bash
   export RUPEEZY_CLIENT_CODE="your_client_code"
   export RUPEEZY_PASSWORD="your_password"
   export RUPEEZY_TOTP_SECRET="your_totp_secret"
   export RUPEEZY_API_KEY="your_api_key"
   export RUPEEZY_APPLICATION_ID="your_app_id"
   ```

## Usage Instructions

### Basic Usage
```bash
python rupeezy_auto_ws.py
```

### What the script does:
1. **Authentication**: Logs into Rupeezy using your credentials and TOTP
2. **Token Management**: Saves access token to `access_token.txt` for session management
3. **WebSocket Connection**: Establishes connection to Rupeezy's WebSocket feed
4. **Data Subscription**: Subscribes to NIFTY 50 (token: 26000) market data
5. **Live Streaming**: Continuously streams and displays real-time price updates

### Sample Output
```
10:30:15 - INFO - 🔢 Generated TOTP: 123456
10:30:15 - INFO - 🔐 Logging into Rupeezy...
10:30:16 - INFO - Status Code: 200
10:30:16 - INFO - ✅ Login successful. Token saved to access_token.txt.
10:30:16 - INFO - 🌐 Connecting to WebSocket...
10:30:17 - INFO - ✅ WebSocket connected. Subscribing to NIFTY (26000)...
10:30:18 - INFO - 📈 {'token': 26000, 'ltp': 19845.50}
10:30:19 - INFO - 📈 {'token': 26000, 'ltp': 19847.25}
```

## Main Functions

### `login_and_get_token(retry=False)`
- **Purpose**: Authenticates with Rupeezy API using TOTP
- **Parameters**: 
  - `retry` (bool): Whether this is a retry attempt
- **Returns**: Access token string
- **Features**: 
  - Automatic TOTP generation
  - Retry logic for expired TOTP codes
  - Token persistence to file

### `decode_ltp_packet(packet_bytes)`
- **Purpose**: Decodes binary market data packets from WebSocket
- **Parameters**: 
  - `packet_bytes` (bytes): Raw binary packet data
- **Returns**: Dictionary with token and LTP (Last Traded Price)
- **Format**: Little-endian binary format (4-byte token + 8-byte double LTP)

### `connect_ws(token)`
- **Purpose**: Establishes and maintains WebSocket connection
- **Parameters**: 
  - `token` (str): Authentication token
- **Features**: 
  - Auto-reconnection on failures
  - Ping/pong keepalive (25s interval)
  - Graceful error handling
  - NIFTY 50 subscription

## Configuration & Customization

### Environment Variables
All sensitive credentials are managed via environment variables:
- `RUPEEZY_CLIENT_CODE`: Your Rupeezy client code
- `RUPEEZY_PASSWORD`: Your account password
- `RUPEEZY_TOTP_SECRET`: TOTP secret key for 2FA
- `RUPEEZY_API_KEY`: API key for authentication
- `RUPEEZY_APPLICATION_ID`: Application identifier

### Subscribing to Different Instruments
To subscribe to different instruments, modify the subscription message in `on_open():`
```python
sub_msg = {
    "exchange": "NSE_EQ",  # Exchange (NSE_EQ, BSE_EQ, etc.)
    "token": 26000,        # Change this to your desired token
    "mode": "ltp",        # Mode: ltp, quote, full
    "message_type": "subscribe"
}
```

### Logging Configuration
Logging is configured at INFO level by default. To change log level:
```python
logging.basicConfig(level=logging.DEBUG)  # For more detailed logs
```

## Troubleshooting

### Common Issues

1. **Login Failed**
   - Check environment variables are set correctly
   - Verify TOTP secret is valid
   - Ensure API credentials are active

2. **WebSocket Connection Issues**
   - Check internet connectivity
   - Verify token is valid (not expired)
   - Check Rupeezy service status

3. **Binary Packet Decode Errors**
   - Usually indicates protocol changes
   - Check packet structure matches expected format

4. **TOTP Authentication Errors**
   - Ensure system clock is synchronized
   - Verify TOTP secret is correctly configured
   - Check if account requires additional verification

### Debug Mode
For troubleshooting, enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## File Structure
```
Rupeezy-LiveFeed/
├── rupeezy_auto_ws.py    # Main WebSocket client script
├── access_token.txt      # Generated token file (auto-created)
├── README.md             # This documentation
└── .env                  # Environment variables (create this)
```

## Security Notes
- Never commit credentials to version control
- Use environment variables for all sensitive data
- Regularly rotate API keys and passwords
- Monitor access token usage and validity

## License
This project is open source. Please ensure compliance with Rupeezy's terms of service when using their API.

## Author
**kriskingg** - [GitHub Profile](https://github.com/kriskingg)

## Disclaimer
This tool is for educational and personal use. Users are responsible for complying with Rupeezy's terms of service and applicable regulations. Use at your own risk.

---
*Last updated: October 2025*
