from io import StringIO
import psycopg2
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import INSERT, filedialog
from scripts.queries import LoadMergeQueries

def main():
    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # fully close Tkinter instance
    root.destroy()

    # Open the file dialog and get the path
    processed_report = filedialog.askopenfilename()

    print(f"Selected file: {processed_report}")

    # load your environment variables specifically the variablle containing database connection credentials
    load_dotenv()
    db_info = os.getenv("DB_URL")
    staging_table = os.getenv("staging_table")
    
    load(db_info, staging_table, processed_report)
    merge(db_info)

def load(db_url, staging_table, processed_report_df):
    """Truncates the staging table and bulk-copies the cleaned CSV data into it."""
    try:
        # establish a connection to the database via psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        # convert dataframe to a CSV format in memory
        buffer = StringIO()
        processed_report_df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        # clear any residual data from previous run
        cur.execute("TRUNCATE TABLE land_row.ground_reports_staging;")

        # create a list of columns formatted for SQL
        columns = ",".join(f'"{col}"' for col in processed_report_df.columns)

        # execute bulk copy query
        sql_copy = f"COPY {staging_table} ({columns}) FROM STDIN WITH CSV"
        cur.copy_expert(sql_copy, buffer)

        # committing changes
        conn.commit()
        print("Valid reports loaded to staging table")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f" Loading to staging table failed. Database changes rolled back. Error: {e}")
    
    finally:
        # safely close communication with the database no matter what
        if cur:
            cur.close()
        if conn:
            conn.close()

def merge(db_url):
    """Executes upsert and relational queries to merge staging data into main table."""
    try:
        # connect to the database via psycopg2
        conn = psycopg2.connect(db_url)

        # open a cursor to perform database ops
        cur = conn.cursor()

        print('Executing merging queries...')
        # execute the merge query
        cur.execute(LoadMergeQueries.ground_reports_refined_upsert_query)
        cur.execute(LoadMergeQueries.insert_new_ro_query)
        cur.execute(LoadMergeQueries.fill_ro_id_query)
        cur.execute(LoadMergeQueries.update_main_table_query)

        # committing changes
        conn.commit()
        print("Data loaded to main table")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f" Merging failed. Database changes rolled back. Error: {e}")
    
    finally:
        # safely close communication with the database no matter what
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 