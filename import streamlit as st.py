import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --------------------------
# DATABASE CONNECTION
# --------------------------

conn = sqlite3.connect("shop.db",check_same_thread=False)
cursor = conn.cursor()

# --------------------------
# CREATE TABLES
# --------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
price REAL,
stock INTEGER,
barcode TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales(
id INTEGER PRIMARY KEY AUTOINCREMENT,
bill_no INTEGER,
product TEXT,
qty INTEGER,
price REAL,
total REAL,
date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS returns(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product TEXT,
qty INTEGER,
date TEXT
)
""")

conn.commit()

# --------------------------
# STREAMLIT UI
# --------------------------

st.title("Retail Shop POS System")

menu = st.sidebar.selectbox(
"Select Menu",
["Add Product","Billing","Return","Inventory","Sales Report"]
)

# --------------------------
# ADD PRODUCT
# --------------------------

if menu=="Add Product":

    st.header("Add Product")

    name = st.text_input("Product Name")
    price = st.number_input("Price")
    stock = st.number_input("Stock")
    barcode = st.text_input("Barcode")

    if st.button("Add Product"):

        cursor.execute(
        "INSERT INTO products(name,price,stock,barcode) VALUES(?,?,?,?)",
        (name,price,stock,barcode)
        )

        conn.commit()

        st.success("Product Added Successfully")

# --------------------------
# BILLING SYSTEM
# --------------------------

elif menu=="Billing":

    st.header("Billing")

    df = pd.read_sql_query("SELECT * FROM products",conn)

    product = st.selectbox("Select Product",df["name"])

    qty = st.number_input("Quantity",1)

    if st.button("Add To Bill"):

        product_data = df[df["name"]==product].iloc[0]

        price = product_data["price"]
        stock = product_data["stock"]

        if qty > stock:
            st.error("Not enough stock")

        else:

            total = price * qty
            new_stock = stock - qty

            cursor.execute(
            "UPDATE products SET stock=? WHERE name=?",
            (new_stock,product)
            )

            cursor.execute(
            "INSERT INTO sales(bill_no,product,qty,price,total,date) VALUES(?,?,?,?,?,?)",
            (1,product,qty,price,total,str(datetime.now()))
            )

            conn.commit()

            st.success(f"Item added to bill | Total = {total}")

# --------------------------
# RETURN SYSTEM
# --------------------------

elif menu=="Return":

    st.header("Return Item")

    product = st.text_input("Product Name")

    qty = st.number_input("Return Quantity")

    if st.button("Return"):

        cursor.execute(
        "SELECT stock FROM products WHERE name=?",
        (product,)
        )

        data = cursor.fetchone()

        if data:

            stock = data[0]

            new_stock = stock + qty

            cursor.execute(
            "UPDATE products SET stock=? WHERE name=?",
            (new_stock,product)
            )

            cursor.execute(
            "INSERT INTO returns(product,qty,date) VALUES(?,?,?)",
            (product,qty,str(datetime.now()))
            )

            conn.commit()

            st.success("Return processed")

        else:

            st.error("Product not found")

# --------------------------
# INVENTORY
# --------------------------

elif menu=="Inventory":

    st.header("Inventory Stock")

    df = pd.read_sql_query("SELECT * FROM products",conn)

    st.dataframe(df)

    low_stock = df[df["stock"] < 10]

    if len(low_stock) > 0:

        st.warning("Low Stock Items")

        st.dataframe(low_stock)

# --------------------------
# SALES REPORT
# --------------------------

elif menu=="Sales Report":

    st.header("Sales Report")

    df = pd.read_sql_query("SELECT * FROM sales",conn)

    st.dataframe(df)

    if len(df)>0:

        total_sales = df["total"].sum()

        st.subheader(f"Total Sales = {total_sales}")

        daily_sales = df.groupby("product")["total"].sum()

        st.bar_chart(daily_sales)