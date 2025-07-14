import pandas as pd
import streamlit as st
import gdown

# Download the file
url = 'https://drive.google.com/uc?id=1jrbBbdiYlYUM3wF2-9r1MpMoBFcBRPgZ'
output = 'Test_Likuid.xlsx'
gdown.download(url, output, quiet=False)

# Read the Excel file
df_drive = pd.read_excel(output)

# Clean 'maturity date' column
if 'maturity date' in df_drive.columns:
    df_drive['maturity date'] = pd.to_datetime(
        df_drive['maturity date'], errors='coerce'
    )  # 'n.a.' becomes NaT

# Make the data editable with proper column config
edited_data = st.data_editor(
    df_drive,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "maturity date": st.column_config.DateColumn(
            label="Maturity Date",
            format="YYYY-MM-DD",
            required=False
        )
    }
)

# Show the result
st.write("Updated Data:")
st.dataframe(edited_data)
