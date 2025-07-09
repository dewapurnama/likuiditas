import streamlit as st
import pandas as pd

# Initial data
data = pd.DataFrame({
    "Item": ["Apple", "Banana"],
    "Qty": [2, 3],
    "Price": [5000, 2000],
    "Total": [10000, 6000]
})

# User edits table
edited_data = st.data_editor(
    data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Total": st.column_config.NumberColumn(disabled=True)  # Read-only formula column
    }
)

# Update Total with formula Qty * Price
edited_data["Total"] = edited_data["Qty"].fillna(0) * edited_data["Price"].fillna(0)

# Optional: show the updated result again
# You can choose to hide this if you want one table only
# st.dataframe(edited_data)
