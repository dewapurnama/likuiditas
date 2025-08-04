import pandas as pd
import streamlit as st
import plotly.express as px
from pandas.tseries.offsets import MonthEnd
import gdown
import numpy as np
from sklearn.linear_model import LinearRegression

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
    
    # --- Sample Assumption ---
    # df_btl must contain 'Bulan' (datetime), 'Reguler', 'Khusus'
    
    # Step 1: Filter rows with valid Reguler and Khusus
    df_filtered = df_btl[
        (df_btl['Reguler'] != 0) & (df_btl['Khusus'] != 0)
    ].dropna(subset=['Reguler', 'Khusus'])
    
    # Step 2: Get last 12 valid entries
    df_last12 = df_filtered.tail(12).copy().sort_values('Bulan')
    
    # Step 3: Prepare X and Y for both models
    known_x = df_last12['Bulan'].dt.month.values.reshape(-1, 1)
    known_y_reg = df_last12['Reguler'].values
    known_y_khs = df_last12['Khusus'].values
    
    # Step 4: Train separate models
    model_reg = LinearRegression()
    model_khs = LinearRegression()
    
    model_reg.fit(known_x, known_y_reg)
    model_khs.fit(known_x, known_y_khs)
    
    # Step 5: Determine the first zero-row after last non-zero data
    last_non_zero_idx = df_btl[(df_btl['Reguler'] != 0) & (df_btl['Khusus'] != 0)].last_valid_index()
    df_after = df_btl.loc[last_non_zero_idx + 1:] if last_non_zero_idx + 1 < len(df_btl) else pd.DataFrame()
    
    # Find first row where either Reguler or Khusus is zero
    zero_start_row = df_after[
        (df_after['Reguler'] == 0) | (df_after['Khusus'] == 0)
    ].head(1)
    
    if not zero_start_row.empty:
        start_date = pd.to_datetime(zero_start_row['Bulan'].values[0]).replace(day=1)
    else:
        # fallback if no zero row found after last valid
        start_date = (df_btl['Bulan'].max() + pd.DateOffset(months=1)).replace(day=1)
    
    # Step 6: Create future dates
    end_date = pd.Timestamp("2050-12-01")
    future_dates = pd.date_range(start=start_date, end=end_date, freq="MS") + pd.offsets.MonthEnd(0)
    
    # Step 7: Predict
    future_month_nums = future_dates.month.values.reshape(-1, 1)
    
    pred_reg = np.ceil(model_reg.predict(future_month_nums))
    pred_khs = np.ceil(model_khs.predict(future_month_nums))
    
    # Step 8: Combine into DataFrame
    df_pred = pd.DataFrame({
        'bulan': future_dates,
        'batal_reg': pred_reg,
        'batal_khs': pred_khs
    })

    def compute_projection(df_pred, df_berangkat, wl_reg, wl_khs, saldo_reg, saldo_khs, sl_reg, sl_khs):
        df_merged = pd.merge(
            df_pred.copy(),
            df_berangkat[['Bulan', 'brk_reg', 'brk_khs']].copy(),
            left_on='bulan',
            right_on='Bulan',
            how='left'
        ).drop(columns=['Bulan'])
    
        df_merged[['brk_reg', 'brk_khs']] = df_merged[['brk_reg', 'brk_khs']].fillna(0).astype(int)
        df_merged['waiting_list_reg'] = 0
        df_merged['waiting_list_khs'] = 0
    
        # ==== REGULER ====
        proj_reg = df_merged.loc[0, 'batal_reg']
        ber_reg = df_merged.loc[0, 'brk_reg']
        wait_reg = max(0, wl_reg - proj_reg - ber_reg)
        df_merged.loc[0, 'waiting_list_reg'] = wait_reg
    
        for i in range(1, len(df_merged)):
            prev = df_merged.loc[i - 1, 'waiting_list_reg']
            if prev == 0:
                df_merged.loc[i:, ['waiting_list_reg', 'batal_reg', 'brk_reg']] = 0
                break
            proj = df_merged.loc[i, 'batal_reg']
            ber = df_merged.loc[i, 'brk_reg']
            rem = prev - proj
            if ber > rem:
                df_merged.loc[i, 'brk_reg'] = max(0, rem)
            df_merged.loc[i, 'waiting_list_reg'] = max(0, prev - proj - df_merged.loc[i, 'brk_reg'])
    
        # ==== KHUSUS ====
        proj_khs = df_merged.loc[0, 'batal_khs']
        ber_khs = df_merged.loc[0, 'brk_khs']
        wait_khs = max(0, wl_khs - proj_khs - ber_khs)
        df_merged.loc[0, 'waiting_list_khs'] = wait_khs
    
        for i in range(1, len(df_merged)):
            prev = df_merged.loc[i - 1, 'waiting_list_khs']
            if prev == 0:
                df_merged.loc[i:, ['waiting_list_khs', 'batal_khs', 'brk_khs']] = 0
                break
            proj = df_merged.loc[i, 'batal_khs']
            ber = df_merged.loc[i, 'brk_khs']
            rem = prev - proj
            if ber > rem:
                df_merged.loc[i, 'brk_khs'] = max(0, rem)
            df_merged.loc[i, 'waiting_list_khs'] = max(0, prev - proj - df_merged.loc[i, 'brk_khs'])
    
            
        # === Batal Value in Rupiah/Thousand USD ===
        df_merged['batal_reg (IDR juta)'] = df_merged['batal_reg'] * saldo_reg
        df_merged['batal_khs (USD ribu)'] = df_merged['batal_khs'] * saldo_khs
        
        # ==== Calculate BIPIH ====
        cutoff_date = df_merged['bulan'].min() + pd.DateOffset(months=13)
    
        def calc_bipih_reg(row):
            if row['bulan'] <= cutoff_date:
                return (row['brk_reg'] * saldo_reg) + (sl_reg if row['brk_reg'] > 0 else 0)
            else:
                return row['brk_reg'] * saldo_reg
    
        def calc_bipih_khs(row):
            if row['bulan'] <= cutoff_date:
                return (row['brk_khs'] * saldo_khs) + (sl_khs if row['brk_khs'] > 0 else 0)
            else:
                return row['brk_khs'] * saldo_khs
    
        df_merged['bipih_reg'] = df_merged.apply(calc_bipih_reg, axis=1)
        df_merged['bipih_khs'] = df_merged.apply(calc_bipih_khs, axis=1)
    
        return df_merged
        
    # Sidebar input
    # Create two columns
    col1, col2, col3, col4 = st.columns(4)
    
    # === Row 1 ===
    with col1:
        wl_reg = st.number_input("Initial Waiting List Reguler", value=5_299_092)
    with col2:
        wl_khs = st.number_input("Initial Waiting List Khusus", value=126_577)
    with col3:
        saldo_reg = st.number_input("Saldo Jemaah Reguler", value=26_837_630.65)
    with col4:
        saldo_khs = st.number_input("Saldo Jemaah Khusus", value=4_447.77)
    
    # === Row 3 ===
    with col1:
        sl_reg = st.number_input("Setoran Lunas Reguler", value=348_246_879_200.0)
    with col2:
        sl_khs = st.number_input("Setoran Lunas Khusus", value=19_980_365.77)
    with col3:
        pnp_reg = st.number_input("Penempatan Reguler", value=28_942_792_290_449.1)
    with col4:
        pnp_khs = st.number_input("Penempatan Khusus", value=378_282_969.67)

    df_final = compute_projection(df_pred, df_berangkat, wl_reg=wl_reg, wl_khs=wl_khs, 
                              saldo_reg=saldo_reg, saldo_khs=saldo_khs, sl_reg=sl_reg, sl_khs=sl_khs)

    df_final['liab_bb_reg']=df_final['batal_reg (IDR juta)']+df_final['bipih_reg']
    df_final['liab_bb_khs']=df_final['batal_khs (USD ribu)']+df_final['bipih_khs']
    df_al_bb = pd.merge(df_final, df_maturity_profile, left_on='bulan', right_on='Date', how='left').drop(columns=['Date', 'Maturity Profile DAU'])
    df_al_bb['Maturity Profile IDR'] = df_al_bb['Maturity Profile IDR'].fillna(0).astype('Int64')
    df_al_bb['Maturity Profile USD'] = df_al_bb['Maturity Profile USD'].fillna(0).astype('Int64')
    df_al_bb['Maturity Profile Khusus'] = df_al_bb['Maturity Profile Khusus'].fillna(0)
    df_al_bb['jatuh_tempo_reg'] = df_al_bb['Maturity Profile IDR']+df_al_bb['Maturity Profile USD'] 

    buckets = [1, 3, 6, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]

    maturity_profile = []
    
    # Regular buckets
    for i, bucket in enumerate(buckets):
        lower = 0 if i == 0 else buckets[i - 1]
        upper = bucket
    
        df_slice = df_al_bb.iloc[lower:upper]
    
        asset_reg = df_slice['jatuh_tempo_reg'].sum()
        liability_reg = df_slice['liab_bb_reg'].sum()
        asset_khs = df_slice['Maturity Profile Khusus'].sum()
        liability_khs = df_slice['liab_bb_khs'].sum()
    
        # ➕ Add fund_placement only to first bucket
        if i == 0:
            asset_reg += pnp_reg
            asset_khs += pnp_khs
    
        maturity_profile.append({
            'waktu': f'{bucket} mo',
            'asset_reg': asset_reg,
            'liab_reg': liability_reg,
            'asset_khs': asset_khs,
            'liab_khs': liability_khs
        })
    
    # ➕ Final "greater than" bucket
    last_upper = buckets[-1]
    df_tail = df_al_bb.iloc[last_upper:]
    
    asset_reg_tail_sum = df_tail['jatuh_tempo_reg'].sum()
    liab_reg_tail_sum = df_tail['liab_bb_reg'].sum()
    asset_khs_tail_sum = df_tail['Maturity Profile Khusus'].sum()
    liab_khs_tail_sum = df_tail['liab_bb_khs'].sum()
    
    maturity_profile.append({
        'waktu': f'>{last_upper} mo',
        'asset_reg': asset_reg_tail_sum,
        'liab_reg': liab_reg_tail_sum,
        'asset_khs': asset_khs_tail_sum,
        'liab_khs': liab_khs_tail_sum
    })
    
    # Convert to DataFrame
    df_matprof = pd.DataFrame(maturity_profile)

    def format_bucket(bucket_str):
        # Convert string like "12 mo" or ">36 mo"
        if ">" in bucket_str:
            num = int(bucket_str.replace('>','').replace(' mo',''))
            return f'>{num // 12} year'
        else:
            num = int(bucket_str.replace(' mo',''))
            if num < 12:
                return f'{num} mo'
            else:
                return f'{num // 12} year'

    col1, col2 = st.columns(2)
    with col1:
        # Apply the formatter
        df_plot = df_matprof.copy()
        df_plot['waktu'] = df_plot['waktu'].apply(format_bucket)
        
        # ---- Step 2: Scale values to Trillions ----
        df_plot['asset_reg'] = df_plot['asset_reg'] / 1_000_000_000_000
        df_plot['liab_reg'] = df_plot['liab_reg'] / 1_000_000_000_000
        
        # ---- Step 3: Melt data for Plotly ----
        df_melted = df_plot.melt(id_vars='waktu', value_vars=['asset_reg', 'liab_reg'],
                                 var_name='Type', value_name='Value')
    
        # ---- Step 3.5: Rename Type for legend ----
        df_melted['Type'] = df_melted['Type'].replace({'asset_reg': 'Asset', 'liab_reg': 'Liability'})
        # ---- Step 4: Create Bar Chart ----
        fig = px.bar(df_melted,
                     x='waktu',
                     y='Value',
                     color='Type',
                     barmode='group',
                     text='Value',
                     labels={'Value': 'Nominal (T)', 'Bucket': 'Time Bucket'},
                     title= 'Asset vs Liability by Maturity Profile (in Trillions)')
        
        # ---- Step 5: Final styling ----
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        
        fig.update_layout(
            title={
                'text': 'Maturity Profile Dana PIH Reguler',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Maturity Profile',
            yaxis_title='Nominal (triliun)',
            yaxis_tickformat=',.2f',
            bargap=0.2,
            template='plotly_white',
        
            # ✅ Legend styling (no "Type" title, centered on top)
            legend_title_text='',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Apply the formatter
        df_plot = df_matprof.copy()
        df_plot['waktu'] = df_plot['waktu'].apply(format_bucket)
        
        # ---- Step 2: Scale values to Trillions ----
        df_plot['asset_khs'] = df_plot['asset_khs'] / 1_000_000
        df_plot['liab_khs'] = df_plot['liab_khs'] / 1_000_000
        
        # ---- Step 2.5: Remove rows where both asset and liability are zero ----
        df_plot = df_plot[~((df_plot['asset_khs'] == 0) & (df_plot['liab_khs'] == 0))].copy()
        
        # ---- Step 3: Melt data for Plotly ----
        df_melted = df_plot.melt(id_vars='waktu', value_vars=['asset_khs', 'liab_khs'],
                                 var_name='Type', value_name='Value')
    
        # ---- Step 3.5: Rename Type for legend ----
        df_melted['Type'] = df_melted['Type'].replace({'asset_khs': 'Asset', 'liab_khs': 'Liability'})
        # ---- Step 4: Create Bar Chart ----
        fig = px.bar(df_melted,
                     x='waktu',
                     y='Value',
                     color='Type',
                     barmode='group',
                     text='Value',
                     labels={'Value': 'Nominal (T)', 'Bucket': 'Time Bucket'},
                     title= 'Asset vs Liability by Maturity Profile (in Trillions)')
        
        # ---- Step 5: Final styling ----
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        
        fig.update_layout(
            title={
                'text': 'Maturity Profile Dana PIH Khusus',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title='Maturity Profile',
            yaxis_title='Nominal (triliun)',
            yaxis_tickformat=',.2f',
            bargap=0.2,
            template='plotly_white',
        
            # ✅ Legend styling (no "Type" title, centered on top)
            legend_title_text='',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.write("Update Matprof:")
    edited_data_pnp = st.data_editor(
        df_matprof,
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
