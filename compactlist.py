import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect('students.db')
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def read_students():
    """Fetches all student records from the database and returns them as a DataFrame."""
    conn = get_db_connection()
    if conn:
        try:
            # The query selects all columns from the 'students' table.
            query = "SELECT roll_no, name, group_name FROM students"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"An error occurred while reading from the database: {e}")
            conn.close()
    return pd.DataFrame() # Return an empty DataFrame on error

def create_pdf(df):
    """Generates a PDF from a DataFrame."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    
    # Define column widths
    col_widths = {
        "roll_no": 25,
        "name": 100,
        "group_name": 20
    }
    
    # Table Header
    pdf.cell(col_widths["roll_no"], 10, 'Roll No.', 1, 0, 'C')
    pdf.cell(col_widths["name"], 10, 'Name', 1, 0, 'C')
    pdf.cell(col_widths["group_name"], 10, 'Group', 1, 1, 'C')
    
    pdf.set_font("Arial", "", 12)
    # Table Rows
    for index, row in df.iterrows():
        pdf.cell(col_widths["roll_no"], 10, str(row['roll_no']), 1, 0)
        pdf.cell(col_widths["name"], 10, str(row['name']), 1, 0)
        pdf.cell(col_widths["group_name"], 10, str(row['group_name']), 1, 1)
        
    # Return PDF as bytes
    # The output is already bytes, no need to encode
    return pdf.output()

# --- Streamlit App ---

st.set_page_config(page_title="MBA DSE BA 2025 Batch", layout="wide")

st.title("MBA DSE BA 2025 Batch")

# --- Sidebar Navigation ---
st.sidebar.title("View Options")
# Create a select box in the sidebar for navigation
app_mode = st.sidebar.selectbox("Choose a view:", ["Compact List"])

# --- Display Content Based on Sidebar Selection ---
if app_mode == "Compact List":
    st.header("Compact Student List")
    # Read and display the data from the database
    student_data = read_students()

    if not student_data.empty:
        # Use st.dataframe to display the data in a table. It's already a DataFrame.
        st.dataframe(
            student_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "roll_no": st.column_config.NumberColumn("Roll No.", format="%d"),
                "name": st.column_config.TextColumn("Name"),
                "group_name": st.column_config.TextColumn("Group"),
            }
        )
        
        st.markdown("---")
        
        # Generate PDF bytes
        pdf_bytes = create_pdf(student_data)
        
        # Add a download button for the PDF
        st.download_button(
            label="Download as PDF",
            data=pdf_bytes,
            file_name="student_list_2025.pdf",
            mime="application/octet-stream"
        )
    else:
        st.warning("No student data found or an error occurred. Please ensure the 'students.db' file is in the same directory and contains a 'students' table.")


