import pandas as pd
import streamlit as st
import plotly.express as px
from pandas.tseries.offsets import MonthEnd
import gdown

st.set_page_config(layout="wide")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["Likuiditas Wajib", "Solvabilitas", "Proyeksi LCR", "Maturity Profile", "Liquidity Gap", "Data"])

# Download the file
url = 'https://drive.google.com/uc?id=16O_hbQ167m9Pnhj84T1IMXvW0hJaeoGf'
output = 'Data Likuiditas (1).xlsx'
gdown.download(url, output, quiet=False)

tab0.markdown(
    "<h1 style='font-size:25px;'>📊 Likuiditas Wajib BPKH</h1>",
    unsafe_allow_html=True
)

with tab0:
    df_inv = pd.read_excel(output, sheet_name="Investasi")
    df_pnp = pd.read_excel(output, sheet_name="Penempatan")
    df_bpih = pd.read_excel(output, sheet_name="BPIH")

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

    st.write("Update Data BPIH:")
    edited_data_bpih = st.data_editor(
        df_bpih,
        use_container_width=True,
        num_rows="dynamic",
    )
    
with tab0:
    # === Prepare Data ===
    df_inv = edited_data_inv
    df_bpih = edited_data_bpih
    df_inv['Maturity Date'] = pd.to_datetime(df_inv['Maturity Date'], errors='coerce')
    df_inv['Nominal'] = pd.to_numeric(df_inv['Nominal'], errors='coerce')

    df_filtered = df_inv[df_inv['Sumber Dana'] == 'PIH Reguler']

    months = pd.date_range(start='2024-01-01', end='2025-12-31', freq='M')
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

    df_short_term_nominal = pd.DataFrame(results)
    df_short_term_nominal['Date'] = pd.to_datetime(df_short_term_nominal['Date'])

    df_pnp = edited_data_pnp
    df_lik = pd.merge(pd.merge(df_short_term_nominal, df_pnp, on='Date', how='outer'), df_bpih, on='Date', how='outer')

    df_lik['Date'] = pd.to_datetime(df_lik['Date'])
    df_lik['Month'] = df_lik['Date'].dt.strftime('%b %Y')
    df_lik['liquidity'] = (df_lik['Short-Term Inv Nominal'] + df_lik['Penempatan']) / df_lik['BPIH']
    df_lik = df_lik.sort_values('Date')

    # === Select Month ===
    col_select, col_empty = st.columns([1, 3])
    today = pd.to_datetime("today").replace(day=1)
    default_month = (today + MonthEnd(0)).strftime('%b %Y')

    months = pd.date_range(start='2025-01-01', end='2025-12-31', freq='M')
    month_options = [m.strftime('%b %Y') for m in months]

    with col_select:
        selected_month_str = st.selectbox("",
            month_options,
            index=month_options.index(default_month) if default_month in month_options else 0, label_visibility="collapsed"
        )
    with col_empty:
        st.empty()

    # === Extract Metrics for Selected Month ===
    selected_date = pd.to_datetime(selected_month_str) + MonthEnd(0)
    row = df_lik[df_lik['Date'] == selected_date]

    # Find previous dates
    prev_month = selected_date - MonthEnd(1)
    prev_year = selected_date - pd.DateOffset(years=1)
    prev_year = prev_year + MonthEnd(0)  # Normalize to EOM

    # Get current & previous values
    def get_val(col, date):
        val = df_lik[df_lik['Date'] == date][col]
        return val.values[0] if not val.empty and pd.notnull(val.values[0]) else None
    
    # Current values
    curr_liq = get_val('liquidity', selected_date)
    curr_inv = get_val('Short-Term Inv Nominal', selected_date)
    curr_pnp = get_val('Penempatan', selected_date)
    curr_bpih = get_val('BPIH', selected_date)
    
    # Previous values
    prev_liq_m = get_val('liquidity', prev_month)
    prev_liq_y = get_val('liquidity', prev_year)
    prev_inv_m = get_val('Short-Term Inv Nominal', prev_month)
    prev_inv_y = get_val('Short-Term Inv Nominal', prev_year)
    prev_pnp_m = get_val('Penempatan', prev_month)
    prev_pnp_y = get_val('Penempatan', prev_year)
    prev_bpih_m = get_val('BPIH', prev_month)
    prev_bpih_y = get_val('BPIH', prev_year)
    
    # Format delta
    def calc_delta(curr, prev):
        if curr is None or prev is None or prev == 0:
            return "-"
        return f"{(curr - prev) / prev * 100:.2f}%"
    
    # Format trillions
    def format_tril(val):
        return f"{val / 1e12:.2f} triliun" if val is not None else "-"
    
    # Show metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "🔥 Likuiditas Wajib",
            f"{curr_liq:.2f}x BPIH" if curr_liq is not None else "-",
            f"{calc_delta(curr_liq, prev_liq_y)} YoY || {calc_delta(curr_liq, prev_liq_m)} MoM",
            border=True,
            help="Angka di atas bulan sekarang bersifat proyeksi",
            label_visibility="visible"
        )
    with col2:
        st.metric(
            "📊 Investasi Jangka Pendek",
            format_tril(curr_inv),
            f"{calc_delta(curr_inv, prev_inv_y)} YoY || {calc_delta(curr_inv, prev_inv_m)} MoM",
            border=True,
            help="Angka di atas bulan sekarang bersifat proyeksi",
            label_visibility="visible"
        )
    with col3:
        st.metric(
            "🟣 Penempatan PIH Reguler",
            format_tril(curr_pnp),
            f"{calc_delta(curr_pnp, prev_pnp_y)} YoY || {calc_delta(curr_pnp, prev_pnp_m)} MoM",
            border=True,
            help="Angka di atas bulan sekarang bersifat proyeksi",
            label_visibility="visible"
        )
    with col4:
        st.metric(
            "📍 BPIH",
            format_tril(curr_bpih),
            f"{calc_delta(curr_bpih, prev_bpih_y)} YoY",
            border=True,
            help="Angka di atas bulan sekarang bersifat proyeksi",
            label_visibility="visible"
        )

    
with tab0:
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
    #col_select, col_plot = st.columns([1, 3])
    
    # Default: this month's end
    #today = pd.to_datetime("today").replace(day=1)
    #default_month = (today + MonthEnd(0)).strftime('%b %Y')
    
    # Month options: Jan–Dec 2025
    #months = pd.date_range(start='2025-01-01', end='2025-12-31', freq='M')
    #month_options = [m.strftime('%b %Y') for m in months]
    
    # Selectbox
    #with col_select:
        #selected_month_str = st.selectbox(
            #"Pilih Bulan",
            #month_options,
            #index=month_options.index(default_month) if default_month in month_options else 0
        #)
    
    # Plot
    #with col_plot:
    selected_month = pd.to_datetime(selected_month_str).strftime('%Y-%m')
    plot_liquidity_by_month(selected_month)

with tab3:
    df_btl = pd.read_excel(output, sheet_name="Pembatalan")
    df_berangkat = pd.read_excel(output, sheet_name="Keberangkatan")
    
    # Ensure proper datetime conversion
    df_inv['Maturity Date'] = pd.to_datetime(df_inv['Maturity Date'], errors='coerce')
    df_inv['Settlement Date'] = pd.to_datetime(df_inv['Settlement Date'], errors='coerce')
    df_inv['Tanggal Jual'] = pd.to_datetime(df_inv['Tanggal Jual'], errors='coerce')
    
    # Drop rows with no Maturity Date and explicitly copy to avoid SettingWithCopyWarning
    df_inv = df_inv.dropna(subset=['Maturity Date']).copy()
    
    # Extract Maturity Month safely
    df_inv.loc[:, 'Maturity Month'] = df_inv['Maturity Date'].dt.to_period('M').dt.to_timestamp('M')
    valid_dates = sorted(df_inv['Maturity Month'].unique())
    
    # Report reference
    report_date = pd.Timestamp('2025-06-30')
    perolehan_cutoff = report_date - MonthEnd(1)
    
    # Result holder
    result = []
    
    for dt in valid_dates:
        start_of_month = dt - MonthEnd(1)
        end_of_month = dt
    
        # Common filter: maturity month & settlement cutoff & no sale
        date_filter = (
            (df_inv['Maturity Date'] > start_of_month) &
            (df_inv['Maturity Date'] <= end_of_month) &
            (df_inv['Settlement Date'] <= perolehan_cutoff) &
            (df_inv['Tanggal Jual'].isna())
        )
    
        # Filter for PIH Reguler
        reguler = df_inv[(df_inv['Sumber Dana'] == "PIH Reguler") & date_filter]
        idr_total = reguler[reguler['Ccy'] == "IDR"]['Nominal'].sum()
        usd_total = reguler[reguler['Ccy'] == "USD"]['Nominal'].sum()
    
        # Filter for PIH Khusus
        khusus = df_inv[(df_inv['Sumber Dana'] == "PIH Khusus") & date_filter]
        usd_khusus_total = khusus[khusus['Ccy'] == "USD"]['Nominal'].sum()
        sar_khusus_total = khusus[khusus['Ccy'] == "SAR"]['Nominal'].sum() / 3.75
        total_khusus = usd_khusus_total + sar_khusus_total
    
        # Filter for DAU
        khusus = df_inv[(df_inv['Sumber Dana'] == "DAU") & date_filter]
        dau_total = khusus[khusus['Ccy'] == "IDR"]['Nominal'].sum()
    
        # Append result
        result.append({
            'Date': dt,
            'Maturity Profile IDR': idr_total,
            'Maturity Profile USD': usd_total,
            'Maturity Profile Khusus': total_khusus,
            'Maturity Profile DAU': dau_total
        })
    
    # Final DataFrame
    df_maturity_profile = pd.DataFrame(result)
    st.write("Update Matprof:")
    edited_data_pnp = st.data_editor(
        df_berangkat,
        use_container_width=True,
        num_rows="dynamic",
    )

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
