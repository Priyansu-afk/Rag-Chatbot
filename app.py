import streamlit as st
from database.schema import init_db
from ui.components import load_css
from auth.login import render_login
from auth.signup import render_signup
from ui.dashboard import Dashboard

# 1. Page Configuration
st.set_page_config(
    page_title="NeuroDocs AI - Intelligent Document OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Initialization
# Ensures tables are created before anyone tries to access them.
init_db()

# 3. Inject CSS Stylesheet
load_css("ui/styles.css")

# 4. Initialize Session States
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"
if "active_conv_id" not in st.session_state:
    st.session_state.active_conv_id = None


# 5. Routing Controller - Called at module level so Streamlit always runs it
def main():
    if not st.session_state.authenticated:
        if st.session_state.auth_page == "login":
            render_login()
        elif st.session_state.auth_page == "signup":
            render_signup()
    else:
        # User is authenticated, render the NeuroDocs dashboard
        dashboard = Dashboard()
        dashboard.render()

# Direct call — Streamlit re-executes the whole script on each interaction,
# so main() must be called at the top level, not inside __name__ guard.
main()
