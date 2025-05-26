import os

STUDENT_IMAGES_DIR = "student_images"
os.makedirs(STUDENT_IMAGES_DIR, exist_ok=True)

def add_student(enrollment, name, student_class, image_file):
    """
    Save student image in student_images folder as EnrollmentName.jpg.
    Does NOT create or update any CSV.
    """
    safe_name = name.replace(" ", "")  # Remove spaces from name
    filename = f"{enrollment}_{safe_name}.jpg"
    image_path = os.path.join(STUDENT_IMAGES_DIR, filename)

    try:
        with open(image_path, "wb") as f:
            f.write(image_file.getbuffer())
        return True, f"Student image saved as {filename}"
    except Exception as e:
        return False, f"Failed to save image: {str(e)}"


def remove_student(enrollment):
    """
    Remove all images starting with enrollment number.
    """
    removed_files = []
    for filename in os.listdir(STUDENT_IMAGES_DIR):
        if filename.startswith(str(enrollment)):
            try:
                os.remove(os.path.join(STUDENT_IMAGES_DIR, filename))
                removed_files.append(filename)
            except Exception as e:
                return False, f"Failed to remove {filename}: {str(e)}"
    if removed_files:
        return True, f"Removed files: {', '.join(removed_files)}"
    else:
        return False, f"No student images found for enrollment {enrollment}"
