import streamlit as st
import requests
import time


CHAT_URL = "http://host.docker.internal:8083/chatbot"

sample_questions = [
   "How much tax I have paid so far?",
   "What are my top 5 expense categories this month?",
   "How much did I spend on each category this month?"
]
def show(user_id=None):
    st.header("🤖 Chat with your AI Agent", divider='rainbow')

    # Initialize session state variables
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if "show_more" not in st.session_state:
        st.session_state["show_more"] = False

    # Create layout
    col1 = st.columns([1])

    # Chat display area
    with col1[0]:
        messages = st.container(height=400)

        # Display chat history
        for msg in st.session_state["chat_history"]:
            messages.chat_message(msg["role"]).write(msg["content"])

    # Handle custom chat input
    if prompt := st.chat_input("Say something"):
        # Show user's message
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        messages.chat_message("user").write(prompt)

        # Show assistant typing animation using placeholder
        with messages.chat_message("assistant"):
            typing_placeholder = st.empty()

            for i in range(3):
                typing_placeholder.markdown(f"**Processing Your Query... (This is a Proof of Concept (POC) solution using a free Natural Language to SQL (NL2SQL) model and working with unindexed, unstructured data. As a result, responses may take longer than usual. In the full solution, performance will significantly improve with: Optimized and indexed datasets, A production-grade NL2SQL engine, Scalable infrastructure)**")
                time.sleep(0.5)

            # Send request to backend
            headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
            data = {"question": prompt, "userID": "1"}
            response = requests.post(CHAT_URL, json=data, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                ai_reply = response_data.get("answer", {}).get("query_text") or response_data.get("query_text",
                                                                                                  "No answer found.")
                st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})
                typing_placeholder.markdown(ai_reply)
            else:
                typing_placeholder.error("Query submission failed!")

    # Sample questions
    st.subheader("Sample Questions")

    initial_display_count = 6
    display_questions = sample_questions if st.session_state["show_more"] else sample_questions[:initial_display_count]

    num_columns = 3
    columns = st.columns(num_columns)

    for i, question in enumerate(display_questions):
        col = columns[i % num_columns]
        if col.button(question):
            st.session_state["chat_history"].append({"role": "user", "content": question})
            messages.chat_message("user").write(question)

            with messages.chat_message("assistant"):
                typing_placeholder = st.empty()

                for i in range(3):
                    typing_placeholder.markdown(f"**Processing Your Query... (This is a Proof of Concept (POC) solution using a free Natural Language to SQL (NL2SQL) model and working with unindexed, unstructured data. As a result, responses may take longer than usual. In the full solution, performance will significantly improve with: Optimized and indexed datasets, A production-grade NL2SQL engine, Scalable infrastructure)**")
                    time.sleep(0.5)

                headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
                data = {"question": question, "userID": "1"}
                response = requests.post(CHAT_URL, json=data, headers=headers)

                if response.status_code == 200:
                    response_data = response.json()
                    ai_reply = response_data.get("answer", {}).get("query_text") or response_data.get("query_text",
                                                                                                      "No answer found.")
                    st.session_state["chat_history"].append({"role": "assistant", "content": ai_reply})
                    typing_placeholder.markdown(ai_reply)
                else:
                    typing_placeholder.error("Query submission failed!")

    # Show More / Show Less toggle
    if len(sample_questions) > initial_display_count:
        if st.session_state["show_more"]:
            if st.button("Show Less"):
                st.session_state["show_more"] = False
                st.rerun()
        else:
            if st.button("Show More"):
                st.session_state["show_more"] = True
                st.rerun()

