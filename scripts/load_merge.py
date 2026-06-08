import psycopg2
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import INSERT, filedialog

def main():

    load()


def load():
    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog and get the path
    file_path_input = filedialog.askopenfilename()
    print(f"Selected File: {file_path_input}")

    # fully close Tkinter instance
    root.destroy()

    try:
        # load variables
        load_dotenv()
        db_url = os.getenv("DB_URL")

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

        # SQL query to merge data from staging to refined table, with conflict handling
        ground_reports_refined_upsert_query = """
            INSERT INTO ground_reports_refined (
                index_no,
                report_date,
                province,
                municipality,
                tax_dec,
                title,
                lot_number,
                survey_number,
                lot_area,
                nego_phase,
                price_sale,
                payment_terms_sale,
                price_lease,
                contract_terms_lease,
                registered_owner,
                mobile_number,
                team_id,
                remarks
            )
            SELECT
                index_no::BIGINT,
                report_date::DATE,
                province::VARCHAR,
                municipality::VARCHAR,
                tax_dec::VARCHAR,
                title::VARCHAR,
                lot_number::VARCHAR,
                survey_number::VARCHAR,
                lot_area::NUMERIC,
                nego_phase::VARCHAR,
                price_sale::NUMERIC,
                payment_terms_sale::VARCHAR,
                price_lease::NUMERIC,
                contract_terms_lease::VARCHAR,
                registered_owner::VARCHAR,
                mobile_number::VARCHAR,
                team_no::SMALLINT,
                remarks::TEXT
            FROM ground_reports_staging
            ON CONFLICT (index_no)
            DO UPDATE
            SET
                report_date = EXCLUDED.report_date,
                province = EXCLUDED.province,
                municipality = EXCLUDED.municipality,
                tax_dec = EXCLUDED.tax_dec,
                title = EXCLUDED.title,
                lot_number = EXCLUDED.lot_number,
                survey_number = EXCLUDED.survey_number,
                lot_area = EXCLUDED.lot_area,
                nego_phase = EXCLUDED.nego_phase,
                price_sale = EXCLUDED.price_sale,
                payment_terms_sale = EXCLUDED.payment_terms_sale,
                price_lease = EXCLUDED.price_lease,
                contract_terms_lease = EXCLUDED.contract_terms_lease,
                registered_owner = EXCLUDED.registered_owner,
                mobile_number = EXCLUDED.mobile_number,
                team_id = EXCLUDED.team_id,
                remarks = EXCLUDED.remarks;
        """

        # insert new registered owners into the ilocos1_ro table
        insert_new_ro_query = """
            INSERT INTO land_row.ilocos1_ro (
                registered_owner,
                contact_number
            )
            SELECT
                grf.registered_owner,
                grf.mobile_number
            FROM land_row.ground_reports_refined grf
            LEFT JOIN land_row.ilocos1_ro ro
                ON grf.registered_owner = ro.registered_owner
            WHERE ro.registered_owner IS NULL;
            """
        # update ro_id referencing ilocos1_ro table
        fill_ro_id_query = """ 
            UPDATE land_row.ground_reports_refined grf
            SET grf.ro_id = ro.id
            FROM land_row.ilocos1_ro ro
            WHERE grf.registered_owner = ro.registered_owner;
        """
        # execute the merge query
        cur.execute(ground_reports_refined_upsert_query)
        cur.execute(insert_new_ro_query)
        cur.execute(fill_ro_id_query)

        # committing changes
        conn.commit()
        print("Data loaded to staging table")

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