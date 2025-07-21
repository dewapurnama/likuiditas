import pandas as pd
import streamlit as st
import plotly.express as px
from pandas.tseries.offsets import MonthEnd
import gdown

st.set_page_config(layout="wide")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["Likuiditas Wajib", "Solvabilitas", "Proyeksi LCR", "Maturity Profile", "Liquidity Gap", "Data"])

# Download the file
url = 'https://drive.google.com/uc?id=1x5Rjpzg7Z5TmVbbeORQLopMbEdShCzD_'
output = 'Data Likuiditas.xlsx'
gdown.download(url, output, quiet=False)

tab0.markdown(
    "<h1 style='font-size:25px;'>📊 Likuiditas Wajib BPKH</h1>",
    unsafe_allow_html=True
)

with tab0:
    df_inv = pd.read_excel(output, sheet_name="Investasi")
    df_pnp = pd.read_excel(output, sheet_name="Penempatan")
    df_bpih = pd.read_excel(output, sheet_name="BPIH")

with tab0:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Likuiditas Wajib", "2.02x BPIH", "25.47% YoY, -1.00% MoM", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col2:
        st.metric("📊 Investasi Jangka Pendek", "8,44 triliun", "", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col3:
        st.metric("🟣 Penempatan PIH Reguler", "28,97 triliun", "", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")
    with col4:
        st.metric("📍 BPIH", "18,53 triliun", "-7,02% YoY", border=True, help="Angka di atas bulan sekarang bersifat proyeksi", label_visibility="visible")

with tab5:
    st.write("Update Data Investasi:")
    edited_data_inv = st.data_editor(
        df_inv,
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

    st.write("Update Data Penempatan:")
    edited_data_pnp = st.data_editor(
        df_pnp,
        use_container_width=True,
        num_rows="dynamic",
    )
    
with tab0:
    # Ensure 'maturity date' is in datetime format
    df_inv=edited_data_inv
    df_inv['Maturity Date'] = pd.to_datetime(df_inv['Maturity Date'], errors='coerce')
    df_inv['Nominal'] = pd.to_numeric(df_inv['Nominal'], errors='coerce')
    
    # Filter only rows where 'sumber dana' is "PIH Reguler"
    df_filtered = df_inv[df_inv['Sumber Dana'] == 'PIH Reguler']
    
    # Define month range as EOM at 23:59:59
    months = pd.date_range(start='2024-01-01', end='2025-12-31', freq='M')
    
    # Collect results
    results = []
    
    for month in months:
        one_year_later = month + pd.DateOffset(years=1)
    
        total_nominal = df_filtered[
            (df_filtered['Maturity Date'] >= month) &
            (df_filtered['Maturity Date'] <= one_year_later)
        ]['Nominal'].sum()
    
        results.append({
            'Date': month.strftime('%Y-%m-%d'),
            'Short-Term Inv Nominal': total_nominal
        })
    
    # Create summary DataFrame
    df_short_term_nominal = pd.DataFrame(results)
    df_short_term_nominal['Date'] = pd.to_datetime(df_short_term_nominal['Date'])

    df_pnp=edited_data_pnp
    
    df_lik = pd.merge(pd.merge(df_short_term_nominal, df_pnp, on='Date', how='outer'), df_bpih, on='Date', how='outer')
    
    # Ensure datetime
    df_lik['Date'] = pd.to_datetime(df_lik['Date'])
    
    # Format for display
    df_lik['Month'] = df_lik['Date'].dt.strftime('%b %Y')  # e.g., Jan 2024
    
    # Calculate liquidity
    df_lik['liquidity'] = (df_lik['Short-Term Inv Nominal'] + df_lik['Penempatan']) / df_lik['BPIH']
    
    # Sort by date
    df_lik = df_lik.sort_values('Date')
    
    def plot_liquidity_by_month(end_month_str):
        end_date = pd.to_datetime(end_month_str) + MonthEnd(0)
        start_date = end_date - pd.DateOffset(months=13) + pd.offsets.MonthBegin(0)
    
        df_lik['Date'] = pd.to_datetime(df_lik['Date'])
        df_filtered = df_lik[(df_lik['Date'] >= start_date) & (df_lik['Date'] <= end_date)].copy()
        df_filtered['Month'] = df_filtered['Date'].dt.strftime('%b %Y')
        df_filtered['liquidity'] = (df_filtered['Short-Term Inv Nominal'] + df_filtered['Penempatan']) / df_filtered['BPIH']
        df_filtered = df_filtered.sort_values('Date')
    
        fig = px.bar(df_filtered, x='Month', y='liquidity', text='liquidity')
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(
            title="Likuiditas Wajib (x BPIH)",
            xaxis_title="Bulan",
            yaxis_title="Likuiditas Wajib",
            template="seaborn"
        )
        fig.add_shape(type="line", x0=0, x1=1, y0=2, y1=2, xref='paper', yref='y', line=dict(color="red", width=2, dash="dot"))
        fig.add_annotation(xref='paper', x=1, y=2, text="2x BPIH", showarrow=False, font=dict(color="red"), yshift=10)
    
        st.plotly_chart(fig, use_container_width=True)

    # Layout: 1/4 for selectbox, 3/4 for plot
    col_select, col_plot = st.columns([1, 3])
    
    # Default: this month's end
    today = pd.to_datetime("today").replace(day=1)
    default_month = (today + MonthEnd(0)).strftime('%b %Y')
    
    # Month options
    months = df_lik['Date'].dt.to_period('M').dropna().unique()
    month_options = sorted([pd.Period(m, freq='M').strftime('%b %Y') for m in months])
    
    # Selectbox
    with col_select:
        selected_month_str = st.selectbox("Pilih Bulan", month_options, index=month_options.index(default_month))
    
    # Plot
    with col_plot:
        selected_month = pd.to_datetime(selected_month_str).strftime('%Y-%m')
        plot_liquidity_by_month(selected_month)

# Download the file
#url = 'https://drive.google.com/uc?id=1jrbBbdiYlYUM3wF2-9r1MpMoBFcBRPgZ'
#output = 'Test_Likuid.xlsx'
#gdown.download(url, output, quiet=False)

# Read the Excel file
#df_drive = pd.read_excel(output)

# Clean 'maturity date' column
#if 'maturity date' in df_drive.columns:
    #df_drive['maturity date'] = pd.to_datetime(
        #df_drive['maturity date'], errors='coerce'
    #)  # 'n.a.' becomes NaT

# Make the data editable with proper column config
#edited_data = st.data_editor(
    #df_drive,
    #use_container_width=True,
    #num_rows="dynamic",
    #column_config={
        #"maturity date": st.column_config.DateColumn(
            #label="Maturity Date",
            #format="YYYY-MM-DD",
            #required=False
        #)
    #}
#)

# Show the result
#st.write("Updated Data:")
#st.dataframe(edited_data)
