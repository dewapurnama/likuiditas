import pandas as pd
import streamlit as st
import gdown

st.set_page_config(layout="wide")

tab0, tab1, tab2, tab3, tab4 = st.tabs(["Likuiditas Wajib", "Solvabilitas", "Proyeksi LCR", "Maturity Profile", "Liquidity Gap"])

tab0.markdown(
    "<h1 style='font-size:25px;'>📊 Likuiditas Wajib BPKH</h1>",
    unsafe_allow_html=True
)

with tab0:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Likuiditas Wajib", "2.02x BPIH", delta="25.47% YoY / -1.00% MoM", delta_color="off", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col2:
        st.metric("📊 Investasi Jangka Pendek", "8,44 triliun", "", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col3:
        st.metric("🟣 Penempatan PIH Reguler", "28,97 triliun", "", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col4:
        st.metric("📍 BPIH", "18,53 triliun", "-7,02% YoY", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
        
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
