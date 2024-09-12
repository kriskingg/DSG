# import logging
# import os
# from vortex_api import AsthaTradeVortexAPI

# # Setup basic logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # Retrieve necessary secrets from environment variables
# api_secret = os.getenv('RUPEEZY_API_KEY')
# application_id = os.getenv('RUPEEZY_APPLICATION_ID')
# access_token = os.getenv('RUPEEZY_ACCESS_TOKEN')

# # Create a client instance
# client = AsthaTradeVortexAPI(api_secret, application_id)
# client.access_token = access_token  # Set the access token directly

# def fetch_order_details(client, order_id):
#     """Fetch order details for a given order ID."""
#     try:
#         response = client.order_history(order_id)
#         logging.info(f"Order Details for {order_id}: {response}")
#     except Exception as e:
#         logging.error(f"Error fetching order details for {order_id}: {str(e)}")

# def fetch_positions(client):
#     """Fetch current positions."""
#     try:
#         response = client.positions()
#         logging.info(f"Current Positions: {response}")
#     except Exception as e:
#         logging.error(f"Error fetching positions: {str(e)}")

# if __name__ == "__main__":
#     # Path to the artifact file
#     artifact_path = "order_ids.txt"

#     # Check if the artifact file exists
#     if os.path.exists(artifact_path):
#         with open(artifact_path, 'r') as file:
#             order_ids = file.read().strip().splitlines()  # Read and split multiple lines into a list
#             logging.info(f"Using Order IDs from artifact: {order_ids}")
            
#             # Fetch order details for each order ID individually
#             for order_id in order_ids:
#                 fetch_order_details(client, order_id)
            
#             # Fetch current positions after processing all orders
#             fetch_positions(client)
#     else:
#         logging.error(f"Artifact file {artifact_path} not found.")
