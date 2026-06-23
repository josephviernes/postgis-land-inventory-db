import sys
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from google.cloud import storage
import os
from dotenv import load_dotenv
import io


def main():
    load_dotenv()
    bucket = os.getenv('bucket')
    folder = os.getenv('folder')
    invalids_folder = os.getenv('invalids_folder')

    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open the 'Save As' dialog
    output_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Choose output name and path"
    )

    if output_path:
        print(f"File will be saved to: {output_path}")
    else:
        print("User cancelled the dialog")
        sys.exit()

    # fully close Tkinter instance
    root.destroy()


    report_df = land_data_processor(bucket, folder, invalids_folder)

    # save valid reports as csv
    report_df.to_csv(output_path, index=False)

def land_data_processor(bucket_name, folder_name, invalids_folder_name) -> pd.DataFrame:
    """
    Downloads the latest ground reports from GCS, cleans the records, 
    archives invalid rows back to a separate folder in GCS, and returns the valid data.
    """
    print('Initializing GCS Client and extracting latest blob...')
    # initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # filter the gcs bucket folder for the latest file path
    blobs = list(bucket.list_blobs(prefix=folder_name)) 
    files = [blob for blob in blobs if not blob.name.endswith('/')] 
    latest_file = max(files, key=lambda b: b.updated, default=None)
    
    if not latest_file:
        print("No files found in the indicated bucket folder.")
        return None
    
    # read file content directly from GCS blob bytes into Pandas
    file_bytes = latest_file.download_as_bytes()
    land_df = pd.read_csv(io.BytesIO(file_bytes))

    nego_phases = [
        "TO BE IDENTIFIED", "FOR NEGOTIATION", "OPEN TO SALE OR LEASE",
        "SECURED LEASE", "GOVERNMENT LAND", "NOT AVAILABLE", "SECURED SALE"
    ]

    print('Commencing data transformation...')
    # clean 'mobile_number' column
    land_df["mobile_number"] = land_df["mobile_number"].astype(str)
    land_df["mobile_number"] = (
        land_df["mobile_number"]
            .str.replace(r'[^0-9]', '', regex=True)
            .str.replace(r'^63', '', regex=True)
            .str.replace(r'^9', '09', regex=True)
    )
    land_df.loc[land_df["mobile_number"].str.len() > 11, "mobile_number"] = np.nan

    # clean registered owner column 
    titles_pattern = r'HON\.|MAYOR|DR\.|KAGAWAD|ATTY\.|KAP\.'
    land_df["registered_owner"] = (
        land_df["registered_owner"]
        .astype(str) # Safeguard in case column contains floats/NaNs
        .str.replace(titles_pattern, '', regex=True)
        .str.strip()
    )

    # handle overflow column caused by unrefined extraction
    if "Unnamed: 19" in land_df.columns:
        land_df["remarks"] = land_df["remarks"].fillna('') + ':' + land_df["Unnamed: 19"].fillna('')
        land_df = land_df.drop(columns=["Unnamed: 19"])

    # delete duplicate rows based on index, keeping the latest entry
    land_df['report_date'] = pd.to_datetime(land_df['report_date'])
    land_df = land_df.sort_values(by='report_date', ascending=False)
    land_df = land_df.drop_duplicates(subset=['index_no'], keep='first')
    
    # filter out entries with invalid 'nego_phase' values
    invalid_entry = land_df[~land_df["nego_phase"].isin(nego_phases)].copy()
    land_df = land_df[land_df["nego_phase"].isin(nego_phases)].copy()

    # check for null values in specified columns and create a boolean mask
    required_cols = ["report_date", "province", "municipality", "registered_owner", "remarks"]
    null_mask = land_df[required_cols].isnull().any(axis=1)

    # append nulls to invalid dataframe, then keep inverted mask (~null_mask)
    invalid_entry = pd.concat([invalid_entry, land_df[null_mask]], ignore_index=True)
    land_df = land_df[~null_mask]

    # setup filename for the invalids export
    _, _, filename = latest_file.name.rpartition('/')
    invalid_entry_filename = filename.replace('.csv', '_invalids.csv')

    # uploads invalid entry back to GCS bucket
    if not invalid_entry.empty:
        csv_buffer = io.StringIO()
        invalid_entry.to_csv(csv_buffer, index=False)
        blob2 = bucket.blob(f"{invalids_folder_name}/{invalid_entry_filename}")
        blob2.upload_from_string(csv_buffer.getvalue(), content_type='text/csv')
        print(f'Invalid reports uploaded to gs://{bucket_name}/{invalids_folder_name}/{invalid_entry_filename}.')
    else:
        print("No invalid rows found.")

    # Return the cleaned valid dataframe object back to main()
    print('Returning valid reports...')
    return land_df

if __name__ == "__main__":
    main() 