import os
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from imgaug import augmenters as iaa
import shutil
import streamlit as st

STUDENT_DB = "students.csv"
STUDENT_IMAGES_DIR = "student_images"

def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_students():
    if os.path.exists(STUDENT_DB):
        return pd.read_csv(STUDENT_DB)
    else:
        return pd.DataFrame(columns=["Enrollment", "Name", "Class", "ImagePath"])

def save_students(df):
    df.to_csv(STUDENT_DB, index=False)

def read_image_from_bytes(image_file):
    image = Image.open(image_file).convert('RGB')
    return np.array(image)

def detect_and_crop_face(image_np):
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        return None
    x, y, w, h = faces[0]
    return image_np[y:y+h, x:x+w]

def generate_augmented_images(image, count=100):
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),
        iaa.Affine(rotate=(-25, 25), shear=(-10, 10), scale=(0.8, 1.2)),
        iaa.AdditiveGaussianNoise(scale=(0, 0.05*255)),
        iaa.Multiply((0.8, 1.2)),
        iaa.LinearContrast((0.75, 1.5))
    ])
    images = [image] * count
    return seq(images=images)

def save_image(image_array, path):
    Image.fromarray(image_array).save(path)

def add_student(enrollment, name, student_class, uploaded_image, s3_url=None):
    try:
        image_np = read_image_from_bytes(uploaded_image)
        cropped_face = detect_and_crop_face(image_np)
        if cropped_face is None:
            return False, "No face detected in the uploaded image."

        clean_name = name.strip().replace(" ", "_")
        clean_class = str(student_class).strip().replace(" ", "_") if pd.notna(student_class) else "Unknown_Class"

        class_folder = os.path.join(STUDENT_IMAGES_DIR, clean_class)
        create_folder_if_not_exists(class_folder)

        student_folder = os.path.join(class_folder, f"{enrollment}_{clean_name}")
        folder_exists = os.path.exists(student_folder)

        students_df = load_students()
        student_exists = enrollment in students_df["Enrollment"].astype(str).values

        if folder_exists or student_exists:
            st.warning(f"Student with enrollment '{enrollment}' already exists.")
            choice = st.radio(f"Overwrite data for {enrollment} - {name}?", ("No", "Yes"))
            if choice == "No":
                return False, "Registration cancelled."
            if folder_exists:
                shutil.rmtree(student_folder)
                create_folder_if_not_exists(student_folder)
            students_df = students_df[students_df["Enrollment"].astype(str) != str(enrollment)]
        else:
            create_folder_if_not_exists(student_folder)

        augmented_images = generate_augmented_images(cropped_face, count=100)
        for i, aug_img in enumerate(augmented_images):
            save_path = os.path.join(student_folder, f"{enrollment}_{clean_name}_{i+1}.jpg")
            save_image(aug_img, save_path)

        new_student = pd.DataFrame([{
            "Enrollment": enrollment,
            "Name": name,
            "Class": clean_class,
            "ImagePath": s3_url if s3_url else ""
        }])

        students_df = pd.concat([students_df, new_student], ignore_index=True)
        save_students(students_df)

        return True, f"Student added successfully! 100 augmented images saved in '{student_folder}'."
    except Exception as e:
        return False, f"Error: {str(e)}"

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
