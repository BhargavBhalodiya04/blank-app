import streamlit as st
import pandas as pd

def display_registered_students(csv_file='students.csv'):
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            st.info("No students registered yet.")
        else:
            st.subheader("📋 Registered Students")
            st.dataframe(df, use_container_width=True)
    except FileNotFoundError:
        st.warning(f"No data found. The file '{csv_file}' does not exist.")
    except Exception as e:
        st.error(f"Error loading student data: {e}")
