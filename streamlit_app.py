import os
import glob
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from PIL import Image
from imgaug import augmenters as iaa

# --- Config and folders ---
st.set_page_config(page_title="Face Recognition Attendance System", layout="wide")

STUDENT_DB = "students.csv"
ATTENDANCE_DIR = "attendance_files"
STUDENT_IMAGES_DIR = "student_images"
os.makedirs(ATTENDANCE_DIR, exist_ok=True)
os.makedirs(STUDENT_IMAGES_DIR, exist_ok=True)

# --- Helper functions ---
def load_students():
    if os.path.exists(STUDENT_DB):
        return pd.read_csv(STUDENT_DB)
    else:
        return pd.DataFrame(columns=["Enrollment", "Name"])

def save_students(df):
    df.to_csv(STUDENT_DB, index=False)

def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_image_from_bytes(image_file):
    # Read uploaded image into PIL.Image then convert to numpy array (RGB)
    image = Image.open(image_file)
    return np.array(image)

def save_image(image_array, path):
    # Save numpy array image to path using PIL.Image
    img = Image.fromarray(image_array)
    img.save(path)

def generate_augmented_images(image, count=100):
    # Define augmentation sequence using imgaug
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),  # horizontal flips
        iaa.Affine(
            rotate=(-25, 25),  # rotate between -25 and 25 degrees
            shear=(-10, 10),   # shear between -10 and 10 degrees
            scale=(0.8, 1.2)   # scale images
        ),
        iaa.AdditiveGaussianNoise(scale=(0, 0.05*255)),
        iaa.Multiply((0.8, 1.2)),
        iaa.LinearContrast((0.75, 1.5)),
    ])

    images = [image] * count  # replicate the same image count times
    augmented_images = seq(images=images)
    return augmented_images

def add_student_with_augmented_images(enrollment, name, uploaded_image):
    try:
        clean_name = name.strip().replace(" ", "_")
        folder_name = f"{enrollment}_{clean_name}"
        student_folder = os.path.join(STUDENT_IMAGES_DIR, folder_name)
        create_folder_if_not_exists(student_folder)

        img = read_image_from_bytes(uploaded_image)
        if img is None:
            return False, "Failed to read uploaded image."

        augmented_images = generate_augmented_images(img, count=100)

        for i, aug_img in enumerate(augmented_images):
            save_path = os.path.join(student_folder, f"{enrollment}_{clean_name}_{i+1}.jpg")
            save_image(aug_img, save_path)

        return True, f"Student images saved successfully to folder '{folder_name}' with 100 augmented images."

    except Exception as e:
        return False, f"Error: {str(e)}"

# --- Sidebar Menu ---
st.sidebar.title("Menu")
st.sidebar.markdown("Select an action:")

menu_option = st.sidebar.radio(
    "",
    ["Train Model", "Add Student", "Remove Student", "Take Attendance", "Download PDF"]
)

st.markdown("## **Face Recognition Attendance System**")

# --- Menu Options ---
if menu_option == "Train Model":
    st.markdown("### Train Face Recognition Model")
    if st.button("Train Now"):
        # TODO: Insert your actual training logic here
        st.success("Model training completed successfully!")

elif menu_option == "Add Student":
    st.markdown("### Add New Student")
    st.markdown("#### Upload Student Image")

    with st.form("add_student_form"):
        enrollment = st.text_input("Enrollment Number")
        name = st.text_input("Student Name")
        uploaded_image = st.file_uploader("Upload Student Face Image", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Add Student")

        if submitted:
            if not enrollment or not name:
                st.error("Please provide both Enrollment Number and Name.")
            elif not uploaded_image:
                st.error("Please upload a student image.")
            else:
                students_df = load_students()
                if enrollment in students_df["Enrollment"].values:
                    st.warning(f"Student with Enrollment {enrollment} already exists.")
                else:
                    # Save student info
                    new_student = pd.DataFrame([[enrollment, name]], columns=["Enrollment", "Name"])
                    students_df = pd.concat([students_df, new_student], ignore_index=True)
                    save_students(students_df)

                    # Save augmented images (100 variants)
                    success, msg = add_student_with_augmented_images(enrollment, name, uploaded_image)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

elif menu_option == "Remove Student":
    st.markdown("### Remove Student")
    students_df = load_students()
    if students_df.empty:
        st.warning("No students found in the database.")
    else:
        enrollment_to_remove = st.selectbox("Select Enrollment Number to remove", students_df["Enrollment"].tolist())

        if st.button("Remove Student"):
            # Filter out student by Enrollment Number
            students_df = students_df[students_df["Enrollment"] != enrollment_to_remove]
            save_students(students_df)

            # Remove all student images matching enrollment number (e.g. 92310133004_Bhavik_1.jpg)
            image_pattern = os.path.join(STUDENT_IMAGES_DIR, f"{enrollment_to_remove}_*")
            files = glob.glob(image_pattern)
            for file_path in files:
                if os.path.isfile(file_path):
                    os.remove(file_path)

            # Also remove folder if empty
            folder_pattern = os.path.join(STUDENT_IMAGES_DIR, f"{enrollment_to_remove}_*")
            folders = glob.glob(folder_pattern)
            for folder in folders:
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)

            st.success(f"Student with Enrollment Number {enrollment_to_remove} removed successfully!")

elif menu_option == "Take Attendance":
    st.markdown("### Upload Images for Attendance")
    uploaded_images = st.file_uploader(
        "Choose image files", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )

    if uploaded_images:
        st.info(f"Received {len(uploaded_images)} file(s). Processing attendance...")
        # TODO: Add your actual face recognition and attendance logic here

        students_df = load_students()
        if students_df.empty:
            st.warning("No students in database. Add students first.")
        else:
            attendance = []
            for img in uploaded_images:
                st.image(img, caption=f"Processed: {img.name}", use_column_width=True)
                # Simulate attendance: mark all students present for demo
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

elif menu_option == "Download PDF":
    st.markdown("### Download Attendance Sheet as PDF")

    attendance_files = [f for f in os.listdir(ATTENDANCE_DIR) if f.startswith("attendance_") and f.endswith(".xlsx")]

    if attendance_files:
        selected_file = st.selectbox("Select an attendance Excel file", attendance_files)
        if selected_file:
            filepath = os.path.join(ATTENDANCE_DIR, selected_file)
            # TODO: Convert Excel to PDF or provide PDF directly
            # For demo: download Excel file renamed as .pdf
            with open(filepath, "rb") as f:
                data = f.read()
            st.download_button(
                label="Download PDF",
                data=data,
                file_name=selected_file.replace(".xlsx", ".pdf"),
                mime="application/pdf"
            )
    else:
        st.warning("No attendance Excel files found.")
