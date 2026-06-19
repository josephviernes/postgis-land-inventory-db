import psycopg2
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import INSERT, filedialog
from queries import LoadMergeQueries

def main():
    # load your environment variables specifically the variablle containing database connection credentials
    load_dotenv()
    db_info = os.getenv("DB_URL")
    
    load(db_info)
    merge()


def load(db_url):
    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog and get the path
    file_path_input = filedialog.askopenfilename()
    print(f"Selected File: {file_path_input}")

    # fully close Tkinter instance
    root.destroy()

    try:
        # establish a connection to the database via psycopg2
        conn = psycopg2.connect(db_url)
        
        # clear any residual data from previous run
        # open the csv file in read mode
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE land_row.ground_reports_staging;")
            with open(file_path_input, 'r', encoding='utf-8') as file:
                cur.copy_expert(
                    sql="COPY land_row.ground_reports_staging FROM STDIN WITH CSV HEADER;",
                    file=file
                )

        # committing changes
        conn.commit()
        print("Data loaded to staging table")

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

def merge():
    # load variables
    load_dotenv()
    db_url = os.getenv("DB_URL")


    try:
        # connect to the database via psycopg2
        conn = psycopg2.connect(db_url)

        # open a cursor to perform database ops
        cur = conn.cursor()

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