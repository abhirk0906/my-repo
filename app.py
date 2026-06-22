import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Sales Management System", layout="wide", page_icon="📊")

# DATABASE CONNECTION
def run_query(sql_string):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",         
        password=st.secrets["db_password"],     
        database="Sales_Management"
    )
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(sql_string)
    
    if sql_string.strip().upper().startswith("SELECT"):
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        cursor.close()
        conn.close()
        return df
    else:
        conn.commit()
        cursor.close()
        conn.close()
        return True

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_branch_id' not in st.session_state:
    st.session_state['user_branch_id'] = None
if 'user_branch_name' not in st.session_state:
    st.session_state['user_branch_name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None


if st.session_state['logged_in'] == False:
    st.title("Sales Management System")
    st.subheader("Welcome Login Page")
    st.info("Please login to check the customer sales report")
    
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        login_sql = f"SELECT u.*, b.branch_name FROM users u LEFT JOIN branches b ON u.branch_id = b.branch_id WHERE u.username = '{username_input}' AND u.password = '{password_input}'"
        user_df = run_query(login_sql)
        
        if user_df is not None and not user_df.empty:
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_df.iloc[0]['role']
            st.session_state['user_branch_id'] = user_df.iloc[0]['branch_id']
            
            # Match NULL values for Super Admin safely
            if user_df.iloc[0]['branch_name'] is None:
                st.session_state['user_branch_name'] = "All Branches"
            else:
                st.session_state['user_branch_name'] = user_df.iloc[0]['branch_name']
                
            st.session_state['username'] = user_df.iloc[0]['username']
            st.success("Success!")
            st.rerun()
        else:
            st.error("Authentication rejected: Invalid account parameters.")
    st.stop()


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📉 Dashboard & Reports", "➕ Data Entry Workspace", "🗃️ Advanced SQL Engine"])

st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 **User:** `{st.session_state['username']}`")
st.sidebar.markdown(f"✍️ **Role:** `{st.session_state['user_role']}`")
st.sidebar.markdown(f"📍 **Branch:** `{st.session_state['user_branch_name']}`")

if st.sidebar.button("Log Out"):
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_branch_id'] = None
    st.session_state['user_branch_name'] = None
    st.session_state['username'] = None
    st.rerun()

if page == "📉 Dashboard & Reports":
    st.title("📈 Student Enrollment Dashboard")
    st.subheader("🔍 Filter Controls")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    
    db_branches = run_query("SELECT branch_name FROM branches")
    branch_list = ["All"]
    if db_branches is not None and not db_branches.empty:
        branch_list = ["All"] + db_branches['branch_name'].tolist()

    with f_col1:
        if st.session_state['user_role'] == 'Super Admin':
            branch_selection = st.selectbox("Branch Name", branch_list)
        else:
            branch_selection = st.session_state['user_branch_name']
            st.selectbox("Branch Name", [branch_selection], disabled=True)
            
    with f_col2:
        selected_product = st.selectbox("Product Name", ["All", "DS", "DA", "BA", "FSD", "SQL", "AI", "ML"])
        
    with f_col3:
        start_date = st.date_input("Start Date", date(2024, 1, 1))
        
    with f_col4:
        end_date = st.date_input("End Date", date(2027, 12, 31)) 
        
    q_build = f"SELECT cs.*, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id WHERE cs.date BETWEEN '{start_date}' AND '{end_date}'"
    
    if st.session_state['user_role'] == 'Admin':
        clean_branch_id = int(st.session_state['user_branch_id'])
        q_build = q_build + f" AND cs.branch_id = {clean_branch_id}"
    elif branch_selection != "All":
        q_build = q_build + f" AND b.branch_name = '{branch_selection}'"
        
    if selected_product != "All":
        q_build = q_build + f" AND cs.product_name = '{selected_product}'"
        
    df_dashboard = run_query(q_build)
    
    st.markdown("### 💵 Financial Summary")
    m1, m2, m3, m4 = st.columns(4)
    
    if df_dashboard is not None and not df_dashboard.empty:
        g_sales = pd.to_numeric(df_dashboard['gross_sales']).sum()
        r_sales = pd.to_numeric(df_dashboard['received_amount']).sum()
        p_sales = pd.to_numeric(df_dashboard['pending_amount']).sum()
        p_pct = (p_sales / g_sales * 100) if g_sales > 0 else 0.0
    else:
        g_sales, r_sales, p_sales, p_pct = 0.0, 0.0, 0.0, 0.0
        
    m1.metric("Overall Revenue (Gross)", f"₹{g_sales:,.2f}")
    m2.metric("Total Received Amount", f"₹{r_sales:,.2f}")
    m3.metric("Total Pending Amount", f"₹{p_sales:,.2f}")
    m4.metric("Pending Collection Pct", f"{p_pct:.1f}%")
    
    st.markdown("---")
    st.subheader("📊 Branch Course Records Summary")
    if df_dashboard is not None and not df_dashboard.empty:
        required_columns = ['sale_id', 'branch_name', 'date', 'name', 'mobile_number', 'product_name', 'gross_sales', 'received_amount', 'pending_amount', 'status']
        st.dataframe(df_dashboard[required_columns], use_container_width=True)
    else:
        st.info("No transaction records found matching your filter selections.")


elif page == "➕ Data Entry Workspace":
    st.title("📝 Operations Record Creator")
    tab_sales, tab_payments = st.tabs(["Add New Sales Entry", "Log Payment Split Details"])
    
    db_branches = run_query("SELECT branch_name FROM branches")
    entry_branch_list = []
    if db_branches is not None and not db_branches.empty:
        entry_branch_list = db_branches['branch_name'].tolist()

    with tab_sales:
        st.subheader("New Sale Generation")
        
        if st.session_state['user_role'] == 'Super Admin':
            target_branch = st.selectbox("Select Target Branch", entry_branch_list)
        else:
            target_branch = st.session_state['user_branch_name']
            st.selectbox("Select Target Branch", [target_branch], disabled=True)
            
        student_name = st.text_input("Student Name")
        mobile_number = st.text_input("Mobile Number")
        gross_amt = st.number_input("Gross Sales Amount (₹)", min_value=0.0, step=100.0)
        initial_status = st.selectbox("Initial Order Status", ["Open", "Close"])
        course_name = st.selectbox("Select Course Name", ["AI", "DS", "DA", "BA", "FSD", "SQL", "ML"])
        joining_date = st.date_input("Joining Date", date.today())
            
        if st.button("Publish Sale Entry"):
            if student_name and mobile_number and gross_amt > 0:
                b_lookup = run_query(f"SELECT branch_id FROM branches WHERE branch_name='{target_branch}'")
                b_id = int(b_lookup.iloc[0]['branch_id'])
                
                ins_q = f"""
                    INSERT INTO customer_sales (branch_id, date, name, mobile_number, product_name, gross_sales, status)
                    VALUES ({b_id}, '{joining_date}', '{student_name}', '{mobile_number}', '{course_name}', {gross_amt}, '{initial_status}')
                """
                run_query(ins_q)
                st.success("New account entity posted to sales ledger successfully!")
            else:
                st.error("Validation failed: Please fill out all standard input fields.")

    with tab_payments:
        st.subheader("Post Payment Installment Split")
        
        if st.session_state['user_role'] == 'Super Admin':
            sales_lookup = "SELECT sale_id, name, pending_amount FROM customer_sales WHERE status='Open'"
        else:
            clean_branch_id = int(st.session_state['user_branch_id'])
            sales_lookup = f"SELECT sale_id, name, pending_amount FROM customer_sales WHERE status='Open' AND branch_id={clean_branch_id}"
            
        open_sales = run_query(sales_lookup)
        
        if open_sales is not None and not open_sales.empty:
            open_sales['selector_str'] = open_sales.apply(lambda r: f"ID {r['sale_id']} - {r['name']} - ₹{float(r['pending_amount']):,.1f} Pending", axis=1)
            sales_dict = dict(zip(open_sales['selector_str'], open_sales['sale_id']))
            
            selected_invoice = st.selectbox("Select Target Active Sale ID Asset", list(sales_dict.keys()))
            pay_channel = st.selectbox("Payment Collection Channel", ["Cash", "UPI", "Card"])
            split_amount = st.number_input("Collected Split Amount Balance (₹)", min_value=0.01, step=10.0)
            payment_date = st.date_input("Payment Date", date.today())
            
            if st.button("Apply Payment Allocation"):
                target_id = int(sales_dict[selected_invoice])
                ins_p = f"""
                    INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
                    VALUES ({target_id}, '{payment_date}', {split_amount}, '{pay_channel}')
                """
                run_query(ins_p)
                st.success("Payment split transaction submitted successfully.")
                st.rerun()
        else:
            st.info("No open sales entries found looking for split installment postings.")


elif page == "🗃️ Advanced SQL Engine":
    st.title("💻 Live SQL Business Analytics Engine")
    
    compliance_queries = {
        "1. Retrieve all records from the sales table": "SELECT * FROM customer_sales;",
        "2. Retrieve all records from the branches table": "SELECT * FROM branches;",
        "3. Retrieve all records from the payment_splits table": "SELECT * FROM payment_splits;",
        "4. Display all sales with status = 'Open'": "SELECT * FROM customer_sales WHERE status = 'Open';",
        "5. Calculate total gross sales across all branches": "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales;",
        "6. Calculate total received amount across all sales": "SELECT SUM(received_amount) AS total_received_amount FROM customer_sales;",
        "7. Calculate total pending amount across all sales": "SELECT SUM(gross_sales - received_amount) AS total_pending_amount FROM customer_sales;",
        "8. Find average gross sales amount": "SELECT AVG(gross_sales) AS avg_gross_sales FROM customer_sales;",
        "9. Retrieve sales details along with branch name": "SELECT cs.sale_id, b.branch_name, cs.date, cs.name, cs.product_name, cs.gross_sales FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id;",
        "10. Retrieve sales details with total payments received via splits": "SELECT cs.sale_id, cs.name, SUM(ps.amount_paid) AS total_paid_splits FROM customer_sales cs LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id GROUP BY cs.sale_id, cs.name;",
        "11. Show branch-wise total gross sales (JOIN & GROUP BY)": "SELECT b.branch_name, SUM(cs.gross_sales) AS total_sales FROM branches b JOIN customer_sales cs ON b.branch_id = cs.branch_id GROUP BY b.branch_name;",
        "12. Display sales along with payment method used": "SELECT DISTINCT cs.sale_id, cs.name, ps.payment_method FROM customer_sales cs JOIN payment_splits ps ON cs.sale_id = ps.sale_id;",
        "13. Find sales where pending amount is greater than 5000": "SELECT *, (gross_sales - received_amount) as pending_amount FROM customer_sales WHERE (gross_sales - received_amount) > 5000;",
        "14. Retrieve top 3 highest gross sales": "SELECT * FROM customer_sales ORDER BY gross_sales DESC LIMIT 3;",
        "15. Find branch with highest total gross sales": "SELECT b.branch_name, SUM(cs.gross_sales) AS total FROM branches b JOIN customer_sales cs ON b.branch_id = cs.branch_id GROUP BY b.branch_name ORDER BY total DESC LIMIT 1;",
    }
    
    selected_op = st.selectbox("Choose Predefined Operational Query:", list(compliance_queries.keys()))
    raw_sql = compliance_queries[selected_op]
    
    st.code(raw_sql, language="sql")
    
    if st.button("Execute Live Database Transaction"):
        out_df = run_query(raw_sql)
        if out_df is not None:
            st.success("Execution completed successfully.")
            st.dataframe(out_df, use_container_width=True)