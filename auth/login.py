import streamlit as st
from database.db import SessionLocal
from database.models import User
from auth.security import verify_password
from ui.components import clean_html


def render_login():
    """
    Renders the futuristic cyberpunk login screen using native Streamlit widgets.
    """
    # Center the login form using columns
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        # App title header
        st.markdown(
            clean_html("""
            <div style="text-align:center; padding: 40px 0 30px 0;">
                <h1 style="font-family: 'Orbitron', 'Courier New', monospace; font-size: 2.8rem;
                           background: linear-gradient(135deg, #ffffff 30%, #00f0ff 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           letter-spacing: 4px; margin: 0;">NEURODOCS AI</h1>
                <p style="font-family: 'Courier New', monospace; font-size: 0.9rem;
                          color: #00f0ff; letter-spacing: 6px; margin-top: 8px;
                          text-shadow: 0 0 8px rgba(0,240,255,0.6);">
                    INTELLIGENT DOCUMENT OS v1.0
                </p>
            </div>
            """),
            unsafe_allow_html=True,
        )

        st.markdown(
            clean_html("""
            <div style="background: rgba(13,17,28,0.8); border: 1px solid rgba(0,240,255,0.25);
                        border-radius: 16px; padding: 32px; margin-bottom: 24px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.6);">
                <h2 style="font-family: 'Courier New', monospace; font-size: 1.1rem;
                           color: #ffffff; border-left: 4px solid #00f0ff; padding-left: 12px;
                           letter-spacing: 2px; margin-bottom: 24px;">
                    SECURE ACCESS TERMINAL
                </h2>
            </div>
            """),
            unsafe_allow_html=True,
        )

        username_input = st.text_input(
            "USERNAME", key="login_username", placeholder="Enter your username..."
        )
        password_input = st.text_input(
            "PASSWORD", type="password", key="login_password", placeholder="Enter your password..."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.button("▶  INITIALIZE SESSION", use_container_width=True, key="login_btn_act")
        with col2:
            signup_redirect = st.button("+ CREATE NEW IDENTITY", use_container_width=True, key="signup_redirect")

        if login_btn:
            if not username_input or not password_input:
                st.error("⚠  Missing authentication fields. Both username and password required.")
                return

            db = SessionLocal()
            try:
                from sqlalchemy import func
                user = db.query(User).filter(func.lower(User.username) == func.lower(username_input)).first()
                if user and verify_password(password_input, user.password_hash):
                    st.session_state.authenticated = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.success("✅  Identity verified. Initializing dashboard...")
                    st.rerun()
                else:
                    st.error("❌  Invalid username or password. Access denied.")
            except Exception as e:
                st.error(f"System fault: {e}")
            finally:
                db.close()

        if signup_redirect:
            st.session_state.auth_page = "signup"
            st.rerun()
