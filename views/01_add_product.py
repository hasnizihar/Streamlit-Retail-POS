import streamlit as st
import database

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

st.subheader("Add New Product")

with st.form("add_product", clear_on_submit=True):
    c1, c2 = st.columns([3, 2])
    with c1:
        name = st.text_input("Product Name")
        barcode = st.text_input("Barcode (optional)")
    with c2:
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        stock = st.number_input("Stock", min_value=0, step=1)

    submitted = st.form_submit_button("Add Product", use_container_width=True)

if submitted:
    if not name:
        st.error("Please provide a product name.")
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products(name,price,stock,barcode) VALUES(?,?,?,?)",
            (name, float(price), int(stock), barcode),
        )
        conn.commit()
        st.success(f"Product '{name}' added successfully!")
