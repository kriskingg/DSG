# import os
# import logging
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Setup basic logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# def get_access_token():
#     """Read access token from the file."""
#     try:
#         with open('./token/access_token.txt', 'r') as file:
#             token = file.read().strip()
#             if token:
#                 logging.debug(f"Access token retrieved: '{token}'")
#             else:
#                 logging.error("Access token is empty.")
#             return token
#     except FileNotFoundError:
#         logging.error("access_token.txt file not found.")
#         return None
#     except Exception as e:
#         logging.error(f"Error reading access token: {e}")
#         return None
