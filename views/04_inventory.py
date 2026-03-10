import streamlit as st
import database
import pandas as pd

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in to access this page.")
    st.stop()
    
# Restrict Admin
if st.session_state.role != "Admin":
    st.error("Inventory is restricted to Admin users.")
    st.stop()

st.subheader("Inventory Dashboard")

conn = database.get_db_connection()
df = pd.read_sql_query("SELECT id, name, price, stock, barcode FROM products", conn)

st.markdown("Edit directly in the table below and click **Save Changes**. To delete, select rows using the checkboxes and delete them.")

# We use session state to track if we need to rerun after a save
if "inventory_refresh" not in st.session_state:
    st.session_state.inventory_refresh = False

edited_df = st.data_editor(
    df, 
    use_container_width=True, 
    hide_index=True,
    num_rows="dynamic", # Allow deletions
    key="inventory_editor",
    disabled=["id"] # ID should not be editable
)

if st.button("Save Changes", type="primary"):
    cursor = conn.cursor()
    # Find deleted rows
    deleted_ids = set(df['id']) - set(edited_df['id'])
    for d_id in deleted_ids:
        cursor.execute("DELETE FROM products WHERE id=?", (d_id,))
    
    # Find modified or newly added rows (handling num_rows='dynamic')
    for _, row in edited_df.iterrows():
        r_id = row.get("id")
        
        # If it's a new row added directly in the table, it will have NaN for ID
        if pd.isna(r_id):
            cursor.execute(
                "INSERT INTO products (name, price, stock, barcode) VALUES (?, ?, ?, ?)",
                (row["name"], row["price"], row["stock"], row["barcode"])
            )
        else:
            # Update existing row
            cursor.execute(
                "UPDATE products SET name=?, price=?, stock=?, barcode=? WHERE id=?",
                (row["name"], row["price"], row["stock"], row["barcode"], r_id)
            )
    
    conn.commit()
    st.success("Changes saved successfully!")
    st.rerun()

low_stock = df[df["stock"] < 10]
if not low_stock.empty:
    st.warning(f"⚠️ {len(low_stock)} items are running low on stock.")
    st.dataframe(low_stock, hide_index=True)

if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Export Inventory CSV", data=csv, file_name="inventory.csv", mime="text/csv")
