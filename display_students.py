import streamlit as st
import boto3
import pandas as pd

def display_registered_students():
    st.title("Registered Students")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
        region_name=st.secrets["aws"]["aws_region"]
    )
    bucket_name = st.secrets["aws"]["bucket_name"]
    base_prefix = "student_images/"

    paginator = s3.get_paginator('list_objects_v2')
    classes = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=base_prefix, Delimiter='/'):
        prefixes = page.get('CommonPrefixes')
        if prefixes:
            classes.extend([p['Prefix'] for p in prefixes])

    if not classes:
        st.warning("No student classes found in the bucket.")
        return

    # List to hold student dicts for DataFrame
    students_list = []

    for class_prefix in classes:
        class_name = class_prefix[len(base_prefix):].strip('/')

        students = []
        for page in paginator.paginate(Bucket=bucket_name, Prefix=class_prefix, Delimiter='/'):
            prefixes = page.get('CommonPrefixes')
            if prefixes:
                students.extend([p['Prefix'] for p in prefixes])

        if not students:
            continue

        for student_prefix in students:
            student_folder = student_prefix[len(class_prefix):].strip('/')
            try:
                enrollment, name_underscored = student_folder.split('_', 1)
                name = name_underscored.replace('_', ' ')
            except ValueError:
                enrollment = student_folder
                name = "Unknown"

            students_list.append({
                "Class": class_name,
                "Enrollment": enrollment,
                "Name": name
            })

    if students_list:
        df = pd.DataFrame(students_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No students found to display.")
