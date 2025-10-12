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
- [Contributing](#contributing)
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
- Handles error logging and recovery

### 💰 price_drop.py
Core module implementing the price drop buying strategy:
- Calculates percentage drops from BuyValue
- Executes buy orders based on drop thresholds
- Handles gap-down scenarios
- Manages quantity calculations (1x, 2x, 3x, etc.)

### ✅ beest_eligibility_and_price_check.py
Manages stock eligibility and price validation:
- Checks if stocks are eligible for additional buying
- Validates current market prices
- Updates eligibility status dynamically
- Performs price data quality checks

### 🔐 login.py
Handles authentication and session management:
- Manages broker API authentication
- Handles session renewal
- Secures API credentials
- Maintains connection stability

## 📈 Trading Strategy

Beest implements a mathematical approach to buying additional quantities based on percentage price drops:

### Formula
```
Percentage Drop = ((BuyValue - Current Price) / BuyValue) × 100
```

### Buying Logic
- **1-2% drop**: Buy 1x AdditionalQuantity
- **2-3% drop**: Buy 2x AdditionalQuantity  
- **3-4% drop**: Buy 3x AdditionalQuantity
- **And so on...**

### Gap Down Handling
When the market opens with a significant gap down:
- Calculate total percentage drop from BuyValue
- Purchase all missed quantities at the opening price
- Example: 3% gap down = buy 3x AdditionalQuantity

### Key Strategy Points
1. **No Redundant Buying**: Each price threshold triggers buying only once per cycle
2. **Gradual Accumulation**: More shares purchased as price drops further
3. **Market Gap Protection**: Handles overnight gaps intelligently
4. **Flexible Thresholds**: Configurable percentage levels

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- AWS Account (for DynamoDB)
- Broker API Access (Zerodha, Upstox, etc.)
- Indian Stock Market Access

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kriskingg/Beest.git
   cd Beest
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials:**
   ```bash
   aws configure
   # Enter your AWS Access Key, Secret Key, and Region
   ```

4. **Set up DynamoDB tables:**
   - Create tables for stock data, trading history, and eligibility status
   - Configure appropriate read/write capacity

5. **Configure broker API:**
   - Update `login.py` with your broker credentials
   - Test API connectivity

6. **Update instrument list:**
   - Modify `rupeezy_instruments_list.txt` with your target stocks
   - Set BuyValue and AdditionalQuantity for each instrument

## 🎮 Usage

### Basic Execution
```bash
python rupeezy/main.py
```

### Configuration Files

**rupeezy_instruments_list.txt** - Format:
```
INSTRUMENT,BuyValue,AdditionalQuantity,Eligible
ALPHAETF,100,10,true
NIFTYBEES,150,5,true
SBIETF,200,8,true
```

### Environment Variables
```bash
export AWS_REGION="your-aws-region"
export BROKER_API_KEY="your-broker-api-key"
export BROKER_SECRET="your-broker-secret"
export DYNAMODB_TABLE="your-table-name"
```

## ⚙️ Configuration

### Strategy Parameters
- **Percentage Thresholds**: Customize drop percentages (default: 1%, 2%, 3%...)
- **Additional Quantity**: Set base quantity for each stock
- **Eligibility Criteria**: Define which stocks are eligible
- **Market Hours**: Configure trading time windows

### Risk Management
- **Maximum Drop**: Set maximum percentage drop for buying
- **Daily Limits**: Configure daily purchase limits
- **Position Sizing**: Manage overall portfolio exposure

## 📚 Examples

### Example 1: Gradual Price Drop
```
Stock: ALPHAETF
BuyValue: ₹100
AdditionalQuantity: 10

Price Movement:
₹100 → ₹99 (1% drop) → Buy 10 shares
₹99 → ₹98 (2% total drop) → Buy 10 more shares
₹98 → ₹97 (3% total drop) → Buy 10 more shares

Total: 30 additional shares purchased
```

### Example 2: Gap Down Scenario
```
Stock: NIFTYBEES
BuyValue: ₹150
AdditionalQuantity: 5

Gap Down:
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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation as needed
- Test thoroughly before submitting

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

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the strategy document (PriceDrop_Buy_Logic.txt)

---

**Happy Trading! 🚀📈**

*Remember: The market rewards patience and discipline. Beest helps you maintain both.*
