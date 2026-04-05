import streamlit as st

def show_loading_overlay(message="Processing your document..."):
    st.markdown(f"""
    <style>
    .loading-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.55);
        backdrop-filter: blur(4px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .loading-box {{
        background: #1e293b;
        padding: 40px 60px;
        border-radius: 12px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.6);
        text-align: center;
        font-family: 'Sora', sans-serif;
        color: #e5e7eb;
        border: 1px solid rgba(148, 163, 184, 0.18);
    }}

    .spinner {{
        border: 4px solid rgba(148, 163, 184, 0.25);
        border-top: 4px solid #7c3aed;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: auto;
    }}

    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>

    <div class="loading-overlay">
        <div class="loading-box">
            <div class="spinner"></div>
            <div>{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
