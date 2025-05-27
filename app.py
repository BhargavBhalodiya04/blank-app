import streamlit as st
from student_manager import add_student, remove_student, get_existing_classes

st.title("Student Management")

existing_classes = get_existing_classes()

with st.form("add_student_form"):
    enrollment = st.text_input("Enrollment Number")
    name = st.text_input("Name")

    if existing_classes:
        student_class = st.selectbox("Select Class", existing_classes)
    else:
        st.error("No classes found. Please create class folders inside 'student_images' folder.")
        student_class = None

    uploaded_image = st.file_uploader("Upload Student Image", type=["jpg", "jpeg", "png"])
    submitted = st.form_submit_button("Add Student")

    if submitted:
        if not enrollment or not name or not student_class or not uploaded_image:
            st.error("Please fill all fields and upload an image.")
        else:
            success, msg = add_student(enrollment, name, student_class, uploaded_image)
            if success:
                st.success(msg)
            else:
                st.error(msg)

st.markdown("---")

enrollment_to_remove = st.text_input("Enter Enrollment Number to remove student")
if st.button("Remove Student"):
    if enrollment_to_remove:
        success, msg = remove_student(enrollment_to_remove)
        if success:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.error("Please enter Enrollment Number.")
