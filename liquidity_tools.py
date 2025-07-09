import pandas as pd
import streamlit as st
import gdown
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Replace with your Google Drive file shareable link
url = 'https://drive.google.com/uc?id=1hkNI_PPqhj0eeJwdMs7gvt8LPU7m8oA0'

# Download the file
output = 'Test_Likuid.xlsx'
gdown.download(url, output, quiet=False)

# Read the Excel file into a pandas DataFrame
df_drive = pd.read_excel(output)

# --- Google Sheets Integration ---
# Path to your service account key file
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(creds)

# Replace with the name of your Google Sheet
sheet_name = "Test_Likuid" # Or whatever your sheet is named
try:
    sheet = client.open(sheet_name).sheet1 # Opens the first worksheet
except gspread.exceptions.SpreadsheetNotFound:
    st.error(f"Google Sheet '{sheet_name}' not found. Please ensure the sheet name is correct and shared with the service account.")
    st.stop()
# --- End Google Sheets Integration ---

st.header("Editable Data Table")

# Editable columns: Item, Qty, Price (Total will be auto-calculated)
edited_data = st.data_editor(
    df_drive,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Total": st.column_config.NumberColumn(disabled=True)  # Make Total read-only
    },
    key="data_editor" # Add a key for the data_editor
)

# Calculate Total again, based on Qty and Price
edited_data["Total"] = edited_data["Qty"].fillna(0) * edited_data["Price"].fillna(0)

# Show the result
st.subheader("Updated Data:")
st.dataframe(edited_data)

if st.button("Save Changes to Google Sheet"):
    try:
        # Convert DataFrame to a list of lists (including header)
        data_to_write = [edited_data.columns.values.tolist()] + edited_data.values.tolist()

        # Clear existing data and write new data
        sheet.clear()
        sheet.update(data_to_write)
        st.success("Changes successfully saved to Google Sheet!")
    except Exception as e:
        st.error(f"Error saving data to Google Sheet: {e}")

st.caption("Note: To make changes persistent, click 'Save Changes to Google Sheet'.")
