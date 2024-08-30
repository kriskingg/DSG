import os
import sqlite3
import logging
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

# S3 Bucket configuration
S3_BUCKET_NAME = 'my-beest-db'
DB_FILE_NAME = 'orders_test.db'

# Initialize the S3 client
logging.debug(f"Using AWS region: {AWS_DEFAULT_REGION}")

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def download_db_from_s3():
    """Download the SQLite database from S3."""
    try:
        logging.debug("Starting download of the database from S3...")
        s3_client.download_file(S3_BUCKET_NAME, DB_FILE_NAME, DB_FILE_NAME)
        logging.info(f"Database {DB_FILE_NAME} downloaded from S3 bucket {S3_BUCKET_NAME}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logging.error(f"Credentials error during S3 download: {e}")
    except ClientError as e:
        logging.error(f"Failed to download {DB_FILE_NAME} from S3 bucket: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during S3 download: {e}")

def modify_db():
    """Modify the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE_NAME)
        c = conn.cursor()
        # Insert new test data
        c.execute("INSERT INTO test_table (test_column) VALUES ('Modified Test Data')")
        conn.commit()
        conn.close()
        logging.info("New test data inserted successfully.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred while modifying data: {e}")

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

if __name__ == '__main__':
    # Download the database from S3
    download_db_from_s3()

    # Modify the database
    modify_db()

    # Upload the modified database back to S3
    upload_db_to_s3()
