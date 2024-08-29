import logging
from db_operations import create_connection, create_table, insert_order
from s3_operations import upload_to_s3
from beest_etf import trigger_order_on_rupeezy, check_order_status, fetch_trade_details

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

DB_FILE = "beest-orders.db"

if __name__ == '__main__':
    # Example data for the order
    token = 7412  # Updated token for ALPHA
    order_quantity = 1  # Default quantity

    order_details = {
        "exchange": "NSE_EQ",
        "token": token,
        "symbol": "ALPHA",
        "transaction_type": "BUY",
        "product": "DELIVERY",
        "variety": "RL-MKT",  # Market Order
        "quantity": order_quantity,
        "price": 0.00,  # Price set to 0 for market order
        "trigger_price": 0.00,
        "disclosed_quantity": 0,
        "validity": "DAY",
        "validity_days": 1,
        "is_amo": False
    }
    
    response = trigger_order_on_rupeezy(order_details)
    if response and response.get('status') == 'success':
        order_id = response['data'].get('orderId')
        logging.info(f"Order placed successfully with ID: {order_id}")
        
        # Check order status to ensure it's executed
        if check_order_status(order_id):
            # Fetch trade details after the order is executed
            trade_details = fetch_trade_details(order_id)
            if trade_details:
                executed_price = trade_details.get('trade_price')
                logging.info(f"Order executed at price: {executed_price}")
                
                # Store the order details in the database
                conn = create_connection(DB_FILE)
                if conn is not None:
                    create_table(conn)
                    order_entry = ("ALPHA", order_quantity, executed_price, "BUY", "DELIVERY", executed_price)
                    insert_order(conn, order_entry)
                    conn.close()

                    # Upload the database to S3
                    upload_to_s3(DB_FILE, 'my-beest-db')
                else:
                    logging.error("Failed to create the database connection.")
            else:
                logging.error("Failed to fetch trade details. Exiting.")
        else:
            logging.error("Order was not executed successfully. Exiting.")
    else:
        logging.error(f"Failed to place order. Response: {response}")
