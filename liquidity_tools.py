import pandas as pd
import streamlit as st
import gdown

# Replace the following URL with your own Google Drive file shareable link
url = 'https://drive.google.com/uc?id=1jrbBbdiYlYUM3wF2-9r1MpMoBFcBRPgZ'

# Download the file
output = 'Test_Likuid.xlsx'
gdown.download(url, output, quiet=False)

# Read the Excel file into a pandas DataFrame
df_drive = pd.read_excel(output)
#st.dataframe(df_drive)

# Editable columns: Item, Qty, Price (Total will be auto-calculated)
edited_data = st.data_editor(
    df_drive,
    use_container_width=True,
    num_rows="dynamic"
    }
)

# Show the result
st.write("Updated Data:")
st.dataframe(edited_data)
