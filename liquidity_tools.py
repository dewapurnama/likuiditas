import pandas as pd
import streamlit as st
import gdown

# Replace the following URL with your own Google Drive file shareable link
url = 'https://drive.google.com/uc?id=1hkNI_PPqhj0eeJwdMs7gvt8LPU7m8oA0'

# Download the file
output = 'Test_Likuid.xlsx'
gdown.download(url, output, quiet=False)

# Read the Excel file into a pandas DataFrame
df_drive = pd.read_excel(output)
st.dataframe(df_drive)
