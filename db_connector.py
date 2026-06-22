from turtle import st

import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=st.secrets["db_password"],
        database="sales_management"
    )