import streamlit as st
import database
import pandas as pd

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

st.subheader("Customer Management")

conn = database.get_db_connection()

with st.expander("➕ Register New Customer", expanded=False):
    with st.form("add_customer", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            c_name = st.text_input("Customer Name")
        with c2:
            phone = st.text_input("Phone Number")
        
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not c_name or not phone:
                st.error("Name and Phone are required")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO customers(name, phone) VALUES(?,?)", (c_name, phone))
                    conn.commit()
                    st.success(f"Customer {c_name} registered successfully!")
                except Exception as e:
                    if "UNIQUE" in str(e):
                        st.error("Phone number already exists.")
                    else:
                        st.error(f"Error: {e}")

st.markdown("---")

df = pd.read_sql_query("SELECT id, name, phone, points FROM customers", conn)

if df.empty:
    st.info("No customers found.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)
