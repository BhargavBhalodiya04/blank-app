import boto3
import streamlit as st
import os
from botocore.exceptions import NoCredentialsError

def upload_to_s3(file_path, s3_key, bucket_name):
    try:
        session = boto3.Session(
            aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
            aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
            region_name=st.secrets["aws"]["aws_region"]
        )
        s3 = session.client('s3')

        s3.upload_file(file_path, bucket_name, s3_key)
        st.success(f"Uploaded to S3: {s3_key}")
        return True
    except FileNotFoundError:
        st.error("The file was not found.")
    except NoCredentialsError:
        st.error("Credentials not available.")
    return False
