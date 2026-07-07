import streamlit as st
from typing import Dict, Any

def clean_html(html_str: str) -> str:
    """
    Cleans HTML string by removing indentation and newlines to prevent
    Streamlit's markdown parser from treating indented text as code blocks.
    """
    return " ".join([line.strip() for line in html_str.split("\n") if line.strip()])

def load_css(css_file_path: str):
    """
    Reads the CSS file and injects it into the Streamlit session.
    """
    try:
        with open(css_file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to inject custom styling: {e}")

def neon_header(title: str, subtitle: str):
    """
    Renders the main futuristic app header.
    """
    st.markdown(
        clean_html(f"""
        <div class="neon-title-container">
            <h1 class="neon-title">{title}</h1>
            <p class="neon-subtitle">{subtitle}</p>
        </div>
        """),
        unsafe_allow_html=True
    )

def glass_card_start(title: str = "", depth: bool = False):
    """
    Begins a glassmorphic container. MUST call glass_card_end() after.
    """
    card_class = "glass-card depth-card" if depth else "glass-card"
    header_html = f'<h2 class="section-title">{title}</h2>' if title else ""
    st.markdown(clean_html(f'<div class="{card_class}">{header_html}'), unsafe_allow_html=True)

def glass_card_end():
    """
    Closes the glassmorphic container.
    """
    st.markdown(clean_html('</div>'), unsafe_allow_html=True)

def metric_card(label: str, value: Any):
    """
    Renders a cyberpunk styled metric.
    """
    st.markdown(
        clean_html(f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """),
        unsafe_allow_html=True
    )

def citation_block(citation: Dict[str, Any]):
    """
    Renders a source citation card.
    """
    source = citation.get("source", "Unknown")
    page = citation.get("page", "?")
    score = citation.get("score", 0)
    snippet = citation.get("snippet", "")
    
    st.markdown(
        clean_html(f"""
        <div class="citation-card">
            <div class="citation-header">
                <span>FILE: {source} (pg. {page})</span>
                <span class="citation-score">MATCH: {score}%</span>
            </div>
            <div style="font-style: italic; color: #8b949e; margin-top: 4px;">
                "{snippet}"
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

def user_profile(username: str, email: str, avatar_path: str = None):
    """
    Renders user profile module in the sidebar.
    """
    # SVG base64 placeholder avatar
    avatar_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#00f0ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:24px; height:24px;">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
    </svg>
    """
    
    st.markdown(
        clean_html(f"""
        <div class="user-card">
            <div style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #00f0ff; box-shadow: 0 0 8px rgba(0, 240, 255, 0.4); margin-right: 12px; display: flex; align-items: center; justify-content: center; background: rgba(0,240,255,0.05);">
                {avatar_svg}
            </div>
            <div class="user-info">
                <div class="user-name">{username.upper()}</div>
                <div class="user-role">OS LEVEL: USER</div>
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )

def holographic_loader():
    """
    Renders an animated holographic scanner bar.
    """
    st.markdown(clean_html('<div class="hologram-loader"></div>'), unsafe_allow_html=True)
