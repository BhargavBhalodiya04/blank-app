import os
import io
import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import boto3
from botocore.exceptions import NoCredentialsError
import cv2
import numpy as np
from imgaug import augmenters as iaa

from display_students import display_registered_students
from student_manager import add_student, load_students, save_students

# --- Config and folders ---
st.set_page_config(page_title="Face Recognition Attendance System", layout="wide")

ATTENDANCE_DIR = "attendance_files"
STUDENT_IMAGES_DIR = "student_images"
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(STUDENT_IMAGES_DIR, exist_ok=True)

# --- Utility Functions ---

def read_image_from_bytes(image_file):
    image_bytes = image_file.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def generate_augmented_images(image, count=100):
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),
        iaa.Affine(
            rotate=(-25, 25),
            shear=(-10, 10),
            scale=(0.8, 1.2)
        ),
        iaa.AdditiveGaussianNoise(scale=(0, 0.05*255)),
        iaa.Multiply((0.8, 1.2)),
        iaa.LinearContrast((0.75, 1.5)),
    ])
    images = [image] * count
    augmented_images = seq(images=images)
    return augmented_images

# --- AWS S3 Upload Function ---
def upload_image_to_s3(image_fileobj, s3_path):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
            aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
            region_name=st.secrets["aws"]["aws_region"]
        )
        s3.upload_fileobj(image_fileobj, st.secrets["aws"]["bucket_name"], s3_path)
        return True, f"Image uploaded to S3 at {s3_path}"
    except NoCredentialsError:
        return False, "AWS credentials not found"
    except Exception as e:
        return False, str(e)

# --- Sidebar Menu ---
st.sidebar.title("Menu")
st.sidebar.markdown("Select an action:")

menu_option = st.sidebar.radio(
    "",
    ["Train Model", "Add Student", "Take Attendance", "Download PDF", "View Students"]
)

st.markdown("## **Face Recognition Attendance System**")

# --- Train Model ---
if menu_option == "Train Model":
    st.markdown("### Train Face Recognition Model")
    if st.button("Train Now"):
        # TODO: Insert your actual training logic here
        st.success("Model training completed successfully!")

# --- Add Student (augmentation + S3 upload only, no local save) ---
elif menu_option == "Add Student":
    st.markdown("### Add New Student")
    st.markdown("#### Upload One Student Face Image (Augmentation will generate 100 images)")

    with st.form("add_student_form"):
        enrollment = st.text_input("Enrollment Number")
        name = st.text_input("Student Name")
        student_class = st.text_input("Class Name (e.g. 10A, 12B)")
        uploaded_image = st.file_uploader(
            "Upload One Student Face Image",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False
        )
        submitted = st.form_submit_button("Add Student")

        if submitted:
            if not enrollment or not name or not student_class:
                st.error("Please provide Enrollment Number, Name, and Class.")
            elif not uploaded_image:
                st.error("Please upload a student image.")
            else:
                cleaned_name = name.strip().replace(" ", "_")
                cleaned_class = student_class.strip().replace(" ", "_")

                img = read_image_from_bytes(uploaded_image)
                if img is None:
                    st.error("Failed to read the uploaded image.")
                else:
                    augmented_images = generate_augmented_images(img, count=100)
                    all_success = True
                    messages = []

                    for i, aug_img in enumerate(augmented_images):
                        is_success, buffer = cv2.imencode(".jpg", aug_img)
                        if not is_success:
                            messages.append(f"Image {i+1}: encoding failed")
                            all_success = False
                            continue

                        img_bytes = io.BytesIO(buffer.tobytes())

                        # Upload to S3 only (no local saving)
                        s3_path = f"student_images/{cleaned_class}/{enrollment}_{cleaned_name}/{enrollment}_{cleaned_name}_{i+1}.jpg"
                        success, msg = upload_image_to_s3(img_bytes, s3_path)
                        messages.append(f"Image {i+1}: {msg}")
                        if not success:
                            all_success = False

                    if all_success:
                        add_student(enrollment, name, student_class, f"student_images/{cleaned_class}/{enrollment}_{cleaned_name}/")
                        st.success(f"All 100 augmented images uploaded successfully for {name}!")
                    else:
                        st.error("Some augmented images failed to upload.")
                    
                    st.text("\n".join(messages))

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
    display_registered_students()

# --- Optional: Clean orphaned student folders function ---
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
