import boto3
import logging

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def upload_to_s3(db_file, bucket_name):
    """Upload the database file to S3."""
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(db_file, bucket_name, db_file)
        logging.info(f"Database {db_file} uploaded to S3 bucket {bucket_name}.")
    except Exception as e:
        logging.error(f"Failed to upload {db_file} to S3: {e}")
