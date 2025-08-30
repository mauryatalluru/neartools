# NearTools — polished MVP (cookie-stable login) — Option A theme
# Keeps your features. Fixes:
# - SINGLE CLICK publish (guard + clean rerun, no double click)
# - No "form_name cannot be modified" error (unique form key & submit handled after the form)
# - Cookie manager "CookiesNotReady" flash hidden (we wait quietly until cookies are ready)
# - "E-mail or Phone Number" label
#
# Tip: add a file named logo.png in the project root for the hero/side logo.

import os
import re
import hashlib
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Tuple

import streamlit as st
import pandas as pd
from streamlit_cookies_manager import EncryptedCookieManager

# ------------------ Professional Startup Branding ------------------
APP_NAME = "NearTools"
TAGLINE  = "Own less. Do more."

# Professional startup color palette
PALETTE = {
    "primary": "#2563EB",     # Professional blue
    "secondary": "#7C3AED",   # Purple accent
    "success": "#10B981",     # Success green
    "warning": "#F59E0B",     # Warning amber
    "danger": "#EF4444",      # Error red
    "dark": "#1F2937",        # Dark text
    "light": "#F9FAFB",       # Light background
    "white": "#FFFFFF",       # Pure white
    "gray": "#6B7280",        # Secondary text
    "border": "#E5E7EB",      # Borders
    "card": "#FFFFFF",        # Card background
    "hover": "#3B82F6",       # Hover state
}

def inject_css():
    st.markdown(f"""
    <style>
      /* Professional Startup CSS Framework */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
      
      :root {{
        --primary: {PALETTE["primary"]};
        --secondary: {PALETTE["secondary"]};
        --success: {PALETTE["success"]};
        --warning: {PALETTE["warning"]};
        --danger: {PALETTE["danger"]};
        --dark: {PALETTE["dark"]};
        --light: {PALETTE["light"]};
        --white: {PALETTE["white"]};
        --gray: {PALETTE["gray"]};
        --border: {PALETTE["border"]};
        --card: {PALETTE["card"]};
        --hover: {PALETTE["hover"]};
      }}
      
      /* Base Styling */
      html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        position: relative;
        min-height: 100vh;
        overflow-y: auto !important;
        overflow-x: visible !important;
      }}
      
      /* Ensure scrolling works */
      [data-testid="stAppViewContainer"] {{
        overflow-y: auto !important;
        overflow-x: visible !important;
      }}
      
      .main .block-container {{
        overflow-y: auto !important;
        overflow-x: visible !important;
      }}
      
      /* Professional Hero Section */
      .hero-section {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        padding: 4rem 2rem;
        margin: -2rem -1rem 3rem -1rem;
        text-align: center;
        border-radius: 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      }}
      
      .hero-section::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
          radial-gradient(circle at 30% 70%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
          radial-gradient(circle at 70% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
        pointer-events: none;
        animation: heroGlow 8s ease-in-out infinite;
      }}
      
      @keyframes heroGlow {{
        0%, 100% {{ opacity: 0.3; }}
        50% {{ opacity: 0.6; }}
      }}
      
      .hero-content {{
        max-width: 900px;
        margin: 0 auto;
      }}
      
      .hero-title {{
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 1rem;
        line-height: 1.1;
        letter-spacing: -0.02em;
        color: white;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
      }}
      
      .hero-subtitle {{
        font-size: 1.25rem;
        margin-bottom: 2rem;
        font-weight: 400;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
      }}
      
      .hero-stats {{
        display: flex;
        gap: 2rem;
        justify-content: center;
        margin-top: 2rem;
        flex-wrap: wrap;
      }}
      
      .hero-stat {{
        text-align: center;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        animation: statFloat 6s ease-in-out infinite;
      }}
      
      .hero-stat:nth-child(1) {{ animation-delay: 0s; }}
      .hero-stat:nth-child(2) {{ animation-delay: 1s; }}
      .hero-stat:nth-child(3) {{ animation-delay: 2s; }}
      .hero-stat:nth-child(4) {{ animation-delay: 3s; }}
      
      .hero-stat:hover {{
        transform: translateY(-8px) scale(1.05);
        background: rgba(255, 255, 255, 0.2);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
      }}
      
      @keyframes statFloat {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
      }}
      
      .hero-stat-number {{
        font-size: 2.5rem;
        font-weight: 900;
        display: block;
        background: linear-gradient(45deg, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
      }}
      
      .hero-stat-label {{
        font-size: 0.875rem;
        opacity: 0.9;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      
      /* Professional Forms */
      .stTextInput>div>div>input,
      .stTextArea textarea,
      .stSelectbox div[data-baseweb="select"]>div,
      .stDateInput input,
      .stNumberInput input {{
        background: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(10px) !important;
        border: 2px solid rgba(0, 0, 0, 0.2) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        color: #000000 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        font-weight: 600 !important;
      }}
      
      .stTextInput>div>div>input:focus,
      .stTextArea textarea:focus,
      .stSelectbox div[data-baseweb="select"]>div:focus-within,
      .stDateInput input:focus,
      .stNumberInput input:focus {{
        outline: none !important;
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15), 0 8px 30px rgba(102, 126, 234, 0.2) !important;
        background: rgba(255, 255, 255, 0.98) !important;
        transform: translateY(-2px) !important;
      }}
      
      .stTextInput>div>div>input:hover,
      .stTextArea textarea:hover,
      .stSelectbox div[data-baseweb="select"]>div:hover,
      .stDateInput input:hover,
      .stNumberInput input:hover {{
        border-color: #9CA3AF !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12) !important;
      }}
      
      /* Professional Buttons */
      .stButton>button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        position: relative !important;
        overflow: hidden !important;
      }}
      
      .stButton>button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
      }}
      
      .stButton>button:hover::before {{
        left: 100%;
      }}
      
      .stButton>button:hover {{
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4) !important;
      }}
      
      .stButton>button:active {{
        transform: translateY(-1px) scale(0.98) !important;
        transition: all 0.1s ease !important;
      }}
      
      /* Professional Tabs */
      .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 16px !important;
        padding: 0.75rem !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
      }}
      
      .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        border-radius: 12px !important;
        color: #374151 !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 1rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
      }}
      
      .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(102, 126, 234, 0.1) !important;
        color: #667eea !important;
        transform: translateY(-2px) !important;
      }}
      
      .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-2px) !important;
      }}
      
      .stTabs [data-baseweb="tab"][aria-selected="true"]::before {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 20px;
        height: 3px;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 2px;
        animation: tabIndicator 0.3s ease-out;
      }}
      
      @keyframes tabIndicator {{
        from {{ width: 0; opacity: 0; }}
        to {{ width: 20px; opacity: 1; }}
      }}
      
      /* Better contrast for expanders and captions */
      .streamlit-expanderHeader {{
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1F2937 !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
      }}
      
      .streamlit-expanderHeader:hover {{
        background: rgba(255, 255, 255, 1) !important;
        border-color: #667eea !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15) !important;
      }}
      
      .streamlit-expanderContent {{
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin-top: 0.5rem !important;
      }}
      
      /* Professional Sidebar */
      [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 2px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 5px 0 20px rgba(31, 38, 135, 0.15) !important;
        overflow-y: auto !important;
        overflow-x: visible !important;
      }}
      
      /* Ensure sidebar content can scroll */
      [data-testid="stSidebar"] > div {{
        overflow-y: auto !important;
        overflow-x: visible !important;
        height: 100vh !important;
      }}
      
      /* Fix sidebar scrolling container */
      [data-testid="stSidebar"] .css-1d391kg {{
        overflow-y: auto !important;
        overflow-x: visible !important;
      }}
      
      /* Sidebar content styling */
      [data-testid="stSidebar"] .stMarkdown {{
        color: #000000 !important;
      }}
      
      [data-testid="stSidebar"] h3 {{
        color: #1e40af !important;
        font-weight: 700 !important;
      }}
      
      [data-testid="stSidebar"] .stSuccess {{
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        color: #065f46 !important;
      }}
      
      /* Professional Cards */
      .pro-card {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.15);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: cardEntrance 0.6s ease-out;
      }}
      
      .pro-card:nth-child(1) {{ animation-delay: 0.1s; }}
      .pro-card:nth-child(2) {{ animation-delay: 0.2s; }}
      .pro-card:nth-child(3) {{ animation-delay: 0.3s; }}
      
      @keyframes cardEntrance {{
        from {{ 
          opacity: 0; 
          transform: translateY(30px) scale(0.95); 
        }}
        to {{ 
          opacity: 1; 
          transform: translateY(0) scale(1); 
        }}
      }}
      
      .pro-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
        transition: left 0.6s ease;
      }}
      
      .pro-card:hover::before {{
        left: 100%;
      }}
      
      .pro-card:hover {{
        box-shadow: 0 25px 60px rgba(31, 38, 135, 0.25);
        transform: translateY(-12px) scale(1.03);
        border-color: rgba(102, 126, 234, 0.3);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.9) 100%);
      }}
      
      .pro-card:active {{
        transform: translateY(-6px) scale(1.01);
        transition: all 0.1s ease;
      }}
      
      .pro-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
      }}
      
      .pro-card-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--dark);
        margin: 0;
      }}
      
      .pro-card-badge {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.75rem;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }}
      
             /* Enhanced Success/Error States */
       .stSuccess {{
         background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%) !important;
         border: 2px solid rgba(16, 185, 129, 0.4) !important;
         border-radius: 12px !important;
         color: #065f46 !important;
         padding: 1rem !important;
         backdrop-filter: blur(10px) !important;
         animation: successPulse 0.6s ease-out !important;
         font-weight: 600 !important;
       }}
      
      .stError {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%) !important;
        border: 2px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 12px !important;
        color: #991b1b !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
        animation: errorShake 0.6s ease-out !important;
      }}
      
      @keyframes successPulse {{
        0% {{ transform: scale(0.95); opacity: 0; }}
        50% {{ transform: scale(1.02); }}
        100% {{ transform: scale(1); opacity: 1; }}
      }}
      
      @keyframes errorShake {{
        0%, 100% {{ transform: translateX(0); }}
        25% {{ transform: translateX(-5px); }}
        75% {{ transform: translateX(5px); }}
      }}
      
      /* Enhanced Info/Warning States */
      .stInfo {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%) !important;
        border: 2px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #1e40af !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
      }}
      
      .stWarning {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%) !important;
        border: 2px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 12px !important;
        color: #92400e !important;
        padding: 1rem !important;
        backdrop-filter: blur(10px) !important;
      }}
      
      /* Loading Animation */
      .loading-dots {{
        display: inline-block;
        position: relative;
        width: 20px;
        height: 20px;
      }}
      
      .loading-dots::after {{
        content: '';
        display: block;
        position: absolute;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: loadingDots 1.2s linear infinite;
      }}
      
      @keyframes loadingDots {{
        0% {{ left: 0; opacity: 1; }}
        50% {{ left: 12px; opacity: 0.5; }}
        100% {{ left: 24px; opacity: 1; }}
      }}
      
      /* Enhanced Typography */
      h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.2 !important;
      }}
      
      /* Smooth Scrolling - Disabled to fix scrolling issues */
      html {{
        scroll-behavior: auto;
      }}
      
      /* Selection Styling */
      ::selection {{
        background: rgba(102, 126, 234, 0.3);
        color: #1f2937;
      }}
      
      /* Enhanced Logo Display - High Quality */
      [data-testid="stImage"] img {{
        image-rendering: -webkit-optimize-contrast !important;
        image-rendering: auto !important;
        filter: contrast(1.1) brightness(1.05) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        background: transparent !important;
        padding: 4px !important;
        transition: all 0.3s ease !important;
      }}
      
      [data-testid="stImage"] img:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25) !important;
        filter: contrast(1.4) brightness(1.15) saturate(1.3) !important;
      }}
      
             /* Logo container styling - Clean and Simple */
       .logo-container {{
         background: transparent !important;
         border-radius: 8px !important;
         padding: 4px !important;
       }}
       
       /* Enhanced Your Listings Section - Better Contrast */
       [data-testid="stContainer"] {{
         background: rgba(255, 255, 255, 0.95) !important;
         border: 2px solid rgba(102, 126, 234, 0.2) !important;
         border-radius: 16px !important;
         padding: 1.5rem !important;
         margin: 1rem 0 !important;
         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
       }}
       
       /* Better text contrast for all content */
       .stMarkdown p, .stMarkdown div {{
         color: #1F2937 !important;
       }}
       
       .stMarkdown strong {{
         color: #000000 !important;
         font-weight: 700 !important;
       }}
       
       .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {{
         color: #1F2937 !important;
         font-weight: 700 !important;
       }}
       
       /* Enhanced button contrast */
       .stButton > button[data-testid="baseButton-secondary"] {{
         background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%) !important;
         color: white !important;
         border: 2px solid rgba(255, 255, 255, 0.2) !important;
         font-weight: 600 !important;
       }}
       
       .stButton > button[data-testid="baseButton-secondary"]:hover {{
         background: linear-gradient(135deg, #4B5563 0%, #374151 100%) !important;
         transform: translateY(-2px) !important;
       }}
     </style>
     """, unsafe_allow_html=True)

# ------------------ Config ------------------
ADMIN_EMAIL = "your.email@example.com"   # set your admin email to see the reset button

DB_DIR     = "data"
DB_PATH    = os.path.join(DB_DIR, "neartools.db")
IMAGES_DIR = "images"
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ------------------ DB schema ------------------
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    location TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    daily_price REAL NOT NULL,
    location TEXT NOT NULL,
    available_from TEXT,
    available_to TEXT,
    image_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    borrower_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_cost REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT NOT NULL,
    FOREIGN KEY(tool_id) REFERENCES tools(id) ON DELETE CASCADE,
    FOREIGN KEY(borrower_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TEXT NOT NULL,
    -- Keep your original FKs to avoid migration surprises
    FOREIGN KEY(tool_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewer_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    with conn:
        conn.executescript(SCHEMA_SQL)
    conn.close()

# ------------------ Auth helpers ------------------
def hash_password(pw: str) -> str:
    salt = "neartools_salt_v1"
    return hashlib.sha256((salt + pw).encode()).hexdigest()

def create_user(name: str, email: str, password: str, location: str = "") -> Tuple[bool, str]:
    conn = get_conn()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users(name, email, password_hash, location, created_at) VALUES(?,?,?,?,?)",
                (name.strip(), email.lower().strip(), hash_password(password), location.strip(), datetime.now(timezone.utc).isoformat()),
            )
        return True, "Account created! You can log in now."
    except sqlite3.IntegrityError:
        return False, "E-mail/Phone already registered. Try logging in."
    finally:
        conn.close()

def verify_user(email: str, password: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        if row and row["password_hash"] == hash_password(password):
            return row
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    finally:
        conn.close()

# ------------------ Data helpers ------------------
def add_tool(owner_id: int, name: str, description: str, category: str, daily_price: float,
             location: str, available_from: Optional[date], available_to: Optional[date],
             image_bytes: Optional[bytes]) -> int:
    image_path = None
    if image_bytes:
        fname = f"tool_{owner_id}_{int(datetime.now(timezone.utc).timestamp())}.jpg"
        image_path = os.path.join(IMAGES_DIR, fname)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
    conn = get_conn()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO tools(owner_id, name, description, category, daily_price, location,
                              available_from, available_to, image_path, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                owner_id, name.strip(), (description or "").strip(), (category or "").strip(),
                float(daily_price), location.strip(),
                available_from.isoformat() if available_from else None,
                available_to.isoformat() if available_to else None,
                image_path, datetime.now(timezone.utc).isoformat(),
            ),
        )
        tool_id = cur.lastrowid
    conn.close()
    return tool_id

def list_tools(keyword: str = "", category: str = "", location: str = "") -> List[sqlite3.Row]:
    kw  = f"%{(keyword or '').lower().strip()}%"
    cat = f"%{(category or '').lower().strip()}%" if category else "%"
    loc = f"%{(location or '').lower().strip()}%" if location else "%"
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT t.*, u.name AS owner_name, u.email AS owner_email
            FROM tools t JOIN users u ON u.id = t.owner_id
            WHERE
                (lower(t.name) LIKE ? OR lower(IFNULL(t.description,'')) LIKE ?)
                AND lower(IFNULL(t.category,'')) LIKE ?
                AND lower(t.location) LIKE ?
            ORDER BY t.created_at DESC
            """,
            (kw, kw, cat, loc),
        )
        return cur.fetchall()
    finally:
        conn.close()

def get_user_tools(owner_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM tools WHERE owner_id=? ORDER BY created_at DESC",
            (owner_id,)
        ).fetchall()
    finally:
        conn.close()

def tool_bookings(tool_id: int) -> List[Tuple[date, date]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT start_date, end_date FROM bookings WHERE tool_id=? AND status='confirmed'",
            (tool_id,)
        ).fetchall()
        return [(date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])) for r in rows]
    finally:
        conn.close()

def is_available(tool: sqlite3.Row, start: date, end: date) -> bool:
    if tool["available_from"] and start < date.fromisoformat(tool["available_from"]):
        return False
    if tool["available_to"] and end > date.fromisoformat(tool["available_to"]):
        return False
    for b_start, b_end in tool_bookings(tool["id"]):
        if not (end < b_start or start > b_end):
            return False
    return True

def create_booking(tool: sqlite3.Row, borrower_id: int, start: date, end: date) -> Tuple[bool, str]:
    days = (end - start).days + 1
    if days <= 0:
        return False, "End date must be the same or after start date."
    if not is_available(tool, start, end):
        return False, "Tool is not available for those dates."
    total_cost = float(tool["daily_price"]) * days
    conn = get_conn()
    with conn:
        conn.execute(
            """
            INSERT INTO bookings(tool_id, borrower_id, start_date, end_date, total_cost, status, created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (tool["id"], borrower_id, start.isoformat(), end.isoformat(), total_cost, "confirmed", datetime.now(timezone.utc).isoformat()),
        )
    conn.close()
    return True, f"Booking confirmed for {days} day(s) — total ${total_cost:.2f}."

def get_user_bookings(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT b.*, t.name AS tool_name, t.image_path, t.owner_id
            FROM bookings b JOIN tools t ON t.id=b.tool_id
            WHERE b.borrower_id=?
            ORDER BY b.created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return rows
    finally:
        conn.close()

def get_tool_bookings(tool_id: int) -> List[sqlite3.Row]:
    """Get all bookings for a specific tool, including borrower details"""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT b.*, u.name AS borrower_name, u.email AS borrower_email
            FROM bookings b JOIN users u ON u.id=b.borrower_id
            WHERE b.tool_id=?
            ORDER BY b.created_at DESC
            """,
            (tool_id,),
        ).fetchall()
        return rows
    finally:
        conn.close()

def cancel_booking(booking_id: int, user_id: int) -> Tuple[bool, str]:
    conn = get_conn()
    try:
        row = conn.execute("SELECT borrower_id, status FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not row:
            return False, "Booking not found."
        if int(row["borrower_id"]) != int(user_id):
            return False, "You can only cancel your own booking."
        if row["status"] != "confirmed":
            return False, "This booking is not confirmed."
        with conn:
            conn.execute("UPDATE bookings SET status='canceled' WHERE id=?", (booking_id,))
        return True, "Booking canceled."
    finally:
        conn.close()

def has_future_confirmed_bookings(tool_id: int) -> bool:
    today = date.today().isoformat()
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM bookings
            WHERE tool_id=? AND status='confirmed' AND end_date >= ?
            """,
            (tool_id, today),
        ).fetchone()
        return int(row["c"] or 0) > 0
    finally:
        conn.close()

def delete_tool(tool_id: int, owner_id: int) -> Tuple[bool, str]:
    conn = get_conn()
    try:
        tool = conn.execute("SELECT owner_id FROM tools WHERE id=?", (tool_id,)).fetchone()
        if not tool:
            return False, "Tool not found."
        if int(tool["owner_id"]) != int(owner_id):
            return False, "You can only delete tools you own."
        if has_future_confirmed_bookings(tool_id):
            return False, "Cannot delete: this tool has upcoming confirmed bookings."
        with conn:
            conn.execute("DELETE FROM tools WHERE id=?", (tool_id,))
        return True, "Tool deleted."
    finally:
        conn.close()

def add_review(tool_id: int, reviewer_id: int, rating: int, comment: str) -> None:
    conn = get_conn()
    with conn:
        conn.execute(
                    "INSERT INTO reviews(tool_id, reviewer_id, rating, comment, created_at) VALUES(?,?,?,?,?)",
        (tool_id, reviewer_id, int(rating), (comment or "").strip(), datetime.now(timezone.utc).isoformat()),
        )
    conn.close()

def get_tool_reviews(tool_id: int) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT r.rating, r.comment, r.created_at, u.name AS reviewer
            FROM reviews r JOIN users u ON u.id=r.reviewer_id
            WHERE r.tool_id=? ORDER BY r.created_at DESC
            """,
            conn,
            params=(tool_id,),
        )
    finally:
        conn.close()

def get_metrics() -> tuple[int, int, int, int]:
    init_db()
    conn = get_conn()
    try:
        users    = conn.execute("SELECT IFNULL(COUNT(*), 0) FROM users").fetchone()[0]
        tools    = conn.execute("SELECT IFNULL(COUNT(*), 0) FROM tools").fetchone()[0]
        bookings = conn.execute("SELECT IFNULL(COUNT(*), 0) FROM bookings").fetchone()[0]
        reviews  = conn.execute("SELECT IFNULL(COUNT(*), 0) FROM reviews").fetchone()[0]
        return int(users), int(tools), int(bookings), int(reviews)
    finally:
        conn.close()

# ------------------ Matching / ranking ------------------
AI_HINTS = {
    "paint": ["ladder", "paint sprayer", "roller", "drop cloth", "tarp", "brush"],
    "ceiling": ["ladder", "roller", "paint sprayer"],
    "mount tv": ["hammer drill", "drill", "stud finder", "level", "driver", "screwdriver"],
    "concrete": ["hammer drill", "masonry", "impact"],
    "build table": ["saw", "circular saw", "jigsaw", "drill", "sander", "clamps"],
    "cut wood": ["saw", "circular saw", "jigsaw"],
    "garden": ["hedge trimmer", "ladder"],
    "hedge": ["hedge trimmer", "ladder"],
    "bbq": ["grill", "barbeque", "barbecue"],
    "pressure wash": ["pressure washer", "power washer", "hose"],
}

def _tokenize(text: str) -> set[str]:
    return set(w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 1)

def _expand_with_hints(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for k, hints in AI_HINTS.items():
        if k in tokens:
            expanded.update(hints)
    return expanded

def _avg_rating_and_count(tool_id: int) -> tuple[float, int]:
    df = get_tool_reviews(tool_id)
    if df.empty:
        return 0.0, 0
    return float(df["rating"].mean()), int(len(df))

def _recent_bookings_count(tool_id: int, days: int = 90) -> int:
    conn = get_conn()
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM bookings WHERE tool_id=? AND created_at >= ?",
            (tool_id, cutoff),
        ).fetchone()
        return int(row["c"] or 0)
    finally:
        conn.close()

def score_tool(tool: sqlite3.Row, job_text: str, start: Optional[date], end: Optional[date]) -> tuple[float, list[str]]:
    reasons, score = [], 0.0
    if start and end:
        if is_available(tool, start, end):
            score += 3.0
            reasons.append("available for your dates")
        else:
            return (-100.0, ["not available for selected dates"])
    if job_text:
        job_tokens = _expand_with_hints(_tokenize(job_text))
        hay = _tokenize(f"{tool['name']} {(tool['description'] or '')} {(tool['category'] or '')}")
        overlap = job_tokens.intersection(hay)
        if overlap:
            score += min(5.0, 1.0 + 0.8 * len(overlap))
            reasons.append("matches: " + ", ".join(list(overlap)[:3]))
        else:
            score -= 0.5
    avg, cnt = _avg_rating_and_count(tool["id"])
    if cnt > 0:
        score += (avg - 3.0) * 0.8
        reasons.append(f"{avg:.1f}⭐ from {cnt}")
    else:
        reasons.append("no reviews yet")
    recent = _recent_bookings_count(tool["id"])
    if recent > 0:
        score += min(3.0, 0.5 + 0.4 * recent)
        reasons.append(f"{recent} recent booking(s)")
    return score, reasons

def rank_tools(tools: list[sqlite3.Row], job_text: str, start, end) -> list[tuple[sqlite3.Row, float, list[str]]]:
    ranked = []
    for t in tools:
        s, reasons = score_tool(t, job_text, start, end)
        ranked.append((t, s, reasons))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked

# ------------------ UI helpers ------------------
def reviews_summary(tool_id: int) -> str:
    df = get_tool_reviews(tool_id)
    if df.empty:
        return "No reviews yet."
    avg = float(df["rating"].mean())
    return f"⭐ {avg:.1f} from {len(df)} review(s)"

def tool_card(tool: sqlite3.Row):
    """Professional tool card with modern startup design"""
    with st.container():
        # Create a professional card layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if tool["image_path"] and os.path.exists(tool["image_path"]):
                st.image(tool["image_path"], width=250)
            else:
                st.markdown("""
                <div style="width: 250px; height: 180px; background: var(--light); 
                            border: 1px solid var(--border); border-radius: 8px; 
                            display: flex; align-items: center; justify-content: center;
                            font-size: 3rem; color: var(--gray);">
                    🧰
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="pro-card">
                <div class="pro-card-header">
                    <h3 class="pro-card-title">{tool['name']}</h3>
                    <span class="pro-card-badge">${tool['daily_price']:.2f}/day</span>
                </div>
                <div style="color: var(--gray); margin-bottom: 1rem; font-size: 0.875rem;">
                    📍 {tool['location']} • {tool['category'] or 'Uncategorized'}
                </div>
                <p style="color: var(--dark); margin-bottom: 1rem; line-height: 1.5;">
                    {tool['description'] or 'No description available.'}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; border-top: 1px solid var(--border);">
                    <div style="color: var(--gray); font-size: 0.875rem;">
                        <strong style="color: var(--dark);">{tool['owner_name']}</strong><br>
                        {tool['owner_email']}
                    </div>
                    <div style="color: var(--gray); font-size: 0.875rem; text-align: right;">
                        {reviews_summary(tool["id"])}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ------------------ App ------------------
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")
    init_db()
    inject_css()

    # ===== Cookie manager (non-blocking) =====
    cookies = EncryptedCookieManager(
        prefix="neartools",
        password=st.secrets.get("COOKIE_PASSWORD", "fallback_dev_only"),
    )
    cookies_ready = cookies.ready()  # don't stop the app if cookies aren't ready yet
 
    # Restore user from cookie if present
    st.session_state.setdefault("user", None)
    saved_email = ""
    if cookies_ready:
        saved_email = (cookies.get("user_email") or "").strip()
    if saved_email and not st.session_state["user"]:
        row = get_user_by_email(saved_email)
        if row:
            st.session_state["user"] = dict(row)


    

    # ===== Hero (logo + greeting) =====
    greet = ""
    if st.session_state.get("user"):
        first = (st.session_state["user"]["name"] or "").split(" ")[0]
        greet = f"Hi, {first} 👋 — "

    col_logo, col_main = st.columns([1, 6], vertical_alignment="center")
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width="stretch")
        else:
            st.write("🧰")
    with col_main:
        st.markdown(
            f"""
            <div class="hero-section">
                <div class="hero-content">
                    <div class="hero-title">{greet}{APP_NAME}</div>
                    <div class="hero-subtitle">{TAGLINE}</div>
                </div>
                <div class="hero-stats">
                    <div class="hero-stat">
                        <div class="hero-stat-number">{get_metrics()[0]}</div>
                        <div class="hero-stat-label">Users</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-number">{get_metrics()[1]}</div>
                        <div class="hero-stat-label">Tools</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-number">{get_metrics()[2]}</div>
                        <div class="hero-stat-label">Bookings</div>
                    </div>
                    <div class="hero-stat">
                        <div class="hero-stat-number">{get_metrics()[3]}</div>
                        <div class="hero-stat-label">Reviews</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ===== Sidebar: auth + admin reset =====
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width="stretch")
        st.markdown("### Own less. Do more.")
        st.header("Account")

        if st.session_state.get("user"):
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); 
                        color: white; padding: 0.75rem 1rem; border-radius: 8px; 
                        margin: 0.5rem 0; text-align: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                <strong style="color: white; font-size: 1rem;">✅ Logged in as {st.session_state['user']['name']}</strong>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log out", key="logout_btn"):
                st.session_state.pop("user", None)
                if cookies_ready:
                    cookies["user_email"] = ""
                    cookies.save()
                st.toast("You’ve been logged out.", icon="✅")
                st.rerun()

        else:
            login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

            with login_tab:
                l_email = st.text_input("E-mail or Phone Number", key="login_email")
                l_pw    = st.text_input("Password", type="password", key="login_pw")

                if st.button("Log in", key="login_btn"):
                    # only attempt login if both fields provided
                    if not l_email or not l_pw:
                        st.warning("Please enter your e-mail/phone and password.")
                    else:
                        u = verify_user(l_email, l_pw)
                        if u:
                            st.session_state["user"] = dict(u)
                            st.session_state["user"] = dict(u)
                            try:
                                cookies["user_email"] = l_email.lower().strip()
                                cookies.save()
                            except Exception:
                                pass
                            st.success("Logged in!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Check your e-mail/phone and password.")




            with signup_tab:
                s_name  = st.text_input("Full name")
                s_email = st.text_input("E-mail or Phone Number")
                s_loc   = st.text_input("Location (City or ZIP)")
                s_pw1   = st.text_input("Password", type="password", key="pw1")
                s_pw2   = st.text_input("Confirm password", type="password", key="pw2")
                if st.button("Create account"):
                    if not (s_name and s_email and s_pw1 and s_pw2):
                        st.error("Please fill all fields.")
                    elif s_pw1 != s_pw2:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = create_user(s_name, s_email, s_pw1, s_loc)
                        (st.success if ok else st.error)(msg)

        st.divider()
        if st.session_state.get("user") and st.session_state["user"]["email"] == ADMIN_EMAIL:
            if st.button("🗑 Reset local database (admin)"):
                try:
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                    init_db()
                    st.success("Database reset. Reload the page.")
                except Exception as e:
                    st.error(f"Could not reset DB: {e}")

    # ===== Tabs =====
    tab_browse, tab_list, tab_book, tab_my_tool_bookings = st.tabs(["Browse", "List a Tool", "My Bookings", "My Tool Bookings"])

    # -------- Browse --------
    with tab_browse:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 1.5rem; border-radius: 12px; 
                    margin: 0 0 1rem 0; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
            <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">Find Tools Near You</h3>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2.6, 2, 2, 2.6])
        with c1:
            job_text = st.text_input("Describe your job (optional)",
                                     placeholder="e.g., Paint ceiling; Mount TV; Build a small table…")
        with c2:
            category = st.selectbox("Category (optional)",
                                    ["", "drill", "ladder", "saw", "sewing machine", "sander", "pressure washer"])
        with c3:
            location = st.text_input("Location filter (optional)")
        with c4:
            d1 = st.date_input("Start date (optional)", value=None, key="browse_start")
            d2 = st.date_input("End date (optional)", value=None, key="browse_end")
            st.caption("Tip: set dates to only see items available for that window.")

        tools = list_tools("", category, location)
        if job_text.strip():
            tools = [t for t in tools if any(tok in (f"{t['name']} {(t['description'] or '')} {(t['category'] or '')}").lower()
                                             for tok in _tokenize(job_text))]

        if not tools:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                        padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
                <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">No Tools Found</h4>
                <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                    Try clearing your filters or be the first to list a tool in your area!
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            ranked = rank_tools(tools, job_text, d1 if d1 else None, d2 if d2 else None)
            for t, score, reasons in ranked:
                tool_card(t)

                df_reviews = get_tool_reviews(t["id"])
                with st.expander(f"Reviews ({len(df_reviews)})"):
                    if df_reviews.empty:
                        st.markdown("""
                        <div style="background: rgba(255, 255, 255, 0.95); 
                                    color: #6B7280; padding: 1rem; border-radius: 8px; 
                                    margin: 0.5rem 0; border: 1px dashed rgba(107, 114, 128, 0.3); 
                                    text-align: center;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
                            <p style="margin: 0; color: #374151; font-weight: 500;">No reviews yet</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        for _, r in df_reviews.iterrows():
                            st.markdown(f"""
                            <div style="background: rgba(255, 255, 255, 0.9); 
                                        color: #1F2937; padding: 0.75rem; border-radius: 6px; 
                                        margin: 0.5rem 0; border: 1px solid rgba(0, 0, 0, 0.05);">
                                                                 <strong style="color: #1F2937;">{int(r['rating'])}⭐</strong> · by <strong style="color: #374151;">{r['reviewer']}</strong> · <span style="color: #6B7280;">{datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')}</span>
                                {f'<br><div style="margin-top: 0.5rem; color: #374151; font-style: italic;">{r["comment"]}</div>' if r["comment"] else ''}
                            </div>
                            """, unsafe_allow_html=True)

                if d1 and d2:
                    ok = score >= 0 and is_available(t, d1, d2)
                    st.write("Availability:", "✅ Available" if ok else "❌ Not available")

                if reasons:
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.95); 
                                color: #1F2937; padding: 0.75rem 1rem; border-radius: 8px; 
                                margin: 0.5rem 0; border: 1px solid rgba(0, 0, 0, 0.1); 
                                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                        <strong style="color: #374151;">Why this result:</strong> {" • ".join(reasons[:4])}
                    </div>
                    """, unsafe_allow_html=True)

                if st.session_state.get("user") and d1 and d2:
                    days = (d2 - d1).days + 1
                    if days > 0:
                        est = float(t["daily_price"]) * days
                        st.write(f"Estimated cost: **${est:.2f}** for **{days}** day(s).")
                    if st.button("Book this tool", key=f"book_{t['id']}"):
                        if is_available(t, d1, d2):
                            ok, msg = create_booking(t, st.session_state["user"]["id"], d1, d2)
                            (st.success if ok else st.error)(msg)
                        else:
                            st.error("Sorry, those dates just got taken.")
                st.divider()

    # -------- List a Tool (single-click, rerun-safe) --------
    with tab_list:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 1.5rem; border-radius: 12px; 
                    margin: 0 0 1rem 0; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
            <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">List a Tool or Appliance</h3>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("user"):
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); 
                        border: 2px dashed rgba(245, 158, 11, 0.3); border-radius: 16px; 
                        padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                <h4 style="color: #92400e; margin: 0 0 0.5rem 0; font-size: 1.25rem;">Login Required</h4>
                <p style="color: #B45309; margin: 0; font-size: 0.9rem;">
                    Please log in to list your tools and start earning!
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Reset submitting flag when form is loaded
            if "submitting" not in st.session_state:
                st.session_state["submitting"] = False
            # (B) Render the form with better submission handling
            with st.form(key=f"list_form_{st.session_state['user']['id']}", clear_on_submit=False):
                name  = st.text_input("Tool name *", placeholder="e.g., Hammer Drill", key=f"name_{st.session_state['user']['id']}")
                desc  = st.text_area("Description", placeholder="Add details, condition, size, etc.", key=f"desc_{st.session_state['user']['id']}")
                cat   = st.text_input("Category", placeholder="e.g., drill, ladder, saw…", key=f"cat_{st.session_state['user']['id']}")
                price = st.number_input("Daily price (USD) *", min_value=1.0, step=1.0, key=f"price_{st.session_state['user']['id']}")
                loc   = st.text_input("Location (City or ZIP) *", key=f"loc_{st.session_state['user']['id']}")
                afrom = st.date_input("Available from", value=None, key=f"afrom_{st.session_state['user']['id']}")
                ato   = st.date_input("Available to", value=None, key=f"ato_{st.session_state['user']['id']}")
                img   = st.file_uploader("Photo (JPG/PNG)", type=["jpg", "jpeg", "png"], key=f"img_{st.session_state['user']['id']}")
                submitted = st.form_submit_button(
                    "🔄 Publishing..." if st.session_state.get("submitting", False) else "Publish listing",
                    disabled=st.session_state.get("submitting", False)
                )

            # (C) Handle form submission with proper state management
            if submitted and not st.session_state.get("submitting", False):
                st.session_state["submitting"] = True
                problems = []
                if not name: problems.append("Tool name")
                if not loc:  problems.append("Location")
                try:
                    price_ok = float(price) >= 1.0
                except Exception:
                    price_ok = False
                if not price_ok: problems.append("Daily price (>= 1)")

                if problems:
                    st.error("Please fill: " + ", ".join(problems))
                else:
                    try:
                        _id = add_tool(
                            st.session_state["user"]["id"],
                            name.strip(),
                            (desc or "").strip(),
                            (cat or "").strip(),
                            float(price),
                            loc.strip(),
                            afrom or None,
                            ato or None,
                            (img.read() if img else None),
                        )
                        st.success(f"✅ Tool successfully listed! Your tool ID is {_id}.")
                        # Reset submitting flag and clear form after successful submission
                        st.session_state["submitting"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Couldn't publish: {e}")
                        st.session_state["submitting"] = False

        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 1.5rem; border-radius: 12px; 
                    margin: 2rem 0 1rem 0; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
            <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">Your Listings</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.get("user"):
            my_tools = get_user_tools(st.session_state["user"]["id"])
            if not my_tools:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                            border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                            padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🧰</div>
                    <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">No Tools Listed Yet</h4>
                    <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                        Start sharing your tools with the community! List your first tool above.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for t in my_tools:
                    with st.container(border=True):
                        cols = st.columns([1, 2, 1])
                        with cols[0]:
                            if t["image_path"] and os.path.exists(t["image_path"]):
                                st.image(t["image_path"], width=120)
                            else:
                                st.markdown("""
                                <div style="width: 120px; height: 90px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                            border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 12px; 
                                            display: flex; align-items: center; justify-content: center;
                                            font-size: 2rem; color: white; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
                                    🧰
                                </div>
                                """, unsafe_allow_html=True)
                        with cols[1]:
                            st.markdown(f"""
                            <div style="padding: 0.5rem 0;">
                                <h4 style="color: #1F2937; margin: 0 0 0.5rem 0; font-size: 1.1rem;">{t['name']}</h4>
                                <p style="color: #6B7280; margin: 0 0 0.5rem 0; font-size: 0.9rem;">
                                    <strong style="color: #059669;">${t['daily_price']:.2f}/day</strong>
                                </p>
                                <p style="color: #374151; margin: 0 0 0.5rem 0; font-size: 0.85rem; line-height: 1.4;">
                                    {t["description"] or "No description available."}
                                </p>
                                <p style="color: #6B7280; margin: 0; font-size: 0.8rem;">
                                    📅 Available: {t['available_from'] or 'Always'} → {t['available_to'] or 'Always'}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        with cols[2]:
                            if st.button("🗑️ Delete", key=f"del_{t['id']}", type="secondary"):
                                ok, msg = delete_tool(t["id"], st.session_state["user"]["id"])
                                (st.success if ok else st.error)(msg)
                                st.rerun()


    # -------- My Bookings --------
    with tab_book:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 1.5rem; border-radius: 12px; 
                    margin: 0 0 1rem 0; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
            <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">Your Bookings</h3>
        </div>
        """, unsafe_allow_html=True)
        if not st.session_state.get("user"):
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                        padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔐</div>
                <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">Login Required</h4>
                <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                    Please log in to view and manage your bookings.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            rows = get_user_bookings(st.session_state["user"]["id"])
            if not rows:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                            border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                            padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">📅</div>
                    <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">No Bookings Yet</h4>
                    <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                        Start browsing tools and make your first booking!
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                for b in rows:
                    with st.container(border=True):
                        st.write(
                            f"**{b['tool_name']}** — {b['start_date']} → {b['end_date']}  "
                            f"•  ${b['total_cost']:.2f}  •  Status: **{b['status']}**"
                        )
                        if b["image_path"] and os.path.exists(b["image_path"]):
                            st.image(b["image_path"], width=160)

                        can_cancel = (b["status"] == "confirmed") and (b["borrower_id"] == st.session_state["user"]["id"])
                        if can_cancel:
                            if st.button("Cancel this booking", key=f"cancel_{b['id']}"):
                                ok, msg = cancel_booking(b["id"], st.session_state["user"]["id"])
                                (st.success if ok else st.error)(msg)
                                st.rerun()

                        with st.expander("Leave a review"):
                            rating  = st.slider("Rating", 1, 5, 5, key=f"rv_{b['id']}")
                            comment = st.text_area("Comment", key=f"rvc_{b['id']}")
                            if st.button("Submit review", key=f"rvb_{b['id']}"):
                                add_review(b["tool_id"], st.session_state["user"]["id"], rating, comment)
                                st.success("Thanks! Review added.")

    # -------- My Tool Bookings (for lenders) --------
    with tab_my_tool_bookings:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 1.5rem; border-radius: 12px; 
                    margin: 0 0 1rem 0; text-align: center; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
            <h3 style="margin: 0; color: white; font-size: 1.5rem; font-weight: 700;">Bookings for My Tools</h3>
        </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("user"):
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                        padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔐</div>
                <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">Login Required</h4>
                <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                    Please log in to view bookings for your tools.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            user_id = st.session_state["user"]["id"]
            my_tools = get_user_tools(user_id)  # Reuse existing function to get tools owned by user

            if not my_tools:
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                            border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                            padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🛠️</div>
                    <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">No Tools Listed Yet</h4>
                    <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                        You haven't listed any tools, so there are no bookings to display.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                all_tool_bookings = []
                for tool in my_tools:
                    bookings = get_tool_bookings(tool["id"])
                    if bookings:
                        for booking in bookings:
                            all_tool_bookings.append({
                                "tool_name": tool["name"],
                                "tool_image": tool["image_path"],
                                "borrower_name": booking["borrower_name"],
                                "borrower_email": booking["borrower_email"],
                                "start_date": booking["start_date"],
                                "end_date": booking["end_date"],
                                "total_cost": booking["total_cost"],
                                "created_at": booking["created_at"]
                            })

                if not all_tool_bookings:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                                border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 16px; 
                                padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">🗓️</div>
                        <h4 style="color: #374151; margin: 0 0 0.5rem 0; font-size: 1.25rem;">No Bookings for Your Tools</h4>
                        <p style="color: #6B7280; margin: 0; font-size: 0.9rem;">
                            Your listed tools haven't been booked yet. Share them more to get rentals!
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    for booking in all_tool_bookings:
                        with st.container(border=True):
                            cols = st.columns([1, 3])
                            with cols[0]:
                                if booking["tool_image"] and os.path.exists(booking["tool_image"]):
                                    st.image(booking["tool_image"], width="stretch")
                                else:
                                    st.write("🧰")
                            with cols[1]:
                                st.markdown(f"""
                                    <div style="color: #1F2937; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
                                        {booking['tool_name']}
                                    </div>
                                    <div style="color: #374151; font-size: 0.95rem; margin-bottom: 0.3rem;">
                                        Booked by: <span style="font-weight: 600;">{booking['borrower_name']}</span> ({booking['borrower_email']})
                                    </div>
                                    <div style="color: #374151; font-size: 0.9rem; margin-bottom: 0.3rem;">
                                        Dates: {booking['start_date']} to {booking['end_date']}
                                    </div>
                                    <div style="color: #374151; font-size: 0.9rem;">
                                        Total Price: <span style="font-weight: 600;">${booking['total_cost']:.2f}</span>
                                    </div>
                                                                         <div style="color: #6B7280; font-size: 0.8rem; margin-top: 0.5rem;">
                                         Booked on: {datetime.fromisoformat(booking['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')}
                                     </div>
                                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

