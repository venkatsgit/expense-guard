import streamlit as st
from streamlit_oauth import OAuth2Component
import requests
import json
from db_util import update_user_db
from streamlit_option_menu import option_menu
from routes.list_data import show as list_data
from routes.upload_data import show as upload_data
from routes.upload_history import show as upload_history
from routes.chat import show as chat

# Set Streamlit page config as the first command in the script
st.set_page_config(layout="wide", page_title="Expense Management")

# OAuth2 Configuration
CLIENT_ID = "1095140358158-ct17rj6hkj4i45kvvspt2l7hknim2ecd.apps.googleusercontent.com"
CLIENT_SECRET = "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"
AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
REDIRECT_URI = "http://localhost:8501"
SCOPE = "openid email profile"

oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REVOKE_URL)

# Fetch user info from Google using the OAuth token
def get_user_info(token):
    headers = {
        "Authorization": f"Bearer {token['access_token']}"
    }
    response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("❌ Failed to fetch user information.")
        return None

# Initialize session state from query params
if "token" not in st.session_state and "token" in st.query_params:
    try:
        token_json = json.loads(st.query_params["token"][0])  # Using query_params directly
        st.session_state.token = token_json
        st.session_state.access_token = token_json["access_token"]
    except Exception as e:
        st.error(f"Error parsing token: {e}")

# OAuth2 Login Flow
if "token" not in st.session_state:
    # st.markdown("<h1>POC <b style='color: #ff4b4b;'> AI Retail Agent </b></h1>", unsafe_allow_html=True)
    # result = oauth2.authorize_button(
    #     name="Login with Google",
    #     redirect_uri=REDIRECT_URI,
    #     scope=SCOPE,
    #     key="google_login"

    # )
    st.markdown(
        """
        <style>
        .main > div {
            padding-left: 0rem;
            padding-right: 0rem;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .title {
            font-size: 2.5em;
            color: #333;
            text-align: center;
            padding-bottom: 0.5em;
            border-bottom: 2px solid #eee;
            margin-bottom: 1em;
        }
        .highlight {
            color: #ff3c3c;
        }
        .description {
            font-size: 1.2em;
            color: #555;
            text-align: center;
            margin-top: -1em;
            margin-bottom: 2em;
        }
        .ai-image {
            display: flex;
            justify-content: center;
            margin-bottom: 2em;
        }
        .st-key-google_login {
            margin-left: 540px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Title + Highlight
    st.markdown(
        "<h1 class='title'>Expense Insights: <span class='highlight'>AI Agent</span></h1>",
        unsafe_allow_html=True
    )

    # Short Description
    st.markdown(
        "<p class='description'>Track and analyze your expenses with the power of AI. Smart. Secure. Seamless.</p>",
        unsafe_allow_html=True
    )

    # --- Google Login Button ---
    result = oauth2.authorize_button(
        name="Login with Google",
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        key="google_login"
    )

    if result and "token" in result:
        st.session_state.token = result["token"]
        st.session_state.access_token = result["token"]["access_token"]
        # Update the query params with the token directly in the URL
        st.rerun()  # This ensures the page reloads with the updated state

# If authenticated, show user info and content menu
else:
    token = st.session_state.token
    user_info = get_user_info(token)

    if user_info:
        update_user_db(user_info)
        st.success(f"Welcome, {user_info.get('name')} 👋")

        # Sidebar with custom menu
        with st.sidebar:
            selected = option_menu(
                "✨ Expense Insights",  # Title
                ["Chat", "Upload Expense", "Upload History", "All Expense"],  # Menu options
                icons=["chat-left-dots", "cloud-upload", "clock-history", "table"],  # Bootstrap icons
                menu_icon="app-indicator",  # Main icon
                default_index=0,
                styles={
                    "container": {"padding": "10px"},
                    "icon": {"color": "orange", "font-size": "18px"},
                    "nav-link-selected": {"background-color": "#ff4b4b"},
                }
            )

            # Logout Button below the menu
            st.sidebar.button("🚪 Logout", key="logout", on_click=lambda: logout())

        # Display content based on menu selection
        if selected == "Chat":
            chat()
        elif selected == "Upload Expense":
            upload_data()
        elif selected == "Upload History":
            upload_history()
        elif selected == "All Expense":
            list_data(user_info.get("email"))

    # Logout Function
    def logout():
        for key in ["token", "access_token"]:
            st.session_state.pop(key, None)
        st.query_params.clear()  # Clear query params from URL after logout
