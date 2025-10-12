# Beest 🐂
An automated stock trading bot that implements a sophisticated price drop buying strategy for Indian equity markets. Beest monitors eligible stocks and automatically purchases additional quantities when prices drop by specific percentage thresholds.
## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Modules](#modules)
- [Trading Strategy](#trading-strategy)
- [Automated Workflows](#automated-workflows)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Future Enhancements](#future-enhancements)
- [Disclaimer](#disclaimer)
## 🎯 Overview
Beest is a Python-based automated trading system designed to capitalize on market dips by implementing a systematic approach to buying additional quantities of stocks as their prices decline. The system uses DynamoDB for data persistence and integrates with stock market APIs for real-time price monitoring.
### Key Benefits
- **Dollar Cost Averaging**: Automatically buys more shares at lower prices
- **Risk Management**: Structured approach to prevent emotional trading
- **Gap Down Handling**: Smart logic for market gap-down scenarios
- **Real-time Monitoring**: Continuous price monitoring and execution
## 🏗️ Architecture
```
Beest/
├── rupeezy/                     # Main application package
│   ├── main.py                 # Application entry point
│   ├── login.py                # Authentication handler
│   ├── price_drop.py           # Core price drop logic
│   └── beest_eligibility_and_price_check.py  # Eligibility checker
├── .github/workflows/          # GitHub Actions automation
│   ├── Trade_Script_with_DB.yml        # Main trading bot automation
│   ├── additional_quantity_logic.yml   # Buy logic testing
│   └── login_with_generated_totp.yml   # Authentication testing
├── PriceDrop_Buy_Logic.txt     # Strategy documentation
├── requirements.txt            # Python dependencies
├── rupeezy_instruments_list.txt # Supported instruments
├── beest_flow                  # Workflow documentation
└── README.md                   # This file
```
## ✨ Key Features
- **Automated Price Monitoring**: Real-time tracking of eligible stocks
- **Percentage-Based Buying**: Purchases additional quantities based on price drop percentages
- **Gap Down Detection**: Handles market gap-down scenarios intelligently
- **DynamoDB Integration**: Persistent storage for stock data and trading history
- **Eligibility Management**: Dynamic eligibility checking for stocks
- **Redundancy Prevention**: Avoids duplicate purchases at same price levels
## 📦 Modules
### 🚀 main.py
The main entry point of the application that orchestrates the entire trading workflow:
- Initializes the trading environment
- Coordinates between different modules
- Manages the main execution loop
### 🔐 login.py
Handles authentication with the trading platform:
- Manages session tokens
- Implements TOTP-based two-factor authentication
- Handles login failures and retries
- Secures API credentials
### 📉 price_drop.py
Core module implementing the price drop buying strategy:
- Monitors real-time price changes
- Calculates percentage drops from initial purchase price
- Executes buy orders based on predefined thresholds
- Implements gap-down detection logic
- Updates DynamoDB with transaction records
- Prevents duplicate purchases at same price levels
### ✅ beest_eligibility_and_price_check.py
Manages stock eligibility and price verification:
- Validates if stocks meet eligibility criteria
- Fetches current market prices
- Cross-references with eligible stock list
- Updates stock status in database
## 📊 Trading Strategy
### Price Drop Thresholds
The bot purchases additional quantities based on these percentage drops:
| Drop % | Action |
|--------|--------|
| 1% | Buy 1 additional quantity |
| 2% | Buy 1 additional quantity |
| 3% | Buy 2 additional quantities |
| 4% | Buy 2 additional quantities |
| 5% | Buy 3 additional quantities |
| 6%+ | Buy 4 additional quantities |
### Gap Down Logic
Special handling for stocks that open significantly lower:
1. Detects gap-down at market open
2. Calculates drop percentage from previous close
3. Executes appropriate buy quantity based on gap percentage
4. Updates tracking to prevent redundant purchases
### Redundancy Prevention
- Tracks all executed purchases in DynamoDB
- Maintains price level history
- Prevents multiple purchases at same drop threshold
- Ensures systematic execution without duplication
## 🤖 Automated Workflows
Beest includes several GitHub Actions workflows for automation and testing:
### 📈 Trade_Script_with_DB.yml
**Purpose**: Main production trading automation workflow
**Trigger**: Scheduled (Monday-Friday at 3:45 AM UTC / 9:15 AM IST)
**Key Functions**:
- Runs the complete trading bot during market hours
- Authenticates with TOTP-based two-factor authentication
- Monitors eligible stocks and executes price drop strategy
- Updates DynamoDB with transaction data
- Handles errors and provides execution logs
**Environment**: Uses AWS credentials and trading API secrets from GitHub Secrets
**Note**: Currently commented out for safety - uncomment when ready for production
### 🧪 additional_quantity_logic.yml
**Purpose**: Testing workflow for additional quantity buying logic
**Trigger**: Manual workflow dispatch
**Key Functions**:
- Tests the price drop threshold calculations
- Validates quantity determination logic
- Ensures gap-down scenarios are handled correctly
- Verifies redundancy prevention mechanisms
**Use Case**: Development and testing of core buying logic before production deployment
**Note**: Currently commented out - enable when testing logic changes
### 🔑 login_with_generated_totp.yml
**Purpose**: Authentication and TOTP generation testing
**Trigger**: Scheduled (weekdays at 3:45 AM UTC) and manual dispatch
**Key Functions**:
- Tests authentication flow with trading platform
- Validates TOTP (Time-based One-Time Password) generation
- Verifies session token management
- Ensures login reliability before trading operations
**Status**: Active workflow for continuous authentication monitoring
### Workflow Benefits
- **Automation**: Eliminates manual intervention for daily trading
- **Consistency**: Executes strategy systematically without emotional bias
- **Reliability**: Continuous testing of authentication and core logic
- **Monitoring**: Provides logs and alerts for troubleshooting
- **Security**: Credentials managed through GitHub Secrets
## 🛠️ Setup Instructions
### Prerequisites
- Python 3.8+
- AWS Account (for DynamoDB)
- Trading platform account with API access
- TOTP secret for two-factor authentication
### Installation
1. Clone the repository:
```bash
git clone https://github.com/kriskingg/Beest.git
cd Beest
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="your_region"
export TRADING_API_KEY="your_api_key"
export TOTP_SECRET="your_totp_secret"
```
4. Configure DynamoDB tables:
- Create table for stock data
- Create table for transaction history
- Set up appropriate indexes
## 🚀 Usage
### Running Locally
```bash
python rupeezy/main.py
```
### Running via GitHub Actions
1. Set up GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `TRADING_API_KEY`
   - `TOTP_SECRET`
2. Uncomment desired workflow in `.github/workflows/`
3. Workflow will run on schedule or manual trigger
### Monitoring
- Check GitHub Actions logs for execution details
- Monitor DynamoDB for transaction records
- Review price drop alerts and purchase confirmations
## ⚙️ Configuration
### Stock Eligibility
Edit `rupeezy_instruments_list.txt` to modify the list of eligible stocks.
### Price Drop Thresholds
Modify the threshold logic in `price_drop.py`:
```python
def calculate_additional_quantity(drop_percentage):
    if drop_percentage >= 6:
        return 4
    elif drop_percentage >= 5:
        return 3
    elif drop_percentage >= 3:
        return 2
    else:
        return 1
```
### Schedule
Adjust workflow schedules in workflow YAML files:
```yaml
schedule:
  - cron: '45 3 * * 1-5'  # Runs Mon-Fri at 9:15 AM IST
```
## 📝 Examples
### Scenario 1: Normal Price Drop
```
Initial Purchase: Stock XYZ at ₹100
Current Price: ₹97 (3% drop)
Action: Buy 2 additional quantities
Result: Average cost reduced, position increased
```
### Scenario 2: Gap Down
```
Previous Close: ₹100
Market Open: ₹94 (6% gap down)
Action: Buy 4 quantities immediately
Result: Capitalized on gap-down opportunity
```
### Scenario 3: Redundancy Prevention
```
First drop to ₹97: Bought 2 quantities
Price fluctuates between ₹96-₹98
Action: No additional purchase until next threshold (₹95)
Result: Avoided redundant purchases
```
## 🔮 Future Enhancements
- Multi-broker support
- Advanced technical indicators integration
- Machine learning for threshold optimization
- Mobile app for real-time notifications
- Portfolio rebalancing automation
- Risk-adjusted position sizing
- Backtesting framework
## ⚠️ Disclaimer
This software is for educational purposes only. Use at your own risk. The authors assume no responsibility for financial losses. Always:
- Test thoroughly in paper trading mode
- Understand the code before running
- Never invest more than you can afford to lose
- Comply with all applicable regulations
- Consult with financial advisors
**Trading involves substantial risk of loss and is not suitable for every investor.**
