import streamlit as st
import pandas as pd
import numpy as np
import gspread as gs
import gspread_dataframe as gd
from oauth2client.service_account import ServiceAccountCredentials

# === Google Sheets Setup ===
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gs.authorize(creds)

# === Target Sheet ===
sheet_url = 'https://docs.google.com/spreadsheets/d/1hkNI_PPqhj0eeJwdMs7gvt8LPU7m8oA0'
sheet = client.open_by_url(sheet_url)
ws = sheet.worksheet("Sheet1")

# === Load data from Google Sheet ===
df_drive = gd.get_as_dataframe(ws).fillna("")

# === Streamlit App ===
st.set_page_config(page_title="Google Sheets Editor", layout="wide")
st.title("📊 Streamlit + Google Sheets Data Editor")

st.write("### ✍️ Edit Data Below")
edited_data = st.data_editor(
    df_drive,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Total": st.column_config.NumberColumn(disabled=True)
    }
)

# Auto-calculate 'Total' column
if 'Qty' in edited_data.columns and 'Price' in edited_data.columns:
    edited_data["Total"] = pd.to_numeric(edited_data["Qty"], errors="coerce").fillna(0) * \
                           pd.to_numeric(edited_data["Price"], errors="coerce").fillna(0)
else:
    st.warning("Columns 'Qty' and 'Price' are required to calculate 'Total'.")

st.write("### ✅ Preview Updated Data")
st.dataframe(edited_data)

# === Save to Google Sheet ===
def update_data(wsname, dfupdate, urlsheet):
    sheet = client.open_by_url(urlsheet)
    wbclient = sheet.worksheet(wsname)
    wbclient.clear()
    gd.set_with_dataframe(wbclient, dfupdate)

if st.button("💾 Save to Google Sheet"):
    try:
        update_data("Sheet1", edited_data, sheet_url)
        st.success("✅ Data saved successfully to Google Sheet!")
    except Exception as e:
        st.error(f"❌ Failed to save: {e}")
