import streamlit as st
from datetime import datetime
from database.db import SessionLocal
from database.models import User, Analytics
from auth.security import hash_password, is_valid_email, is_valid_username
from ui.components import clean_html


def render_signup():
    """
    Renders the futuristic cyberpunk signup screen using native Streamlit widgets.
    """
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
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
                    CREATE COGNITIVE IDENTITY
                </h2>
            </div>
            """),
            unsafe_allow_html=True,
        )

        username = st.text_input(
            "USERNAME", key="signup_username",
            placeholder="3–20 alphanumeric characters or underscores"
        )
        email = st.text_input(
            "EMAIL ADDRESS", key="signup_email",
            placeholder="user@domain.com"
        )
        password = st.text_input(
            "PASSWORD", type="password", key="signup_password",
            placeholder="Minimum 6 characters"
        )
        confirm_password = st.text_input(
            "CONFIRM PASSWORD", type="password", key="signup_confirm",
            placeholder="Re-enter password"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            signup_btn = st.button("✅  PROVISION IDENTITY", use_container_width=True, key="signup_btn_act")
        with col2:
            login_redirect = st.button("← BACK TO LOGIN", use_container_width=True, key="login_redirect")

        if signup_btn:
            # Validation
            if not username or not email or not password or not confirm_password:
                st.error("⚠  All fields are required.")
                return
            if not is_valid_username(username):
                st.error("⚠  Username must be 3–20 characters (letters, numbers, underscores only).")
                return
            if not is_valid_email(email):
                st.error("⚠  Please enter a valid email address.")
                return
            if password != confirm_password:
                st.error("⚠  Passwords do not match.")
                return
            if len(password) < 6:
                st.error("⚠  Password must be at least 6 characters.")
                return

            db = SessionLocal()
            try:
                from sqlalchemy import func
                exists = db.query(User).filter(
                    (func.lower(User.username) == func.lower(username)) | 
                    (func.lower(User.email) == func.lower(email))
                ).first()
                if exists:
                    st.error("⚠  Username or email is already registered.")
                    return

                # Create user
                hashed = hash_password(password)
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=hashed,
                    created_at=datetime.utcnow()
                )
                db.add(new_user)
                db.flush()

                # Seed analytics row
                user_analytics = Analytics(
                    user_id=new_user.id,
                    total_documents=0,
                    total_questions=0,
                    last_activity=datetime.utcnow()
                )
                db.add(user_analytics)
                db.commit()

                st.success("✅  Identity registered successfully! Please log in.")
                st.session_state.auth_page = "login"
                st.rerun()

            except Exception as e:
                db.rollback()
                st.error(f"Registration failed: {e}")
            finally:
                db.close()

        if login_redirect:
            st.session_state.auth_page = "login"
            st.rerun()
