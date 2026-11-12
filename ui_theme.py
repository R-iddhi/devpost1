import streamlit as st

_CSS = """<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', sans-serif; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.stApp { background: #F4F7FB; }
.block-container { max-width: 1120px; padding-top: 1.5rem; padding-bottom: 4rem; }
[data-testid="stHeading"] h1 { display: none; }
h2, h3 { font-weight: 600; color: #0B1F3A; letter-spacing: -0.2px; }
hr { margin: 2rem 0; border-color: #E3E8EF; }
[data-testid="stSidebar"] { background: #0B1F3A; }
[data-testid="stSidebar"] * { color: #E6EEF9; }
.hero { background: linear-gradient(135deg, #0B1F3A 0%, #003087 55%, #0070BA 100%); border-radius: 22px; padding: 28px 34px 26px; color: #FFFFFF; margin-bottom: 1.6rem; box-shadow: 0 14px 34px rgba(0, 48, 135, 0.28); }
.hero-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.brand { display: flex; align-items: center; gap: 12px; }
.logo { width: 40px; height: 40px; border-radius: 12px; background: #FFFFFF; color: #003087; font-weight: 700; font-size: 1.25rem; display: flex; align-items: center; justify-content: center; }
.brand-name { font-weight: 700; font-size: 1.1rem; }
.brand-sub { font-size: 0.78rem; opacity: 0.8; }
.chips span { background: rgba(255, 255, 255, 0.16); padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; margin-left: 6px; font-weight: 500; }
.hero .hero-title { color: #FFFFFF; font-size: 2.3rem; line-height: 1.15; font-weight: 700; letter-spacing: -0.8px; margin: 26px 0 8px; }
.hero-text { max-width: 640px; opacity: 0.88; font-size: 1rem; margin: 0 0 20px; }
.steps { display: flex; gap: 10px; flex-wrap: wrap; }
.step { background: rgba(255, 255, 255, 0.12); border: 1px solid rgba(255, 255, 255, 0.22); padding: 8px 16px; border-radius: 12px; font-size: 0.85rem; font-weight: 500; }
.step b { display: inline-flex; width: 22px; height: 22px; border-radius: 50%; background: #FFFFFF; color: #003087; align-items: center; justify-content: center; margin-right: 8px; font-size: 0.75rem; }
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 14px; padding: 16px 20px; box-shadow: 0 2px 10px rgba(0, 48, 135, 0.06); }
[data-testid="stMetricLabel"] { color: #5B6475; font-weight: 500; }
[data-testid="stMetricValue"] { color: #003087; font-weight: 600; }
.stButton > button, [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] { border-radius: 10px; font-weight: 600; padding: 0.65rem 1.2rem; transition: all 0.15s ease; }
[data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #0070BA, #003087); border: none; color: #FFFFFF; }
[data-testid="stBaseButton-primary"]:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0, 112, 186, 0.35); }
[data-testid="stBaseButton-secondary"] { border: 1px solid #0070BA; color: #0070BA; background: #FFFFFF; }
[data-testid="stBaseButton-secondary"]:hover { background: #EAF1FB; }
[data-testid="stChatMessage"] { background: #FFFFFF; border: 1px solid #E3E8EF; border-radius: 14px; padding: 14px 18px; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0, 48, 135, 0.05); }
[data-testid="stAlert"] { border-radius: 12px; border: none; }
[data-testid="stExpander"] { border: 1px solid #E3E8EF; border-radius: 12px; background: #FAFBFD; }
[data-testid="stDataFrame"] { border: 1px solid #E3E8EF; border-radius: 12px; overflow: hidden; }
[data-baseweb="select"] > div { border-radius: 10px; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #0070BA, #003087); }
</style>
<div class="hero"><div class="hero-top"><div class="brand"><div class="logo">S</div><div><div class="brand-name">Settle</div><div class="brand-sub">AI invoice negotiation workspace</div></div></div><div class="chips"><span>PayPal Sandbox</span><span>Qwen 2.5 (local)</span><span>Human approval</span></div></div><h1 class="hero-title">Get paid sooner,<br>without the chasing.</h1><p class="hero-text">Two AI agents negotiate an early-payment discount. Python enforces the money rules. You approve. PayPal settles.</p><div class="steps"><div class="step"><b>1</b>Negotiate</div><div class="step"><b>2</b>Approve</div><div class="step"><b>3</b>Invoice</div><div class="step"><b>4</b>Paid</div></div></div>"""


def apply():
    st.markdown(_CSS, unsafe_allow_html=True)