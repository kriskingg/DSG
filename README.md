# Beest 🐂

An automated stock trading bot that implements a sophisticated price drop buying strategy for Indian equity markets. Beest monitors eligible stocks and ETFs, automatically purchasing additional quantities when prices drop by specific percentage thresholds.

**Current Focus:** Defence, Gold, and Silver sector ETFs for strategic portfolio diversification.

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

Beest is a Python-based automated trading system designed to capitalize on market dips by implementing a systematic approach to buying additional quantities of stocks and ETFs as their prices decline. The system uses DynamoDB for data persistence and integrates with stock market APIs for real-time price monitoring.

### Key Benefits

- **Dollar Cost Averaging**: Automatically buys more shares at lower prices
- **Risk Management**: Structured approach to prevent emotional trading
- **Gap Down Handling**: Smart logic for market gap-down scenarios
- **Real-time Monitoring**: Continuous price monitoring and execution
- **Sector ETF Focus**: Strategic focus on Defence, Gold, and Silver ETFs for diversification

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
├── rupeezy_instruments_list.txt # Supported instruments (Defence, Gold, Silver ETFs)
├── beest_flow                  # Workflow documentation
└── README.md                   # This file
```

## ✨ Key Features

### 1. Intelligent Price Drop Detection
- Monitors price drops across configurable thresholds (3%, 5%, 6%+)
- Calculates quantity to purchase based on drop severity
- Prevents redundant purchases at same price levels

### 2. Gap Down Strategy
- Special handling for market gap-downs
- Immediate execution when gap exceeds threshold
- Capitalizes on panic selling opportunities

### 3. ETF-Focused Portfolio
- **Defence Sector ETFs**: Capitalize on India's defence modernization
- **Gold ETFs**: Hedge against market volatility and inflation
- **Silver ETFs**: Industrial demand and precious metal exposure
- Easy to configure via `rupeezy_instruments_list.txt`

### 4. Enhanced Notification System
- **Price Drop Alerts**: Instant notifications when drop thresholds are met
- **Purchase Confirmations**: Detailed transaction records with timestamps
- **Eligibility Updates**: Track which instruments are ready for monitoring
- **Error Notifications**: Immediate alerts for authentication or execution issues

### 5. Automated Workflow Management
- **Scheduled Runs**: Automatic execution during market hours (Mon-Fri 9:15 AM IST)
- **Manual Triggers**: On-demand workflow runs via GitHub Actions UI
- **Authentication Flow**: Secure TOTP-based login with credential management
- **Database Integration**: Persistent storage using AWS DynamoDB

## 📦 Modules

### rupeezy/main.py
- Main orchestration logic
- Coordinates login, eligibility checks, and price monitoring
- Handles workflow execution flow

### rupeezy/login.py
- Authentication with broker platform
- TOTP generation and validation
- Session management

### rupeezy/price_drop.py
- Core price drop calculation logic
- Determines purchase quantities based on drop percentage
- Implements redundancy prevention

### rupeezy/beest_eligibility_and_price_check.py
- Validates instruments eligibility
- Real-time price monitoring
- Triggers purchases when conditions are met

## 📈 Trading Strategy

### Price Drop Thresholds

| Drop Percentage | Additional Quantity | Strategy Rationale |
|----------------|-------------------|-------------------|
| 3-4.9% | 2 shares | Moderate dip - conservative entry |
| 5-5.9% | 3 shares | Significant dip - increased position |
| 6%+ | 4 shares | Major dip - aggressive accumulation |

### Key Strategy Rules

1. **First Purchase Requirement**: Must own at least 1 share before bot activates
2. **Redundancy Prevention**: No duplicate purchases at same price level
3. **Gap Down Logic**: Immediate purchase at market open if gap exceeds threshold
4. **Intraday Monitoring**: Continuous price checks during trading hours

## 🤖 Automated Workflows

### 1. Trade_Script_with_DB.yml (Main Trading Bot)
- **Schedule**: Monday-Friday at 9:15 AM IST (`cron: '45 3 * * 1-5'`)
- **Manual Trigger**: Available via GitHub Actions UI
- **Function**: Executes complete trading cycle
  - Login authentication
  - Eligibility verification
  - Price monitoring
  - Purchase execution
  - DynamoDB logging

### 2. additional_quantity_logic.yml (Buy Logic Testing)
- **Purpose**: Test and validate buy quantity calculations
- **Manual Trigger Only**: For development and testing
- **Use Case**: Verify logic changes before production deployment

### 3. login_with_generated_totp.yml (Authentication Testing)
- **Purpose**: Validate TOTP generation and login flow
- **Manual Trigger Only**: For credential verification
- **Use Case**: Troubleshoot authentication issues

### Workflow Notification Improvements

- **Structured Logging**: All transactions recorded with timestamps and prices
- **Status Updates**: Real-time workflow status in GitHub Actions UI
- **Error Handling**: Comprehensive error messages with actionable insights
- **Purchase History**: Complete audit trail in DynamoDB

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8+
- AWS account (for DynamoDB)
- GitHub account (for Actions)
- Broker account credentials

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/kriskingg/DSG.git
   cd DSG
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter AWS Access Key ID
   # Enter AWS Secret Access Key
   # Default region: ap-south-1 (or your preferred region)
   ```

4. **Set Up GitHub Secrets**
   - Go to Repository Settings → Secrets and Variables → Actions
   - Add the following secrets:
     - `USERID`: Your broker user ID
     - `PASSWORD`: Your broker password
     - `TOTP_SECRET`: Your TOTP secret key
     - `AWS_ACCESS_KEY_ID`: AWS access key
     - `AWS_SECRET_ACCESS_KEY`: AWS secret key

5. **Configure Instruments**
   - Edit `rupeezy_instruments_list.txt` to specify ETFs/stocks to monitor

6. **Enable GitHub Actions**
   - Go to Repository → Actions → Enable workflows

### DynamoDB Table Setup

Create a DynamoDB table with the following configuration:
- **Table Name**: `beest-transactions` (or configure in code)
- **Primary Key**: `transaction_id` (String)
- **Region**: ap-south-1 (or your preferred region)

## 💻 Usage

### Automated Execution

The bot runs automatically Monday-Friday at 9:15 AM IST via GitHub Actions.

### Manual Execution

1. Navigate to Actions tab in GitHub repository
2. Select desired workflow (Trade_Script_with_DB.yml for production)
3. Click "Run workflow" → Select branch (main) → Click "Run workflow"
4. Monitor execution logs in real-time
5. Review results in DynamoDB

### Monitoring

- **GitHub Actions Logs**: Real-time execution details and status updates
- **DynamoDB Console**: Transaction history and purchase records
- **Notifications**: Integrated alerts for price drops and purchases

## ⚙️ Configuration

### ETF and Stock Selection

**File**: `rupeezy_instruments_list.txt`

Currently configured for Defence, Gold, and Silver sector ETFs:

```
DEFENCE ETF SYMBOL
GOLD ETF SYMBOL
SILVER ETF SYMBOL
```

**Setup Notes:**
- Add one instrument symbol per line
- Use exact symbols as recognized by your broker platform
- Defence ETFs: Track Indian defence sector stocks (e.g., HAL, BEL, BDL)
- Gold ETFs: Track gold prices (e.g., GOLDBEES, GOLDSHARE)
- Silver ETFs: Track silver prices (e.g., SILVERBEES, SILVERETF)
- Must own at least 1 share of each instrument before bot activates
- Bot will monitor all listed instruments during trading hours

### Notification Logic Configuration

**Default Notification Events:**
1. **Eligibility Check**: When instruments are validated for monitoring
2. **Price Drop Detection**: When drop threshold (3%/5%/6%) is met
3. **Purchase Execution**: Confirmation with quantity, price, and timestamp
4. **Error Events**: Authentication failures, API errors, execution issues

**Customization**: Modify notification settings in workflow files and Python modules.

### Price Drop Thresholds

Modify the threshold logic in `price_drop.py`:

```python
def calculate_additional_quantity(drop_percentage):
    if drop_percentage >= 6:
        return 4  # Aggressive buy on major dip
    elif drop_percentage >= 5:
        return 3  # Moderate buy on significant dip
    elif drop_percentage >= 3:
        return 2  # Conservative buy on minor dip
    else:
        return 1  # Minimal buy for small movements
```

### Workflow Schedule Configuration

Adjust automated run timing in workflow YAML files:

**File**: `.github/workflows/Trade_Script_with_DB.yml`

```yaml
on:
  schedule:
    - cron: '45 3 * * 1-5'  # 9:15 AM IST (3:45 AM UTC), Monday-Friday
  workflow_dispatch:  # Enables manual triggering
```

**Schedule Customization:**
- Cron format: `minute hour day month weekday`
- Default: 9:15 AM IST during market hours (Mon-Fri)
- Adjust for different market monitoring times
- `workflow_dispatch` enables manual runs via GitHub Actions UI

### Manual vs. Scheduled Workflow Runs

**Scheduled Runs:**
- Automatic execution based on cron schedule
- No user intervention required
- Ideal for consistent market monitoring
- Configured in workflow YAML under `schedule:`

**Manual Runs:**
- On-demand execution via GitHub Actions UI
- Useful for testing, debugging, or opportunistic trades
- Available for all workflows via `workflow_dispatch` trigger
- Steps:
  1. Go to Actions tab
  2. Select workflow
  3. Click "Run workflow"
  4. Select branch and confirm

## 📝 Examples

### Scenario 1: Defence ETF Price Drop
```
Initial Purchase: DEFENCE ETF at ₹150
Current Price: ₹145.50 (3% drop)
Action: Buy 2 additional quantities
Notification: "Defence ETF dropped 3% to ₹145.50. Purchased 2 shares."
Result: Average cost reduced to ₹147.75, position increased
```

### Scenario 2: Gold ETF Gap Down
```
Previous Close: ₹5,000
Market Open: ₹4,700 (6% gap down)
Action: Buy 4 quantities immediately
Notification: "Gold ETF gap down 6% to ₹4,700. Purchased 4 shares."
Result: Capitalized on panic selling, strong position at discount
```

### Scenario 3: Silver ETF Redundancy Prevention
```
First drop to ₹70,000: Bought 2 quantities
Price fluctuates between ₹69,500-₹71,000
Action: No additional purchase until next threshold (₹68,000 = 5% drop)
Notification: No alert sent (redundancy prevention active)
Result: Avoided overbuying at same price level
```

## 🔮 Future Enhancements

- Multi-broker support (Zerodha, Upstox, Angel One)
- Advanced technical indicators integration (RSI, MACD, Moving Averages)
- Machine learning for threshold optimization
- Mobile app for real-time notifications
- Portfolio rebalancing automation
- Risk-adjusted position sizing
- Backtesting framework
- Expanded sector coverage (IT, Banking, Pharma ETFs)
- Stop-loss automation
- Profit-taking strategies

## ⚠️ Disclaimer

This software is for educational purposes only. Use at your own risk. The authors assume no responsibility for financial losses. Always:

- Test thoroughly in paper trading mode
- Understand the code before running
- Never invest more than you can afford to lose
- Comply with all applicable regulations
- Consult with financial advisors
- Monitor automated trades regularly

**Trading involves substantial risk of loss and is not suitable for every investor.**

ETFs are subject to market risk, tracking error, and liquidity risks. Past performance is not indicative of future results.
