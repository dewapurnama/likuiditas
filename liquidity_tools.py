import streamlit as st
import pandas as pd

# Initial data
data = pd.DataFrame({
    "Item": ["Apple", "Banana"],
    "Qty": [2, 3],
    "Price": [5000, 2000],
    "Total": [10000, 6000]
})

# Editable columns: Item, Qty, Price (Total will be auto-calculated)
edited_data = st.data_editor(
    data,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Total": st.column_config.NumberColumn(disabled=True)  # Make Total read-only
    }
)

# Calculate Total again, based on Qty and Price
edited_data["Total"] = edited_data["Qty"].fillna(0) * edited_data["Price"].fillna(0)

# Show the result
st.write("Updated Data:")
st.dataframe(edited_data)
