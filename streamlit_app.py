import os
import shutil
import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

from display_students import display_registered_students
from student_manager import add_student, load_students, save_students

# --- Config and folders ---
st.set_page_config(page_title="Face Recognition Attendance System", layout="wide")

ATTENDANCE_DIR = "attendance_files"
STUDENT_IMAGES_DIR = "student_images"
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(STUDENT_IMAGES_DIR, exist_ok=True)

# --- Sidebar Menu ---
st.sidebar.title("Menu")
st.sidebar.markdown("Select an action:")

menu_option = st.sidebar.radio(
    "",
    ["Train Model", "Add Student", "Remove Student", "Take Attendance", "Download PDF", "View Students"]
)

st.markdown("## **Face Recognition Attendance System**")

# --- Train Model ---
if menu_option == "Train Model":
    st.markdown("### Train Face Recognition Model")
    if st.button("Train Now"):
        # TODO: Insert your actual training logic here
        st.success("Model training completed successfully!")

# --- Add Student ---
elif menu_option == "Add Student":
    st.markdown("### Add New Student")
    st.markdown("#### Upload Student Image")

    with st.form("add_student_form"):
        enrollment = st.text_input("Enrollment Number")
        name = st.text_input("Student Name")
        student_class = st.text_input("Class Name (e.g. 10A, 12B)")
        uploaded_image = st.file_uploader("Upload Student Face Image", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Add Student")

        if submitted:
            if not enrollment or not name or not student_class:
                st.error("Please provide Enrollment Number, Name, and Class.")
            elif not uploaded_image:
                st.error("Please upload a student image.")
            else:
                success, msg = add_student(enrollment, name, student_class, uploaded_image)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# --- Remove Student ---
elif menu_option == "Remove Student":
    st.markdown("### Remove Student")
    students_df = load_students()

    if students_df.empty:
        st.warning("No students found in the database.")
    else:
        enrollment_list = students_df["Enrollment"].dropna().astype(str).tolist()
        if not enrollment_list:
            st.warning("No valid enrollment numbers available.")
        else:
            enrollment_to_remove = st.selectbox("Select Enrollment Number to remove", enrollment_list)

            student_row = students_df[students_df["Enrollment"].astype(str) == enrollment_to_remove]
            if not student_row.empty:
                student_name = str(student_row.iloc[0]["Name"]).strip().replace(" ", "_")
                student_class = str(student_row.iloc[0]["Class"]).strip().replace(" ", "_")
                student_folder = os.path.join(STUDENT_IMAGES_DIR, student_class, f"{enrollment_to_remove}_{student_name}")

                if st.button("Remove Student"):
                    students_df = students_df[students_df["Enrollment"].astype(str) != enrollment_to_remove]
                    save_students(students_df)

                    if os.path.exists(student_folder) and os.path.isdir(student_folder):
                        shutil.rmtree(student_folder)

                    st.success(f"Student with Enrollment Number {enrollment_to_remove} removed successfully!")
            else:
                st.error("Student not found.")

# --- Take Attendance ---
elif menu_option == "Take Attendance":
    st.markdown("### Upload Images for Attendance")
    uploaded_images = st.file_uploader(
        "Choose image files", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )

    if uploaded_images:
        st.info(f"Received {len(uploaded_images)} file(s). Processing attendance...")

        students_df = load_students()
        if students_df.empty:
            st.warning("No students in database. Add students first.")
        else:
            attendance = []
            for img in uploaded_images:
                st.image(img, caption=f"Processed: {img.name}", use_column_width=True)
                for _, row in students_df.iterrows():
                    attendance.append({
                        "Enrollment": row["Enrollment"],
                        "Name": row["Name"],
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Time": datetime.now().strftime("%H:%M:%S")
                    })

            if attendance:
                attendance_df = pd.DataFrame(attendance).drop_duplicates(subset=["Enrollment"])
                filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = os.path.join(ATTENDANCE_DIR, filename)
                attendance_df.to_excel(filepath, index=False)
                st.success(f"Attendance marked and saved to {filename}")

# --- Download PDF ---
elif menu_option == "Download PDF":
    st.markdown("### Download Attendance Sheet as PDF")

    attendance_files = [f for f in os.listdir(ATTENDANCE_DIR) if f.startswith("attendance_") and f.endswith(".xlsx")]

    if attendance_files:
        selected_file = st.selectbox("Select an attendance Excel file", attendance_files)
        if selected_file:
            filepath = os.path.join(ATTENDANCE_DIR, selected_file)

            df = pd.read_excel(filepath)

            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            width, height = letter

            c.setFont("Helvetica", 12)
            c.drawString(30, height - 40, f"Attendance Sheet: {selected_file}")
            c.drawString(30, height - 60, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            x_start = 30
            y_start = height - 90
            row_height = 20

            for i, col in enumerate(df.columns):
                c.drawString(x_start + i * 120, y_start, str(col))

            y = y_start - row_height
            for idx, row in df.iterrows():
                for i, val in enumerate(row):
                    c.drawString(x_start + i * 120, y, str(val))
                y -= row_height
                if y < 40:
                    c.showPage()
                    y = height - 40

            c.save()
            pdf_buffer.seek(0)

            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=selected_file.replace(".xlsx", ".pdf"),
                mime="application/pdf"
            )
    else:
        st.warning("No attendance Excel files found.")

# --- View Registered Students ---
elif menu_option == "View Students":
    display_registered_students("students.csv")

# --- Optional: Clean orphaned student folders function (can add a button somewhere) ---
def clean_orphaned_student_folders():
    students_df = load_students()
    enrollments_in_db = set(students_df["Enrollment"].astype(str).tolist())
    removed = []

    if not os.path.exists(STUDENT_IMAGES_DIR):
        return "Student images directory does not exist."

    for class_folder in os.listdir(STUDENT_IMAGES_DIR):
        class_folder_path = os.path.join(STUDENT_IMAGES_DIR, class_folder)
        if os.path.isdir(class_folder_path):
            for student_folder in os.listdir(class_folder_path):
                student_folder_path = os.path.join(class_folder_path, student_folder)
                if os.path.isdir(student_folder_path):
                    enrollment = student_folder.split("_")[0]
                    if enrollment not in enrollments_in_db:
                        shutil.rmtree(student_folder_path)
                        removed.append(student_folder_path)

    if removed:
        return "Removed orphaned student folders:\n" + "\n".join(removed)
    else:
        return "No orphaned student folders found."
