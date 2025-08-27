# NearTools — full MVP with branding + persistent login + upgraded AI Helper (bundles)
# Put your logo file as "logo.png" in the same folder as this file.

import os, json, hashlib, sqlite3
from datetime import date, datetime
from typing import Optional, List, Tuple

import streamlit as st
import pandas as pd

# ---------- Optional AI libs ----------
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_OK = True
except Exception:
    SKLEARN_OK = False

APP_NAME = "NearTools"           # Title text only (no subtitle)
TAGLINE  = "Own less. Do more."  # Shown under the name

# ---------- Paths ----------
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "neartools.db")
IMAGES_DIR = "images"
REMEMBER_FILE = os.path.join(DB_DIR, "remember_me.json")  # persistent login

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------- Schema ----------
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
    FOREIGN KEY(tool_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewer_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

# ---------- DB helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    with conn:
        conn.executescript(SCHEMA_SQL)
    conn.close()

# ---------- Auth ----------
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
        return False, "Email already registered. Try logging in."
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

# ---------- Persistent login ("Keep me signed in") ----------
def remember_user(email: str):
    try:
        with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump({"email": email}, f)
    except Exception:
        pass

def read_remembered_user() -> Optional[str]:
    try:
        if os.path.exists(REMEMBER_FILE):
            with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("email")
    except Exception:
        return None
    return None

def forget_user():
    try:
        if os.path.exists(REMEMBER_FILE):
            os.remove(REMEMBER_FILE)
    except Exception:
        pass

# ---------- Tool & booking ops ----------
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
            INSERT INTO tools(owner_id, name, description, category, daily_price, location, available_from, available_to, image_path, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                owner_id, name.strip(), description.strip(), category.strip(), float(daily_price),
                location.strip(),
                available_from.isoformat() if available_from else None,
                available_to.isoformat() if available_to else None,
                image_path,
                datetime.utcnow().isoformat(),
            ),
        )
        tool_id = cur.lastrowid
    conn.close()
    return tool_id

def list_tools(keyword: str = "", category: str = "", location: str = "") -> List[sqlite3.Row]:
    kw = f"%{keyword.lower().strip()}%"
    cat = f"%{category.lower().strip()}%" if category else "%"
    loc = f"%{location.lower().strip()}%" if location else "%"
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT t.*, u.name AS owner_name, u.email AS owner_email
            FROM tools t JOIN users u ON u.id = t.owner_id
            WHERE lower(t.name) LIKE ? AND lower(IFNULL(t.category,'')) LIKE ? AND lower(t.location) LIKE ?
            ORDER BY t.created_at DESC
            """,
            (kw, cat, loc),
        )
        return cur.fetchall()
    finally:
        conn.close()

def tool_bookings(tool_id: int) -> List[Tuple[date, date]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT start_date, end_date FROM bookings WHERE tool_id=? AND status='confirmed'", (tool_id,)
        ).fetchall()
        return [(date.fromisoformat(r["start_date"]), date.fromisoformat(r["end_date"])) for r in rows]
    finally:
        conn.close()

def is_available(tool: sqlite3.Row, start: date, end: date) -> bool:
    if tool["available_from"]:
        if start < date.fromisoformat(tool["available_from"]):
            return False
    if tool["available_to"]:
        if end > date.fromisoformat(tool["available_to"]):
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

def add_review(tool_id: int, reviewer_id: int, rating: int, comment: str) -> None:
    conn = get_conn()
    with conn:
        conn.execute(
            "INSERT INTO reviews(tool_id, reviewer_id, rating, comment, created_at) VALUES(?,?,?,?,?)",
            (tool_id, reviewer_id, int(rating), comment.strip(), datetime.utcnow().isoformat()),
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

# ---------- AI suggestions (Upgraded: Task → Tool Bundles) ----------
TASK_TOOL_MAP = {
    "mount tv": {
        "triggers": ["mount tv", "tv mount", "tv on wall", "fix tv", "attach tv", "tv bracket"],
        "tools": {
            "hammer drill": ["hammer drill", "drill", "masonry"],
            "stud finder": ["stud finder"],
            "level": ["level"],
            "screwdriver / driver": ["screwdriver", "impact driver", "driver"]
        }
    },
    "paint room / ceiling": {
        "triggers": ["paint", "ceiling", "wall paint", "roller", "emulsion", "primer"],
        "tools": {
            "ladder": ["ladder"],
            "paint sprayer / roller": ["paint sprayer", "sprayer", "roller", "paint roller"],
            "drop cloth / tarp": ["drop cloth", "tarp"]
        }
    },
    "cut wood / build furniture": {
        "triggers": ["build table", "build shelf", "cut wood", "wood cutting", "carpentry", "2x4", "plywood"],
        "tools": {
            "circular saw / jigsaw": ["circular saw", "jigsaw", "saw"],
            "drill / driver": ["drill", "driver", "impact driver"],
            "sander": ["sander", "orbital sander"],
            "clamps": ["clamp", "clamps"]
        }
    },
    "pressure wash patio / driveway": {
        "triggers": ["pressure wash", "power wash", "clean driveway", "clean patio", "mildew"],
        "tools": {
            "pressure washer": ["pressure washer", "power washer"],
            "extension hose": ["hose", "extension hose"]
        }
    },
    "garden / hedge trimming": {
        "triggers": ["trim hedge", "hedges", "garden cleanup", "yard work", "prune"],
        "tools": {
            "hedge trimmer": ["hedge trimmer", "trimmer"],
            "ladder": ["ladder"]
        }
    },
    "sewing / costume / alterations": {
        "triggers": ["sew", "costume", "alterations", "hem", "fabric", "patch"],
        "tools": {
            "sewing machine": ["sewing machine", "sew machine"],
            "iron / steamer": ["iron", "steamer"]
        }
    },
}

FALLBACK_HINTS = {
    "drill": ["drill", "hammer drill", "masonry", "screw", "mount tv", "shelf", "hole"],
    "ladder": ["ladder", "roof", "gutter", "paint", "ceiling"],
    "saw": ["saw", "cut wood", "trim", "plywood", "deck", "table"],
    "sewing machine": ["sew", "stitch", "fabric", "hem", "costume"],
    "sander": ["sand", "refinish", "furniture"],
    "pressure washer": ["wash", "driveway", "patio", "pressure"],
}

def _find_matching_listings(all_tools: list, keywords: list[str]) -> list:
    out = []
    kw_lower = [k.lower() for k in keywords]
    for t in all_tools:
        hay = f"{t['name']} {(t['description'] or '')} {(t['category'] or '')}".lower()
        if any(k in hay for k in kw_lower):
            out.append(t)
    return out

def ai_bundle(task_text: str) -> tuple[Optional[str], dict]:
    tl = (task_text or "").lower()
    best_key, best_score = None, 0
    for key, spec in TASK_TOOL_MAP.items():
        score = sum(1 for trig in spec["triggers"] if trig in tl)
        if score > best_score:
            best_key, best_score = key, score
    if best_key and best_score > 0:
        return best_key, TASK_TOOL_MAP[best_key]["tools"]
    return None, {}

def ai_suggest_bundles(task_text: str, all_tools: list, requested_start: Optional[date], requested_end: Optional[date], location_filter: str):
    # Pre-filter pool by location + availability
    pool = list(all_tools)
    if location_filter:
        pool = [t for t in pool if location_filter.lower() in (t["location"] or "").lower()]
    if requested_start and requested_end:
        pool = [t for t in pool if is_available(t, requested_start, requested_end)]

    task_key, needed = ai_bundle(task_text)
    groups = []
    if needed:
        for label, kw in needed.items():
            matches = _find_matching_listings(pool, kw)
            groups.append({"label": label, "listings": matches})
        return task_key, groups

    # Fallback: score labels by keyword presence in task
    tl = (task_text or "").lower()
    scored = []
    for label, kw in FALLBACK_HINTS.items():
        score = sum(1 for w in kw if w in tl)
        if score > 0:
            matches = _find_matching_listings(pool, kw)
            scored.append((score, {"label": label, "listings": matches}))
    scored.sort(key=lambda x: x[0], reverse=True)
    return None, [g for _, g in scored[:5]]

# ---------- Branding ----------
PALETTE = {
    "green": "#2F6D3A",
    "leaf": "#8FBF65",
    "teal": "#23A094",
    "orange": "#F59E0B",
    "ink": "#1F2A1C",
    "card": "#F0F3EE",
    "bg": "#FAFAF7",
}

def inject_css():
    st.markdown(f"""
    <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background: {PALETTE["bg"]};
        }}
        .hero {{
            background: linear-gradient(90deg, {PALETTE["leaf"]}33 0%, {PALETTE["teal"]}33 50%, {PALETTE["orange"]}33 100%);
            border: 1px solid #e7eadf;
            border-radius: 24px;
            padding: 18px 22px;
            margin-bottom: 18px;
        }}
        .hero .title {{
            font-weight: 900;
            font-size: 2.1rem;
            margin: 0;
            color: {PALETTE["ink"]};
        }}
        .hero .tagline {{
            margin: 2px 0 0 0;
            font-size: 1.1rem;
            color: #556355;
        }}
        .stButton>button {{
            background: {PALETTE["green"]};
            color: white;
            border-radius: 10px;
            padding: 0.6rem 0.9rem;
            border: 0;
        }}
        .stButton>button:hover {{ background: {PALETTE["teal"]}; }}
        div[data-baseweb="tab-list"] > div[aria-selected="true"]::after {{ background: {PALETTE["green"]}; }}
        .stTextInput>div>div>input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
            background: white; border-radius: 10px; border: 1px solid #dfe4da;
        }}
    </style>
    """, unsafe_allow_html=True)

# ---------- UI helpers ----------
def reviews_summary(tool_id: int) -> str:
    df = get_tool_reviews(tool_id)
    if df.empty:
        return "No reviews yet."
    avg = float(df["rating"].mean())
    return f"⭐ {avg:.1f} from {len(df)} review(s)"

def tool_card(tool: sqlite3.Row):
    with st.container(border=True):
        cols = st.columns([1, 2, 2])
        with cols[0]:
            if tool["image_path"] and os.path.exists(tool["image_path"]):
                st.image(tool["image_path"], use_container_width=True)
            else:
                st.write("🧰")
        with cols[1]:
            st.subheader(tool["name"])
            st.write(f"**Category:** {tool['category'] or '—'}  \n**Location:** {tool['location']}")
            st.write(tool["description"] or "No description.")
            st.write(f"**Daily price:** ${tool['daily_price']:.2f}")
            st.caption(reviews_summary(tool["id"]))
        with cols[2]:
            st.write(f"**Owner:** {tool['owner_name']}  \n**Email:** {tool['owner_email']}")

# ---------- App ----------
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🧰", layout="wide")
    init_db()
    inject_css()

    # STICKY LOGIN (session + disk). Do NOT overwrite on rerun.
    st.session_state.setdefault("user", None)

    # Auto-restore from disk (keeps login after refresh/restart)
    if st.session_state["user"] is None:
        remembered = read_remembered_user()
        if remembered:
            row = get_user_by_email(remembered)
            if row:
                st.session_state["user"] = dict(row)

    # Big landing hero with large logo + only tagline
    logo_col, text_col = st.columns([1, 5], vertical_alignment="center")
    with logo_col:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.write("🧰")
    with text_col:
        st.markdown(
            f"""
            <div class="hero">
                <div class="title">{APP_NAME}</div>
                <div class="tagline">{TAGLINE}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Sidebar (logo, tagline, auth)
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        st.markdown("### Own less. Do more.")
        st.header("Account")

        if st.session_state.get("user"):
            st.success(f"Logged in as {st.session_state['user']['name']}")
            if st.button("Log out"):
                st.session_state["user"] = None
                forget_user()
                st.rerun()
        else:
            login_tab, signup_tab = st.tabs(["Log in", "Sign up"])
            with login_tab:
                l_email = st.text_input("Email", key="login_email")
                l_pw = st.text_input("Password", type="password", key="login_pw")
                keep = st.checkbox("Keep me signed in", value=True)
                if st.button("Log in"):
                    u = verify_user(l_email, l_pw)
                    if u:
                        st.session_state["user"] = dict(u)
                        if keep:
                            remember_user(l_email)
                        st.success("Logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            with signup_tab:
                s_name = st.text_input("Full name")
                s_email = st.text_input("Email")
                s_loc = st.text_input("Location (City or ZIP)")
                s_pw1 = st.text_input("Password", type="password", key="pw1")
                s_pw2 = st.text_input("Confirm password", type="password", key="pw2")
                if st.button("Create account"):
                    if not (s_name and s_email and s_pw1 and s_pw2):
                        st.error("Please fill all fields.")
                    elif s_pw1 != s_pw2:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = create_user(s_name, s_email, s_pw1, s_loc)
                        (st.success if ok else st.error)(msg)

        st.divider()
        if st.button("🗑 Reset local database"):
            try:
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                forget_user()
                init_db()
                st.success("Database reset. Reload the page.")
            except Exception as e:
                st.error(f"Could not reset DB: {e}")

        # Main tabs (Browse, List, Bookings)
    tabs = st.tabs(["Browse", "List a Tool", "My Bookings"])

    # -------- Browse --------
    with tabs[0]:
        st.subheader("Find tools near you")
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        with c1:
            keyword = st.text_input("Keyword (e.g., drill, sander)")
        with c2:
            category = st.selectbox(
                "Category (optional)",
                ["", "drill", "ladder", "saw", "sewing machine", "sander", "pressure washer"],
            )
        with c3:
            location = st.text_input("Location filter (optional)")
        with c4:
            st.caption("Select dates (optional) then scroll down to book")
            d1 = st.date_input("Start date", value=None, key="browse_start")
            d2 = st.date_input("End date", value=None, key="browse_end")

        tools = list_tools(keyword, category, location)
        if not tools:
            st.info("No tools found. Try clearing filters or list your first tool.")
        else:
            for t in tools:
                tool_card(t)

                can_check = (d1 is not None) and (d2 is not None)
                if can_check:
                    ok = is_available(t, d1, d2)
                    st.write("Availability:", "✅ Available for selected dates" if ok else "❌ Not available for selected dates")

                if st.session_state.get("user") and can_check:
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

    # -------- List a Tool --------
    with tabs[1]:
        st.subheader("List a tool or appliance")
        if not st.session_state.get("user"):
            st.warning("Please log in to list a tool.")
        else:
            with st.form("list_tool_form", clear_on_submit=True):
                name = st.text_input("Tool name *", placeholder="e.g., Hammer Drill")
                desc = st.text_area("Description", placeholder="Add details, condition, size, etc.")
                cat = st.text_input("Category", placeholder="e.g., drill, ladder, saw…")
                price = st.number_input("Daily price (USD) *", min_value=1.0, step=1.0)
                loc = st.text_input("Location (City or ZIP) *")
                afrom = st.date_input("Available from", value=None, key="afrom")
                ato = st.date_input("Available to", value=None, key="ato")
                img = st.file_uploader("Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])

                submitted = st.form_submit_button("Publish listing")
                if submitted:
                    if not (name and price and loc):
                        st.error("Name, price, and location are required.")
                    else:
                        img_bytes = img.read() if img else None
                        _id = add_tool(
                            st.session_state["user"]["id"],
                            name,
                            desc,
                            cat,
                            price,
                            loc,
                            afrom or None,
                            ato or None,
                            img_bytes,
                        )
                        st.success(f"Listed! Your tool ID is { _id }.")

    # -------- My Bookings --------
    with tabs[2]:
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
                            f"**{b['tool_name']}** — {b['start_date']} → {b['end_date']}  •  ${b['total_cost']:.2f}"
                        )
                        if b["image_path"] and os.path.exists(b["image_path"]):
                            st.image(b["image_path"], width=160)

                        try:
                            ended = date.fromisoformat(b["end_date"]) <= date.today()
                        except Exception:
                            ended = True

                        if ended:
                            with st.expander("Leave a review"):
                                rating = st.slider("Rating", 1, 5, 5, key=f"rv_{b['id']}")
                                comment = st.text_area("Comment", key=f"rvc_{b['id']}")
                                if st.button("Submit review", key=f"rvb_{b['id']}"):
                                    add_review(b["tool_id"], st.session_state["user"]["id"], rating, comment)
                                    st.success("Thanks! Review added.")

if __name__ == "__main__":
    main()

