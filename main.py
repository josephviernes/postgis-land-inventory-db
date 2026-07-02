from scripts.data_processor import land_data_processor as transform
from scripts.load_merge import load, merge
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    bucket = os.getenv('bucket')
    folder = os.getenv('folder')
    invalids_folder = os.getenv('invalids_folder')
    db_url = os.getenv('DB_URL')
    staging_table = os.getenv("staging_table")

    latest_report_df = transform(bucket, folder, invalids_folder)
    load(db_url, staging_table, latest_report_df)
    merge(db_url)

if __name__ == "__main__": 
    main()