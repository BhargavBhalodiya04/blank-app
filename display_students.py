import pandas as pd
import streamlit as st

# def display_registered_students(csv_file='students.csv'):
#     try:
#         df = pd.read_csv(csv_file)
#         if df.empty:
#             st.info("No students registered yet.")
#         else:
#             st.subheader("📋 Registered Students")
#             st.dataframe(df, use_container_width=True)
#     except FileNotFoundError:
#         st.warning(f"No data found. The file '{csv_file}' does not exist.")
#     except Exception as e:
#         st.error(f"Error loading student data: {e}")

def display_registered_students(csv_file):
    df = pd.read_csv(csv_file)
    if df.empty:
        st.warning("No students to display.")
        return

    st.markdown("### Registered Students")
    for _, row in df.iterrows():
        st.write(f"**Enrollment:** {row['Enrollment']}")
        st.write(f"**Name:** {row['Name']}")
        st.write(f"**Class:** {row['Class']}")
        if "ImagePath" in row and row["ImagePath"].startswith("http"):
            st.image(row["ImagePath"], width=150, caption=row["Name"])
        elif "ImagePath" in row:
            # For bucket path (not public URL), you can show a message instead
            st.info(f"Image stored at S3: {row['ImagePath']}")
        st.markdown("---")
