import streamlit as st
import database
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()

st.subheader("Billing / Point of Sale")

conn = database.get_db_connection()

if "cart" not in st.session_state:
    st.session_state.cart = []

def get_cart_df():
    if not st.session_state.cart:
        return pd.DataFrame(columns=["product", "qty", "price", "total"])
    return pd.DataFrame(st.session_state.cart)

def generate_pdf_receipt(bill_no, receipt_rows, customer_name, subtotal, discount, grand_total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(w=200, h=10, text="Retail POS - Receipt", new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.set_font("helvetica", size=12)
    pdf.cell(w=200, h=10, text=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align='L')
    pdf.cell(w=200, h=10, text=f"Bill No: {bill_no}", new_x="LMARGIN", new_y="NEXT", align='L')
    if customer_name:
        pdf.cell(w=200, h=10, text=f"Customer: {customer_name}", new_x="LMARGIN", new_y="NEXT", align='L')
        
    pdf.line(10, 45, 200, 45)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(w=80, h=10, text='Item', border=1)
    pdf.cell(w=30, h=10, text='Qty', border=1)
    pdf.cell(w=40, h=10, text='Price', border=1)
    pdf.cell(w=40, h=10, text='Total', border=1, new_x="LMARGIN", new_y="NEXT")

    # Table Data
    pdf.set_font("helvetica", size=12)
    for item in receipt_rows:
        pdf.cell(w=80, h=10, text=str(item['product']), border=1)
        pdf.cell(w=30, h=10, text=str(item['qty']), border=1)
        pdf.cell(w=40, h=10, text=f"${item['price']:.2f}", border=1)
        pdf.cell(w=40, h=10, text=f"${item['total']:.2f}", border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(w=200, h=10, text=f"Subtotal: ${subtotal:.2f}", new_x="LMARGIN", new_y="NEXT", align='R')
    if discount > 0:
        pdf.cell(w=200, h=10, text=f"Discount: -${discount:.2f}", new_x="LMARGIN", new_y="NEXT", align='R')
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(w=200, h=10, text=f"Grand Total: ${grand_total:.2f}", new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.cell(w=200, h=10, text="Thank you for your purchase!", new_x="LMARGIN", new_y="NEXT", align='C')
    
    return bytes(pdf.output())

products_df = pd.read_sql_query("SELECT * FROM products", conn)
customers_df = pd.read_sql_query("SELECT id, name, phone FROM customers", conn)

if products_df.empty:
    st.info("No products available — add products first from Inventory/Add Product.")
else:
    left, right = st.columns([3, 2])

    with left:
        st.markdown("### Add Items to Cart")
        search = st.text_input("Search product by name or barcode")
        if search:
            filtered = products_df[
                products_df["name"].str.contains(search, case=False, na=False) |
                products_df["barcode"].str.contains(search, case=False, na=False)
            ]
        else:
            filtered = products_df

        if not filtered.empty:
            product = st.selectbox("Product", filtered["name"].tolist())
            qty = st.number_input("Quantity", min_value=1, step=1)
            if st.button("Add to Cart", use_container_width=True):
                p = products_df[products_df["name"] == product].iloc[0]
                # Check current cart for existing qty
                current_qty_in_cart = sum([item["qty"] for item in st.session_state.cart if item["product"] == product])
                
                if (int(qty) + current_qty_in_cart) > int(p["stock"]):
                    st.error("Not enough stock available!")
                else:
                    price = float(p["price"])
                    total = round(price * int(qty), 2)
                    
                    # See if product is already in cart, if so update qty, else append
                    found = False
                    for item in st.session_state.cart:
                        if item["product"] == product:
                            item["qty"] += int(qty)
                            item["total"] = round(item["price"] * item["qty"], 2)
                            found = True
                            break
                    
                    if not found:
                        st.session_state.cart.append(
                            {"product": product, "qty": int(qty), "price": price, "total": total}
                        )
                    st.success(f"Added {qty} x {product} to cart")
        else:
            st.warning("No matching products found.")
            

    with right:
        st.markdown("### Checkout")
        
        # Customer Selection
        st.markdown("**Link Customer (Optional)**")
        customer_options = ["None"] + [f"{row['name']} ({row['phone']})" for _, row in customers_df.iterrows()]
        selected_customer = st.selectbox("Customer", customer_options)
        
        st.markdown("**Cart Details**")
        df_cart = get_cart_df()
        
        if df_cart.empty:
            st.info("Cart is currently empty.")
        else:
            # We display cart items with an option to remove them
            for idx, item in enumerate(st.session_state.cart):
                colA, colB, colC = st.columns([3, 1, 1.5])
                with colA:
                    st.write(f"**{item['product']}** (x{item['qty']})")
                with colB:
                    st.write(f"${item['total']:.2f}")
                with colC:
                    if st.button("Drop", key=f"remove_{idx}", help="Remove this item", use_container_width=True, icon=":material/delete:"):
                        st.session_state.cart.pop(idx)
                        st.rerun()

        st.markdown("---")
        subtotal = df_cart["total"].sum() if not df_cart.empty else 0.0
        
        # Discount Calculation
        discount_type = st.radio("Apply Discount", ["None", "Percentage (%)", "Flat Amount ($)"], horizontal=True)
        discount_amount = 0.0
        
        if discount_type == "Percentage (%)":
            d_val = st.number_input("Discount %", min_value=0.0, max_value=100.0, step=1.0)
            discount_amount = round(subtotal * (d_val / 100), 2)
        elif discount_type == "Flat Amount ($)":
            d_val = st.number_input("Discount Amount", min_value=0.0, max_value=float(subtotal), step=1.0)
            discount_amount = d_val
            
        grand_total = subtotal - discount_amount
        
        st.markdown(f"**Subtotal: ${subtotal:.2f}**")
        if discount_amount > 0:
            st.markdown(f"**Discount: -${discount_amount:.2f}**")
        st.markdown(f"#### Grand Total: ${grand_total:.2f}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        with c2:
            if st.button("Complete Sale", type="primary", use_container_width=True):
                if not st.session_state.cart:
                    st.error("Cart is empty")
                else:
                    bill_no = int(datetime.now().timestamp())
                    customer_id = None
                    customer_name = ""
                    if selected_customer != "None":
                        # Extract phone to find ID
                        phone = selected_customer.split("(")[1].replace(")", "")
                        cust_row = customers_df[customers_df["phone"] == phone]
                        if not cust_row.empty:
                            customer_id = int(cust_row.iloc[0]["id"])
                            customer_name = cust_row.iloc[0]["name"]

                    receipt_rows = []
                    cursor = conn.cursor()
                    
                    # Pro-rate discount to accurately log revenue
                    discount_ratio = 1.0 - (discount_amount / subtotal) if subtotal > 0 else 1.0
                    
                    for item in st.session_state.cart:
                        # Update stock (double check just in case)
                        cursor.execute("SELECT stock, price FROM products WHERE name=?", (item["product"],))
                        row = cursor.fetchone()
                        if row:
                            stock_now = int(row["stock"])
                            new_stock = stock_now - int(item["qty"])
                            cursor.execute(
                                "UPDATE products SET stock=? WHERE name=?", (new_stock, item["product"])
                            )
                            # Log sale
                            item_db_total = round(item["total"] * discount_ratio, 2)
                            cursor.execute(
                                """INSERT INTO sales(bill_no,product,qty,price,total,date,customer_id) 
                                   VALUES(?,?,?,?,?,?,?)""",
                                (
                                    bill_no,
                                    item["product"],
                                    item["qty"],
                                    item["price"],
                                    item_db_total,
                                    str(datetime.now()),
                                    customer_id
                                ),
                            )
                            receipt_rows.append(item)
                            
                    # Optionally award points to customer (1 point per 10$ spent)
                    if customer_id:
                        points_earned = int(grand_total // 10)
                        cursor.execute("UPDATE customers SET points = points + ? WHERE id = ?", (points_earned, customer_id))

                    conn.commit()
                    st.session_state.cart = [] # Clear cart after sale
                    
                    st.success(f"Checkout complete! Bill # {bill_no}")
                    st.session_state.receipt_data = {
                        "bill_no": bill_no,
                        "rows": receipt_rows,
                        "customer": customer_name,
                        "subtotal": subtotal,
                        "discount": discount_amount,
                        "total": grand_total
                    }
                    st.rerun()

    # Show receipt generation if a sale just completed
    if "receipt_data" in st.session_state:
        st.markdown("---")
        st.markdown(f"**Receipt for Bill #{st.session_state.receipt_data['bill_no']}**")
        rd = st.session_state.receipt_data
        pdf_bytes = generate_pdf_receipt(rd["bill_no"], rd["rows"], rd["customer"], rd["subtotal"], rd["discount"], rd["total"])
        st.download_button(
            label="📄 Download PDF Receipt",
            data=pdf_bytes,
            file_name=f"receipt_{rd['bill_no']}.pdf",
            mime="application/pdf"
        )
        if st.button("Close Receipt"):
            del st.session_state.receipt_data
            st.rerun()
