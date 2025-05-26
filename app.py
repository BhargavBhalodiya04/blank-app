import streamlit as st
from student_manager import add_student, remove_student

st.title("Student Management")

with st.form("add_student_form"):
    enrollment = st.text_input("Enrollment Number")
    name = st.text_input("Name")
    student_class = st.text_input("Class (not saved)")
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
