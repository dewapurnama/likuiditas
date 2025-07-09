st.write("📝 Input your data below:")
input_data = st.data_editor(
    data.drop(columns=["Total"]),
    num_rows="dynamic",
    use_container_width=True
)

# Calculate output
input_data["Total"] = input_data["Qty"].fillna(0) * input_data["Price"].fillna(0)

st.write("📊 Auto-calculated result:")
st.dataframe(input_data)
