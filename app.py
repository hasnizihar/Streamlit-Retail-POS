import streamlit as st
import database # Initializes the DB
import pandas as pd

# --------------------------
# PAGE CONFIGURATION
# --------------------------
st.set_page_config(page_title="Retail POS Dashboard", page_icon=":shopping_cart:", layout="wide")

# --------------------------
# SESSION STATE INITIALIZATION
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    
if "username" not in st.session_state:
    st.session_state.username = ""
    
if "role" not in st.session_state:
    st.session_state.role = ""

# --------------------------
# AUTHENTICATION FUNCTIONS
# --------------------------
def login(username, password):
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Basic plain-text authentication (upgrade to hashing in production)
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    
    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = user["role"]
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.cart = [] # clear cart on logout
    st.rerun()

# --------------------------
# LOGIN SCREEN
# --------------------------
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🏬 Retail POS System</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='background-color: #f0f2f6; padding: 2rem; border-radius: 10px; margin-top: 20px;'>", unsafe_allow_html=True)
        st.subheader("Login Access")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("Demo Credentials"):
            st.write("**Admin:** admin / admin")
            st.write("**Cashier:** cashier / cashier")

# --------------------------
# MAIN DASHBOARD (WHEN LOGGED IN)
# --------------------------
else:
    # Sidebar
    st.sidebar.markdown(f"**User Setup:** {st.session_state.username.capitalize()} ({st.session_state.role})")
    
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
        
    st.sidebar.divider()
    
    # Define Pages
    dashboard = st.Page(
        page="views/dashboard.py", # We will extract the dashboard to a view
        title="Dashboard", 
        icon=":material/dashboard:",
        default=True
    )
    add_product = st.Page("views/01_add_product.py", title="Add Product", icon=":material/add_box:")
    billing = st.Page("views/02_billing.py", title="Billing", icon=":material/point_of_sale:")
    returns = st.Page("views/03_returns.py", title="Returns", icon=":material/assignment_return:")
    customers = st.Page("views/04_customers.py", title="Customers", icon=":material/groups:")
    inventory = st.Page("views/04_inventory.py", title="Inventory", icon=":material/inventory_2:")
    sales_report = st.Page("views/05_sales_report.py", title="Sales Report", icon=":material/analytics:")

    # Navigation logic based on role
    if st.session_state.role == "Admin":
        pg = st.navigation(
            {
                "Main": [dashboard, billing, returns],
                "Management": [inventory, add_product, customers, sales_report]
            }
        )
    else:
        # Cashier role
        pg = st.navigation(
            {
                "Main": [dashboard, billing, returns],
                "Management": [customers]
            }
        )

    pg.run()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Streamlit Application")
    print("="*50)
    print("\nPlease run this application using the Streamlit CLI:\n")
    print("    streamlit run app.py\n")
    print("="*50 + "\n")
