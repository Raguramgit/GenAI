"""
Eagle Restaurant Restaurant - Streamlit Application
Neon UI + Invoice PDF generation
Color updates:
- Payment Method displayed text -> black
- Place Order button text -> black
- Quantity (number input) text -> black
- Subtotal text -> white
"""

import streamlit as st
import json
import os
import re
from datetime import datetime
from typing import List, TypedDict
import uuid
from PIL import Image
from io import BytesIO

# Try imports for PDF generation
HAS_REPORTLAB = False
HAS_FPDF = False
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except Exception:
    try:
        from fpdf import FPDF
        HAS_FPDF = True
    except Exception:
        HAS_REPORTLAB = False
        HAS_FPDF = False

# ----------------------------
# Configuration & Assets
# ----------------------------
GST_RATE = 0.18  # 18% GST
RESTAURANT_PHONE = "+918056443430"
INVOICE_DIR = "invoices"
os.makedirs(INVOICE_DIR, exist_ok=True)

ASSET_PATHS = {
    "Eagle Restaurant_mutton_biryani": "attached_assets/generated_images/Eagle Restaurant_mutton_biryani_plate_f6f3494a.png",
    "chicken_biryani": "attached_assets/generated_images/Tamil_chicken_biryani_presentation_6a6e9772.png",
    "egg_biryani": "attached_assets/generated_images/Tamil_egg_biryani_99000536.png",
    "kuska_biryani": "attached_assets/generated_images/Kuska_vegetarian_biryani_67c48f53.png",
    "chicken_65": "attached_assets/generated_images/Authentic_Chicken_65_pieces_31efd37d.png",
    "mutton_chops": "attached_assets/generated_images/Grilled_mutton_chops_a6c87776.png",
    "chicken_pepper": "attached_assets/generated_images/Chicken_pepper_fry_6f5dd909.png",
    "dragon_chicken": "attached_assets/generated_images/Dragon_chicken_Indo-Chinese_dish_b76eaaa3.png",
    "mutton_soup": "attached_assets/generated_images/Mutton_milagu_pepper_soup_1c90ef1c.png",
    "chicken_soup": "attached_assets/generated_images/Tamil_chicken_milagu_soup_ccd19843.png",
    "rasam": "attached_assets/generated_images/Traditional_Tamil_rasam_22e69ddf.png",
    "chettinad_chicken": "attached_assets/generated_images/Chettinad_chicken_curry_fcb68c0a.png",
    "mutton_curry": "attached_assets/generated_images/Mutton_kuzhambu_curry_bbd4fea9.png",
    "fish_curry": "attached_assets/generated_images/Tamil_fish_curry_dca1f9c1.png",
    "dalcha": "attached_assets/generated_images/Tamil_dalcha_curry_390335f3.png",
    "parotta": "attached_assets/generated_images/Layered_wheat_parotta_18a4d819.png",
    "chicken_kothu": "attached_assets/generated_images/Chicken_kothu_parotta_20437096.png",
    "egg_kothu": "attached_assets/generated_images/Egg_kothu_parotta_389ce98d.png",
    "nool_parotta": "attached_assets/generated_images/Nool_string_parotta_cc58ff8c.png",
    "filter_coffee": "attached_assets/generated_images/South_Indian_filter_coffee_e7194eb8.png",
    "lime_soda": "attached_assets/generated_images/Fresh_lime_soda_drink_0109079f.png",
    "jigarthanda": "attached_assets/generated_images/Traditional_jigarthanda_drink_d80cceef.png",
    "lassi": "attached_assets/generated_images/Traditional_Indian_lassi_6d76111a.png",
    "video": "attached_assets/the-legend-tvc_1758275969805.mp4"
}

# ----------------------------
# Data Models
# ----------------------------
class MenuItem(TypedDict):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_path: str
    available: bool

class CartItem(TypedDict):
    menuItem: MenuItem
    quantity: int

class Customer(TypedDict):
    name: str
    phone: str
    email: str
    address: str

class OrderItem(TypedDict):
    menuItemId: str
    quantity: int
    unitPrice: float
    totalPrice: float

class Order(TypedDict):
    id: str
    customer: Customer
    orderType: str
    paymentMethod: str
    subtotal: float
    gstAmount: float
    total: float
    orderItems: List[OrderItem]
    createdAt: str

class Review(TypedDict):
    id: str
    customerName: str
    rating: int
    comment: str
    createdAt: str

# ----------------------------
# Menu Data
# ----------------------------
MENU_ITEMS: List[MenuItem] = [
    {"id":"1","name":"Eagle Restaurant Mutton Biryani","description":"Our signature mutton biryani with aromatic spices and premium basmati rice","price":280.0,"category":"Biryani","image_path":ASSET_PATHS["Eagle Restaurant_mutton_biryani"],"available":True},
    {"id":"2","name":"Chicken Biryani","description":"Tender chicken pieces cooked with fragrant biryani rice and traditional spices","price":240.0,"category":"Biryani","image_path":ASSET_PATHS["chicken_biryani"],"available":True},
    {"id":"3","name":"Egg Biryani","description":"Boiled eggs layered with flavorful biryani rice and aromatic herbs","price":180.0,"category":"Biryani","image_path":ASSET_PATHS["egg_biryani"],"available":True},
    {"id":"4","name":"Kuska Biryani","description":"Vegetarian biryani with fragrant rice and traditional spices","price":150.0,"category":"Biryani","image_path":ASSET_PATHS["kuska_biryani"],"available":True},
    {"id":"5","name":"Chicken 65","description":"Spicy deep-fried chicken pieces with curry leaves and green chilies","price":220.0,"category":"Starters","image_path":ASSET_PATHS["chicken_65"],"available":True},
    {"id":"6","name":"Mutton Chops","description":"Grilled mutton chops marinated with traditional Tamil spices","price":320.0,"category":"Starters","image_path":ASSET_PATHS["mutton_chops"],"available":True},
    {"id":"7","name":"Chicken Pepper Fry","description":"Tender chicken pieces tossed with black pepper and onions","price":250.0,"category":"Starters","image_path":ASSET_PATHS["chicken_pepper"],"available":True},
    {"id":"8","name":"Dragon Chicken","description":"Indo-Chinese style chicken with bell peppers and spicy sauce","price":280.0,"category":"Starters","image_path":ASSET_PATHS["dragon_chicken"],"available":True},
    {"id":"9","name":"Mutton Milagu Soup","description":"Rich mutton soup with black pepper and traditional Tamil spices","price":120.0,"category":"Soups","image_path":ASSET_PATHS["mutton_soup"],"available":True},
    {"id":"10","name":"Chicken Milagu Soup","description":"Clear chicken soup with pepper and aromatic herbs","price":100.0,"category":"Soups","image_path":ASSET_PATHS["chicken_soup"],"available":True},
    {"id":"11","name":"Traditional Rasam","description":"Traditional Tamil rasam with tomatoes and tamarind","price":80.0,"category":"Soups","image_path":ASSET_PATHS["rasam"],"available":True},
    {"id":"12","name":"Chettinad Chicken","description":"Spicy chicken curry with authentic Chettinad spices and coconut","price":260.0,"category":"Curries","image_path":ASSET_PATHS["chettinad_chicken"],"available":True},
    {"id":"13","name":"Mutton Kuzhambu","description":"Traditional Tamil mutton curry cooked in clay pots","price":300.0,"category":"Curries","image_path":ASSET_PATHS["mutton_curry"],"available":True},
    {"id":"14","name":"Fish Curry","description":"Fresh fish cooked in tangy coconut curry with curry leaves","price":240.0,"category":"Curries","image_path":ASSET_PATHS["fish_curry"],"available":True},
    {"id":"15","name":"Dalcha","description":"Traditional Tamil dal curry with vegetables and spices","price":160.0,"category":"Curries","image_path":ASSET_PATHS["dalcha"],"available":True},
    {"id":"16","name":"Kerala Parotta","description":"Flaky layered bread served with spicy curry","price":15.0,"category":"Parottas & Breads","image_path":ASSET_PATHS["parotta"],"available":True},
    {"id":"17","name":"Chicken Kothu Parotta","description":"Shredded parotta stir-fried with chicken and vegetables","price":180.0,"category":"Parottas & Breads","image_path":ASSET_PATHS["chicken_kothu"],"available":True},
    {"id":"18","name":"Egg Kothu Parotta","description":"Shredded parotta tossed with scrambled eggs and spices","price":140.0,"category":"Parottas & Breads","image_path":ASSET_PATHS["egg_kothu"],"available":True},
    {"id":"19","name":"Nool Parotta","description":"String-like thin parotta served with spicy gravy","price":25.0,"category":"Parottas & Breads","image_path":ASSET_PATHS["nool_parotta"],"available":True},
    {"id":"20","name":"Filter Coffee","description":"Traditional South Indian filter coffee with fresh milk","price":30.0,"category":"Beverages","image_path":ASSET_PATHS["filter_coffee"],"available":True},
    {"id":"21","name":"Fresh Lime Soda","description":"Refreshing lime soda with mint and ice","price":40.0,"category":"Beverages","image_path":ASSET_PATHS["lime_soda"],"available":True},
    {"id":"22","name":"Jigarthanda","description":"Traditional Madurai drink with milk, ice cream and basil seeds","price":60.0,"category":"Beverages","image_path":ASSET_PATHS["jigarthanda"],"available":True},
    {"id":"23","name":"Sweet Lassi","description":"Traditional Indian yogurt drink with sugar and cardamom","price":50.0,"category":"Beverages","image_path":ASSET_PATHS["lassi"],"available":True},
]

CATEGORIES = ["Biryani", "Starters", "Soups", "Curries", "Parottas & Breads", "Beverages"]
ORDER_TYPES = ["dine-in", "takeaway"]
PAYMENT_METHODS = ["cash", "upi-gpay", "upi-phonepe", "credit-card", "debit-card"]

# ----------------------------
# Helpers: images, persistence, cart, phone normalization
# ----------------------------
@st.cache_data
def load_image(image_path: str):
    try:
        if os.path.exists(image_path):
            return Image.open(image_path)
        else:
            img = Image.new('RGB', (400, 260), color=(18, 18, 18))
            return img
    except Exception:
        return Image.new('RGB', (400, 260), color=(18, 18, 18))

def init_session_state():
    if 'cart' not in st.session_state:
        st.session_state.cart = {}
    if 'orders' not in st.session_state:
        st.session_state.orders = load_orders()
    if 'reviews' not in st.session_state:
        st.session_state.reviews = load_reviews()
    if 'customer' not in st.session_state:
        st.session_state.customer = {"name": "", "phone": "", "email": "", "address": ""}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"

def load_orders() -> List[Order]:
    try:
        if os.path.exists('orders.json'):
            with open('orders.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_orders():
    try:
        with open('orders.json', 'w') as f:
            json.dump(st.session_state.orders, f, indent=2)
    except Exception:
        pass

def load_reviews() -> List[Review]:
    try:
        if os.path.exists('reviews.json'):
            with open('reviews.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_reviews():
    try:
        with open('reviews.json', 'w') as f:
            json.dump(st.session_state.reviews, f, indent=2)
    except Exception:
        pass

def add_to_cart(item: MenuItem):
    item_id = item['id']
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['quantity'] += 1
    else:
        st.session_state.cart[item_id] = {'menuItem': item, 'quantity': 1}

def update_cart_quantity(item_id: str, quantity: int):
    if quantity <= 0:
        if item_id in st.session_state.cart:
            del st.session_state.cart[item_id]
    else:
        if item_id in st.session_state.cart:
            st.session_state.cart[item_id]['quantity'] = quantity

def remove_from_cart(item_id: str):
    if item_id in st.session_state.cart:
        del st.session_state.cart[item_id]

def clear_cart():
    st.session_state.cart = {}

def get_cart_total():
    subtotal = sum(item['menuItem']['price'] * item['quantity'] for item in st.session_state.cart.values())
    gst_amount = subtotal * GST_RATE
    total = subtotal + gst_amount
    return subtotal, gst_amount, total

def get_cart_count():
    return sum(item['quantity'] for item in st.session_state.cart.values())

def normalize_phone(phone: str) -> str:
    phone_digits = re.sub(r'[^0-9]', '', phone)
    if len(phone_digits) == 10 and not phone_digits.startswith('91'):
        phone_digits = '91' + phone_digits
    if len(phone_digits) < 10 or len(phone_digits) > 15:
        raise ValueError('Invalid phone number format')
    return phone_digits

def create_whatsapp_message(order: Order, invoice_filename: str = None) -> str:
    message = f"*Eagle Restaurant Restaurant*%0A"
    message += f"*Order Confirmation*%0A%0A"
    message += f"*Customer:* {order['customer']['name']}%0A"
    message += f"*Phone:* {order['customer']['phone']}%0A"
    message += f"*Order ID:* {order['id']}%0A"
    message += f"*Type:* {order['orderType'].replace('-', ' ').upper()}%0A"
    message += f"*Payment:* {order['paymentMethod'].replace('-', ' ').upper()}%0A%0A"
    message += f"*Order Items:*%0A"
    for i, item in enumerate(order['orderItems'], 1):
        menu_item = next((m for m in MENU_ITEMS if m['id'] == item['menuItemId']), None)
        item_name = menu_item['name'] if menu_item else 'Item'
        message += f"{i}. {item['quantity']}x {item_name} - ₹{item['totalPrice']:.2f}%0A"
    gst_rate = (order['gstAmount'] / order['subtotal'] * 100) if order['subtotal'] > 0 else GST_RATE*100
    message += f"%0A*Bill Summary:*%0A"
    message += f"Subtotal: ₹{order['subtotal']:.2f}%0A"
    message += f"GST ({gst_rate:.1f}%): ₹{order['gstAmount']:.2f}%0A"
    message += f"*Total: ₹{order['total']:.2f}*%0A%0A"
    if invoice_filename:
        message += f"Invoice: {invoice_filename}%0A"
        message += f"Note: To share the PDF via WhatsApp you must attach it from your device or use WhatsApp Business API.%0A%0A"
    message += f"123 Dindigul Main Road, Dindigul, Tamil Nadu 624001%0A%0A"
    message += f"Thank you for ordering with us!"
    return message

def get_whatsapp_url(phone: str, message: str) -> str:
    normalized_phone = normalize_phone(phone)
    return f"https://wa.me/{normalized_phone}?text={message}"

# ----------------------------
# Invoice PDF generation helpers (reportlab / fpdf / html fallback)
# ----------------------------
def invoice_html(order: Order) -> str:
    lines = []
    lines.append(f"<h2>Eagle Restaurant Restaurant</h2>")
    lines.append(f"<p>Invoice: {order['id']}<br/>Date: {datetime.fromisoformat(order['createdAt']).strftime('%d %b %Y %H:%M')}</p>")
    lines.append("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>")
    lines.append("<tr><th>No</th><th>Item</th><th>Qty</th><th>Unit</th><th>Total</th></tr>")
    for i, it in enumerate(order['orderItems'], 1):
        mi = next((m for m in MENU_ITEMS if m['id'] == it['menuItemId']), None)
        name = mi['name'] if mi else "Item"
        lines.append(f"<tr><td>{i}</td><td>{name}</td><td>{it['quantity']}</td><td>₹{it['unitPrice']:.2f}</td><td>₹{it['totalPrice']:.2f}</td></tr>")
    lines.append("</table>")
    lines.append(f"<p>Subtotal: ₹{order['subtotal']:.2f}<br/>GST: ₹{order['gstAmount']:.2f}<br/><strong>Total: ₹{order['total']:.2f}</strong></p>")
    lines.append("<p>This is a computer-generated invoice.</p>")
    return "\n".join(lines)

def generate_invoice_bytes(order: Order) -> bytes:
    pdf_buffer = BytesIO()
    try:
        if HAS_REPORTLAB:
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            margin = 40
            y = height - margin
            c.setFont("Helvetica-Bold", 18)
            c.drawString(margin, y, "Eagle Restaurant Restaurant")
            c.setFont("Helvetica", 10)
            y -= 22
            c.drawString(margin, y, "123 Dindigul Main Road, Dindigul, Tamil Nadu 624001")
            y -= 18
            c.drawString(margin, y, f"Phone: {RESTAURANT_PHONE}")
            y -= 24
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y, f"Invoice: {order['id']}")
            c.setFont("Helvetica", 10)
            c.drawString(width - 200, y, f"Date: {datetime.fromisoformat(order['createdAt']).strftime('%d %b %Y %H:%M')}")
            y -= 26
            c.line(margin, y, width - margin, y)
            y -= 18
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin, y, "Bill To:")
            c.setFont("Helvetica", 10)
            c.drawString(margin + 60, y, order['customer'].get('name', ''))
            y -= 16
            c.drawString(margin + 60, y, order['customer'].get('address', ''))
            y -= 20
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin, y, "No")
            c.drawString(margin + 40, y, "Item")
            c.drawString(width - 260, y, "Qty")
            c.drawString(width - 200, y, "Unit")
            c.drawString(width - 120, y, "Total")
            y -= 12
            c.line(margin, y, width - margin, y)
            y -= 12
            c.setFont("Helvetica", 10)
            for i, it in enumerate(order['orderItems'], 1):
                mi = next((m for m in MENU_ITEMS if m['id'] == it['menuItemId']), None)
                name = mi['name'] if mi else "Item"
                c.drawString(margin, y, str(i))
                c.drawString(margin + 40, y, (name[:40] + '...') if len(name) > 40 else name)
                c.drawString(width - 260, y, str(it['quantity']))
                c.drawString(width - 200, y, f"₹{it['unitPrice']:.2f}")
                c.drawString(width - 120, y, f"₹{it['totalPrice']:.2f}")
                y -= 16
                if y < 120:
                    c.showPage()
                    y = height - margin
            y -= 8
            c.line(margin, y, width - margin, y)
            y -= 18
            c.drawRightString(width - 120, y, f"Subtotal: ₹{order['subtotal']:.2f}")
            y -= 14
            c.drawRightString(width - 120, y, f"GST ({GST_RATE*100:.0f}%): ₹{order['gstAmount']:.2f}")
            y -= 14
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(width - 120, y, f"Total: ₹{order['total']:.2f}")
            y -= 26
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(margin, y, "This is a computer-generated invoice.")
            c.showPage()
            c.save()
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            return pdf_bytes
        elif HAS_FPDF:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 8, "Eagle Restaurant Restaurant", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, "123 Dindigul Main Road, Dindigul, Tamil Nadu 624001", ln=True)
            pdf.cell(0, 6, f"Phone: {RESTAURANT_PHONE}", ln=True)
            pdf.ln(4)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 6, f"Invoice: {order['id']}", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, f"Date: {datetime.fromisoformat(order['createdAt']).strftime('%d %b %Y %H:%M')}", ln=True)
            pdf.ln(6)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(10, 6, "No", border=1)
            pdf.cell(90, 6, "Item", border=1)
            pdf.cell(20, 6, "Qty", border=1, align="R")
            pdf.cell(30, 6, "Unit", border=1, align="R")
            pdf.cell(30, 6, "Total", border=1, align="R")
            pdf.ln()
            pdf.set_font("Arial", size=10)
            for i, it in enumerate(order['orderItems'], 1):
                mi = next((m for m in MENU_ITEMS if m['id'] == it['menuItemId']), None)
                name = mi['name'] if mi else "Item"
                pdf.cell(10, 6, str(i), border=1)
                pdf.cell(90, 6, name[:45], border=1)
                pdf.cell(20, 6, str(it['quantity']), border=1, align="R")
                pdf.cell(30, 6, f"₹{it['unitPrice']:.2f}", border=1, align="R")
                pdf.cell(30, 6, f"₹{it['totalPrice']:.2f}", border=1, align="R")
                pdf.ln()
            pdf.ln(2)
            pdf.cell(0, 6, f"Subtotal: ₹{order['subtotal']:.2f}", ln=True, align="R")
            pdf.cell(0, 6, f"GST ({GST_RATE*100:.0f}%): ₹{order['gstAmount']:.2f}", ln=True, align="R")
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"Total: ₹{order['total']:.2f}", ln=True, align="R")
            pdf.ln(6)
            pdf.set_font("Arial", "I", 8)
            pdf.cell(0, 6, "This is a computer-generated invoice.", ln=True)
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            return pdf_bytes
        else:
            html = invoice_html(order)
            return html.encode("utf-8")
    except Exception:
        html = invoice_html(order)
        return html.encode("utf-8")

def save_invoice_file(order: Order) -> str:
    filename = f"invoice_{order['id']}.pdf"
    path = os.path.join(INVOICE_DIR, filename)
    pdf_bytes = generate_invoice_bytes(order)
    if not (HAS_REPORTLAB or HAS_FPDF):
        path = os.path.join(INVOICE_DIR, f"invoice_{order['id']}.html")
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        return path
    else:
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        return path

# ----------------------------
# UI: Neon CSS + targeted color overrides requested
# ----------------------------
NEON_CSS = """
<style>
html, body, .stApp {
    background: radial-gradient(1200px 600px at 10% 10%, rgba(0,245,255,0.06), transparent 8%),
                linear-gradient(135deg, #001f28 0%, #003049 25%, #2a0f6a 70%, #7b2ff7 100%);
    background-attachment: fixed;
    color: #e6fbff;
}
.stApp::after {
    content: "";
    pointer-events: none;
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 4px 4px;
    mix-blend-mode: overlay;
    opacity: 0.65;
    animation: grain 8s steps(10) infinite;
}
@keyframes grain {
    0% { transform: translateY(0); }
    50% { transform: translateY(2px); }
    100% { transform: translateY(0); }
}

/* default neon button look */
.stButton > button {
    width: 100%;
    transition: all 0.18s ease;
    border-radius: 12px;
    background: linear-gradient(90deg, rgba(0,245,255,0.10), rgba(123,47,247,0.12));
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 8px 30px rgba(123,47,247,0.14), 0 0 18px rgba(0,245,255,0.08) inset;
    color: #e6fbff;
    font-weight: 700;
    text-shadow: 0 1px 6px rgba(0,245,255,0.08);
}
.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 40px rgba(123,47,247,0.28), 0 0 26px rgba(0,245,255,0.18);
    border-color: rgba(255,255,255,0.14);
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    text-shadow: 0 2px 18px rgba(123,47,247,0.7), 0 0 12px rgba(0,245,255,0.45);
    color: #eaffff !important;
}
.stMetric {
    text-align: center;
    background: rgba(255,255,255,0.02);
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 6px 30px rgba(0,0,0,0.35), 0 0 14px rgba(0,245,255,0.04) inset;
    border: 1px solid rgba(255,255,255,0.03);
}

/* Keep general labels white */
div[data-testid="stForm"] label,
.stTextInput label, .stTextArea label, .stNumberInput label,
.stRadio label {
    color: #ffffff !important;
}

/* Make radio option text white */
div[role="radiogroup"] label, div[role="radiogroup"] span {
    color: #ffffff !important;
}

/* Subtotal (metrics/invoice area) must be white - high specificity */
.stMetric, .stMetric * , .invoice-area, .invoice-area * {
    color: #ffffff !important;
}

/* ---------- Payment Method (displayed value) -> BLACK ---------- */
/* Target the select component whose aria-label equals "Payment Method" */
div[aria-label="Payment Method"] , div[aria-label="Payment Method"] * {
    color: black !important;
}

/* Also target the inner display/title element inside that select (some Streamlit versions) */
div[aria-label="Payment Method"] div[title], div[aria-label="Payment Method"] span {
    color: black !important;
}

/* Fallback - if the element has a data-testid or other structure */
div[role="button"][aria-label="Payment Method"], div[role="button"][aria-label="Payment Method"] * {
    color: black !important;
}

/* ---------- Quantity (number input) text -> BLACK ---------- */
/* Target number input field text and spinner */
.stNumberInput input, .stNumberInput, .stNumberInput * {
    color: black !important;
}

/* For accessibility variations: target elements with aria-label containing 'Quantity' */
div[aria-label*="Quantity"], div[aria-label*="Quantity"] * {
    color: black !important;
}

/* Make +/- buttons text (if they are rendered as simple buttons nearby) black too */
button[id^="minus_"] , button[id^="plus_"], button[title^="minus"], button[title^="plus"] {
    color: black !important;
}

/* ---------- Place Order button text -> BLACK (keeps neon-pink bg if you had it) ---------- */
/* Target the form submit button specifically */
form .stButton:last-of-type > button {
    color: black !important;
    /* If you want neon-pink background keep it; here we keep previous neon-pink background if present */
    background: linear-gradient(90deg, #ff2fa8, #ff5fb0) !important;
    border: 1px solid rgba(255,47,168,0.9) !important;
    box-shadow: 0 8px 30px rgba(255,47,168,0.18) !important;
    font-weight: 800 !important;
}

/* Hover for place order */
form .stButton:last-of-type > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(255,47,168,0.25) !important;
}

/* Ensure Download Invoice button retains readable text */
.stDownloadButton > button {
    color: black !important;
}

/* Small responsive fallback selectors */
div[role="radiogroup"] label, label, span {
    /* no-op fallback - don't change default unless targeted above */
}

/* end CSS */
</style>
"""
st.markdown(NEON_CSS, unsafe_allow_html=True)

# ----------------------------
# Page Renderers (full features)
# ----------------------------
def render_hero_section():
    st.markdown("### 🎬 The Legend of Eagle Restaurant")
    try:
        if os.path.exists(ASSET_PATHS["video"]):
            with open(ASSET_PATHS["video"], "rb") as vf:
                st.video(vf.read())
        else:
            st.markdown("""
            <div style="width:100%;height:240px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(90deg, rgba(255,255,255,0.02), rgba(0,0,0,0.06));">
                <strong>Video not found — enjoy our flavors via the menu below 🍽️</strong>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.info("Couldn't load the hero video.")

def render_home_page():
    st.markdown("""
    <div style="text-align:center;padding:1.4rem;border-radius:12px;">
        <h1 style="margin:0; font-size:2.2rem;">🍽️ Eagle Restaurant</h1>
        <p style="opacity:0.9;margin-top:6px;">Legendary Biryani — Authentic Tamil Nadu Flavors</p>
    </div>
    """, unsafe_allow_html=True)
    render_hero_section()
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🛒 Order Now - Explore Our Menu", use_container_width=True, key="cta_order"):
            st.session_state.current_page = "Menu"
            st.rerun()

def render_menu_item_card(item):
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        try:
            img = load_image(item['image_path'])
            st.image(img, use_container_width=True)
        except Exception:
            st.write("Image error")
    with col2:
        st.subheader(f"🍽️ {item['name']}")
        st.write(item['description'])
        st.markdown(f"**₹{item['price']:.0f}**")
        item_id = item['id']
        qty = st.session_state.cart.get(item_id, {}).get('quantity', 0)
        if qty == 0:
            if st.button(f"🛒 Add to Cart", key=f"add_{item_id}"):
                add_to_cart(item)
                st.success(f"Added {item['name']} to cart.")
                st.rerun()
        else:
            st.markdown(f"**In Cart: {qty}**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("➖", key=f"minus_{item_id}"):
                    update_cart_quantity(item_id, qty-1)
                    st.rerun()
            with c2:
                if st.button("➕", key=f"plus_{item_id}"):
                    update_cart_quantity(item_id, qty+1)
                    st.rerun()

def render_menu_page():
    st.title("🍽️ Our Authentic Menu")
    selected_category = st.radio("Select Category:", ["All"] + CATEGORIES, horizontal=True, key="menu_category")
    if selected_category == "All":
        filtered = MENU_ITEMS
    else:
        filtered = [m for m in MENU_ITEMS if m['category'] == selected_category]
    if not filtered:
        st.info("No items in this category.")
    else:
        for it in filtered:
            render_menu_item_card(it)

def create_order_from_cart(customer: dict, order_type: str, payment_method: str):
    subtotal, gst_amount, total = get_cart_total()
    order_items = []
    for iid, cart_item in st.session_state.cart.items():
        mi = cart_item['menuItem']
        q = cart_item['quantity']
        order_items.append({'menuItemId': iid, 'quantity': q, 'unitPrice': mi['price'], 'totalPrice': mi['price'] * q})
    order_id = f"THA{datetime.now().strftime('%Y%m%d%H%M')}{str(uuid.uuid4())[:4].upper()}"
    order = {
        'id': order_id,
        'customer': customer,
        'orderType': order_type,
        'paymentMethod': payment_method,
        'subtotal': subtotal,
        'gstAmount': gst_amount,
        'total': total,
        'orderItems': order_items,
        'createdAt': datetime.now().isoformat()
    }
    return order

def render_cart_page():
    st.title("🛒 Your Cart & Checkout")
    if not st.session_state.cart:
        st.info("Your cart is empty.")
        if st.button("🔍 Browse Menu"):
            st.session_state.current_page = "Menu"
            st.rerun()
        return

    st.subheader("Order Summary")
    total_items = 0
    for item_id, cart_item in list(st.session_state.cart.items()):
        menu_item = cart_item['menuItem']
        quantity = cart_item['quantity']
        total_items += quantity
        with st.expander(f"{menu_item['name']} — Qty: {quantity}", expanded=True):
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            with c1:
                st.write(menu_item['description'])
                st.caption(f"₹{menu_item['price']:.2f} per item")
            with c2:
                new_qty = st.number_input("Quantity", min_value=1, value=quantity, key=f"num_{item_id}")
                if new_qty != quantity:
                    update_cart_quantity(item_id, new_qty)
                    st.rerun()
            with c3:
                st.metric("Subtotal", f"₹{menu_item['price']*quantity:.2f}")
            with c4:
                if st.button("🗑️ Remove", key=f"remove_{item_id}"):
                    remove_from_cart(item_id)
                    st.rerun()

    subtotal, gst_amount, total = get_cart_total()
    st.markdown("---")

    st.markdown(f"""
    <div class="invoice-area" style="padding:12px;border-radius:10px;background:linear-gradient(90deg, rgba(255,255,255,0.02), rgba(0,0,0,0.04));">
        <strong>Items:</strong> {total_items} &nbsp;&nbsp; <strong style="color:#ffffff">Subtotal:</strong> <strong style="color:#ffffff">₹{subtotal:.2f}</strong> <br>
        <strong style="color:#ffffff">GST ({GST_RATE*100:.0f}%):</strong> <strong style="color:#ffffff">₹{gst_amount:.2f}</strong> &nbsp;&nbsp;
        <strong style="font-size:1.1rem;color:#ffffff">Total: ₹{total:.2f}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Generate Invoice (outside form)
    st.markdown("### Invoice")
    gen_col1, gen_col2 = st.columns([1,2])
    with gen_col1:
        if st.button("📄 Generate & Download Invoice (PDF)", key="generate_invoice_outside"):
            name_tmp = st.session_state.customer.get('name','Guest')
            phone_tmp = st.session_state.customer.get('phone','')
            email_tmp = st.session_state.customer.get('email','')
            addr_tmp = st.session_state.customer.get('address','')
            temp_customer = {"name": name_tmp or "Guest", "phone": phone_tmp or "", "email": email_tmp or "", "address": addr_tmp or ""}
            temp_order = create_order_from_cart(temp_customer, ORDER_TYPES[0], PAYMENT_METHODS[0])
            temp_order['createdAt'] = datetime.now().isoformat()
            pdf_bytes = generate_invoice_bytes(temp_order)
            filename = f"invoice_{temp_order['id']}.pdf" if (HAS_REPORTLAB or HAS_FPDF) else f"invoice_{temp_order['id']}.html"
            st.download_button("⬇️ Download Invoice", pdf_bytes, file_name=filename, mime='application/pdf' if (HAS_REPORTLAB or HAS_FPDF) else 'text/html')
            st.success("Invoice generated for current cart (preview).")

    with gen_col2:
        st.caption("Generate a printable invoice for the current cart (no order required).")

    st.markdown("---")

    # Checkout form
    st.subheader("Checkout Details")
    with st.form("checkout"):
        order_type = st.selectbox("Order Type", ORDER_TYPES, format_func=lambda x: x.replace("-", " ").title())
        st.markdown("#### Customer Info")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", value=st.session_state.customer.get('name', ''))
            phone = st.text_input("Phone Number *", value=st.session_state.customer.get('phone', ''))
        with c2:
            email = st.text_input("Email", value=st.session_state.customer.get('email', ''))
            address = st.text_area("Address", value=st.session_state.customer.get('address', ''))
        # Payment Method - displayed text targeted to be black via CSS using aria-label
        payment_method = st.selectbox("Payment Method", PAYMENT_METHODS, format_func=lambda x: {
            "cash":"💵 Cash on Delivery",
            "upi-gpay":"📱 UPI - Google Pay",
            "upi-phonepe":"📱 UPI - PhonePe",
            "credit-card":"💳 Credit Card",
            "debit-card":"💳 Debit Card"
        }.get(x,x))

        # Place Order submit button
        submit = st.form_submit_button("🚀 Place Order")
        if submit:
            if not name or not phone:
                st.error("Please provide your name and phone number.")
            else:
                try:
                    normalized_phone = normalize_phone(phone)
                    st.session_state.customer = {"name":name,"phone":phone,"email":email,"address":address}
                    order = create_order_from_cart(st.session_state.customer, order_type, payment_method)
                    st.session_state.orders.append(order)
                    save_orders()
                    invoice_path = save_invoice_file(order)
                    invoice_filename = os.path.basename(invoice_path)
                    st.success(f"Order placed! Order ID: {order['id']}")
                    st.balloons()
                    msg = create_whatsapp_message(order, invoice_filename=invoice_filename)
                    wa = get_whatsapp_url(phone, msg)
                    st.markdown(f"[📤 Send Bill via WhatsApp]({wa})")
                    try:
                        with open(invoice_path, "rb") as f:
                            pdf_data = f.read()
                        st.download_button("⬇️ Download Invoice (Saved PDF)", pdf_data, file_name=invoice_filename, mime='application/pdf' if (HAS_REPORTLAB or HAS_FPDF) else 'text/html')
                    except Exception:
                        st.info(f"Invoice saved at: {invoice_path}")
                    clear_cart()
                except ValueError as e:
                    st.error(f"Invalid phone: {e}")
                except Exception as e:
                    st.error(f"Failed to place order. Try again. ({e})")

def render_reviews_page():
    st.title("⭐ Customer Reviews")
    if st.session_state.reviews:
        avg = sum(r['rating'] for r in st.session_state.reviews)/len(st.session_state.reviews)
        st.metric("Average Rating", f"{avg:.1f} ⭐")
    st.markdown("---")
    with st.form("review_form"):
        name = st.text_input("Your name")
        rating = st.radio("Rating", [5,4,3,2,1], index=0, horizontal=True)
        comment = st.text_area("Comment", height=100)
        if st.form_submit_button("Submit Review"):
            if not name or not comment:
                st.error("Please fill name and comment.")
            else:
                rev = {'id':str(uuid.uuid4()),'customerName':name,'rating':rating,'comment':comment,'createdAt':datetime.now().isoformat()}
                st.session_state.reviews.insert(0, rev)
                save_reviews()
                st.success("Thanks for your review!")
                st.rerun()
    st.markdown("---")
    if st.session_state.reviews:
        for r in st.session_state.reviews:
            st.markdown(f"**{r['customerName']}** — {'⭐'*r['rating']}  <small style='color:#bfefff'>{datetime.fromisoformat(r['createdAt']).strftime('%b %d, %Y')}</small>", unsafe_allow_html=True)
            st.write(r['comment'])
            st.markdown("---")
    else:
        st.info("No reviews yet — be the first!")

def render_contact_page():
    st.title("📞 Contact & Location")
    st.markdown(f"""
    **Phone:** [ {RESTAURANT_PHONE} ](tel:{RESTAURANT_PHONE})  
    **Email:** [ contact@Eagle Restaurant.com ](mailto:contact@Eagle Restaurant.com)  
    **Address:** 123 Vijayapathi Main Road, \nNear Velan Multispeciality Hospital, \nRadhpuram,\nTirunelveli, \nTamil Nadu 627111
    """)
    st.markdown("---")
    st.markdown("**Business Hours**: 11:00 AM - 11:00 PM (Daily)")

# ----------------------------
# Main App
# ----------------------------
def main():
    st.set_page_config(page_title="Eagle Restaurant - Neon", page_icon="🍽️", layout="wide", initial_sidebar_state="collapsed")
    init_session_state()

    nav1, nav2, nav3, nav4, nav5 = st.columns(5)
    with nav1:
        if st.button("🏠 Home", key="nav_home"):
            st.session_state.current_page = "Home"
            st.rerun()
    with nav2:
        if st.button("🍽️ Menu", key="nav_menu"):
            st.session_state.current_page = "Menu"
            st.rerun()
    with nav3:
        if st.button("🛒 Cart & Checkout", key="nav_cart"):
            st.session_state.current_page = "Cart & Checkout"
            st.rerun()
    with nav4:
        if st.button("⭐ Reviews", key="nav_reviews"):
            st.session_state.current_page = "Reviews"
            st.rerun()
    with nav5:
        if st.button("📞 Contact", key="nav_contact"):
            st.session_state.current_page = "Contact"
            st.rerun()

    cart_count = get_cart_count()
    if cart_count > 0:
        subtotal, gst_amount, total = get_cart_total()
        st.markdown(f"<div style='text-align:right;'>🛒 {cart_count} items — ₹{total:.2f}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:right;color:#bfefff'>🛒 Cart empty</div>", unsafe_allow_html=True)

    st.markdown("---")

    page = st.session_state.current_page
    if page == "Home":
        render_home_page()
    elif page == "Menu":
        render_menu_page()
    elif page == "Cart & Checkout":
        render_cart_page()
    elif page == "Reviews":
        render_reviews_page()
    elif page == "Contact":
        render_contact_page()
    else:
        render_home_page()

    st.markdown("---")
    st.markdown("""
    <div style='text-align:center;color:#bfefff;padding:12px;'>
        🍽️ Eagle Restaurant — Legendary Biryani Since 1957 • © 2024
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
