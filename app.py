import os

# Must run before `import streamlit` (Streamlit may import protobuf before Chroma loads).
# os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import streamlit as st

st.set_page_config(layout="wide", page_title="DocQueryAI")

theme_base = st.get_option("theme.base") or "light"
theme_primary = st.get_option("theme.primaryColor") or "#7C3AED"
theme_bg = st.get_option("theme.backgroundColor") or ("#0b1120" if theme_base == "dark" else "#ffffff")
theme_text = st.get_option("theme.textColor") or ("#e5e7eb" if theme_base == "dark" else "#0f172a")
theme_secondary_bg = st.get_option("theme.secondaryBackgroundColor") or ("#020617" if theme_base == "dark" else "#f1f5f9")

# Tune muted text per theme so light mode isn't dull.
muted_text = "#94a3b8" if theme_base == "dark" else "#475569"

st.markdown(
    f"""
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
:root {{
    --dq-primary: {theme_primary};
    --dq-bg: {theme_bg};
    --dq-text: {theme_text};
    --dq-secondary-bg: {theme_secondary_bg};
    --dq-muted: {muted_text};
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
[data-testid="stSidebar"] { display: none; }

[data-testid="stMainBlockContainer"] {
    padding-top: 40px !important;
    padding-bottom: 0 !important;
}

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background: radial-gradient(circle at 25% 20%, rgba(124, 58, 237, 0.18) 0%, var(--dq-bg) 55%);
    color: var(--dq-text);
}

.main .block-container {
    padding-top: 0;
    padding-bottom: 0;  
}

/* Brand*/
.brand-bar {
    margin-top:0 !important;   
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    font-size: 2.5rem;
    margin-bottom: 20px;
    color: var(--dq-primary);
}

.brand-icon {
    font-size: 42px;
    color: var(--dq-primary);
}

/* HERO FLEX */
.hero-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

/* Title */
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 1.5rem;
}

/* Tagline */
.hero-tagline {
    font-size: 1.2rem;
    color: var(--dq-muted);
    margin-bottom: 2rem;
    max-width: 650px;
}

/* Accent colors */
.purple { color: var(--dq-primary); }
.orange { color: #FF7A18; }

/* Force button wrapper to center */
.hero-button {
    display: flex !important;
    justify-content: center !important;
    width: 100%;
}

/* Button styling */
.hero-button {
    background: linear-gradient(135deg, var(--dq-primary), #6D28D9);
    color: white;
    border-radius: 8px;
    padding: 0.85rem 1.8rem;
    border: none;
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4);
    transition: all 0.2s ease;
    font-family: 'Sora', sans-serif;
}

.hero-button:hover { transform: translateY(-2px); }

/*Section Divider*/
.section-divider {
    width: 140px;
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 40px auto 20px auto;
}

.section-container {
    max-width: 1100px;
    margin: 0 auto;
    text-align: center;
}

.section-title {
    font-size: 2.0rem;
    font-weight: 600;
    margin-bottom: 10px;
}

.section-subtitle {
    font-size: 1.0rem;
    color: var(--dq-muted);
    margin-bottom: 60px;
}

/*STEPS SECTION*/
.steps-grid {
    display: flex;
    justify-content: space-between;
    gap: 40px;
    flex-wrap: wrap;
    max-width: 1100px;
    margin: 0 auto 80px auto;
    padding: 0 20px;
    text-align: left;
}

.step-item {
    flex: 1;
    min-width: 280px;
}

.step-label {
    color: var(--dq-primary);
    font-weight: 600;
    margin-bottom: 10px;
}

.step-title {
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.step-desc {
    color: var(--dq-muted);
    font-size: 1.05rem;
    line-height: 1.6;
}

.step-desc a {
    color: #FF7A18;
    text-decoration: none;
}

.step-desc a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .hero-title { font-size: 2.5rem; }
}

.accent-orange{
    color: #FF8000;
}

.upload-link {
    text-decoration: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# Branding 
st.markdown("""
<div class="brand-bar">
    <div class="brand">
        <span class="material-icons brand-icon">psychology</span>
        DocQueryAI
    </div>
</div>
""", unsafe_allow_html=True)

# Hero Content
st.markdown("""
<div class="hero-container">
    <div class="hero-title">
        Ask anything. Get grounded answers from <br>
        <span class="purple">Documents</span> in <span class="orange">seconds</span>
    </div>
    <div class="hero-tagline">
        DocQueryAI allows you to have a conversation with your PDF documents.
    </div>
    <div>
        <a href="/upload" target="_self" class="upload-link">
            <button class="hero-button"> Get Started 
                <span style="padding-left: 10px;" class="material-icons icon">login</span>
            </button>
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# section divider
st.markdown("""
  <div class="section-divider"></div>
""", unsafe_allow_html=True)

# docquery usage
st.markdown("""
<div class="section-container">
    <div class="section-title">
        Start to chat with your PDF in seconds
    </div>
    <div class="section-subtitle">
        Finding information on your PDF files is now easier than ever.
    </div>
</div>
""", unsafe_allow_html=True)

# steps section
st.markdown("""
<div class="steps-grid">
     <div class="step-item">
        <div class="step-label">Step 1</div>
        <div class="step-title">Upload your PDF file</div>
        <div class="step-desc">
            We'll process your PDF file and you can start to chat with it instantly. Use <span class="accent-orange">text-based PDFs</span> for best results.
        </div>
    </div>
    <div class="step-item">
        <div class="step-label">Step 2</div>
        <div class="step-title">Smart Indexing</div>
        <div class="step-desc">
            We transform your document into a searchable knowledge base, enabling precise and context-aware answers in seconds.
        </div>
    </div>
    <div class="step-item">
        <div class="step-label">Step 3</div>
        <div class="step-title">Start asking your questions</div>
        <div class="step-desc">
            Now you are all ready to query with DocQueryAI.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


