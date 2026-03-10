import streamlit as st
import database
import pandas as pd
from datetime import datetime

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

# Restrict to Admin
if st.session_state.role != "Admin":
    st.error("Access is restricted to Admin users.")
    st.stop()

st.subheader("Sales Report & Analytics")

conn = database.get_db_connection()

df = pd.read_sql_query("SELECT id, bill_no, product, qty, price, total, date, customer_id FROM sales", conn)

if df.empty:
    st.info("No sales data available yet.")
    st.stop()

# Basic Date Parsing: Assuming date is stored as a string "YYYY-MM-DD HH:MM:SS.mmmmmm"
# We handle conversion safely
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["DateOnly"] = df["date"].dt.date

# Filtering
col1, col2 = st.columns(2)
with col1:
    min_d = df["DateOnly"].min()
    max_d = df["DateOnly"].max()
    if pd.isna(min_d) or pd.isna(max_d):
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
    else:
        start_date = st.date_input("Start Date", min_value=min_d, max_value=max_d, value=min_d)
        end_date = st.date_input("End Date", min_value=min_d, max_value=max_d, value=max_d)

mask = (df["DateOnly"] >= start_date) & (df["DateOnly"] <= end_date)
filtered_df = df.loc[mask].copy()

if filtered_df.empty:
    st.warning("No sales found in the selected date range.")
else:
    total_sales = filtered_df["total"].sum()
    st.metric("Total Sales in Date Range", f"${total_sales:.2f}")
    
    # Chart by Product
    sales_by_product = filtered_df.groupby("product")["total"].sum().sort_values(ascending=False)
    st.bar_chart(sales_by_product)
    
    st.dataframe(filtered_df.drop(columns=["DateOnly"]), use_container_width=True, hide_index=True)
    
    # Export
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Export Sales CSV", data=csv, file_name=f"sales_report_{start_date}_to_{end_date}.csv")
