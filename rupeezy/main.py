import logging
import os
import boto3
from vortex_api import AsthaTradeVortexAPI
from vortex_api import Constants as Vc

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

def fetch_eligible_stocks_from_dynamodb():
    """Fetch all eligible stocks from DynamoDB."""
    try:
        response = dynamodb.scan(
            TableName='StockEligibility',
            FilterExpression="EligibilityStatus = :status",
            ExpressionAttributeValues={':status': {'S': 'Eligible'}}
        )
        return response['Items']
    except Exception as e:
        logging.error(f"Error fetching eligible stocks from DynamoDB: {e}")
        return []

def trigger_order_via_sdk(client, order_details):
    """Trigger an order using the SDK."""
    try:
        variety = Vc.VarietyTypes.REGULAR_MARKET_ORDER if order_details['variety'] == "RL-MKT" else Vc.VarietyTypes.REGULAR_LIMIT_ORDER
        response = client.place_order(
            exchange=Vc.ExchangeTypes.NSE_EQUITY,
            token=order_details['token'],
            transaction_type=Vc.TransactionSides.BUY if order_details['transaction_type'] == "BUY" else Vc.TransactionSides.SELL,
            product=Vc.ProductTypes.DELIVERY,
            variety=variety,
            quantity=order_details['quantity'],
            price=order_details['price'],
            trigger_price=order_details['trigger_price'],
            disclosed_quantity=order_details['disclosed_quantity'],
            validity=Vc.ValidityTypes.FULL_DAY if order_details['validity'] == "DAY" else Vc.ValidityTypes.IMMEDIATE_OR_CANCEL
        )
        logging.debug(f"Order Response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error during order placement: {str(e)}")
        return None

if __name__ == "__main__":
    # Retrieve necessary secrets from environment variables
    api_secret = os.getenv('RUPEEZY_API_KEY')  # API Key from GitHub Secrets
    application_id = os.getenv('RUPEEZY_APPLICATION_ID')  # Application ID from GitHub Secrets
    access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')  # Access token from GitHub Secrets

    # Create a client instance
    client = AsthaTradeVortexAPI(api_secret, application_id)
    client.access_token = access_token  # Set the access token directly

    # Fetch eligible stocks from DynamoDB
    eligible_stocks = fetch_eligible_stocks_from_dynamodb()

    if not eligible_stocks:
        logging.info("No eligible stocks found.")
    else:
        for stock in eligible_stocks:
            order_details = {
                "exchange": "NSE_EQ",
                "token": int(stock['Token']['N']),  # Assuming the 'Token' attribute holds the token value
                "symbol": stock['InstrumentName']['S'],
                "transaction_type": "BUY",  # You can modify this based on the stock data
                "product": "DELIVERY",
                "variety": "RL-MKT",  # Assuming market order, modify if needed
                "quantity": 1,  # Modify based on your requirement
                "price": 0.0,  # For market orders, price can be 0
                "trigger_price": 0.0,
                "disclosed_quantity": 0,
                "validity": "DAY",
                "validity_days": 1,
                "is_amo": False
            }
            
            # Place the order for the eligible stock
            response = trigger_order_via_sdk(client, order_details)
            if response:
                logging.info(f"Order placed successfully for {stock['InstrumentName']['S']}: {response}")
            else:
                logging.error(f"Order placement failed for {stock['InstrumentName']['S']}")
