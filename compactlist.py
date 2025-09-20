import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import re
from datetime import datetime

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

def create_signature_pdf(df):
    """Generates a PDF for signatures from a DataFrame with dynamic column widths."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)

    # --- Dynamic Width Calculation ---
    pdf.set_font('Helvetica', 'B', 12)
    name_header_width = pdf.get_string_width('Name') + 6
    pdf.set_font('Helvetica', '', 12)
    max_name_width = max(pdf.get_string_width(str(name)) for name in df['name']) + 6
    name_col_width = max(name_header_width, max_name_width)

    col_widths = {
        "roll_no": 20, "name": name_col_width, "group_name": 15, "signature": 50
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
        roll_no = str(row['roll_no']).encode('latin-1', 'replace').decode('latin-1')
        name = str(row['name']).encode('latin-1', 'replace').decode('latin-1')
        group_name = str(row['group_name']).encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(col_widths["roll_no"], 10, roll_no, 1, 0)
        pdf.cell(col_widths["name"], 10, name, 1, 0)
        pdf.cell(col_widths["group_name"], 10, group_name, 1, 0)
        pdf.cell(col_widths["signature"], 10, '', 1, 1)

    return bytes(pdf.output())

def create_attendance_pdf(df, attendance_date, course_name, course_type, num_classes):
    """Generates a PDF with an attendance status column, course details, and a summary."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)

    # --- PDF Header ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'MBA DSE BA 2025 - Attendance Sheet', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, f"Date: {attendance_date.strftime('%B %d, %Y')}", 0, 1, 'L')
    pdf.cell(0, 8, f"Course: {course_name} ({course_type})", 0, 1, 'L')
    pdf.cell(0, 8, f"Number of Classes Held: {num_classes}", 0, 1, 'L')
    pdf.ln(5) # Add a little space before the table

    # --- Dynamic Width Calculation ---
    pdf.set_font('Helvetica', 'B', 12)
    name_header_width = pdf.get_string_width('Name') + 6
    pdf.set_font('Helvetica', '', 12)
    # Adjust available width for the new signature column
    available_width = pdf.w - 20 # A4 width minus margins
    name_col_width = max(pdf.get_string_width(str(name)) for name in df['name']) + 6
    name_col_width = max(name_header_width, name_col_width)


    col_widths = {
        "roll_no": 15, "name": name_col_width, "group_name": 15, "status": 20, "signature": 40
    }

    # Adjust name column width if it's too wide
    fixed_cols_width = col_widths["roll_no"] + col_widths["group_name"] + col_widths["status"] + col_widths["signature"]
    col_widths["name"] = available_width - fixed_cols_width


    # --- Table Header ---
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(col_widths["roll_no"], 10, 'Roll No.', 1, 0, 'C')
    pdf.cell(col_widths["name"], 10, 'Name', 1, 0, 'C')
    pdf.cell(col_widths["group_name"], 10, 'Group', 1, 0, 'C')
    pdf.cell(col_widths["status"], 10, 'Status', 1, 0, 'C')
    pdf.cell(col_widths["signature"], 10, 'Signature', 1, 1, 'C')

    # --- Table Rows ---
    pdf.set_font('Helvetica', '', 12)
    for _, row in df.iterrows():
        # Set color for absent students
        if row['status'] == 'Absent':
            pdf.set_fill_color(255, 204, 203)  # Light red
            fill = True
        else:
            fill = False

        roll_no = str(row['roll_no']).encode('latin-1', 'replace').decode('latin-1')
        name = str(row['name']).encode('latin-1', 'replace').decode('latin-1')
        group_name = str(row['group_name']).encode('latin-1', 'replace').decode('latin-1')

        pdf.cell(col_widths["roll_no"], 10, roll_no, 1, 0, 'C', fill)
        pdf.cell(col_widths["name"], 10, name, 1, 0, fill=fill)
        pdf.cell(col_widths["group_name"], 10, group_name, 1, 0, 'C', fill)
        pdf.cell(col_widths["status"], 10, row['status'], 1, 0, 'C', fill)
        pdf.cell(col_widths["signature"], 10, '', 1, 1, fill=fill)


    # --- Attendance Summary ---
    pdf.ln(10) # Add some space after the table
    present_count = df['status'].value_counts().get('Present', 0)
    absent_count = df['status'].value_counts().get('Absent', 0)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"Total Present: {present_count}", 0, 1, 'L')
    pdf.cell(0, 8, f"Total Absent: {absent_count}", 0, 1, 'L')

    return bytes(pdf.output())


# --- Streamlit App ---
st.set_page_config(page_title="MBA DSE BA 2025 Batch", layout="wide")
st.title("MBA DSE BA 2025 Batch")

# --- Sidebar Navigation ---
st.sidebar.title("View Options")
app_mode = st.sidebar.selectbox("Choose a view:", ["Attendance Maker", "Compact List"])

# --- Student Data Loading ---
student_data = read_students()

# --- Display Content Based on Sidebar Selection ---
if app_mode == "Compact List":
    st.header("Compact Student List")
    if not student_data.empty:
        st.dataframe(
            student_data, use_container_width=True, hide_index=True,
            column_config={
                "roll_no": st.column_config.NumberColumn("Roll No.", format="%d"),
                "name": st.column_config.TextColumn("Name"),
                "group_name": st.column_config.TextColumn("Group"),
            }
        )
        st.markdown("---")
        try:
            pdf_bytes = create_signature_pdf(student_data)
            st.download_button(
                label="Download as PDF for Signatures", data=pdf_bytes,
                file_name="student_signature_sheet.pdf", mime="application/pdf"
            )
        except Exception as e:
            st.error(f"An error occurred while generating the PDF: {e}")
    else:
        st.warning("No student data found.")

elif app_mode == "Attendance Maker":
    st.header("Attendance Maker")
    if not student_data.empty:
        # --- New Input Fields ---
        st.subheader("Course Details")
        course_list = [
            "Indian Knowledge System", "Marketing", "Management", "Analytics",
            "Visualisation", "Economics", "Statistics", "Accounting"
        ]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            attendance_date = st.date_input("Select Date", datetime.now())
        with col2:
            course_name = st.selectbox("Select Course", course_list)
        with col3:
            course_type = st.selectbox("Select Type", ["Theory", "Practical"])
        with col4:
            num_classes = st.selectbox("Classes Held", [1, 2, 3, 4])

        st.markdown("---")

        # --- Attendance Input ---
        st.subheader("Mark Attendance")
        input_method = st.radio("How do you want to mark attendance?", ('Enter Absentees', 'Enter Present'))
        roll_numbers_str = st.text_area("Enter roll numbers (comma, space, or newline separated):")

        if st.button("Generate Attendance PDF"):
            if roll_numbers_str.strip():
                number_list = re.findall(r'\d+', roll_numbers_str)
                input_rolls = {int(num) for num in number_list}

                total_rolls = set(student_data['roll_no'])

                # Check for and warn about invalid roll numbers
                out_of_range_rolls = input_rolls - total_rolls
                if out_of_range_rolls:
                    st.warning(f"The following roll numbers were ignored as they are not in the class list: {sorted(list(out_of_range_rolls))}")

                if input_method == 'Enter Absentees':
                    absent_rolls = input_rolls.intersection(total_rolls)
                    present_rolls = total_rolls - absent_rolls
                else:
                    present_rolls = input_rolls.intersection(total_rolls)
                    absent_rolls = total_rolls - present_rolls

                def get_status(roll):
                    return "Present" if roll in present_rolls else "Absent"

                attendance_df = student_data.copy()
                attendance_df['status'] = attendance_df['roll_no'].apply(get_status)

                try:
                    # Pass new details to the PDF function
                    pdf_bytes = create_attendance_pdf(attendance_df, attendance_date, course_name, course_type, num_classes)
                    st.download_button(
                        label="Download Attendance Sheet", data=pdf_bytes,
                        file_name=f"attendance_{attendance_date.strftime('%Y-%m-%d')}.pdf", mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"An error occurred while generating the PDF: {e}")
            else:
                st.warning("Please enter some roll numbers.")
    else:
        st.warning("No student data found.")

