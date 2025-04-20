import streamlit as st
import requests
import traceback
import pandas as pd
from datetime import datetime

def show(user_id=None):
    st.header("📤 Upload Your Expense File", divider='rainbow')
    st.markdown("Upload your `.csv` expense file to add data to the system.")

    # Upload section
    with st.container():
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed")

        if uploaded_file is not None:
            with st.status("Uploading...", expanded=True) as status:
                try:
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                    }
                    headers = {
                        "Authorization": f"Bearer {st.session_state['access_token']}"
                    }
                    data = {"file_name": "expenses"}

                    upload_url = "http://host.docker.internal:8081/api/file/upload"
                    response = requests.post(upload_url, files=files, data=data, headers=headers)

                    if response.ok:
                        status.update(label="✅ File uploaded successfully!", state="complete")
                        st.success("Your file has been processed and uploaded.")
                    else:
                        status.update(label="❌ Upload failed", state="error")
                        st.error(f"Upload failed with status code: {response.status_code}")
                        try:
                            error_msg = response.json().get("message")
                            if error_msg:
                                st.error(f"Server message: {error_msg}")
                        except Exception:
                            pass
                except Exception as e:
                    status.update(label="❌ Upload failed", state="error")
                    st.error("Something went wrong during upload.")
                    st.error(str(e))
                    st.text(traceback.format_exc())