import os
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from imgaug import augmenters as iaa

STUDENT_DB = "students.csv"
STUDENT_IMAGES_DIR = "student_images"

def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_students():
    if os.path.exists(STUDENT_DB):
        return pd.read_csv(STUDENT_DB)
    else:
        return pd.DataFrame(columns=["Enrollment", "Name", "Class"])

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
    cropped_face = image_np[y:y+h, x:x+w]
    return cropped_face

def generate_augmented_images(image, count=100):
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),  # horizontal flips 50% chance
        iaa.Affine(
            rotate=(-25, 25),
            shear=(-10, 10),
            scale=(0.8, 1.2)
        ),
        iaa.AdditiveGaussianNoise(scale=(0, 0.05*255)),
        iaa.Multiply((0.8, 1.2)),
        iaa.LinearContrast((0.75, 1.5))
    ])

    images = [image] * count
    augmented_images = seq(images=images)
    return augmented_images

def save_image(image_array, path):
    img = Image.fromarray(image_array)
    img.save(path)

def add_student(enrollment, name, student_class, uploaded_image):
    try:
        image_np = read_image_from_bytes(uploaded_image)

        cropped_face = detect_and_crop_face(image_np)
        if cropped_face is None:
            return False, "No face detected in the uploaded image."

        clean_name = name.strip().replace(" ", "_")
        clean_class = student_class.strip().replace(" ", "_")

        class_folder = os.path.join(STUDENT_IMAGES_DIR, clean_class)
        create_folder_if_not_exists(class_folder)

        student_folder = os.path.join(class_folder, f"{enrollment}_{clean_name}")
        create_folder_if_not_exists(student_folder)

        # Generate 100 augmented images from cropped face
        augmented_images = generate_augmented_images(cropped_face, count=100)

        for i, aug_img in enumerate(augmented_images):
            save_path = os.path.join(student_folder, f"{enrollment}_{clean_name}_{i+1}.jpg")
            save_image(aug_img, save_path)

        students_df = load_students()
        if enrollment in students_df["Enrollment"].values:
            return False, f"Student with Enrollment {enrollment} already exists."

        new_student = pd.DataFrame([[enrollment, name, student_class.strip()]], columns=["Enrollment", "Name", "Class"])
        students_df = pd.concat([students_df, new_student], ignore_index=True)
        save_students(students_df)

        return True, f"Student added successfully! 100 augmented face images saved in folder '{student_folder}'."

    except Exception as e:
        return False, f"Error: {str(e)}"
