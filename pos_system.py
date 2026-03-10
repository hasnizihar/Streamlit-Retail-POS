import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Small UI polish
st.set_page_config(page_title="Retail POS", layout="wide")

# --------------------------
# DATABASE CONNECTION
# --------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

st.markdown("# :shopping_cart: Retail Shop POS System")

menu = st.sidebar.selectbox(
    "Menu",
    ["Add Product", "Billing", "Return", "Inventory", "Sales Report"],
)

if "cart" not in st.session_state:
    st.session_state.cart = []

def cart_df():
    if not st.session_state.cart:
        return pd.DataFrame(columns=["product", "qty", "price", "total"])
    return pd.DataFrame(st.session_state.cart)

# Sidebar quick metrics
try:
    sidebar_df = pd.read_sql_query("SELECT * FROM products", conn)
    with st.sidebar:
        st.markdown("### Inventory Summary")
        st.metric("Products", len(sidebar_df))
        st.metric("Total Stock", int(sidebar_df["stock"].sum()) if len(sidebar_df) else 0)
        stock_value = (sidebar_df["price"] * sidebar_df["stock"]).sum() if len(sidebar_df) else 0
        st.metric("Stock Value", f"{stock_value:.2f}")
        low = sidebar_df[sidebar_df["stock"] < 10]
        if not low.empty:
            st.markdown("**Low stock:**")
            for _, r in low.iterrows():
                st.write(f"- {r['name']} ({int(r['stock'])})")
except Exception:
    pass

# --------------------------
# ADD PRODUCT
# --------------------------

if menu == "Add Product":
    st.subheader("Add Product")

    with st.form("add_product", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            name = st.text_input("Product Name")
            barcode = st.text_input("Barcode (optional)")
        with c2:
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            stock = st.number_input("Stock", min_value=0, step=1)

        submitted = st.form_submit_button("Add Product")

    if submitted:
        if not name:
            st.error("Please provide a product name.")
        else:
            cursor.execute(
                "INSERT INTO products(name,price,stock,barcode) VALUES(?,?,?,?)",
                (name, float(price), int(stock), barcode),
            )
            conn.commit()
            st.success("Product added successfully")

# --------------------------
# BILLING SYSTEM
# --------------------------

elif menu == "Billing":
    st.subheader("Billing / Point of Sale")

    products_df = pd.read_sql_query("SELECT * FROM products", conn)
    if products_df.empty:
        st.info("No products available — add products first.")
    else:
        left, mid, right = st.columns([2, 3, 2])

        with left:
            search = st.text_input("Search product")
            if search:
                filtered = products_df[products_df["name"].str.contains(search, case=False, na=False)]
            else:
                filtered = products_df

            product = st.selectbox("Product", filtered["name"].tolist())
            qty = st.number_input("Quantity", min_value=1, step=1)
            if st.button("Add to Cart"):
                p = products_df[products_df["name"] == product].iloc[0]
                if int(qty) > int(p["stock"]):
                    st.error("Not enough stock")
                else:
                    price = float(p["price"])
                    total = round(price * int(qty), 2)
                    st.session_state.cart.append(
                        {"product": product, "qty": int(qty), "price": price, "total": total}
                    )
                    st.success(f"Added {qty} x {product} to cart")

        with mid:
            st.markdown("**Cart**")
            df_cart = cart_df()
            st.dataframe(df_cart, use_container_width=True)
            subtotal = df_cart["total"].sum() if not df_cart.empty else 0
            st.markdown(f"**Subtotal:** {subtotal:.2f}")

        with right:
            if st.button("Clear Cart"):
                st.session_state.cart = []
            if st.button("Checkout"):
                if not st.session_state.cart:
                    st.error("Cart is empty")
                else:
                    bill_no = int(datetime.now().timestamp())
                    receipt_rows = []
                    for item in st.session_state.cart:
                        # update stock
                        cursor.execute(
                            "SELECT stock, price FROM products WHERE name=?", (item["product"],)
                        )
                        row = cursor.fetchone()
                        if not row:
                            continue
                        stock_now = int(row[0])
                        new_stock = stock_now - int(item["qty"])
                        cursor.execute(
                            "UPDATE products SET stock=? WHERE name=?", (new_stock, item["product"])
                        )
                        cursor.execute(
                            "INSERT INTO sales(bill_no,product,qty,price,total,date) VALUES(?,?,?,?,?,?)",
                            (
                                bill_no,
                                item["product"],
                                item["qty"],
                                item["price"],
                                item["total"],
                                str(datetime.now()),
                            ),
                        )
                        receipt_rows.append(item)
                    conn.commit()
                    st.success(f"Checkout complete — Bill # {bill_no}")
                    # show receipt and allow download
                    if receipt_rows:
                        receipt_df = pd.DataFrame(receipt_rows)
                        receipt_df["bill_no"] = bill_no
                        receipt_df["date"] = str(datetime.now())
                        with st.expander("View Receipt"):
                            st.write(receipt_df)
                            csv = receipt_df.to_csv(index=False).encode("utf-8")
                            st.download_button("Download Receipt (CSV)", data=csv, file_name=f"receipt_{bill_no}.csv")

                    st.session_state.cart = []
                    # refresh products_df for UI
                    products_df = pd.read_sql_query("SELECT * FROM products", conn)

# --------------------------
# RETURN SYSTEM
# --------------------------

elif menu == "Return":
    st.subheader("Process Return")
    products_df = pd.read_sql_query("SELECT * FROM products", conn)
    product = st.selectbox("Product", products_df["name"]) if not products_df.empty else None
    qty = st.number_input("Return Quantity", min_value=1, step=1)

    if st.button("Process Return"):
        if not product:
            st.error("No products available")
        else:
            cursor.execute("SELECT stock FROM products WHERE name=?", (product,))
            data = cursor.fetchone()
            if data:
                stock = int(data[0])
                new_stock = stock + int(qty)
                cursor.execute("UPDATE products SET stock=? WHERE name=?", (new_stock, product))
                cursor.execute(
                    "INSERT INTO returns(product,qty,date) VALUES(?,?,?)",
                    (product, int(qty), str(datetime.now())),
                )
                conn.commit()
                st.success("Return processed")
            else:
                st.error("Product not found")

# --------------------------
# INVENTORY
# --------------------------

elif menu == "Inventory":
    st.subheader("Inventory")
    df = pd.read_sql_query("SELECT * FROM products", conn)
    st.dataframe(df, use_container_width=True)

    low_stock = df[df["stock"] < 10]
    if not low_stock.empty:
        st.warning("Low stock items")
        st.dataframe(low_stock)

    export = st.button("Export Inventory CSV")
    if export and not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Inventory", data=csv, file_name="inventory.csv")

# --------------------------
# SALES REPORT
# --------------------------

elif menu == "Sales Report":
    st.subheader("Sales Report")
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    st.dataframe(df, use_container_width=True)

    if not df.empty:
        total_sales = df["total"].sum()
        st.metric("Total Sales", f"{total_sales:.2f}")
        sales_by_product = df.groupby("product")["total"].sum().sort_values(ascending=False)
        st.bar_chart(sales_by_product)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Export Sales CSV", data=csv, file_name="sales.csv")