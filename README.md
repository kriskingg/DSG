# Beest 🐂
An automated stock trading bot that implements a sophisticated price drop buying strategy for Indian equity markets. Beest monitors eligible stocks and automatically purchases additional quantities when prices drop by specific percentage thresholds.
## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Modules](#modules)
- [Trading Strategy](#trading-strategy)
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
- Handles graceful shutdowns
### 🔐 login.py
Manages authentication with the broker API:
- Handles login credentials securely
- Maintains active sessions
- Manages token refresh
- Provides authentication services to other modules
### 📉 price_drop.py
Core logic for price drop detection and execution:
- Monitors real-time price changes
- Calculates percentage drops
- Determines purchase quantities
- Executes buy orders
- Updates DynamoDB records
### ✅ beest_eligibility_and_price_check.py
Manages stock eligibility and price validation:
- Checks if stocks meet eligibility criteria
- Validates current prices
- Updates eligibility status
- Maintains price history
## 📈 Trading Strategy
### Core Concept
Beest implements a systematic approach to buying stocks as they decline in price, based on predefined percentage thresholds.
### Purchase Logic
```
Initial Purchase: Buy BaseQuantity shares at InitialPrice
Price Drop -2%: Buy AdditionalQuantity more shares
Price Drop -4%: Buy AdditionalQuantity more shares
Price Drop -6%: Buy AdditionalQuantity more shares
... and so on
```
### Gap Down Handling
When a stock opens with a gap down:
```
If gap down >= 2%:
  Calculate: GapDownMultiplier = floor(GapDownPercentage / 2)
  Buy: GapDownMultiplier × AdditionalQuantity shares
```
### Key Parameters
- **BaseQuantity**: Initial number of shares to purchase
- **AdditionalQuantity**: Additional shares to buy at each threshold
- **InitialPrice**: First purchase price (reference point)
- **PriceDropThreshold**: Percentage drop that triggers a purchase (typically 2%)
- **LastPurchasePrice**: Most recent purchase price to prevent duplicate buys
## 🛠️ Setup Instructions
### Prerequisites
- Python 3.8+
- AWS Account (for DynamoDB)
- Broker API credentials
- Indian equity market access
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
3. Configure AWS credentials:
```bash
aws configure
```
4. Set up environment variables:
```bash
export BROKER_API_KEY="your_api_key"
export BROKER_SECRET="your_secret"
export DYNAMODB_TABLE="your_table_name"
```
### DynamoDB Setup
Create a DynamoDB table with:
- Primary Key: `StockSymbol` (String)
- Sort Key: `Timestamp` (Number)
- Required attributes:
  - `BaseQuantity`
  - `AdditionalQuantity`
  - `InitialPrice`
  - `LastPurchasePrice`
  - `IsEligible`
## 💻 Usage
### Basic Usage
```bash
python rupeezy/main.py
```
### With Custom Configuration
```bash
python rupeezy/main.py --config custom_config.json
```
### Checking Eligibility
```bash
python rupeezy/beest_eligibility_and_price_check.py
```
## ⚙️ Configuration
### config.json Example
```json
{
  "base_quantity": 10,
  "additional_quantity": 5,
  "price_drop_threshold": 2.0,
  "monitoring_interval": 60,
  "eligible_stocks": [
    "RELIANCE",
    "TCS",
    "INFY"
  ],
  "trading_hours": {
    "start": "09:15",
    "end": "15:30"
  }
}
```
### Environment Variables
- `BROKER_API_KEY`: Your broker API key
- `BROKER_SECRET`: Your broker secret
- `DYNAMODB_TABLE`: DynamoDB table name
- `AWS_REGION`: AWS region for DynamoDB
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
## 📊 Examples
### Example 1: Normal Price Drop Scenario
```
Stock: RELIANCE
InitialPrice: ₹2500
BaseQuantity: 10
AdditionalQuantity: 5
Sequence:
1. Day 1: Buy 10 shares @ ₹2500 (Initial)
2. Price drops to ₹2450 (-2%): Buy 5 shares
3. Price drops to ₹2400 (-4%): Buy 5 shares
4. Price drops to ₹2350 (-6%): Buy 5 shares
Total: 25 shares, Average Price: ₹2425
```
### Example 2: Gap Down Scenario
```
Stock: TCS
Previous Close: ₹3600
InitialPrice: ₹3600
AdditionalQuantity: 5
Scenario:
Next Day Open: ₹3480 (-3.33%)
GapDownMultiplier: floor(3.33 / 2) = 1
Action: Buy 5 shares (1x AdditionalQuantity) @ ₹3480
```
### Example 3: Large Gap Down
```
Stock: INFY
Previous Close: ₹1500
InitialPrice: ₹1500
AdditionalQuantity: 5
Scenario:
Next Day Open: ₹1450 (-3.33%)
GapDownMultiplier: floor(3.33 / 2) = 1
Action: Buy 5 shares (1x AdditionalQuantity) @ ₹1450
```
Original Example 3 had wrong math:
Previous Close: ₹150
Next Day Open: ₹145 (3.33% gap down)
Action: Buy 15 shares (3x AdditionalQuantity) at ₹145
```
## 🚀 Future Enhancements
- [ ] **Web Dashboard**: Real-time monitoring interface
- [ ] **Mobile App**: iOS/Android trading alerts
- [ ] **Advanced Analytics**: Performance tracking and reporting
- [ ] **Multi-Broker Support**: Integration with multiple brokers
- [ ] **Machine Learning**: Predictive price drop models
- [ ] **Backtesting Engine**: Strategy validation on historical data
- [ ] **Portfolio Rebalancing**: Automatic portfolio optimization
- [ ] **Options Trading**: Extend strategy to options
- [ ] **Risk Metrics**: Real-time risk assessment
- [ ] **Social Trading**: Share strategies with community
## ⚠️ Disclaimer
**IMPORTANT**: This software is for educational and research purposes only. 
- **No Financial Advice**: This is not financial advice
- **Use at Your Own Risk**: Trading involves significant financial risk
- **Test Thoroughly**: Always test with small amounts first
- **Market Risks**: Past performance doesn't guarantee future results
- **Regulatory Compliance**: Ensure compliance with local regulations
### Risk Warnings
- Automated trading can result in significant losses
- Market conditions can change rapidly
- Technical failures may occur
- Always monitor your positions
- Have stop-loss mechanisms in place
### Private Project Notice
**This is a private project. Redistribution, copying, or sharing without permission is strictly prohibited.**
## 📞 Support
For questions, issues, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the strategy document (PriceDrop_Buy_Logic.txt)
---
**Happy Trading! 🚀📈**
*Remember: The market rewards patience and discipline. Beest helps you maintain both.*
