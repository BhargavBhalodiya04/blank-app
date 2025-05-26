import os
import cv2
import numpy as np
from imgaug import augmenters as iaa

STUDENT_IMAGES_DIR = "student_images"

def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def read_image_from_bytes(image_file):
    # Read bytes from Streamlit uploaded file and convert to OpenCV image (numpy array)
    image_bytes = image_file.read()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def generate_augmented_images(image, count=100):
    # Define augmentation sequence
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
    """
    Adds a student by creating a folder 'Enrollment_Name' and
    saving 100 augmented images generated from uploaded_image.
    
    Args:
        enrollment (str): Enrollment number
        name (str): Student name (spaces replaced with underscores)
        uploaded_image (UploadedFile): Streamlit uploaded image file

    Returns:
        (bool, str): success flag and message
    """
    try:
        # Clean name (replace spaces with underscores)
        clean_name = name.strip().replace(" ", "_")
        folder_name = f"{enrollment}_{clean_name}"
        student_folder = os.path.join(STUDENT_IMAGES_DIR, folder_name)
        create_folder_if_not_exists(student_folder)

        # Read uploaded image into OpenCV format
        img = read_image_from_bytes(uploaded_image)

        if img is None:
            return False, "Failed to read uploaded image."

        # Generate 100 augmented images
        augmented_images = generate_augmented_images(img, count=100)

        # Save augmented images to student folder
        for i, aug_img in enumerate(augmented_images):
            save_path = os.path.join(student_folder, f"{enrollment}_{clean_name}_{i+1}.jpg")
            cv2.imwrite(save_path, aug_img)

        return True, f"Student images saved successfully to folder '{folder_name}' with 100 augmented images."

    except Exception as e:
        return False, f"Error: {str(e)}"

