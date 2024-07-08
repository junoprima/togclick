import pyodbc
import pymongo
import json
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# MSSQL connection details
mssql_server = '10.2.1.10'
mssql_database = 'RX2'
mssql_username = 'rx'
mssql_password = 'rxdatabase'
stored_procedure = 'Web_OrderHistory'

# MongoDB connection details
mongodb_uri = 'mongodb://togclick:P%40ssw0rd@13.251.191.127:27017'
mongodb_database = 'togclick'
mongodb_collection = 'togclick'

# File to store the last processed timestamp
timestamp_file = 'last_processed_timestamp.txt'

def get_last_processed_timestamp():
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            return file.read().strip()
    else:
        # Default to a very old date if the file does not exist
        return '1900-01-01 00:00:00'

def update_last_processed_timestamp(timestamp):
    with open(timestamp_file, 'w') as file:
        file.write(timestamp)

def fetch_data_from_mssql():
    logging.info('Connecting to MSSQL database...')
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={mssql_server};DATABASE={mssql_database};UID={mssql_username};PWD={mssql_password}')
    cursor = conn.cursor()
    logging.info('Executing stored procedure...')
    cursor.execute(f'EXEC {stored_procedure}')
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    data = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    conn.close()
    logging.info(f'Fetched {len(data)} records from MSSQL.')
    
    if data:
        logging.info(f'Sample record keys: {list(data[0].keys())}')
    
    return data

def filter_new_data(data, last_processed_timestamp):
    new_data = [record for record in data if record['FinishedDate'] > last_processed_timestamp]  # Update this field name if needed
    logging.info(f'Filtered {len(new_data)} new/updated records based on last processed timestamp.')
    return new_data

def upsert_mongodb(data):
    logging.info('Connecting to MongoDB...')
    client = pymongo.MongoClient(mongodb_uri)
    db = client[mongodb_database]
    collection = db[mongodb_collection]

    # Create an index on OrderCode and Side to speed up the upsert operation
    collection.create_index([("OrderCode", pymongo.ASCENDING), ("Side", pymongo.ASCENDING)], unique=True)
    logging.info('Index on OrderCode and Side ensured.')

    # Batch insert operation
    batch_size = 1000  # Adjust the batch size as needed
    total_batches = (len(data) + batch_size - 1) // batch_size
    logging.info(f'Starting batch upsert with batch size {batch_size}.')

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        for record in batch:
            composite_key = {'OrderCode': record['OrderCode'], 'Side': record['Side']}
            collection.update_one(composite_key, {'$set': record}, upsert=True)
        logging.info(f'Processed batch {i//batch_size + 1} of {total_batches}.')

    client.close()
    logging.info('MongoDB upsert operation completed.')

def main():
    logging.info('Script started.')
    start_time = datetime.now()

    last_processed_timestamp = get_last_processed_timestamp()
    data = fetch_data_from_mssql()
    new_data = filter_new_data(data, last_processed_timestamp)

    if new_data:
        upsert_mongodb(new_data)
        # Update the last processed timestamp
        latest_timestamp = max(record['FinishedDate'] for record in new_data)  # Update this field name if needed
        update_last_processed_timestamp(latest_timestamp)
        logging.info(f'Updated last processed timestamp to {latest_timestamp}.')
    else:
        logging.info('No new records to process.')

    end_time = datetime.now()
    logging.info(f'Script completed in {end_time - start_time}.')

if __name__ == "__main__":
    main()
