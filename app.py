import streamlit as st
from db_connector import get_connection
import pandas as pd

st.set_page_config(page_title="Sales Management System", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

conn = get_connection()
cursor = conn.cursor(dictionary=True)

def login():
    st.title("Sales Management System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            st.session_state.user = user
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout():
    st.session_state.user = None
    st.rerun()

def dashboard():
    user = st.session_state.user

    st.sidebar.write(f"{user['username']} ({user['role']})")

    if st.sidebar.button("Logout"):
        logout()

    if user["role"] == "Super Admin":
        menu_options = ["Dashboard", "Add Sale", "Add Payment", "View Sales", "Reports", "SQL Query Analysis"]
    else:
        menu_options = ["Dashboard", "Add Sale", "Add Payment", "View Sales", "Reports"]

    menu = st.sidebar.selectbox("Menu", menu_options)

    if menu == "Dashboard":
        st.header("Business Overview")

        if user["role"] == "Super Admin":
            cursor.execute("SELECT SUM(gross_sales) total FROM customer_sales")
            total_sales = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT SUM(received_amount) total FROM customer_sales")
            received = cursor.fetchone()["total"] or 0
        else:
            cursor.execute("SELECT SUM(gross_sales) total FROM customer_sales WHERE branch_id = %s", (user["branch_id"],))
            total_sales = cursor.fetchone()["total"] or 0

            cursor.execute("SELECT SUM(received_amount) total FROM customer_sales WHERE branch_id = %s", (user["branch_id"],))
            received = cursor.fetchone()["total"] or 0

        pending = total_sales - received

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sales", total_sales)
        col2.metric("Received", received)
        col3.metric("Pending", pending)

    elif menu == "Add Sale":
        st.header("Add Sales Entry")

        if user["role"] == "Super Admin":
            cursor.execute("SELECT * FROM branches")
            branches = cursor.fetchall()
            branch_map = {b["branch_name"]: b["branch_id"] for b in branches}
            branch_selection = st.selectbox("Branch", list(branch_map.keys()))
            selected_branch_id = branch_map[branch_selection]
        else:
            selected_branch_id = user["branch_id"]
            st.info(f"Adding entry for your assigned Branch ID: {selected_branch_id}")

        name = st.text_input("Customer Name")
        mobile = st.text_input("Mobile")
        product = st.text_input("Product")
        amount = st.number_input("Gross Sales", min_value=0.0)

        if st.button("Save Sale"):
            cursor.execute("""
                INSERT INTO customer_sales
                (branch_id, date, name, mobile_number, product_name, gross_sales)
                VALUES (%s, CURDATE(), %s, %s, %s, %s)
            """, (selected_branch_id, name, mobile, product, amount))
            conn.commit()
            st.success("Sale added successfully!")

    elif menu == "Add Payment":
        st.header("Add Payment")

        if user["role"] == "Super Admin":
            cursor.execute("SELECT sale_id FROM customer_sales WHERE status='Open'")
        else:
            cursor.execute("SELECT sale_id FROM customer_sales WHERE status='Open' AND branch_id = %s", (user["branch_id"],))
            
        sales = [s["sale_id"] for s in cursor.fetchall()]

        if sales:
            sale_id = st.selectbox("Sale ID", sales)
            amount = st.number_input("Amount Paid", min_value=0.0)
            method = st.selectbox("Method", ["Cash", "UPI", "Card"])

            if st.button("Add Payment"):
                cursor.execute("""
                    INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                    VALUES (%s, CURDATE(), %s, %s)
                """, (sale_id, amount, method))
                conn.commit()
                st.success("Payment recorded")
        else:
            st.warning("No open sales found requiring payments.")

    elif menu == "View Sales":
        st.header("Sales Data")

        if user["role"] == "Super Admin":
            cursor.execute("""
                SELECT s.*, b.branch_name
                FROM customer_sales s
                JOIN branches b ON s.branch_id = b.branch_id
            """)
        else:
            cursor.execute("""
                SELECT s.*, b.branch_name
                FROM customer_sales s
                JOIN branches b ON s.branch_id = b.branch_id
                WHERE s.branch_id = %s
            """, (user["branch_id"],))
            
        data = cursor.fetchall()
        if data:
            st.dataframe(pd.DataFrame(data))
        else:
            st.info("No records found.")

    elif menu == "Reports":
        st.header("Analytics")

        if user["role"] == "Super Admin":
            cursor.execute("""
                SELECT b.branch_name, SUM(s.gross_sales) total_sales
                FROM customer_sales s
                JOIN branches b ON s.branch_id=b.branch_id
                GROUP BY b.branch_id
            """)
            df = pd.DataFrame(cursor.fetchall())
            if not df.empty:
                st.bar_chart(df.set_index("branch_name"))
        else:
            cursor.execute("""
                SELECT product_name, SUM(gross_sales) total_sales
                FROM customer_sales
                WHERE branch_id = %s
                GROUP BY product_name
            """, (user["branch_id"],))
            df = pd.DataFrame(cursor.fetchall())
            if not df.empty:
                st.subheader("Product Performance (Your Branch)")
                st.bar_chart(df.set_index("product_name"))
            else:
                st.info("No chart data available for this branch yet.")

    elif menu == "SQL Query Analysis" and user["role"] == "Super Admin":
        st.header(" 15 Predefined SQL Query Analysis")
        
        st.markdown("### 1. Total Sales Records")
        cursor.execute("SELECT COUNT(*) AS total_sales FROM customer_sales")
        st.metric("Row Count", cursor.fetchone()["total_sales"])
        
        st.markdown("### 2. Total Gross Sales Revenue")
        cursor.execute("SELECT SUM(gross_sales) AS total FROM customer_sales")
        st.metric("Gross Revenue", f"${cursor.fetchone()['total'] or 0:,.2f}")
        
        st.markdown("### 3. Total Received Amount")
        cursor.execute("SELECT SUM(received_amount) AS total FROM customer_sales")
        st.metric("Collected Funds", f"${cursor.fetchone()['total'] or 0:,.2f}")

        st.markdown("### 4. Total Outstanding (Pending) Amount")
        cursor.execute("SELECT SUM(pending_amount) AS total FROM customer_sales")
        st.metric("Outstanding Balance", f"${cursor.fetchone()['total'] or 0:,.2f}")

        st.markdown("### 5. Open Sales Details")
        cursor.execute("SELECT * FROM customer_sales WHERE status='Open'")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 6. Closed Sales Details")
        cursor.execute("SELECT * FROM customer_sales WHERE status='Close'")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 7. Top 3 Highest Invoiced Sales")
        cursor.execute("SELECT * FROM customer_sales ORDER BY gross_sales DESC LIMIT 3")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 8. Revenue Performance by Branch")
        cursor.execute("SELECT branch_id, SUM(gross_sales) AS revenue FROM customer_sales GROUP BY branch_id")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 9. Share of Payment Methods")
        cursor.execute("SELECT payment_method, SUM(amount_paid) AS total FROM payment_splits GROUP BY payment_method")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 10. Average Value per Transaction")
        cursor.execute("SELECT AVG(gross_sales) AS average_sale FROM customer_sales")
        st.metric("Average Sale Value", f"${cursor.fetchone()['average_sale'] or 0:,.2f}")

        st.markdown("### 11. Highest Ever Value Sale Transaction")
        cursor.execute("SELECT MAX(gross_sales) AS max_sale FROM customer_sales")
        st.metric("Max Sale Value", f"${cursor.fetchone()['max_sale'] or 0:,.2f}")

        st.markdown("### 12. Lowest Ever Value Sale Transaction")
        cursor.execute("SELECT MIN(gross_sales) AS min_sale FROM customer_sales")
        st.metric("Min Sale Value", f"${cursor.fetchone()['min_sale'] or 0:,.2f}")

        st.markdown("### 13. Transaction Volumes Count by Branch")
        cursor.execute("SELECT branch_id, COUNT(*) AS txn_count FROM customer_sales GROUP BY branch_id")
        st.dataframe(pd.DataFrame(cursor.fetchall()))

        st.markdown("### 14. Total Number of Split Installment Payments Made")
        cursor.execute("SELECT COUNT(*) AS total_payments FROM payment_splits")
        st.metric("Payment Tranches Count", cursor.fetchone()["total_payments"])

        st.markdown("### 15. Overall Pending Collection Rate (%)")
        cursor.execute("SELECT ROUND((SUM(pending_amount) / SUM(gross_sales)) * 100, 2) AS pending_percentage FROM customer_sales")
        res = cursor.fetchone()
        st.metric("Uncollected Risk Index", f"{res['pending_percentage'] or 0}%")


if st.session_state.user is None:
    login()
else:
    dashboard()