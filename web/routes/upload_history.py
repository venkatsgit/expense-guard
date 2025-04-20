import streamlit as st
import requests
import pandas as pd

def show():
    st.header("⏱️ Upload History", divider='rainbow')

    try:
        headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

        response = requests.get("http://host.docker.internal:8081/api/file/gethistory", headers=headers)


        if response.status_code == 200:
            response_data = response.json()
            df = pd.DataFrame(response_data["data"])

            if not df.empty:
                df = df[["file_name", "status", "message", "uploaded_at"]]
                df.rename(columns={
                    "file_name": "📁 File",
                    "status": "🟢 Status",
                    "message": "📝 Message",
                    "uploaded_at": "📅 Upload Date"
                }, inplace=True)

                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No upload history found.")
        else:
            st.error("Failed to retrieve upload history. Please try again later.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")