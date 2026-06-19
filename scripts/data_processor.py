import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
import sys

def main():

    land_data_processor()


def land_data_processor():
    nego_phases = [
        "TO BE IDENTIFIED",
        "FOR NEGOTIATION",
        "OPEN TO SALE OR LEASE",
        "SECURED LEASE",
        "GOVERNMENT LAND",
        "NOT AVAILABLE",
        "SECURED SALE"
    ]

    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog and get the path
    file_path_input = filedialog.askopenfilename()

    print(f"Selected file: {file_path_input}")


    # Open the 'Save As' dialog
    file_path_output = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Choose output name and path"
    )

    if file_path_output:
        print(f"File will be saved to: {file_path_output}")
    else:
        print("User cancelled the dialog")
        sys.exit() 

    
    # load newly reported entries for Ilocos Region
    land_df = pd.read_csv(file_path_input)


    # clean 'mobile_number' column; erase non-numeric characters, remove '63' at the beginning, put '0' at the beginning
    land_df["mobile_number"] = land_df["mobile_number"].astype(str)
    land_df["mobile_number"] = (
        land_df["mobile_number"]
            .str.replace(r'[^0-9]', '', regex=True)
            .str.replace(r'^63', '', regex=True)
            .str.replace(r'^9', '09', regex=True)
    )
    # filter column 'mobile_number' with more than 11 digits (philippine mobile number is only 11 digits)
    land_df.loc[land_df["mobile_number"].str.len() > 11, "mobile_number"] = np.nan


    # clear registered owner names by removing titles such as 'HON.', 'MAYOR', 'DR.', 'KAGAWAD', 'ATTY.', and 'KAP.'
    titles_pattern = r'HON\.|MAYOR|DR\.|KAGAWAD|ATTY\.|KAP\.'

    land_df["registered_owner"] = (
        land_df["registered_owner"]
        .str.replace(titles_pattern, '', regex=True)
        .str.strip()
    )
    land_df["registered_owner"]

    # handle overflow column caused by unrefined extraction
    if "Unnamed: 19" in land_df.columns:
        # combine 'remarks' and 'Unnamed: 19', also fills NaN values with empty strings
        land_df["remarks"] = land_df["remarks"].fillna('') + ':' + land_df["Unnamed: 19"].fillna('')

        # drop 'Unnamed: 19' column
        land_df = land_df.drop(columns=["Unnamed: 19"])


    # delete duplicate rows based on index, keeping the latest entry
    land_df['date'] = pd.to_datetime(land_df['date'])
    land_df = land_df.sort_values(by='date', ascending=False)
    land_df = land_df.drop_duplicates(subset=['index_no'], keep='first')
    

    # filter out entries with invalid 'nego_phase' values and store them in a separate DataFrame
    invalid_entry = land_df[~land_df["nego_phase"].isin(nego_phases)]
    land_df = land_df[land_df["nego_phase"].isin(nego_phases)]

    # check for null values in the specified columns and create a boolean mask
    null_mask = land_df[["date", "province", "municipality", "registered_owner", "remarks"]].isnull().any(axis=1)

    # append rows with null values in the specified columns to the invalid_entry DataFrame
    invalid_entry = pd.concat([invalid_entry, land_df[null_mask]], ignore_index=True)

    # remove rows with null values in the specified columns
    land_df = land_df[~land_df[["date", "province", "municipality", "registered_owner", "remarks"]].isnull().any(axis=1)]

    # create the invalid entry filename by replacing the extension of the output file path with '_invalids.csv'
    invalid_entry_filename = file_path_output.replace('.csv', '_invalids.csv')
    return land_df.to_csv(file_path_output, index=False), invalid_entry.to_csv(invalid_entry_filename, index=False)

if __name__ == "__main__":
    main() 