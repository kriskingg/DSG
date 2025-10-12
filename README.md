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
- Implements percentage-based buying logic
- Handles gap-down scenarios
- Executes buy orders
- Updates DynamoDB records

### ✅ beest_eligibility_and_price_check.py

Manages stock eligibility and price verification:

- Checks if stocks are eligible for trading
- Verifies current market prices
- Updates eligibility status in database
- Provides price data to other modules

## 📊 Trading Strategy

### Core Concept

The strategy is based on buying additional quantities of stocks as they drop in price by specific percentage thresholds (typically 2%):

1. **Initial Purchase**: Buy initial quantity at entry price
2. **Price Drop Monitoring**: Monitor for 2% price drops
3. **Additional Purchases**: Buy more shares at each 2% drop level
4. **Gap Down Handling**: Smart multiplier-based buying for overnight gaps

### Key Attributes per Stock

- **InitialPrice**: Entry price for the stock
- **AdditionalQuantity**: Number of shares to buy at each drop
- **LastActionPrice**: Last price at which action was taken
- **EligibilityStatus**: Whether stock is eligible for trading

### Gap Down Logic

When a stock gaps down (opens significantly lower than previous close):

```python
GapDownPercentage = ((PreviousClose - CurrentPrice) / PreviousClose) × 100
GapDownMultiplier = floor(GapDownPercentage / 2)
QuantityToBuy = GapDownMultiplier × AdditionalQuantity
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- AWS Account (for DynamoDB)
- Broker API credentials (e.g., Zerodha, Angel One)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kriskingg/Beest.git
   cd Beest
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials**
   ```bash
   aws configure
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```
   BROKER_API_KEY=your_api_key
   BROKER_API_SECRET=your_api_secret
   AWS_REGION=your_region
   DYNAMODB_TABLE_NAME=your_table_name
   ```

5. **Initialize DynamoDB table**
   Run the setup script (if provided) or create table manually

## 🎮 Usage

### Running the Bot

```bash
python rupeezy/main.py
```

### Monitoring

The bot will:
- Log in to broker API
- Load eligible stocks from DynamoDB
- Monitor prices continuously
- Execute trades automatically based on strategy
- Update database with trade information

### Stopping the Bot

Use `Ctrl+C` for graceful shutdown

## ⚙️ Configuration

### Stock Eligibility

Stocks must meet these criteria:
- Listed in `rupeezy_instruments_list.txt`
- Have `EligibilityStatus` = true in DynamoDB
- Have required attributes (InitialPrice, AdditionalQuantity)

### Adjustable Parameters

- **Price Drop Percentage**: Default 2%, configurable per stock
- **Additional Quantity**: Number of shares per drop level
- **Monitoring Interval**: Frequency of price checks
- **Maximum Position Size**: Upper limit on total holdings

## 📝 Examples

### Example 1: Regular Price Drop

```
Stock: RELIANCE
InitialPrice: ₹2500
AdditionalQuantity: 5

Scenario:
- Price drops to ₹2450 (-2%): Buy 5 shares @ ₹2450
- Price drops to ₹2400 (-4%): Buy 5 shares @ ₹2400
- Price drops to ₹2350 (-6%): Buy 5 shares @ ₹2350

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

---

## 🚀 Future Enhancements

### 📊 Analytics & Monitoring

- [ ] **Web Dashboard** - Real-time monitoring interface with live charts and position tracking
- [ ] **Advanced Analytics** - Comprehensive performance tracking, P&L reports, and trade history analysis
- [ ] **Risk Metrics** - Real-time risk assessment with position sizing and exposure monitoring

### 📱 Mobile & Accessibility

- [ ] **Mobile App** - iOS/Android applications with push notifications for trading alerts
- [ ] **Social Trading** - Community features to share strategies and performance insights

### 🤖 Intelligence & Automation

- [ ] **Machine Learning** - Predictive models for price drop probability and optimal entry points
- [ ] **Backtesting Engine** - Validate strategies against historical data with detailed simulation reports
- [ ] **Portfolio Rebalancing** - Automatic portfolio optimization based on performance and risk parameters

### 🔧 Platform Expansion

- [ ] **Multi-Broker Support** - Integration with multiple brokers (Zerodha, Upstox, Angel One, etc.)
- [ ] **Options Trading** - Extend the price drop strategy to options contracts
- [ ] **International Markets** - Support for US, European, and other global markets

---

## ⚠️ Disclaimer

### 📢 Important Notice

**This software is provided for educational and research purposes only.**

### 🚨 Risk Warnings

#### Financial Risks
- ❌ **No Financial Advice** - This tool does NOT constitute financial, investment, or trading advice
- 💰 **Significant Loss Potential** - Automated trading can result in substantial financial losses
- 📉 **Market Volatility** - Markets can change rapidly and unpredictably, leading to unexpected outcomes
- ⏱️ **Past Performance** - Historical results do not guarantee or predict future performance

#### Technical Risks
- 🔧 **System Failures** - Technical glitches, API failures, or connectivity issues may occur
- 💻 **Software Bugs** - Despite testing, the software may contain bugs or errors
- 🔌 **Downtime** - Broker APIs or AWS services may experience unexpected downtime

#### Trading Risks
- 🎯 **Test First** - Always test thoroughly with small amounts or paper trading before live deployment
- 👀 **Active Monitoring** - Never leave automated systems completely unattended
- 🛡️ **Stop Loss** - Implement and maintain proper stop-loss mechanisms
- 📊 **Position Sizing** - Use appropriate position sizes relative to your total portfolio

### ⚖️ Regulatory & Legal

- 📜 **Compliance Required** - Ensure full compliance with your local securities regulations
- 🌍 **Jurisdictional Differences** - Trading laws vary by country and region
- 🔒 **Know Your Obligations** - Understand tax implications and reporting requirements

### 💡 Best Practices

- ✅ Start with paper trading or minimal capital
- ✅ Understand the strategy completely before deploying
- ✅ Monitor positions regularly and have an exit plan
- ✅ Keep detailed records of all trades for tax purposes
- ✅ Only invest what you can afford to lose

---

## 🔒 Private Project Notice

### 📋 Usage Rights

**This is a private project.**

- 🚫 **No Redistribution** - Redistribution of this code is strictly prohibited
- 🚫 **No Copying** - Copying or replicating this software without permission is not allowed
- 🚫 **No Sharing** - Sharing with third parties requires explicit written permission
- 📧 **Contact Required** - For licensing inquiries, please open an issue on GitHub

### ⚡ Authorized Use

This code is intended solely for:
- ✅ Personal use by authorized individuals
- ✅ Educational study and research
- ✅ Evaluation purposes with proper authorization

All other uses require prior written consent from the project owner.

---

## 📞 Support

### 🆘 Getting Help

If you encounter issues or have questions:

#### 1️⃣ Check Documentation First
- 📖 Review this README thoroughly
- 📄 Read the strategy document: `PriceDrop_Buy_Logic.txt`
- 🔄 Check the workflow diagram: `beest_flow`

#### 2️⃣ Search Existing Issues
- 🔍 Browse [existing GitHub issues](https://github.com/kriskingg/Beest/issues) for similar problems
- 💡 Many common questions are already answered

#### 3️⃣ Create New Issue
- 🐛 **Bug Reports** - Include error messages, logs, and steps to reproduce
- 💡 **Feature Requests** - Clearly describe the proposed enhancement
- ❓ **Questions** - Provide context about what you're trying to accomplish

#### 4️⃣ Issue Guidelines

When opening an issue, please include:
- ✏️ Clear and descriptive title
- 📝 Detailed description of the problem or question
- 🖥️ Environment details (OS, Python version, broker)
- 📋 Relevant code snippets or logs (sanitize sensitive data)
- ✅ Steps already taken to troubleshoot

---

**Happy Trading! 🚀📈**

*Remember: The market rewards patience and discipline. Beest helps you maintain both.* 🐂💪
