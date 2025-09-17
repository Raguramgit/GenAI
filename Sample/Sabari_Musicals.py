# Sabari Musicals – Customer Service & Sales Assistant
# Streamlit one-file app
# Features:
# - Studio appointment scheduling (create/reschedule/cancel) with working-hours validation
# - Instrument catalog (buy/sell), cart & basic checkout
# - Repair cost estimator & intake form
# - Purchase Order (PO) creation & validation with downloadable JSON
# - Delivery request flow with address validation
# - Simple FAQs and contact info
# - Creative, dynamic UI (badges, cards, progress, toasts)

import json
from datetime import datetime, date, time, timedelta
from typing import List, Dict

import pandas as pd
import streamlit as st

# ---------------------------
# Page Setup & Styling
# ---------------------------
st.set_page_config(
    page_title="Sabari Musicals",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="auto",
)

# Simple brand palette
PRIMARY = "#6C63FF"
ACCENT = "#00C2A8"
DANGER = "#E54F6D"
MUTED = "#8C8FA1"
BG_SOFT = "#0f1117"  # plays nice with dark mode; Streamlit auto-inverts OK

custom_css = f"""
<style>
/****** Global tweaks ******/
.reportview-container .main .block-container{{
  padding-top: 1.5rem; padding-bottom: 1.5rem; max-width: 1250px;
}}
:root {{
  --brand: {PRIMARY};
  --accent: {ACCENT};
  --danger: {DANGER};
  --muted: {MUTED};
}}
.badge {{
  display:inline-block; padding:.25rem .6rem; border-radius:999px;
  font-size:.75rem; background:var(--brand); color:white; margin-left:.5rem;
}}
.card {{
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; padding: 1rem; box-shadow: 0 4px 18px rgba(0,0,0,.12);
}}
.highlight {{ color: var(--accent); }}
.small {{ color: var(--muted); font-size:.85rem; }}
hr.soft {{ border:0; border-top:1px solid rgba(255,255,255,.08); margin: .75rem 0 1rem; }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------------------------
# Constants & Data
# ---------------------------
WORKING_HOURS = {
    "Mon": (time(8, 30), time(21, 30)),
    "Tue": (time(8, 30), time(21, 30)),
    "Wed": (time(8, 30), time(21, 30)),
    "Thu": (time(8, 30), time(21, 30)),
    "Fri": (time(8, 30), time(21, 30)),
    "Sat": (time(10, 0), time(18, 0)),
    "Sun": None,  # Holiday
}

SERVICES = [
    "Buy & sell musical instruments",
    "Buy & sell recording studio equipment",
    "Low-cost repair for faulty instruments",
    "Home & office audio/video setup",
    "DJ gears & accessories",
]

CATALOG = [
    {"SKU": "FLT-STD-01", "Item": "Flute (Student)", "Brand": "Saras", "Price": 2000, "Stock": 12},
    {"SKU": "FLT-PRO-02", "Item": "Flute (Professional)", "Brand": "Yamaha", "Price": 10000, "Stock": 4},
    {"SKU": "GTR-AC-01", "Item": "Acoustic Guitar", "Brand": "Fender", "Price": 12000, "Stock": 7},
    {"SKU": "KB-61-01", "Item": "Keyboard 61-keys", "Brand": "Casio", "Price": 8500, "Stock": 9},
    {"SKU": "MIC-CND-01", "Item": "Condenser Microphone", "Brand": "AKG", "Price": 9500, "Stock": 6},
    {"SKU": "PA-JBL-16", "Item": "JBL + Behringer HA400 Bundle", "Brand": "JBL/Behringer", "Price": 28999, "Stock": 3},
    {"SKU": "BOSE-L1-16", "Item": "Bose L1 Pro16 PA System", "Brand": "Bose", "Price": 129000, "Stock": 2},
]

REPAIR_BASE = {
    "Guitar": 600,  # inspection + setup
    "Keyboard": 500,
    "Flute": 400,
    "Microphone": 450,
}
REPAIR_PARTS = {
    "String set": 350,
    "Bridge/Saddle": 700,
    "Key contact strip": 1200,
    "Pads (pair)": 500,
    "XLR socket": 250,
}

# ---------------------------
# Helpers
# ---------------------------
@st.cache_data
def df_catalog() -> pd.DataFrame:
    return pd.DataFrame(CATALOG)


def weekday_name(d: date) -> str:
    return d.strftime("%a")  # Mon, Tue, ...


def in_working_hours(d: date) -> bool:
    wh = WORKING_HOURS.get(weekday_name(d))
    return wh is not None


def build_time_slots(d: date, step_min: int = 60) -> List[str]:
    """Return list of time slot labels within working hours for the date d.
    If closed, returns []."""
    wd = weekday_name(d)
    hours = WORKING_HOURS.get(wd)
    if hours is None:
        return []
    start, end = hours
    slots = []
    t = datetime.combine(d, start)
    end_dt = datetime.combine(d, end)
    while t <= end_dt - timedelta(minutes=step_min):
        slots.append(t.strftime("%I:%M %p"))
        t += timedelta(minutes=step_min)
    return slots


def toast_success(msg: str):
    st.toast(msg)


# ---------------------------
# Session State
# ---------------------------
if "cart" not in st.session_state:
    st.session_state.cart: Dict[str, int] = {}
if "appointments" not in st.session_state:
    st.session_state.appointments: Dict[str, Dict] = {}
if "purchase_orders" not in st.session_state:
    st.session_state.purchase_orders: List[Dict] = []
if "deliveries" not in st.session_state:
    st.session_state.deliveries: List[Dict] = []

# ---------------------------
# Header
# ---------------------------
left, mid, right = st.columns([3,2,3])
with left:
    st.markdown("# 🎵 Sabari Musicals Pvt Ltd <span class='badge'>  30+ years of Experiance in Musical Industry</span>", unsafe_allow_html=True)
with mid:
    st.markdown("<div class='large'>Mon–Fri 8:30AM–9:30PM · Sat 10AM–6PM · Sun Holiday</div>", unsafe_allow_html=True)
with right:
    st.metric("Customer Satisfaction", "4.9/5", "+107 reviews")

st.markdown("---")

# ---------------------------
# Sidebar – Quick Actions
# ---------------------------
st.sidebar.header("Quick Actions")
qa = st.sidebar.radio(
    "What would you like to do?",
    [
        "Buy/Sell",
        "Studio Booking",
        "Repairs",
        "Purchase Orders",
        "Delivery",
        "FAQs",
    ],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.markdown("#### Contact Us")
st.sidebar.markdown("#### Visit us: 123 Music Lane, Melody City, 56789")
st.sidebar.markdown("📞 +91 98765 43210")
st.sidebar.markdown("✉️SM@musicland.com")
# ---------------------------
# BUY / SELL
# ---------------------------
if qa == "Buy/Sell":
    st.markdown("# Buy & Sell Instruments")

    df = df_catalog()
    search = st.text_input("Search by name/brand/SKU", placeholder="e.g., flute, Bose, GTR-AC-01")
    if search:
        mask = (
            df["Item"].str.contains(search, case=False)
            | df["Brand"].str.contains(search, case=False)
            | df["SKU"].str.contains(search, case=False)
        )
        view = df[mask].copy()
    else:
        view = df.copy()

    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("# Add to Cart")
    sku = st.selectbox("Select SKU", view["SKU"] if not view.empty else [""], index=0)
    qty = st.number_input("Quantity", value=1, min_value=1, step=1)
    add = st.button("Add Item to Cart", use_container_width=True)
    if add and sku:
        stock = int(df.loc[df.SKU == sku, "Stock"].iloc[0])
        if qty <= stock:
            st.session_state.cart[sku] = st.session_state.cart.get(sku, 0) + qty
            toast_success("Added to cart.")
        else:
            st.error("Requested quantity exceeds available stock.")

    if st.session_state.cart:
        st.markdown("#### Your Cart")
        cart_rows = []
        for sku, q in st.session_state.cart.items():
            row = df.loc[df.SKU == sku].iloc[0].to_dict()
            row.update({"Qty": q, "Line Total": q * row["Price"]})
            cart_rows.append(row)
        cart_df = pd.DataFrame(cart_rows)[["SKU", "Item", "Brand", "Price", "Qty", "Line Total"]]
        st.dataframe(cart_df, use_container_width=True, hide_index=True)
        total = int(cart_df["Line Total"].sum())
        st.success(f"Cart Total: ₹{total}")

        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            if st.button("Clear Cart", use_container_width=True):
                st.session_state.cart.clear()
                st.warning("Cart cleared.")
        with col2:
            cust_name = st.text_input("Your Name", key="buy_name")
            cust_phone = st.text_input("Phone", key="buy_phone")
        with col3:
            proceed = st.button("Proceed to Checkout", use_container_width=True)
        if proceed:
            if not cust_name or not cust_phone:
                st.error("Please provide your name and phone number.")
            else:
                st.success(
                    f"Thanks {cust_name}! We will contact you at {cust_phone} to complete the purchase.")

    st.markdown("---")
    st.markdown("# Want to Sell Your Gear?")
    with st.form("sell_form"):
        si_item = st.text_input("Item name & model")
        si_cond = st.selectbox("Condition", ["Mint", "Good", "Fair", "Needs repair"])
        si_price = st.number_input("Expected price (₹)", min_value=0, step=500)
        si_phone = st.text_input("Your phone")
        submitted = st.form_submit_button("Submit for Quote")
        if submitted:
            if si_item and si_phone:
                st.success("Thanks! Our team will evaluate and reach out with a quote.")
            else:
                st.error("Please fill item and phone.")

# ---------------------------
# STUDIO BOOKING
# ---------------------------
elif qa == "Studio Booking":
    st.markdown("# Recording Studio Appointments")

    bdate = st.date_input("Choose date", value=date.today(), min_value=date.today())

    if not in_working_hours(bdate):
        st.error("We are closed on Sundays. Please pick another day.")
    else:
        slots = build_time_slots(bdate, step_min=60)
        if not slots:
            st.warning("No slots available for the chosen day.")
        else:
            name = st.text_input("Your Name")
            phone = st.text_input("Phone")
            slot = st.selectbox("Available time slots", slots)
            purpose = st.selectbox("Purpose", ["Vocal recording", "Instrumental", "Podcast", "Mix/Master", "Other"])
            create = st.button("Book Appointment", use_container_width=True)
            if create:
                if not name or not phone:
                    st.error("Please enter your name and phone.")
                else:
                    appt_id = f"AP{len(st.session_state.appointments)+1:04d}"
                    st.session_state.appointments[appt_id] = {
                        "Date": bdate.isoformat(),
                        "Slot": slot,
                        "Name": name,
                        "Phone": phone,
                        "Purpose": purpose,
                        "Status": "Booked",
                    }
                    st.success(f"Appointment booked: {appt_id} on {bdate} at {slot}.")

    if st.session_state.appointments:
        st.markdown("# Your Appointments")
        adf = pd.DataFrame.from_dict(st.session_state.appointments, orient="index")
        st.dataframe(adf, use_container_width=True)

        edit_id = st.selectbox("Select appointment to modify", list(st.session_state.appointments.keys()))
        action = st.radio("Action", ["Reschedule", "Cancel"], horizontal=True)
        if action == "Reschedule":
            new_date = st.date_input("New date", value=bdate, key="resched_date")
            if not in_working_hours(new_date):
                st.warning("Selected day is a holiday. Choose another.")
            else:
                new_slot = st.selectbox("New slot", build_time_slots(new_date), key="resched_slot")
                if st.button("Confirm Reschedule", type="primary"):
                    ap = st.session_state.appointments[edit_id]
                    ap["Date"] = new_date.isoformat()
                    ap["Slot"] = new_slot
                    ap["Status"] = "Rescheduled"
                    toast_success("Rescheduled successfully.")
        else:
            if st.button("Confirm Cancellation", help="This cannot be undone"):
                st.session_state.appointments[edit_id]["Status"] = "Cancelled"
                st.warning("Appointment cancelled.")

# ---------------------------
# REPAIRS
# ---------------------------
elif qa == "Repairs":
    st.markdown("# Repair Estimates & Intake")
    colA, colB = st.columns(2)
    with colA:
        device = st.selectbox("Instrument/Device", list(REPAIR_BASE.keys()))
        severity = st.slider("Issue severity (1=minor, 5=major)", 1, 5, 2)
        parts = st.multiselect("Likely parts needed (optional)", list(REPAIR_PARTS.keys()))
        urgent = st.checkbox("Urgent service (adds 20%)")
        est_btn = st.button("Get Estimate")
    with colB:
        st.markdown("""
        - Low-cost diagnostics are included.
        - We confirm final quote after inspection.
        - Typical turnaround: 2–5 days (depends on parts).
        """)

    if est_btn:
        base = REPAIR_BASE[device]
        sev_add = (severity - 1) * 250
        parts_cost = sum(REPAIR_PARTS[p] for p in parts)
        subtotal = base + sev_add + parts_cost
        total = int(subtotal * 1.2) if urgent else subtotal
        with st.container(border=True):
            st.markdown(f"**Estimated Cost:** ₹{total}")
            st.caption(f"Base ₹{base} + Severity ₹{sev_add} + Parts ₹{parts_cost} {'+ Urgent 20%' if urgent else ''}")

    st.markdown("---")
    st.markdown("# Create Repair Ticket")
    with st.form("repair_form"):
        r_name = st.text_input("Your Name")
        r_phone = st.text_input("Phone")
        r_item = st.text_input("Instrument/Model")
        r_issue = st.text_area("Describe the issue")
        r_submit = st.form_submit_button("Submit Ticket")
        if r_submit:
            if r_name and r_phone and r_item:
                st.success("Thanks! We’ve logged your repair. Our tech will call you shortly.")
            else:
                st.error("Please fill name, phone, and instrument.")

# ---------------------------
# PURCHASE ORDERS
# ---------------------------
elif qa == "Purchase Orders":
    st.markdown("# Create & Validate Purchase Orders")

    df = df_catalog()
    with st.form("po_form"):
        buyer = st.text_input("Buyer Name")
        phone = st.text_input("Phone")
        vendor = st.text_input("Vendor/Supplier")
        sku_sel = st.multiselect("Select SKUs", df["SKU"].tolist())
        qtys = {}
        for sku in sku_sel:
            maxq = int(df.loc[df.SKU == sku, "Stock"].iloc[0])
            qtys[sku] = st.number_input(f"Qty for {sku}", 1, maxq, 1)
        create_po = st.form_submit_button("Create PO")

    if create_po:
        if not (buyer and phone and vendor and sku_sel):
            st.error("Please complete all fields and select items.")
        else:
            lines = []
            for sku in sku_sel:
                row = df.loc[df.SKU == sku].iloc[0]
                q = qtys[sku]
                lines.append({
                    "SKU": sku,
                    "Item": row["Item"],
                    "Qty": q,
                    "UnitPrice": int(row["Price"]),
                    "LineTotal": int(q * row["Price"]),
                })
            total = sum(l["LineTotal"] for l in lines)
            po = {
                "PO_ID": f"PO{len(st.session_state.purchase_orders)+1:04d}",
                "Buyer": buyer,
                "Phone": phone,
                "Vendor": vendor,
                "Date": datetime.now().isoformat(timespec='seconds'),
                "Lines": lines,
                "Total": int(total),
            }
            # Simple validation
            issues = []
            if total <= 0:
                issues.append("Total must be greater than 0.")
            for l in lines:
                if l["Qty"] <= 0:
                    issues.append(f"Invalid qty for {l['SKU']}")
            if issues:
                st.error("\n".join(issues))
            else:
                st.session_state.purchase_orders.append(po)
                st.success(f"PO created: {po['PO_ID']} · Total ₹{po['Total']}")
                st.json(po)
                st.download_button(
                    "Download PO (JSON)", data=json.dumps(po, indent=2), file_name=f"{po['PO_ID']}.json", mime="application/json"
                )

    if st.session_state.purchase_orders:
        st.markdown("# Existing POs")
        podf = pd.DataFrame(st.session_state.purchase_orders)
        st.dataframe(podf[["PO_ID", "Buyer", "Vendor", "Total", "Date"]], use_container_width=True, hide_index=True)

# ---------------------------
# DELIVERY
# ---------------------------
elif qa == "Delivery":
    st.markdown("# Delivery Request")

    with st.form("delivery_form"):
        d_name = st.text_input("Customer Name")
        d_phone = st.text_input("Phone")
        d_address = st.text_area("Delivery Address")
        d_city = st.text_input("City")
        d_post = st.text_input("Pincode")
        d_items = st.text_area("Items to deliver (one per line)", placeholder="e.g., FLT-STD-01 x1\nKB-61-01 x2")
        d_slot_date = st.date_input("Preferred delivery date", value=date.today() + timedelta(days=1), min_value=date.today())
        d_slot = st.selectbox("Preferred time slot", ["10:00 AM - 1:00 PM", "1:00 PM - 4:00 PM", "4:00 PM - 7:00 PM"]) 
        submit = st.form_submit_button("Create Delivery")

    if submit:
        if not all([d_name, d_phone, d_address, d_city, d_post, d_items]):
            st.error("Please fill all fields.")
        else:
            rec = {
                "DLV_ID": f"DLV{len(st.session_state.deliveries)+1:04d}",
                "Name": d_name,
                "Phone": d_phone,
                "Address": d_address,
                "City": d_city,
                "Pincode": d_post,
                "Items": d_items.splitlines(),
                "Date": d_slot_date.isoformat(),
                "Slot": d_slot,
                "Status": "Scheduled",
            }
            st.session_state.deliveries.append(rec)
            st.success(f"Delivery scheduled: {rec['DLV_ID']} on {rec['Date']} ({rec['Slot']})")
            st.json(rec)

    if st.session_state.deliveries:
        st.markdown("# Deliveries")
        ddf = pd.DataFrame(st.session_state.deliveries)
        st.dataframe(ddf, use_container_width=True, hide_index=True)

# ---------------------------
# FAQs
# ---------------------------
elif qa == "FAQs":
    st.markdown("# FAQs & Quick Info")

    with st.expander("What services do you offer?"):
        st.write("\n".join([f"• {s}\n" for s in SERVICES]))
    with st.expander("Working hours"):
        st.write("Mon–Fri: 8:30 AM – 9:30 PM  Sat: 10:00 AM – 6:00 PM Sun: Holiday")
    with st.expander("Can you suggest a low-cost flute?"):
        st.write("I’m happy to help! We have flutes from ₹2000 to ₹10000. Which one would you like to buy?")
    with st.expander("Office audio/video setup options"):
        st.write("Option 1: JBL with Behringer HA400 4-Channel Headphone Amplifier\n Option 2: Bose L1 Pro16 Portable Linear Array PA System")

# ---------------------------
# Footer Banner
# ---------------------------
st.markdown("### Thank you for Purchasing in Sabari Musicals! 🎶 ")
st.markdown("### Visit again soon for more services!")


