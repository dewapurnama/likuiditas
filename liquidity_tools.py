import pandas as pd
import streamlit as st
import gdown

url = 'https://drive.google.com/uc?id=1jrbBbdiYlYUM3wF2-9r1MpMoBFcBRPgZ'
output = 'Test_Likuid.xlsx'
gdown.download(url, output, quiet=False)

df_drive = pd.read_excel(output)

# Convert datetime column to string to make it editable
if 'maturity date' in df_drive.columns:
    df_drive['maturity date'] = df_drive['maturity date'].astype(str)

# Make a copy to avoid potential issues
df_editable = df_drive.copy()

edited_data = st.data_editor(
    df_editable,
    use_container_width=True,
    num_rows="dynamic"
)

st.write("Updated Data:")
st.dataframe(edited_data)
