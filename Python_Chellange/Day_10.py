# event_registration_system.py
import streamlit as st
import pandas as pd
from datetime import datetime
import re
import uuid
from typing import Dict, List

# ---------------------------
# Event Registration System (In-memory, Light Theme Only)
# ---------------------------
st.set_page_config(
    page_title="Event Registration System 🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# Session-state storage
# ---------------------------
def init_session_state():
    if "registrations" not in st.session_state:
        st.session_state.registrations = []
    # inputs stored in session so widgets persist between reruns
    if "input_name" not in st.session_state:
        st.session_state.input_name = ""
    if "input_email" not in st.session_state:
        st.session_state.input_email = ""
    if "input_phone" not in st.session_state:
        st.session_state.input_phone = ""
    if "input_org" not in st.session_state:
        st.session_state.input_org = ""
    if "input_event_choice" not in st.session_state:
        st.session_state.input_event_choice = "AWS Community Builder"
    if "input_attendance" not in st.session_state:
        st.session_state.input_attendance = "In-person"
    if "input_notes" not in st.session_state:
        st.session_state.input_notes = ""
    # dietary selection stored separately
    if "input_dietary" not in st.session_state:
        st.session_state.input_dietary = None
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False

# ---------------------------
# Helpers
# ---------------------------
def html_escape(s) -> str:
    """Simple HTML escape to avoid user-supplied HTML rendering."""
    if s is None:
        return ""
    s = str(s)
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )

# ---------------------------
# Validation
# ---------------------------
def is_valid_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    cleaned = re.sub(r"[^0-9]", "", phone)
    return 7 <= len(cleaned) <= 15

# ---------------------------
# In-memory operations
# ---------------------------
def create_registration(registration_data: Dict) -> bool:
    registration_data["id"] = str(uuid.uuid4())
    registration_data["timestamp"] = datetime.now()
    st.session_state.registrations.insert(0, registration_data)
    return True

def get_registrations() -> List[Dict]:
    return st.session_state.registrations

def get_recent_registrations(limit: int = 9) -> List[Dict]:
    return st.session_state.registrations[:limit]

def clear_all_registrations() -> bool:
    st.session_state.registrations = []
    return True

def export_to_csv(registrations: List[Dict]) -> str:
    if not registrations:
        return ""
    df = pd.DataFrame(registrations)
    cols = ["name", "email", "phone", "organization", "event_choice",
            "attendance", "dietary", "notes", "timestamp"]
    df = df[[c for c in cols if c in df.columns]]
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.to_csv(index=False)

# ---------------------------
# Styles (Light Theme Only)
# ---------------------------
def apply_styles():
    st.markdown(
        """
        <style>
        .stApp { background-color: #ffffff; color: #0b1220; }
        h1, h2, h3 { color: #1565c0 !important; }
        .metric-card {
            background: #f7fbff;
            border: 1px solid #1565c0;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .registration-card {
            background: #f7fbff;
            border-radius: 8px;
            padding: 0.75rem;
            margin: 0.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .stButton > button {
            background-color: #1CA9C9 !important; /* Peacock blue */
            color: white !important;
            border-radius: 8px;
        }
        .badge {
            display:inline-block;
            padding:2px 8px;
            border-radius:12px;
            font-size:0.8em;
            margin-left:6px;
        }
        .badge-dietary { background:#fff3e0; color:#bf360c; border:1px solid #ffd8b1; }
        .badge-attendance { background:#e3f2fd; color:#0b59a6; border:1px solid #cfe8ff; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# UI Components
# ---------------------------
def render_registration_form():
    st.markdown("### 📝 Registration Form (reactive)")
    # two-column layout for inputs
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.input_name = st.text_input("Full Name *", value=st.session_state.input_name, key="input_name_widget")
        st.session_state.input_email = st.text_input("Email Address *", value=st.session_state.input_email, key="input_email_widget")
        st.session_state.input_phone = st.text_input("Phone (Optional)", value=st.session_state.input_phone, key="input_phone_widget")
        st.session_state.input_org = st.text_input("Organization / Company (Optional)", value=st.session_state.input_org, key="input_org_widget")
    with col2:
        st.session_state.input_event_choice = st.selectbox(
            "Event Choice *",
            ["AWS Community Builder", "GenAI", "Machine Learning", "Hackathon", "Networking"],
            index=0,
            key="input_event_choice_widget"
        )
        # attendance is reactive — selecting "In-person" will show the expander
        st.session_state.input_attendance = st.radio(
            "Attendance Type *",
            ["In-person", "Virtual"],
            index=0 if st.session_state.input_attendance == "In-person" else 1,
            key="input_attendance_widget"
        )

        # show dietary expander only when In-person is selected
        if st.session_state.input_attendance == "In-person":
            # show expander expanded by default so it's visible immediately
            with st.expander("🍽️ Dietary Preference", expanded=True):
                st.session_state.input_dietary = st.radio(
                    "Choose:",
                    ["Veg", "Non-Veg"],
                    index=0 if st.session_state.input_dietary == "Veg" else 1 if st.session_state.input_dietary == "Non-Veg" else 0,
                    key="input_dietary_widget"
                )
        else:
            # clear dietary if Virtual is chosen
            st.session_state.input_dietary = None

    # notes and register button (reactive)
    st.session_state.input_notes = st.text_area("Additional Notes (Optional)", value=st.session_state.input_notes, max_chars=500, key="input_notes_widget")

    # Register action
    if st.button("🎉 Register Now", use_container_width=True):
        # validate
        errors = []
        name = st.session_state.input_name.strip()
        email = st.session_state.input_email.strip()
        phone = st.session_state.input_phone.strip()
        event_choice = st.session_state.input_event_choice
        attendance = st.session_state.input_attendance
        dietary = st.session_state.input_dietary
        notes = st.session_state.input_notes.strip()

        if not name:
            errors.append("Please enter your name.")
        if not is_valid_email(email):
            errors.append("Please provide a valid email address.")
        if phone and not is_valid_phone(phone):
            errors.append("Please provide a valid phone number (7-15 digits).")
        if not event_choice:
            errors.append("Please select an event.")
        # If in-person but dietary isn't set, prompt user
        if attendance == "In-person" and not dietary:
            errors.append("Please choose a dietary preference (Veg / Non-Veg).")

        if errors:
            for e in errors:
                st.error(e)
        else:
            reg = {
                "name": name,
                "email": email,
                "phone": phone or None,
                "organization": st.session_state.input_org.strip() or None,
                "event_choice": event_choice,
                "attendance": attendance,
                "dietary": dietary if attendance == "In-person" else None,
                "notes": notes or None
            }
            if create_registration(reg):
                st.success("✅ Registration successful!")
                st.balloons()
                # reset fields after successful registration (preserve event choice)
                st.session_state.input_name = ""
                st.session_state.input_email = ""
                st.session_state.input_phone = ""
                st.session_state.input_org = ""
                st.session_state.input_notes = ""
                st.session_state.input_dietary = None
                st.rerun()

def render_statistics():
    regs = get_registrations()
    st.markdown("### 📊 Registration Statistics")
    if not regs:
        st.info("No registrations yet.")
        return
    total = len(regs)
    in_person = sum(1 for r in regs if r["attendance"] == "In-person")
    virtual = total - in_person
    event_counts = {}
    for r in regs:
        event_counts[r["event_choice"]] = event_counts.get(r["event_choice"], 0) + 1
    most_popular = max(event_counts.items(), key=lambda x: x[1]) if event_counts else None
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='metric-card'><h2>{total}</h2><p>Total</p></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'><h3>{in_person}</h3><p>In-person</p></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'><h3>{virtual}</h3><p>Virtual</p></div>", unsafe_allow_html=True)
    if most_popular:
        col4.markdown(f"<div class='metric-card'><h4>{html_escape(most_popular[0])}</h4><p>Most Popular ({most_popular[1]})</p></div>", unsafe_allow_html=True)

def render_recent_registrations():
    st.markdown("### 🕒 Recent Registrations")
    regs = get_recent_registrations(9)
    if not regs:
        st.info("No registrations yet.")
        return

    cols = st.columns(3)
    for i, r in enumerate(regs):
        col = cols[i % 3]

        # timestamp -> human readable
        ts = r.get("timestamp", datetime.now())
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except Exception:
                ts = datetime.now()
        ago = datetime.now() - ts
        if ago.days:
            time_str = f"{ago.days}d ago"
        elif ago.seconds > 3600:
            time_str = f"{ago.seconds // 3600}h ago"
        elif ago.seconds > 60:
            time_str = f"{ago.seconds // 60}m ago"
        else:
            time_str = "Just now"

        # attendance -> border color
        attendance_raw = r.get("attendance") or ""
        attendance = str(attendance_raw).lower()
        if "in" in attendance:
            border_color = "#2e7d32"  # green
        else:
            border_color = "#1565c0"  # blue

        # badges (always strings, escaped)
        dietary_val = r.get("dietary")
        dietary_badge_html = (
            '<span class="badge badge-dietary">' + html_escape(dietary_val) + "</span>"
            if dietary_val
            else ""
        )
        attendance_badge_html = (
            '<span class="badge badge-attendance">' + html_escape(r.get("attendance", "-")) + "</span>"
        )

        # optional organization line (escaped)
        org_val = r.get("organization")
        org_html = "<small>🏢 " + html_escape(org_val) + "</small><br>" if org_val else ""

        # event choice safe string
        event_choice_str = html_escape(r.get("event_choice", "-"))
        name_str = html_escape(r.get("name", "-"))
        email_str = html_escape(r.get("email", "-"))

        # assemble HTML safely using concatenation
        card_html = (
            '<div class="registration-card" style="border-left: 6px solid '
            + border_color
            + ';">'
            + '<div style="display:flex; justify-content:space-between; align-items:flex-start;">'
            + '<div>'
            + "<strong>"
            + name_str
            + "</strong><br>"
            + "<small>📧 "
            + email_str
            + "</small><br>"
            + org_html
            + '<div style="margin-top:6px;">'
            + '<span style="background:#e3f2fd; padding:2px 6px; border-radius:4px; margin-right:6px; font-size:0.85em;">'
            + event_choice_str
            + "</span>"
            + attendance_badge_html
            + dietary_badge_html
            + "</div>"  # close badges container
            + "</div>"  # close left column
            + '<div style="text-align:right; color:#666;">'
            + "<small>"
            + time_str
            + "</small>"
            + "</div>"  # close right column
            + "</div>"  # close flex container
            + "</div>"  # close card
        )

        try:
            col.markdown(card_html, unsafe_allow_html=True)
        except Exception as e:
            col.error("Failed to render card.")
            col.write({"name": r.get("name"), "email": r.get("email"), "error": str(e)})

def render_organizer_controls():
    st.markdown("## 🔧 Organizer Controls")
    regs = get_registrations()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📥 Export CSV", use_container_width=True):
            if regs:
                st.download_button("⬇️ Download CSV File", export_to_csv(regs),
                                   f"registrations_{datetime.now().strftime('%Y-%m-%d')}.csv",
                                   "text/csv", use_container_width=True)
            else:
                st.warning("No data to export.")
    with col2:
        if st.button("💾 Save to Server", use_container_width=True):
            if regs:
                st.success(f"✅ Saved {len(regs)} regs to server (simulated).")
            else:
                st.warning("No data to save.")
    with col3:
        if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
            if regs:
                if st.session_state.confirm_clear:
                    clear_all_registrations()
                    st.success("✅ All cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("⚠️ Click again to confirm clear.")
            else:
                st.info("No data to clear.")

def render_data_table():
    st.markdown("### 📋 All Registrations")
    regs = get_registrations()
    if not regs:
        st.info("No registrations yet.")
        return
    df = pd.DataFrame(regs)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------
# Main App
# ---------------------------
def main():
    init_session_state()
    st.markdown("# 🎉 Event Registration System")
    st.markdown("**Register for events — organizers can view, export, and manage registrations**")
    apply_styles()

    with st.sidebar:
        st.markdown("### 📍 Navigation")
        page = st.radio("Go to:",
            ["🏠 Registration & Overview", "📊 Statistics & Recent", "🔧 Organizer Controls", "📋 All Data"])

    if page == "🏠 Registration & Overview":
        c1, c2 = st.columns([2, 1])
        with c1:
            render_registration_form()
            st.markdown("---")
            render_recent_registrations()
        with c2:
            render_statistics()
    elif page == "📊 Statistics & Recent":
        render_statistics()
        st.markdown("---")
        render_recent_registrations()
    elif page == "🔧 Organizer Controls":
        render_organizer_controls()
    elif page == "📋 All Data":
        render_data_table()

    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit — happy event planning! 🎉")

if __name__ == "__main__":
    main()
