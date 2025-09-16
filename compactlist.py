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
    """Generates a PDF from a DataFrame with dynamic column widths."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)

    # --- Dynamic Width Calculation ---
    # Calculate width for the 'Name' header, adding some padding
    pdf.set_font('Helvetica', 'B', 12)
    name_header_width = pdf.get_string_width('Name') + 6 

    # Find the maximum width required for the names in the dataframe, adding padding
    pdf.set_font('Helvetica', '', 12)
    max_name_width = max(pdf.get_string_width(str(name)) for name in df['name']) + 6

    # The final name column width is the larger of the header or the longest name
    name_col_width = max(name_header_width, max_name_width)
    
    # Define final column widths
    col_widths = {
        "roll_no": 20,              # A fixed, suitable width
        "name": name_col_width,     # The dynamically calculated width
        "group_name": 15,           # A smaller fixed width for the group
        "signature": 50             # A fixed width for the signature column
    }
    
    # --- Table Header ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(col_widths["roll_no"], 10, 'Roll No.', 1, 0, 'C')
    pdf.cell(col_widths["name"], 10, 'Name', 1, 0, 'C')
    pdf.cell(col_widths["group_name"], 10, 'Group', 1, 0, 'C')
    pdf.cell(col_widths["signature"], 10, 'Signature', 1, 1, 'C')
    
    # --- Table Rows ---
    pdf.set_font('Helvetica', '', 12)
    for index, row in df.iterrows():
        # Encode strings to latin-1 to handle special characters if any
        roll_no = str(row['roll_no']).encode('latin-1', 'replace').decode('latin-1')
        name = str(row['name']).encode('latin-1', 'replace').decode('latin-1')
        group_name = str(row['group_name']).encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(col_widths["roll_no"], 10, roll_no, 1, 0)
        pdf.cell(col_widths["name"], 10, name, 1, 0)
        pdf.cell(col_widths["group_name"], 10, group_name, 1, 0)
        pdf.cell(col_widths["signature"], 10, '', 1, 1) # Add an empty cell for the signature
        
    # Return PDF as bytes, explicitly converting from bytearray if necessary.
    return bytes(pdf.output())

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
        try:
            pdf_bytes = create_pdf(student_data)
            # Add a download button for the PDF
            st.download_button(
                label="Download as PDF",
                data=pdf_bytes,
                file_name="student_attendance_2025.pdf",
                mime="application/pdf" # Correct mime type for PDF
            )
        except Exception as e:
            st.error(f"An error occurred while generating the PDF: {e}")

    else:
        st.warning("No student data found or an error occurred. Please ensure the 'students.db' file is in the same directory and contains a 'students' table.")

