import os
import logging
from datetime import datetime
import pytz
import sqlite3
import boto3
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# S3 Bucket configuration
S3_BUCKET_NAME = 'my-beest-db'
DB_FILE_NAME = 'beest-orders.db'

# Initialize the S3 client
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def upload_db_to_s3():
    """Upload the SQLite database to S3."""
    try:
        logging.debug("Starting upload of the database to S3...")
        s3_client.upload_file(DB_FILE_NAME, S3_BUCKET_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} uploaded to S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 upload: {e}")
    except ClientError as e:
        logging.error(f"Failed to upload {DB_FILE_NAME} to S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {e}")

def store_order(order_details):
    """Store order details in SQLite database."""
    retries = 5
    while retries > 0:
        try:
            conn = sqlite3.connect(DB_FILE_NAME)
            c = conn.cursor()
            logging.debug(f"Storing order: {order_details}")
            
            # Convert current time to IST
            ist = pytz.timezone('Asia/Kolkata')
            ist_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

            # Insert order details into the orders table
            c.execute("""
                INSERT INTO orders (symbol, quantity, price, order_type, product, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_details['symbol'],
                order_details['quantity'],
                order_details['price'],
                order_details['transaction_type'],  # Ensure this matches the correct key
                order_details['product'],
                ist_time
            ))
            conn.commit()
            conn.close()
            logging.debug("Order stored successfully.")
            break
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                retries -= 1
                sleep(1)
                logging.warning(f"Database is locked, retrying {retries} more times")
            else:
                logging.error(f"SQLite error occurred: {e}")
                break
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            break

if __name__ == '__main__':
    # Example order details (these would typically be passed from the previous script)
    order_details = {
        "symbol": "ALPHAETF",
        "quantity": 1,
        "price": 29.25,
        "transaction_type": "BUY",
        "product": "DELIVERY",
    }

    # Store the order in the database
    store_order(order_details)

    # Upload the updated database back to S3
    upload_db_to_s3()
