import boto3
from datetime import datetime
import pytz
import logging

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-south-1')

# Default quantity to purchase for eligible stocks
DEFAULT_QUANTITY = 5

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to calculate additional quantity based on the price drop
def calculate_additional_quantity(default_quantity, drop_percentage):
    return int(default_quantity * 2 * drop_percentage)

# Function to update stock eligibility and reset ineligible stocks
def update_stock_eligibility():
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Scan the StockEligibility table for all instruments
    response = dynamodb.scan(TableName='StockEligibility')
    items = response.get('Items', [])

    for item in items:
        instrument_name = item['InstrumentName']['S']
        eligibility = item.get('Eligibility', {}).get('S', None)
        initial_price = item.get('InitialPrice', {}).get('N', None)
        
        if eligibility == 'Eligible' and initial_price:
            initial_price = float(initial_price)
            
            # Assume we have a function to get the current price of the instrument
            current_price = get_current_price(instrument_name)
            price_drop_percentage = ((initial_price - current_price) / initial_price) * 100
            
            if price_drop_percentage > 0:
                # Calculate the total quantity to buy
                additional_quantity = calculate_additional_quantity(DEFAULT_QUANTITY, price_drop_percentage)
                total_quantity = DEFAULT_QUANTITY + additional_quantity
                logging.info(f"Stock {instrument_name} eligible with price drop of {price_drop_percentage}%. "
                             f"Placing order for {total_quantity} shares at {current_price}.")
                
                # Update LastUpdated timestamp
                dynamodb.update_item(
                    TableName='StockEligibility',
                    Key={'InstrumentName': {'S': instrument_name}, 'Eligibility': {'S': 'Eligible'}},
                    UpdateExpression="SET LastUpdated = :lu",
                    ExpressionAttributeValues={
                        ':lu': {'S': current_time}
                    }
                )
            else:
                logging.info(f"Stock {instrument_name} has no significant price drop.")
        
        elif eligibility == 'Ineligible':
            # Reset the stock details in DynamoDB
            dynamodb.update_item(
                TableName='StockEligibility',
                Key={'InstrumentName': {'S': instrument_name}},
                UpdateExpression="SET InitialPrice = :none, EligibilityStatus = :ineligible, LastUpdated = :lu",
                ExpressionAttributeValues={
                    ':none': {'N': '0'},
                    ':ineligible': {'S': 'Ineligible'},
                    ':lu': {'S': current_time}
                }
            )
            logging.info(f"Stock {instrument_name} is ineligible. Resetting initial price and status.")

# Function to get the current price of the stock (placeholder for actual API call)
def get_current_price(instrument_name):
    # You should replace this with actual stock price retrieval logic (e.g., API call)
    return 28.35  # Placeholder value for ALPHAETF

# if __name__ == "__main__":
#     update_stock_eligibility()
