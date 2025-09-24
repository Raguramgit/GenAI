# meeting_with_genai_fixed_v3.py
"""
Hospital Appointment Scheduler — LangChain GenAI helpers integrated.
Edit: removed the GenAI (LangChain) status expander from the dashboard.
Preserves full original behavior and UI (except the removed expander).
"""

import os
import io
import json
import csv
import streamlit as st
from datetime import datetime, timedelta, date, time as dtime
import pytz
import calendar
from dateutil.parser import isoparse
from dotenv import load_dotenv

load_dotenv()

# Google API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# -------- LANGCHAIN / GenAI SETUP (safe import) ----------
ai_available = False
ai_import_error = None
llm_chain_create_desc = None
llm_chain_summarize = None
llm_chain_cancel_msg = None

try:
    from langchain import LLMChain, PromptTemplate
    from langchain.chat_models import ChatOpenAI

    desc_template = PromptTemplate(
        input_variables=["subject", "patient_name", "patient_age", "patient_gender", "symptoms", "duration", "date", "time", "phone"],
        template=(
            "You are a professional medical admin assistant. "
            "Create a concise, polite calendar event description for an appointment "
            "titled '{subject}' for patient {patient_name} (age {patient_age}, {patient_gender}). "
            "Symptoms / reason: {symptoms}. Duration: {duration} minutes. "
            "Appointment date/time: {date} at {time}. Contact phone: {phone}. "
            "Keep it short (2-4 sentences), professional and suitable for a calendar invite."
        )
    )

    summarize_template = PromptTemplate(
        input_variables=["notes"],
        template=(
            "You are a helpful assistant that summarizes clinical notes for quick review. "
            "Summarize the following notes into a 1-2 sentence summary suitable for a patient's profile: {notes}"
        )
    )

    cancel_template = PromptTemplate(
        input_variables=["subject", "patient_name", "date", "time", "reason"],
        template=(
            "Draft a short, professional cancellation message to be sent to appointment attendees. "
            "Appointment: '{subject}' for {patient_name} scheduled on {date} at {time}. "
            "Reason (optional): {reason}. Keep it polite and include next steps (ask to reschedule)."
        )
    )

    llm_model_name = os.getenv("LLM_MODEL_NAME", None)
    llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    if llm_model_name:
        llm = ChatOpenAI(model_name=llm_model_name, temperature=llm_temperature)
    else:
        llm = ChatOpenAI(temperature=llm_temperature)

    llm_chain_create_desc = LLMChain(llm=llm, prompt=desc_template)
    llm_chain_summarize = LLMChain(llm=llm, prompt=summarize_template)
    llm_chain_cancel_msg = LLMChain(llm=llm, prompt=cancel_template)

    ai_available = True
except Exception as e:
    ai_available = False
    ai_import_error = e

# -------- CONFIG ----------
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/spreadsheets"
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
TIMEZONE = "Asia/Kolkata"

PATIENTS_FILE = "patients.json"
PATIENTS_SHEET_ID = os.getenv("PATIENTS_SHEET_ID")
PATIENTS_SHEET_TAB = "patients"

HOSPITAL_DOCTOR_NAME = os.getenv("HOSPITAL_DOCTOR_NAME", "Dr. Anil Kumar")
HOSPITAL_PHONE = os.getenv("HOSPITAL_PHONE", "+91-9876543210")
HOSPITAL_ADDRESS = os.getenv("HOSPITAL_ADDRESS", "123 Health St., Wellness City")

EXCLUDE_DATE = None

PATIENT_FIELDS = [
    "email", "name", "phone", "age", "gender", "mrn",
    "allergies", "blood_group", "last_appointment", "notes"
]

# -------- Google auth & services ----------
def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Create OAuth client credentials in Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
    return creds

def get_calendar_service(creds):
    return build("calendar", "v3", credentials=creds)

def get_sheets_service(creds):
    return build("sheets", "v4", credentials=creds)

# -------- Sheet helpers ----------
def sheet_available(creds):
    return bool(PATIENTS_SHEET_ID and creds)

def ensure_sheet_tab(sheets_service):
    try:
        ss = sheets_service.spreadsheets()
        try:
            _ = ss.values().get(spreadsheetId=PATIENTS_SHEET_ID, range=f"{PATIENTS_SHEET_TAB}!A1:Z1").execute()
        except Exception:
            headers = PATIENT_FIELDS
            body = {"values": [headers]}
            try:
                ss.values().append(
                    spreadsheetId=PATIENTS_SHEET_ID,
                    range=f"{PATIENTS_SHEET_TAB}!A1",
                    valueInputOption="RAW",
                    body=body
                ).execute()
            except Exception:
                return False
        return True
    except Exception:
        return False

def load_patients_from_sheet(sheets_service):
    patients = {}
    try:
        ss = sheets_service.spreadsheets()
        resp = ss.values().get(
            spreadsheetId=PATIENTS_SHEET_ID,
            range=f"{PATIENTS_SHEET_TAB}!A2:Z10000"
        ).execute()
        rows = resp.get("values", [])
        for r in rows:
            r = r + [""] * (len(PATIENT_FIELDS) - len(r))
            rec = dict(zip(PATIENT_FIELDS, r[:len(PATIENT_FIELDS)]))
            if rec.get("email"):
                patients[rec["email"]] = rec
    except Exception:
        pass
    return patients

def append_or_update_patient_sheet(sheets_service, patient):
    try:
        ss = sheets_service.spreadsheets()
        resp = ss.values().get(
            spreadsheetId=PATIENTS_SHEET_ID,
            range=f"{PATIENTS_SHEET_TAB}!A1:Z10000"
        ).execute()
        rows = resp.get("values", [])
        data_rows = rows[1:] if len(rows) > 1 else []
        email_col = 0
        match_idx = None
        for i, r in enumerate(data_rows):
            if len(r) > email_col and r[email_col] == patient.get("email"):
                match_idx = i + 2
                break
        values = [patient.get(f, "") for f in PATIENT_FIELDS]
        if match_idx:
            range_addr = f"{PATIENTS_SHEET_TAB}!A{match_idx}:{chr(ord('A')+len(PATIENT_FIELDS)-1)}{match_idx}"
            body = {"values": [values]}
            ss.values().update(
                spreadsheetId=PATIENTS_SHEET_ID,
                range=range_addr,
                valueInputOption="RAW",
                body=body
            ).execute()
        else:
            body = {"values": [values]}
            ss.values().append(
                spreadsheetId=PATIENTS_SHEET_ID,
                range=f"{PATIENTS_SHEET_TAB}!A2",
                valueInputOption="RAW",
                body=body
            ).execute()
        return True
    except Exception:
        return False

# -------- Local JSON fallback helpers ----------
def load_patients_json():
    if not os.path.exists(PATIENTS_FILE):
        return {}
    try:
        with open(PATIENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def save_patients_json(d):
    try:
        with open(PATIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Failed to save local patients.json: {e}")

# -------- Unified upsert/load functions ----------
def upsert_patient_record_shared(creds, patient):
    if sheet_available(creds):
        try:
            sheets_service = get_sheets_service(creds)
            ok = ensure_sheet_tab(sheets_service)
            if ok and append_or_update_patient_sheet(sheets_service, patient):
                return True
        except Exception:
            pass
    patients = load_patients_json()
    patients[patient["email"]] = patient
    save_patients_json(patients)
    return True

def load_patients(creds=None):
    if sheet_available(creds):
        try:
            sheets_service = get_sheets_service(creds)
            ok = ensure_sheet_tab(sheets_service)
            if ok:
                patients = load_patients_from_sheet(sheets_service)
                if patients:
                    return patients
        except Exception:
            pass
    return load_patients_json()

# -------- Calendar helpers ----------
def iso_from_dt(dt: datetime, tzname=TIMEZONE):
    tz = pytz.timezone(tzname)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    return dt.astimezone(tz).isoformat()

def dt_from_iso(iso_str: str):
    return isoparse(iso_str)

def check_availability(service, start_dt: datetime, end_dt: datetime, exclude_event_id: str = None):
    tz = pytz.timezone(TIMEZONE)
    start_of_day = tz.localize(datetime.combine(start_dt.date(), dtime.min)) - timedelta(days=1)
    end_of_day = tz.localize(datetime.combine(end_dt.date(), dtime.max)) + timedelta(days=1)
    timeMin = start_of_day.astimezone(pytz.utc).isoformat()
    timeMax = end_of_day.astimezone(pytz.utc).isoformat()
    results = service.events().list(
        calendarId="primary",
        timeMin=timeMin,
        timeMax=timeMax,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    items = results.get("items", [])
    conflicts = []
    for ev in items:
        ev_id = ev.get("id")
        if exclude_event_id and ev_id == exclude_event_id:
            continue
        s = ev.get("start", {}).get("dateTime")
        e = ev.get("end", {}).get("dateTime")
        if not s or not e:
            continue
        ev_start = dt_from_iso(s)
        ev_end = dt_from_iso(e)
        if ev_start.tzinfo is None:
            ev_start = pytz.timezone(TIMEZONE).localize(ev_start)
        if ev_end.tzinfo is None:
            ev_end = pytz.timezone(TIMEZONE).localize(ev_end)
        if not (ev_end <= start_dt or ev_start >= end_dt):
            conflicts.append(ev)
    return conflicts

def create_calendar_event(service, subject, start_dt: datetime, duration_min: int, attendees_emails, description, timezone=TIMEZONE):
    end_dt = start_dt + timedelta(minutes=duration_min)
    conflicts = check_availability(service, start_dt, end_dt)
    if conflicts:
        return {"error": "conflict", "conflicts": conflicts, "requested_start": start_dt}
    event = {
        "summary": subject,
        "description": description,
        "start": {"dateTime": iso_from_dt(start_dt, timezone), "timeZone": timezone},
        "end": {"dateTime": iso_from_dt(end_dt, timezone), "timeZone": timezone},
        "attendees": [{"email": e.strip()} for e in attendees_emails],
        "reminders": {"useDefault": True},
    }
    created = service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
    return {"created": created}

def list_upcoming_events(service, max_results=200):
    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])
    filtered = []
    tz = pytz.timezone(TIMEZONE)
    for ev in events:
        s = ev.get('start', {}).get('dateTime')
        if not s:
            continue
        ev_start = dt_from_iso(s).astimezone(tz)
        if EXCLUDE_DATE and ev_start.date() == EXCLUDE_DATE:
            continue
        filtered.append(ev)
    return filtered

def get_events_for_patient(service, email, past=False, max_results=1000):
    tz = pytz.timezone(TIMEZONE)
    now = datetime.utcnow().isoformat() + "Z"
    if past:
        timeMin = "1970-01-01T00:00:00Z"
        timeMax = now
    else:
        timeMin = now
        timeMax = (datetime.utcnow() + timedelta(days=365*2)).isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary",
        timeMin=timeMin,
        timeMax=timeMax,
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results
    ).execute()
    items = events_result.get("items", [])
    result = []
    for ev in items:
        attendees = ev.get('attendees', [])
        emails = [a.get('email') for a in attendees]
        if email in emails:
            result.append(ev)
    return result

def update_event(service, event_id, new_start_dt: datetime=None, new_duration_min: int=None, new_subject: str=None, new_attendees: list=None, new_description: str=None, timezone=TIMEZONE):
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    if new_start_dt and new_duration_min:
        new_end_dt = new_start_dt + timedelta(minutes=new_duration_min)
        conflicts = check_availability(service, new_start_dt, new_end_dt, exclude_event_id=event_id)
        if conflicts:
            return {"error": "conflict", "conflicts": conflicts, "requested_start": new_start_dt}
        event["start"] = {"dateTime": iso_from_dt(new_start_dt, timezone), "timeZone": timezone}
        event["end"] = {"dateTime": iso_from_dt(new_end_dt, timezone), "timeZone": timezone}
    if new_subject:
        event["summary"] = new_subject
    if new_description is not None:
        event["description"] = new_description
    if new_attendees is not None:
        event["attendees"] = [{"email": e.strip()} for e in new_attendees]
    updated = service.events().update(calendarId="primary", eventId=event_id, body=event, sendUpdates="all").execute()
    return updated

def cancel_event(service, event_id):
    service.events().delete(calendarId="primary", eventId=event_id, sendUpdates="all").execute()
    return True

# -------- Time helpers ----------
def to_24_hour(hour12: int, minute: int, ampm: str) -> int:
    if ampm.upper() == 'AM':
        return 0 if hour12 == 12 else hour12
    else:
        return 12 if hour12 == 12 else hour12 + 12

def build_time_from_manual(hour12: int, minute: int, ampm: str):
    h24 = to_24_hour(hour12, minute, ampm)
    return dtime(hour=h24, minute=minute)

def split_time_to_manual(t: dtime):
    h = t.hour
    if h == 0:
        hour12 = 12
        ampm = 'AM'
    elif h < 12:
        hour12 = h
        ampm = 'AM'
    elif h == 12:
        hour12 = 12
        ampm = 'PM'
    else:
        hour12 = h - 12
        ampm = 'PM'
    return hour12, t.minute, ampm

# -------- GenAI helper wrappers ----------
def genai_create_description(subject, patient_name, patient_age, patient_gender, symptoms, duration, date_str, time_str, phone):
    if not ai_available or not llm_chain_create_desc:
        return ""
    try:
        out = llm_chain_create_desc.run({
            "subject": subject,
            "patient_name": patient_name or "Patient",
            "patient_age": patient_age or "",
            "patient_gender": patient_gender or "",
            "symptoms": symptoms or "General consultation",
            "duration": str(duration),
            "date": date_str,
            "time": time_str,
            "phone": phone or ""
        })
        return out.strip()
    except Exception as e:
        st.warning(f"GenAI description generation failed: {e}")
        return ""

def genai_summarize_notes(notes_text):
    if not ai_available or not llm_chain_summarize:
        return ""
    try:
        return llm_chain_summarize.run({"notes": notes_text}).strip()
    except Exception as e:
        st.warning(f"GenAI summary failed: {e}")
        return ""

def genai_cancel_message(subject, patient_name, date_str, time_str, reason):
    if not ai_available or not llm_chain_cancel_msg:
        return ""
    try:
        return llm_chain_cancel_msg.run({
            "subject": subject,
            "patient_name": patient_name or "Patient",
            "date": date_str,
            "time": time_str,
            "reason": reason or ""
        }).strip()
    except Exception as e:
        st.warning(f"GenAI cancel message generation failed: {e}")
        return ""

# -------- UI & App logic ----------
st.set_page_config(page_title="Hospital Appointment Scheduler", layout="wide")

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #f5f9ff; }
.title-strip { background: linear-gradient(90deg, #00bfff, #00e5ff); padding: 18px; border-radius: 8px; color: white; margin-bottom: 8px; }
.title-strip h1 { color: white !important; margin: 0; padding: 0; font-size: 28px; }
.subtitle-strip { background: #ffdf91; padding: 10px; border-radius: 6px; color: #000; margin-bottom: 14px; }
.subtitle-strip p { margin: 0; padding: 0; }
.login-card { background: linear-gradient(180deg, #ffffff, #f7fbff); border-radius: 10px; padding: 18px; text-align: center; box-shadow: 0 6px 18px rgba(0,0,0,0.06); transition: transform 0.12s; }
.login-card:hover { transform: translateY(-4px); }
.tile { background: linear-gradient(180deg,#ffffff,#f1f8ff); border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 6px 18px rgba(0,0,0,0.06); cursor: pointer; }
.small-card { background: #ffffff; border-radius: 6px; padding: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.contact-box { background: #fff8e6; border-radius: 8px; padding: 12px; border: 1px solid #f0d9a6; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="title-strip"><h1>🏥 Velan Multispecility Hospital </h1></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle-strip"><p>Appointment Scheduler — Schedule and Manage patient appointments.</p></div>',
    unsafe_allow_html=True,
)

# Session state defaults (include AI flags)
defaults = {
    'logged_in': False,
    'role': None,
    'user_email': None,
    'nav': None,
    'show_patient_login': False,
    'show_doctor_login': False,
    'selected_event_id': None,
    'confirm_delete_id': None,
    'edit_profile_email': None,
    'manage_selected_email': None,
    'use_ai_description': False,
    'use_ai_summarize': False,
    'use_ai_cancel': False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.markdown("### Login")
if not st.session_state['logged_in']:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### Patient")
        st.markdown("<p>To Book Appoinment with Doctor Signin Here .</p>", unsafe_allow_html=True)
        if st.button("Sign in (Patient)", key="open_patient_form"):
            st.session_state['show_patient_login'] = not st.session_state.get('show_patient_login', False)
        if st.session_state.get('show_patient_login', False):
            st.markdown("#### Patient Sign in")
            pat_email = st.text_input("Email", key="inline_pat_email")
            if st.button("Sign in as Patient", key="inline_pat_signin"):
                if pat_email:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'patient'
                    st.session_state['user_email'] = pat_email
                    st.success("Signed in as patient")
                    st.session_state['show_patient_login'] = False
                    st.rerun()
                else:
                    st.error("Please enter an email")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### Doctor")
        st.markdown("<p>View and Manage Patients Appointment.</p>", unsafe_allow_html=True)
        if st.button("Sign in (Doctor)", key="open_doctor_form"):
            st.session_state['show_doctor_login'] = not st.session_state.get('show_doctor_login', False)
        if st.session_state.get('show_doctor_login', False):
            st.markdown("#### Doctor Sign in")
            doc_email = st.text_input("Email", key="inline_doc_email")
            doc_pass = st.text_input("Password", type="password", key="inline_doc_pass")
            DOCTOR_PASSWORD = os.getenv('DOCTOR_PASSWORD', 'docpass')
            if st.button("Sign in as Doctor", key="inline_doc_signin"):
                if doc_email and doc_pass == DOCTOR_PASSWORD:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'doctor'
                    st.session_state['user_email'] = doc_email
                    st.success("Signed in as doctor")
                    st.session_state['show_doctor_login'] = False
                    st.rerun()
                else:
                    st.error("Invalid doctor credentials")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.success(f"Signed in as {st.session_state['role']} ({st.session_state['user_email']})")
    st.markdown("### Quick actions")
    if st.session_state['role'] == 'doctor':
        t1, t2, t3 = st.columns(3)
        with t1:
            if st.button("", key="doc_tile_create"):
                st.session_state['nav'] = 'create'
            st.markdown('<div class="tile"><h4>Create Appointment</h4><p>Quickly create a new appointment</p></div>', unsafe_allow_html=True)
        with t2:
            if st.button("", key="doc_tile_calendar"):
                st.session_state['nav'] = 'calendar'
            st.markdown('<div class="tile"><h4>View Calendar</h4><p>Open the monthly calendar</p></div>', unsafe_allow_html=True)
        with t3:
            if st.button("", key="doc_tile_manage"):
                st.session_state['nav'] = 'manage'
            st.markdown('<div class="tile"><h4>Manage Patients</h4><p>Patient list & records</p></div>', unsafe_allow_html=True)
    else:
        t1, t2, t3 = st.columns(3)
        with t1:
            if st.button("", key="pat_tile_book"):
                st.session_state['nav'] = 'create'
            st.markdown('<div class="tile"><h4>Book Appointment</h4><p>Schedule a new appointment</p></div>', unsafe_allow_html=True)
        with t2:
            if st.button("", key="pat_tile_my"):
                st.session_state['nav'] = 'my_appointments'
            st.markdown('<div class="tile"><h4>My Appointments</h4><p>View or cancel your bookings</p></div>', unsafe_allow_html=True)
        with t3:
            if st.button("", key="pat_tile_contact"):
                st.session_state['nav'] = 'contact'
            st.markdown('<div class="tile"><h4>Contact Clinic</h4><p>Contact details & instructions</p></div>', unsafe_allow_html=True)

    if st.button("Sign out", key="signout_after_login"):
        for key in [
            'logged_in', 'role', 'user_email', 'nav',
            'selected_event_id', 'confirm_delete_id',
            'edit_profile_email', 'manage_selected_email'
        ]:
            st.session_state[key] = None if key != 'logged_in' else False
        st.rerun()

if not st.session_state.get('logged_in'):
    st.stop()

# initialize google creds + services
try:
    creds = get_google_credentials()
    calendar_service = get_calendar_service(creds)
    sheets_service = None
    if PATIENTS_SHEET_ID:
        try:
            sheets_service = get_sheets_service(creds)
            ensure_sheet_tab(sheets_service)
        except Exception:
            sheets_service = None
except FileNotFoundError as fe:
    st.error(str(fe))
    st.stop()
except Exception as e:
    st.error("Failed to initialize Google services.")
    st.exception(e)
    st.stop()

# reload patients dict from storage
patients = load_patients(creds)

# Layout columns
left, right = st.columns((2, 1))

# Ensure these lists always exist before any conditional usage
todays_appointments = []
patient_events = []

with left:
    st.header("Create a new appointment")
    with st.form("create_form_main"):
        subject = st.text_input("Appointment subject", value="Consultation")
        # Patient fields
        patient_name = st.text_input("Patient name", placeholder="Full name (for patient records)")
        patient_phone = st.text_input("Patient phone", placeholder="+91xxxxxxxxxx")
        patient_age = st.number_input("Patient age", min_value=0, max_value=150, value=0)
        patient_gender = st.selectbox("Gender", options=["", "Male", "Female", "Other"])
        patient_mrn = st.text_input("Medical Record ID (MRN)", placeholder="Optional MRN")
        patient_allergies = st.text_input("Allergies (comma separated)", placeholder="e.g. Penicillin, Nuts")
        patient_blood_group = st.text_input("Blood group", placeholder="e.g. A+, O-")
        date_val = st.date_input("Appointment date")
        col_h, col_m, col_amp = st.columns((1, 1, 1))
        with col_h:
            hour12 = st.selectbox('Hour', options=list(range(1, 13)), index=9)
        with col_m:
            minute = st.selectbox('Minute', options=[0, 15, 30, 45], index=0)
        with col_amp:
            ampm = st.selectbox('AM/PM', options=['AM', 'PM'], index=0)
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=30)
        recipients = st.text_area("Recipients' email IDs (comma separated)", placeholder="patient@example.com")
        description = st.text_area(
            "Appointment description (reason for visit, location, instructions)",
            placeholder="Brief description that will appear in the calendar invite."
        )

        # ---- GenAI options (non-invasive) ----
        st.markdown("### Optional AI helpers")
        col_ai1, col_ai2, col_ai3 = st.columns(3)
        with col_ai1:
            st.checkbox("Auto-generate description (GenAI)", value=st.session_state.get('use_ai_description', False), key="use_ai_description")
        with col_ai2:
            st.checkbox("Auto-summarize notes (GenAI) on save", value=st.session_state.get('use_ai_summarize', False), key="use_ai_summarize")
        with col_ai3:
            st.checkbox("Allow AI to draft cancellation messages", value=st.session_state.get('use_ai_cancel', False), key="use_ai_cancel")

        create_btn = st.form_submit_button("Create appointment and notify attendees")

    if create_btn:
        if not subject:
            st.error("Please add a subject.")
        elif not recipients.strip():
            st.error("Please add at least one recipient email.")
        else:
            attendees_list = [e.strip() for e in recipients.split(",") if e.strip()]
            tz = pytz.timezone(TIMEZONE)
            time_obj = build_time_from_manual(hour12, minute, ampm)
            start_dt_naive = datetime.combine(date_val, time_obj)
            start_dt = tz.localize(start_dt_naive)
            description_text = description or ""

            # If AI description requested and available, generate one (keeps original if provided)
            if st.session_state.get('use_ai_description', False):
                if not ai_available:
                    st.warning("GenAI not available — cannot auto-generate description.")
                else:
                    date_str = date_val.strftime("%Y-%m-%d")
                    time_str = f"{hour12}:{str(minute).zfill(2)} {ampm}"
                    gen_desc = genai_create_description(
                        subject=subject,
                        patient_name=patient_name,
                        patient_age=str(patient_age),
                        patient_gender=patient_gender,
                        symptoms=description_text or "No additional notes provided",
                        duration=duration,
                        date_str=date_str,
                        time_str=time_str,
                        phone=patient_phone
                    )
                    if gen_desc:
                        description_text = gen_desc
                        st.info("GenAI generated description applied to the event.")

            try:
                result = create_calendar_event(
                    calendar_service, subject, start_dt, duration, attendees_list, description_text
                )
                if isinstance(result, dict) and result.get("error") == "conflict":
                    st.error("Selected time not available. Please select another time slot.")
                else:
                    created = result.get('created') if isinstance(result, dict) else result
                    st.success("✅ Appointment created and attendees notified via calendar updates.")
                    st.write("Event link:", created.get('htmlLink'))
                    now_iso = start_dt.astimezone(pytz.timezone(TIMEZONE)).isoformat()
                    for idx, email in enumerate(attendees_list):
                        patient_record = {
                            "email": email,
                            "name": patient_name if idx == 0 and patient_name else patients.get(email, {}).get("name", ""),
                            "phone": patient_phone if idx == 0 and patient_phone else patients.get(email, {}).get("phone", ""),
                            "age": str(patient_age) if idx == 0 and patient_age else patients.get(email, {}).get("age", ""),
                            "gender": patient_gender if idx == 0 and patient_gender else patients.get(email, {}).get("gender", ""),
                            "mrn": patient_mrn if idx == 0 and patient_mrn else patients.get(email, {}).get("mrn", ""),
                            "allergies": patient_allergies if idx == 0 and patient_allergies else patients.get(email, {}).get("allergies", ""),
                            "blood_group": patient_blood_group if idx == 0 and patient_blood_group else patients.get(email, {}).get("blood_group", ""),
                            "last_appointment": now_iso,
                            "notes": description_text or patients.get(email, {}).get("notes", "")
                        }

                        # Optionally run summarization on notes before saving (non-destructive)
                        if st.session_state.get('use_ai_summarize', False) and ai_available and patient_record.get("notes"):
                            summed = genai_summarize_notes(patient_record["notes"])
                            if summed:
                                patient_record["notes"] = summed + " (summary)"

                        upsert_patient_record_shared(creds, patient_record)
                    patients = load_patients(creds)
            except Exception as e:
                st.error("Failed to create appointment.")
                st.exception(e)

    st.markdown("---")

    # Manage Patients (Doctor) or My Appointments (Patient)
    if st.session_state.get('role') == 'doctor':
        st.header("Manage Patients & Events")
        if st.session_state.get('nav') == 'manage' or st.button("Open Manage Patients", key="open_manage_patients"):
            st.subheader("Manage Patients")
            patients = load_patients(creds)
            pat_list = list(patients.values())
            if not pat_list:
                st.info("No patient records yet.")
            else:
                q = st.text_input(
                    "Search patients by name, email, MRN, phone or allergies",
                    key="manage_search"
                )
                if q:
                    ql = q.lower()
                    pat_list = [
                        p for p in pat_list
                        if ql in (p.get('name', '') or '').lower()
                        or ql in (p.get('email', '') or '').lower()
                        or ql in (p.get('mrn', '') or '').lower()
                        or ql in (p.get('phone', '') or '').lower()
                        or ql in (p.get('allergies', '') or '').lower()
                    ]

                rows = []
                for p in pat_list:
                    rows.append({
                        "Email": p.get('email', ''), "Name": p.get('name', ''), "Phone": p.get('phone', ''),
                        "Age": p.get('age', ''), "Gender": p.get('gender', ''), "MRN": p.get('mrn', ''),
                        "Allergies": p.get('allergies', ''), "Blood group": p.get('blood_group', ''),
                        "Last appointment": p.get('last_appointment', '') or "", "Notes": p.get('notes', '')
                    })
                st.table(rows)

                # CSV export
                csv_buffer = io.StringIO()
                writer = csv.DictWriter(csv_buffer, fieldnames=[
                    "Email", "Name", "Phone", "Age", "Gender", "MRN",
                    "Allergies", "Blood group", "Last appointment", "Notes"
                ])
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
                csv_data = csv_buffer.getvalue()
                st.download_button("Download patient list (CSV)", data=csv_data, file_name="patients.csv", mime="text/csv")

                # Select patient to view/edit
                sel_email = st.selectbox(
                    "Select patient to view/edit profile",
                    options=[""] + [p.get('email') for p in pat_list],
                    key="manage_select"
                )

                if sel_email:
                    st.session_state['manage_selected_email'] = sel_email
                else:
                    st.session_state['manage_selected_email'] = None

                if st.session_state.get('manage_selected_email'):
                    sel_email = st.session_state.get('manage_selected_email')
                    rec = patients.get(sel_email, {})
                    st.markdown("### Patient Profile")
                    st.write(f"**Name:** {rec.get('name','')}")
                    st.write(f"**Email:** {rec.get('email','')}")
                    st.write(f"**Phone:** {rec.get('phone','')}")
                    st.write(f"**Age:** {rec.get('age','')}")
                    st.write(f"**Gender:** {rec.get('gender','')}")
                    st.write(f"**MRN:** {rec.get('mrn','')}")
                    st.write(f"**Allergies:** {rec.get('allergies','')}")
                    st.write(f"**Blood group:** {rec.get('blood_group','')}")
                    st.write(f"**Last appointment:** {rec.get('last_appointment','')}")
                    st.write("**Notes:**")
                    st.write(rec.get('notes',''))

                    st.markdown("---")
                    if st.session_state.get('role') == 'doctor':
                        if st.button("Edit Profile", key=f"edit_btn_{sel_email}"):
                            st.session_state['edit_profile_email'] = sel_email

                        if st.session_state.get('edit_profile_email') == sel_email:
                            with st.expander("Edit patient profile", expanded=True):
                                with st.form(f"edit_profile_form_{sel_email}"):
                                    edit_name = st.text_input("Name", value=rec.get('name',''), key=f"form_name_{sel_email}")
                                    edit_phone = st.text_input("Phone", value=rec.get('phone',''), key=f"form_phone_{sel_email}")
                                    edit_age = st.number_input("Age", min_value=0, max_value=150, value=int(rec.get('age') or 0), key=f"form_age_{sel_email}")
                                    edit_gender = st.selectbox(
                                        "Gender",
                                        options=["", "Male", "Female", "Other"],
                                        index=(["","Male","Female","Other"].index(rec.get('gender')) if rec.get('gender') in ["Male","Female","Other"] else 0),
                                        key=f"form_gender_{sel_email}"
                                    )
                                    edit_mrn = st.text_input("MRN", value=rec.get('mrn',''), key=f"form_mrn_{sel_email}")
                                    edit_allergies = st.text_input("Allergies (comma separated)", value=rec.get('allergies',''), key=f"form_allergies_{sel_email}")
                                    edit_blood = st.text_input("Blood group", value=rec.get('blood_group',''), key=f"form_blood_{sel_email}")
                                    edit_notes = st.text_area("Notes", value=rec.get('notes',''), key=f"form_notes_{sel_email}")
                                    save_profile = st.form_submit_button("Save patient profile", key=f"save_profile_{sel_email}")
                                    cancel_edit = st.form_submit_button("Cancel", key=f"cancel_edit_{sel_email}")
                                if save_profile:
                                    updated = {
                                        "email": sel_email,
                                        "name": edit_name,
                                        "phone": edit_phone,
                                        "age": str(edit_age),
                                        "gender": edit_gender,
                                        "mrn": edit_mrn,
                                        "allergies": edit_allergies,
                                        "blood_group": edit_blood,
                                        "last_appointment": rec.get('last_appointment',''),
                                        "notes": edit_notes
                                    }
                                    ok = upsert_patient_record_shared(creds, updated)
                                    if ok:
                                        st.success("Patient profile updated.")
                                        patients = load_patients(creds)
                                        st.session_state['edit_profile_email'] = None
                                        st.rerun()
                                    else:
                                        st.error("Failed to update patient profile.")
                                if cancel_edit:
                                    st.session_state['edit_profile_email'] = None
                                    st.rerun()
                    else:
                        st.info("Profile is read-only for your role.")

    # doctor selected event details
    if st.session_state.get('selected_event_id'):
        events = list_upcoming_events(calendar_service, max_results=500)
        sel_id = st.session_state['selected_event_id']
        selected_event = next((e for e in events if e.get('id') == sel_id), None)
        if selected_event:
            st.markdown('---')
            st.subheader('Selected event details')
            summary = selected_event.get('summary', '(no title)')
            start_iso = selected_event.get('start', {}).get('dateTime')
            end_iso = selected_event.get('end', {}).get('dateTime')
            description_text = selected_event.get('description', '')
            attendees = selected_event.get('attendees', [])
            attendee_emails = ", ".join([a.get('email') for a in attendees]) if attendees else ''
            st.markdown(f"**{summary}**")
            st.write(f"{start_iso} — {end_iso}")
            if attendee_emails:
                st.write(f"Attendees: {attendee_emails}")
            if description_text:
                st.write("Description:")
                st.write(description_text)
            st.markdown('---')
            cancel_reason = st.text_area('Cancel reason (optional)', placeholder='Reason for cancellation (shown in confirmation)', key=f'doc_cancel_reason_{sel_id}')

            if st.session_state.get('use_ai_cancel', False) and ai_available:
                try:
                    s_dt = dt_from_iso(start_iso).astimezone(pytz.timezone(TIMEZONE))
                    date_str = s_dt.strftime("%Y-%m-%d")
                    time_str = s_dt.strftime("%I:%M %p")
                except Exception:
                    date_str = ""
                    time_str = ""
                if st.button("Draft cancellation message (GenAI)", key=f"gen_cancel_{sel_id}"):
                    gen_msg = genai_cancel_message(summary, patient_name=selected_event.get('summary',''), date_str=date_str, time_str=time_str, reason=cancel_reason or "")
                    if gen_msg:
                        st.text_area("Generated cancellation message (edit as needed)", value=gen_msg, key=f"gen_cancel_msg_area_{sel_id}", height=150)

            if st.button('Confirm Delete (Doctor)', key=f'doc_confirm_delete_{sel_id}'):
                try:
                    cancel_event(calendar_service, sel_id)
                    if cancel_reason:
                        st.success(f"✅ Appointment cancelled and attendees were notified. Reason: {cancel_reason}")
                    else:
                        st.success('✅ Appointment cancelled and attendees were notified.')
                    st.session_state['selected_event_id'] = None
                    st.rerun()
                except Exception as e:
                    st.error('Failed to cancel appointment.')
                    st.exception(e)

    # Patient view: My Appointments
    else:
        st.header('My Appointments')
        events = list_upcoming_events(calendar_service, max_results=500)
        tz = pytz.timezone(TIMEZONE)
        user_email = st.session_state.get('user_email')
        today_local = datetime.now(tz).date()
        # Build patient_events and todays_appointments here (they were pre-defined above)
        todays_appointments = []
        patient_events = []
        for ev in events:
            attendees = ev.get('attendees', [])
            emails = [a.get('email') for a in attendees]
            if user_email in emails:
                s = ev.get('start', {}).get('dateTime')
                if not s:
                    continue
                ev_start = dt_from_iso(s).astimezone(tz)
                if EXCLUDE_DATE and ev_start.date() == EXCLUDE_DATE:
                    continue
                if ev_start.date() == today_local:
                    todays_appointments.append(ev)
                else:
                    patient_events.append(ev)

    # Now safe to reference todays_appointments and patient_events
    if todays_appointments:
        st.subheader("Today's appointments")
        for ev in todays_appointments:
            ev_id = ev.get('id')
            start = ev.get('start', {}).get('dateTime')
            end = ev.get('end', {}).get('dateTime')
            summary = ev.get('summary', '(no title)')
            st.markdown(f"**{summary}**")
            st.write(f"{start} — {end}")
            if st.button('Cancel', key=f'patient_cancel_today_{ev_id}'):
                st.session_state['confirm_delete_id'] = ev_id
    else:
        st.info("No appointments for today.")

    st.markdown('---')
    st.subheader('Upcoming appointments')
    if not patient_events:
        st.info('You have no upcoming appointments.')
    else:
        for ev in patient_events:
            ev_id = ev.get('id')
            start = ev.get('start', {}).get('dateTime')
            end = ev.get('end', {}).get('dateTime')
            summary = ev.get('summary', '(no title)')
            st.markdown(f"**{summary}**")
            st.write(f"{start} — {end}")
            if st.button('Cancel', key=f'patient_cancel_{ev_id}'):
                st.session_state['confirm_delete_id'] = ev_id

    if st.session_state.get('confirm_delete_id'):
        cid = st.session_state['confirm_delete_id']
        deleting_event = next((e for e in (todays_appointments + patient_events) if e.get('id') == cid), None)
        if deleting_event:
            st.markdown('---')
            st.warning('You are about to cancel this appointment. This will send cancellation emails to attendees.')
            cancel_reason = st.text_area(
                'Cancel reason (optional)',
                placeholder='Reason for cancellation (this will be shown in the confirmation)',
                key=f'cancel_reason_{cid}'
            )

            if st.session_state.get('use_ai_cancel', False) and ai_available:
                if st.button('Draft cancellation message (GenAI)', key=f'patient_gen_cancel_{cid}'):
                    try:
                        s_iso = deleting_event.get('start', {}).get('dateTime')
                        s_dt = dt_from_iso(s_iso).astimezone(pytz.timezone(TIMEZONE))
                        date_str = s_dt.strftime("%Y-%m-%d")
                        time_str = s_dt.strftime("%I:%M %p")
                        gen_msg = genai_cancel_message(deleting_event.get('summary',''), deleting_event.get('summary',''), date_str, time_str, cancel_reason or "")
                        if gen_msg:
                            st.text_area("Generated cancellation message (edit as needed)", value=gen_msg, key=f"patient_gen_cancel_msg_{cid}", height=150)
                    except Exception as e:
                        st.warning(f"Failed to craft GenAI cancellation message: {e}")

            if st.button('Confirm Cancel Appointment', key=f'confirm_cancel_patient_{cid}'):
                try:
                    cancel_event(calendar_service, cid)
                    if cancel_reason:
                        st.success(f"✅ Appointment cancelled. Reason: {cancel_reason}")
                    else:
                        st.success('✅ Appointment cancelled.')
                    st.session_state['confirm_delete_id'] = None
                    st.rerun()
                except Exception as e:
                    st.error('Failed to cancel appointment.')
                    st.exception(e)

# RIGHT side: Contact & calendar
with right:
    if st.session_state.get('nav') == 'contact' or st.button("Show Contact Clinic", key="right_show_contact"):
        st.markdown('<div class="contact-box">', unsafe_allow_html=True)
        st.markdown(f"**Contact Clinic**")
        st.write(f"Doctor: {HOSPITAL_DOCTOR_NAME}")
        st.write(f"Phone: {HOSPITAL_PHONE}")
        st.write(f"Address: {HOSPITAL_ADDRESS}")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get('role') == 'doctor':
        st.header("Monthly calendar (Doctor view)")
        today = datetime.now(pytz.timezone(TIMEZONE))
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Month", options=list(range(1, 13)), index=today.month - 1, format_func=lambda x: calendar.month_name[x])
        with col2:
            year = st.number_input("Year", min_value=1970, max_value=2100, value=today.year)
        days = {}
        try:
            tz = pytz.timezone(TIMEZONE)
            first_day = date(year, month, 1)
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = date(year, month, last_day_num)
            start_dt = tz.localize(datetime.combine(first_day, dtime.min))
            end_dt = tz.localize(datetime.combine(last_day, dtime.max))
            results = calendar_service.events().list(
                calendarId="primary",
                timeMin=start_dt.astimezone(pytz.utc).isoformat(),
                timeMax=end_dt.astimezone(pytz.utc).isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            items = results.get("items", [])
            for d in range(1, last_day_num + 1):
                days[d] = []
            for ev in items:
                s = ev.get("start", {}).get("dateTime")
                if not s:
                    continue
                ev_start = dt_from_iso(s).astimezone(tz)
                day = ev_start.day
                if EXCLUDE_DATE and ev_start.date() == EXCLUDE_DATE:
                    continue
                days.setdefault(day, []).append(ev)
        except Exception:
            st.error("Failed to load monthly events.")
        month_matrix = calendar.monthcalendar(year, month)
        st.markdown(f"### {calendar.month_name[month]} {year}")
        for week in month_matrix:
            cols = st.columns(7)
            for i, daynum in enumerate(week):
                with cols[i]:
                    if daynum == 0:
                        st.write("")
                    else:
                        evs = days.get(daynum, [])
                        count = len(evs)
                        box_html = f"<div class='small-card'><div style='font-weight:600;color:#0b3d91'>{daynum}</div><div style='font-size:12px;color:#555'>{count} events</div></div>"
                        st.markdown(box_html, unsafe_allow_html=True)
                        if st.button("View day", key=f"view_{year}_{month}_{daynum}"):
                            st.session_state['selected_day'] = date(year, month, daynum)
                            st.session_state['selected_event_id'] = None
        st.markdown("---")
        if st.session_state.get('selected_day'):
            sel_date = st.session_state['selected_day']
            st.subheader(f"Events on {sel_date.strftime('%A, %d %B %Y')}")
            evs = days.get(sel_date.day, []) if sel_date.month == month and sel_date.year == year else []
            if not evs:
                st.info("No events for selected date.")
            else:
                for ev in evs:
                    ev_id = ev.get('id')
                    summary = ev.get('summary', '(no title)')
                    start = ev.get('start', {}).get('dateTime')
                    end = ev.get('end', {}).get('dateTime')
                    st.markdown(f"**{summary}**")
                    st.write(f"{start} — {end}")
                    cols_ev = st.columns((1, 1, 1))
                    with cols_ev[0]:
                        if st.button("Details", key=f"details_{ev_id}"):
                            st.session_state['selected_event_id'] = ev_id
                            st.rerun()
                    with cols_ev[1]:
                        if st.button("Edit", key=f"edit_{ev_id}"):
                            st.session_state['selected_event_id'] = ev_id
                            st.rerun()
                    with cols_ev[2]:
                        if st.button("Cancel", key=f"cancel_{ev_id}"):
                            st.session_state['selected_event_id'] = ev_id
                            st.session_state[f'inline_cancel_{ev_id}'] = True
                for ev in evs:
                    ev_id = ev.get('id')
                    inline_flag = st.session_state.get(f'inline_cancel_{ev_id}', False)
                    if inline_flag:
                        st.markdown('---')
                        st.warning('You are about to cancel this event. This will send cancellation emails to attendees.')
                        cancel_reason = st.text_area('Cancel reason (optional)', placeholder='Reason for cancellation (shown in confirmation)', key=f'inline_cancel_reason_{ev_id}')
                        if st.session_state.get('use_ai_cancel', False) and ai_available:
                            if st.button('Draft inline cancellation message (GenAI)', key=f'inline_gen_cancel_{ev_id}'):
                                try:
                                    s_iso = ev.get('start', {}).get('dateTime')
                                    s_dt = dt_from_iso(s_iso).astimezone(pytz.timezone(TIMEZONE))
                                    date_str = s_dt.strftime("%Y-%m-%d")
                                    time_str = s_dt.strftime("%I:%M %p")
                                    gen_msg = genai_cancel_message(ev.get('summary',''), ev.get('summary',''), date_str, time_str, cancel_reason or "")
                                    if gen_msg:
                                        st.text_area("Generated cancellation message (edit as needed)", value=gen_msg, key=f"inline_gen_cancel_msg_{ev_id}", height=150)
                                except Exception as e:
                                    st.warning(f"Failed to craft GenAI cancellation message: {e}")
                        if st.button('Confirm Delete (inline)', key=f'inline_confirm_delete_{ev_id}'):
                            try:
                                cancel_event(calendar_service, ev_id)
                                st.session_state.pop(f'inline_cancel_{ev_id}', None)
                                st.session_state['selected_event_id'] = None
                                if cancel_reason:
                                    st.success(f"✅ Appointment cancelled and attendees were notified. Reason: {cancel_reason}")
                                else:
                                    st.success("✅ Appointment cancelled and attendees were notified.")
                                st.rerun()
                            except Exception as e:
                                st.error('Failed to cancel appointment.')
                                st.exception(e)
    else:
        if st.session_state.get('nav') == 'my_appointments' or st.button("Show My Appointments (compact)", key="right_show_my"):
            user_email = st.session_state.get('user_email')
            upcoming = list_upcoming_events(calendar_service, max_results=50)
            tz = pytz.timezone(TIMEZONE)
            user_upcoming = []
            for ev in upcoming:
                attendees = ev.get('attendees', [])
                emails = [a.get('email') for a in attendees]
                if user_email in emails:
                    s = ev.get('start', {}).get('dateTime')
                    if not s:
                        continue
                    ev_start = dt_from_iso(s).astimezone(tz)
                    user_upcoming.append((ev_start, ev))
            user_upcoming.sort(key=lambda x: x[0])
            st.markdown("### Next appointments")
            if not user_upcoming:
                st.info("No upcoming appointments.")
            else:
                for ev_start, ev in user_upcoming[:3]:
                    st.write(f"- {ev.get('summary','(no title)')} — {ev_start.strftime('%Y-%m-%d %I:%M %p')}")

st.markdown("---")
st.caption("Doctors can edit patient profiles (Edit Profile button opens an expander form below the details). Patients see read-only profile views.")
