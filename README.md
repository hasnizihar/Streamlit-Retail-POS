# Streamlit Retail POS System 🏬

A complete Point of Sale (POS) system built with Python, Streamlit, and SQLite. This application provides a full suite of features for retail management including inventory tracking, cart checkout, customer relationships, discount systems, and live analytics.

## Features

* **Authentication System**: Role-based access control protecting sensitive pages (`Admin` vs `Cashier`).
* **Interactive Dashboard**: A live command center showing 7-day revenue trends, best-selling products, and a real-time feed of the last 5 transactions.
* **Inventory Management**: An interactive grid (`st.data_editor`) allowing admins to easily edit prices, update stock levels, and delete products directly inline.
* **Point of Sale (Billing)**: Add products to a cart, apply percentage or flat-rate discounts, link optional registered customers, and checkout.
* **PDF Receipts**: Automatically generates a downloadable PDF receipt upon checkout using `fpdf2`.
* **Advanced Reporting**: View total historical sales and filter by date range.

## Setup & Installation

### 1. Requirements
Ensure you have Python 3.8+ installed.

### 2. Clone and Install
```bash
git clone https://github.com/hasnizihar/Streamlit-Retail-POS.git
cd Streamlit-Retail-POS
pip install -r requirements.txt
```

### 3. Run the Application
The most critical step is to run the application using the Streamlit CLI, **not** the standard Python execution command:
```bash
streamlit run app.py
```

After running that command, your terminal will print out a local URL. 
- **Example:** `Local URL: http://localhost:8501`
- **Action:** Open your web browser (Chrome, Edge, etc.) and paste that exact URL into the top search bar to view your live POS dashboard.

> [!CAUTION]
> If you try to run the app using `python app.py`, it will print a warning and exit. Streamlit applications must be launched via the `streamlit run` engine to function correctly.

## Default Credentials
When the application first connects to the database, it creates a default Admin user:
- **Username:** `admin`
- **Password:** `admin`
