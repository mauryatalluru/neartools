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
from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple

import streamlit as st
import pandas as pd
from streamlit_cookies_manager import EncryptedCookieManager

# ------------------ Branding ------------------
APP_NAME = "NearTools"
TAGLINE  = "Own less. Do more."

PALETTE = {
    "green":  "#2F6D3A",   # primary
    "leaf":   "#9BCB8F",   # accent
    "teal":   "#39A68C",   # hover
    "orange": "#F2B266",   # secondary
    "ink":    "#1E2A1C",   # headings
    "card":   "#F6F8F4",   # card surface
    "bg":     "#E9F0E6",   # page background
    "stroke": "#DCE5D8",   # borders
}

def inject_css():
    st.markdown(f"""
    <style>
      :root {{
        --bg: {PALETTE["bg"]};
        --card: {PALETTE["card"]};
        --stroke: {PALETTE["stroke"]};
        --ink: {PALETTE["ink"]};
        --green: {PALETTE["green"]};
        --leaf: {PALETTE["leaf"]};
        --teal: {PALETTE["teal"]};
        --orange: {PALETTE["orange"]};
      }}
      html, body, [data-testid="stAppViewContainer"] {{
        background: var(--bg);
      }}
      .hero {{
        background: linear-gradient(90deg, rgba(155,203,143,.20) 0%,
                                         rgba(57,166,140,.14) 60%,
                                         rgba(242,178,102,.12) 100%);
        border: 1px solid var(--stroke);
        border-radius: 22px;
        padding: 16px 20px;
        margin: 8px 0 16px 0;
        box-shadow: 0 8px 24px rgba(26, 58, 34, .06);
      }}
      .hero .title {{ font-weight: 900; letter-spacing: .2px; font-size: 1.6rem; margin: 0; color: var(--ink); }}
      .hero .tagline {{ margin: 2px 0 0 0; font-size: .98rem; color: #5a6a5c; }}
      .pill {{
        background: var(--card); border: 1px solid var(--stroke); border-radius: 14px;
        padding: 10px 14px; text-align: center; box-shadow: 0 3px 12px rgba(26,58,34,.05);
      }}
      .pill .k {{ font-size: 1.15rem; font-weight: 800; color: var(--ink); }}
      .pill .lbl {{ font-size: .78rem; color: #6a776a; margin-top:2px; }}
      .stTextInput>div>div>input,
      .stTextArea textarea,
      .stSelectbox div[data-baseweb="select"]>div,
      .stDateInput input {{
        background: white; border-radius: 10px; border: 1px solid var(--stroke);
        box-shadow: inset 0 2px 6px rgba(26,58,34,.04);
      }}
      .stTextInput>div>div>input:focus,
      .stTextArea textarea:focus,
      .stSelectbox div[data-baseweb="select"]>div:focus-within,
      .stDateInput input:focus {{
        outline: none !important; border-color: var(--leaf);
        box-shadow: 0 0 0 3px rgba(155,203,143,.35);
      }}
      .stButton>button {{
        background: var(--green); color: white; border-radius: 10px; border: 0;
        padding: .55rem .9rem; font-weight: 700; box-shadow: 0 6px 14px rgba(47,109,58,.18);
      }}
      .stButton>button:hover {{ background: var(--teal); }}
      button[role="tab"][aria-selected="true"] {{ border-bottom: 3px solid var(--green) !important; }}
      [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(155,203,143,.12), rgba(233,240,230,.6));
        border-right: 1px solid var(--stroke);
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
                (name.strip(), email.lower().strip(), hash_password(password), location.strip(), datetime.utcnow().isoformat()),
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
        fname = f"tool_{owner_id}_{int(datetime.utcnow().timestamp())}.jpg"
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
                image_path, datetime.utcnow().isoformat(),
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
            (tool["id"], borrower_id, start.isoformat(), end.isoformat(), total_cost, "confirmed", datetime.utcnow().isoformat()),
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
            (tool_id, reviewer_id, int(rating), (comment or "").strip(), datetime.utcnow().isoformat()),
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
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
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
    with st.container(border=True):
        c0, c1, c2 = st.columns([1, 2, 2])
        with c0:
            if tool["image_path"] and os.path.exists(tool["image_path"]):
                st.image(tool["image_path"], use_container_width=True)
            else:
                st.write("🧰")
        with c1:
            st.subheader(tool["name"])
            st.write(f"**Category:** {tool['category'] or '—'}  \n**Location:** {tool['location']}")
            st.write(tool["description"] or "No description.")
            st.write(f"**Daily price:** ${tool['daily_price']:.2f}")
            st.caption(reviews_summary(tool["id"]))
        with c2:
            st.write(f"**Owner:** {tool['owner_name']}  \n**Email:** {tool['owner_email']}")

# ------------------ App ------------------
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")
    init_db()
    inject_css()

    # ===== Cookie manager – wait silently until ready (prevents red traceback flash) =====
    cookies = EncryptedCookieManager(
        prefix="neartools",
        password=st.secrets.get("COOKIE_PASSWORD", "fallback_dev_only"),
    )
    try:
        if not cookies.ready():
            st.empty()  # render nothing while cookie backend initializes
            st.stop()
    except Exception:
        st.empty()
        st.stop()

    # ===== Restore user from cookie if present =====
    st.session_state.setdefault("user", None)
    saved_email = (cookies.get("user_email") or "").strip()
    if saved_email and not st.session_state["user"]:
        row = get_user_by_email(saved_email)
        if row:
            st.session_state["user"] = dict(row)

    # ===== one-shot guard to stop double publish =====
    st.session_state.setdefault("publish_guard", False)
    if st.session_state["publish_guard"]:
        # Clear the guard at the start of each fresh render
        st.session_state["publish_guard"] = False

    # ===== Hero (logo + greeting) =====
    greet = ""
    if st.session_state.get("user"):
        first = (st.session_state["user"]["name"] or "").split(" ")[0]
        greet = f"Hi, {first} 👋 — "

    col_logo, col_main = st.columns([1, 6], vertical_alignment="center")
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.write("🧰")
    with col_main:
        st.markdown(
            f"""
            <div class="hero">
                <div class="title">{greet}{APP_NAME}</div>
                <div class="tagline">{TAGLINE}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        # Metrics row
        try:
            m_users, m_tools, m_bookings, m_reviews = get_metrics()
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Users", m_users)
            with c2: st.metric("Tools", m_tools)
            with c3: st.metric("Bookings", m_bookings)
            with c4: st.metric("Reviews", m_reviews)
        except Exception as e:
            st.warning(f"Metrics unavailable: {e}")

    # ===== Sidebar: auth + admin reset =====
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        st.markdown("### Own less. Do more.")
        st.header("Account")

        if st.session_state.get("user"):
            st.success(f"Logged in as {st.session_state['user']['name']}")
            if st.button("Log out", key="logout_btn"):
                st.session_state.pop("user", None)
                try:
                    cookies["user_email"] = ""
                    cookies.save()
                except Exception as e:
                    st.warning(f"Could not update cookies: {e}")
                st.toast("You’ve been logged out.", icon="✅")
                st.rerun()
        else:
            login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

            with login_tab:
                l_email = st.text_input("E-mail or Phone Number", key="login_email")
                l_pw    = st.text_input("Password", type="password", key="login_pw")
                if st.button("Log in"):
                    u = verify_user(l_email, l_pw)
                    if u:
                        st.session_state["user"] = dict(u)
                        cookies["user_email"] = l_email.lower().strip()
                        cookies.save()
                        st.success("Logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

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
    tab_browse, tab_list, tab_book = st.tabs(["Browse", "List a Tool", "My Bookings"])

    # -------- Browse --------
    with tab_browse:
        st.subheader("Find tools near you")
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
            st.info("No tools found. Try clearing filters or list your first tool.")
        else:
            ranked = rank_tools(tools, job_text, d1 if d1 else None, d2 if d2 else None)
            for t, score, reasons in ranked:
                tool_card(t)

                df_reviews = get_tool_reviews(t["id"])
                with st.expander(f"Reviews ({len(df_reviews)})"):
                    if df_reviews.empty:
                        st.write("No reviews yet.")
                    else:
                        for _, r in df_reviews.iterrows():
                            st.write(f"**{int(r['rating'])}⭐** · by {r['reviewer']} · {r['created_at']}")
                            if r["comment"]:
                                st.write(r["comment"])
                            st.markdown("---")

                if d1 and d2:
                    ok = score >= 0 and is_available(t, d1, d2)
                    st.write("Availability:", "✅ Available" if ok else "❌ Not available")

                if reasons:
                    st.caption("Why this result: " + " • ".join(reasons[:4]))

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

    # -------- List a Tool (SINGLE CLICK publish) --------
    with tab_list:
        st.subheader("List a tool or appliance")
        if not st.session_state.get("user"):
            st.warning("Please log in to list a tool.")
        else:
            # Build the form (unique key). We handle submission AFTER the form.
            with st.form(key="list_form_v3", clear_on_submit=True):
                name  = st.text_input("Tool name *", placeholder="e.g., Hammer Drill")
                desc  = st.text_area("Description", placeholder="Add details, condition, size, etc.")
                cat   = st.text_input("Category", placeholder="e.g., drill, ladder, saw…")
                price = st.number_input("Daily price (USD) *", min_value=1.0, step=1.0)
                loc   = st.text_input("Location (City or ZIP) *")
                afrom = st.date_input("Available from", value=None, key="afrom")
                ato   = st.date_input("Available to", value=None, key="ato")
                img   = st.file_uploader("Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
                submitted = st.form_submit_button("Publish listing", key="publish_btn_v3")

            # Handle submit here (no double fire). Guard prevents the "second click" issue.
            if submitted and not st.session_state.get("publish_guard", False):
                errors = []
                if not name: errors.append("Tool name")
                if not loc: errors.append("Location")
                try:
                    price_ok = float(price) >= 1.0
                except Exception:
                    price_ok = False
                if not price_ok: errors.append("Daily price (>= 1)")

                if errors:
                    st.error("Please fill: " + ", ".join(errors))
                else:
                    try:
                        img_bytes = img.read() if img else None
                        _id = add_tool(
                            st.session_state["user"]["id"], name, desc, cat, price, loc,
                            afrom or None, ato or None, img_bytes
                        )
                        st.success(f"Listed! Your tool ID is {_id}.")
                        # arm guard and clean rerender so the button doesn’t fire again
                        st.session_state["publish_guard"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't publish: {e}")

        st.markdown("### Your listings")
        if st.session_state.get("user"):
            my_tools = get_user_tools(st.session_state["user"]["id"])
            if not my_tools:
                st.info("You haven't listed anything yet.")
            else:
                for t in my_tools:
                    with st.container(border=True):
                        cols = st.columns([1, 3, 1])
                        with cols[0]:
                            if t["image_path"] and os.path.exists(t["image_path"]):
                                st.image(t["image_path"], use_container_width=True)
                            else:
                                st.write("🧰")
                        with cols[1]:
                            st.write(f"**{t['name']}** — ${t['daily_price']:.2f}/day")
                            st.caption((t["description"] or "")[:120])
                            st.write(f"Availability: {t['available_from'] or '—'} → {t['available_to'] or '—'}")
                        with cols[2]:
                            if st.button("Delete", key=f"del_{t['id']}"):
                                ok, msg = delete_tool(t["id"], st.session_state["user"]["id"])
                                (st.success if ok else st.error)(msg)
                                st.rerun()

    # -------- My Bookings --------
    with tab_book:
        st.subheader("Your bookings")
        if not st.session_state.get("user"):
            st.info("Log in to view bookings.")
        else:
            rows = get_user_bookings(st.session_state["user"]["id"])
            if not rows:
                st.info("No bookings yet.")
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

if __name__ == "__main__":
    main()