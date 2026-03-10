import streamlit as st
import database
import pandas as pd
from datetime import datetime

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

st.subheader("Process Return")

conn = database.get_db_connection()
products_df = pd.read_sql_query("SELECT name FROM products", conn)

if products_df.empty:
    st.info("No products available.")
    st.stop()

product = st.selectbox("Product", products_df["name"])
qty = st.number_input("Return Quantity", min_value=1, step=1)

if st.button("Process Return", use_container_width=True):
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE name=?", (product,))
    data = cursor.fetchone()
    
    if data:
        stock = int(data["stock"])
        new_stock = stock + int(qty)
        
        cursor.execute("UPDATE products SET stock=? WHERE name=?", (new_stock, product))
        cursor.execute(
            "INSERT INTO returns(product,qty,date) VALUES(?,?,?)",
            (product, int(qty), str(datetime.now())),
        )
        conn.commit()
        st.success(f"Return processed for {qty}x {product}. Stock updated to {new_stock}.")
    else:
        st.error("Product not found.")
