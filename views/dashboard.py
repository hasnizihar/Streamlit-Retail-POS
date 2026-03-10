import streamlit as st
import database
import pandas as pd
from datetime import datetime, timedelta

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

st.markdown("# :shopping_cart: Retail POS Dashboard")
st.write(f"Welcome back, **{st.session_state.username.capitalize()}**!")

try:
    conn = database.get_db_connection()
    c = conn.cursor()
    
    # --- 1. Top Level Metrics ---
    st.markdown("### Quick Stats")
    col1, col2, col3, col4 = st.columns(4)
    
    # Products
    c.execute("SELECT COUNT(*) FROM products")
    col1.metric("Products Available", c.fetchone()[0])
    
    # Customers
    c.execute("SELECT COUNT(*) FROM customers")
    col2.metric("Registered Customers", c.fetchone()[0])
    
    # Today's Sales
    today_str = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(total) FROM sales WHERE date LIKE ?", (f"{today_str}%",))
    today_sales = c.fetchone()[0]
    col3.metric("Sales Today ($)", f"{today_sales:.2f}" if today_sales else "0.00")
    
    # Low Stock Alerts
    c.execute("SELECT COUNT(*) FROM products WHERE stock < 10")
    col4.metric("Low Stock Items", c.fetchone()[0])
    
    st.markdown("---")
    
    # --- 2. Analytics Charts ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### 7-Day Revenue Trend")
        # Get past 7 days of sales
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        df_sales = pd.read_sql_query(
            "SELECT date, total FROM sales WHERE date >= ?", 
            conn, params=(seven_days_ago,)
        )
        if not df_sales.empty:
            # Parse dates and aggregate by day
            df_sales["date"] = pd.to_datetime(df_sales["date"], errors="coerce").dt.date
            daily_revenue = df_sales.groupby("date")["total"].sum().reset_index()
            daily_revenue.set_index("date", inplace=True)
            st.area_chart(daily_revenue)
        else:
            st.info("Not enough sales data for trend chart.")

    with chart_col2:
        st.markdown("#### Top 5 Best Selling Products")
        df_top = pd.read_sql_query(
            "SELECT product, SUM(total) as revenue FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 5",
            conn
        )
        if not df_top.empty:
            df_top.set_index("product", inplace=True)
            st.bar_chart(df_top)
        else:
            st.info("No sales data available yet.")
            
    st.markdown("---")

    # --- 3. Recent Transactions Log ---
    st.markdown("#### Recent Transactions (Live Feed)")
    # Get last 5 distinct bills
    df_recent = pd.read_sql_query("""
        SELECT s.bill_no, s.date, SUM(s.total) as final_total, 
               IFNULL(c.name, 'Guest') as customer_name
        FROM sales s
        LEFT JOIN customers c ON s.customer_id = c.id
        GROUP BY s.bill_no
        ORDER BY s.date DESC 
        LIMIT 5
    """, conn)
    
    if not df_recent.empty:
        # Format the dataframe for display
        df_recent["date"] = pd.to_datetime(df_recent["date"]).dt.strftime("%Y-%m-%d %I:%M %p")
        df_recent.rename(columns={
            "bill_no": "Bill No.", 
            "date": "Date & Time", 
            "final_total": "Grand Total ($)",
            "customer_name": "Customer"
        }, inplace=True)
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions have been recorded yet.")
        
except Exception as e:
    st.error(f"Error loading dashboard: {e}")
