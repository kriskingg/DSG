# import boto3
# from decimal import Decimal

# # Mock function to fetch current stock price (you will replace this with a real API call)
# def get_current_price(instrument):
#     mock_prices = {
#         'ALPHAETF': 98.0,  # Example price for ALPHAETF
#         'NIFTYBEES': 97.5, # Example price for NIFTYBEES
#     }
#     return mock_prices.get(instrument, None)

# # Function to check if the stock is down by 1% or more
# def calculate_percentage_drop(buy_value, current_price):
#     return ((buy_value - current_price) / buy_value) * 100

# # Connect to DynamoDB
# dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('YourDynamoDBTable')

# # Function to update DynamoDB with new BuyValue
# def update_buy_value(instrument, new_buy_value):
#     table.update_item(
#         Key={'Instrument': instrument},
#         UpdateExpression="SET BuyValue = :bv",
#         ExpressionAttributeValues={':bv': Decimal(new_buy_value)}
#     )
#     print(f"{instrument}: BuyValue set to {new_buy_value}")

# # Function to reset BuyValue when stock becomes ineligible
# def reset_buy_value(instrument):
#     table.update_item(
#         Key={'Instrument': instrument},
#         UpdateExpression="REMOVE BuyValue"
#     )
#     print(f"{instrument}: BuyValue reset (stock ineligible)")

# # Function to process additional quantity logic
# def process_additional_quantity():
#     # Fetch eligible instruments from DynamoDB
#     response = table.scan()  # Assuming a table scan; optimize with query if needed
#     items = response.get('Items', [])

#     for item in items:
#         instrument = item['Instrument']
#         additional_quantity = int(item['AdditionalQuantity'])
#         eligibility_status = item.get('Eligibility', 'Not Eligible')
        
#         # Check if BuyValue exists; set to None if not present
#         buy_value = item.get('BuyValue', None)

#         if eligibility_status != 'Eligible':
#             print(f"{instrument} is not eligible for trading. Resetting BuyValue.")
#             reset_buy_value(instrument)
#             continue

#         # Fetch current price from the API
#         current_price = get_current_price(instrument)
#         if current_price is None:
#             print(f"Could not fetch the current price for {instrument}. Skipping.")
#             continue

#         # If stock just became eligible and there's no BuyValue, record the first transaction
#         if buy_value is None:
#             update_buy_value(instrument, current_price)
#             buy_value = Decimal(current_price)  # Set BuyValue to the current price for this iteration

#         # Calculate the percentage drop
#         percentage_drop = calculate_percentage_drop(buy_value, Decimal(current_price))

#         # Determine the action based on the percentage drop
#         if percentage_drop >= 2:
#             # If 2% down or more, buy twice the AdditionalQuantity
#             print(f"{instrument} is down by {percentage_drop:.2f}% - Buying twice the AdditionalQuantity ({2 * additional_quantity} units)")
#             # Trigger your order logic here to buy 2 * additional_quantity
#         elif percentage_drop >= 1:
#             # If 1% down or more, buy the AdditionalQuantity
#             print(f"{instrument} is down by {percentage_drop:.2f}% - Buying the AdditionalQuantity ({additional_quantity} units)")
#             # Trigger your order logic here to buy additional_quantity
#         else:
#             # If the price hasn't dropped by at least 1%, no action is taken
#             print(f"{instrument} is down by {percentage_drop:.2f}% - No action taken")

# if __name__ == "__main__":
#     process_additional_quantity()
