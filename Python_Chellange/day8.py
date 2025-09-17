import streamlit as st

# Neon & playful style
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle, #ff00aa, #ff5500, #ffdd00);
        color: #fff;
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    .title {
        font-size: 3rem;
        font-weight: 900;
        text-shadow: 1px 1px 6px #00000088;
        margin-bottom: 0.5rem;
    }
    .converter-box {
        background: rgba(0,0,0,0.3);
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 0 15px #fff9;
    }
    .stButton>button {
        background: #ff0088;
        color: #fff;
        font-weight: 700;
        border-radius: 15px;
        padding: 10px 25px;
        font-size: 1.2rem;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    .stButton>button:hover {
        background: #ff44aa;
    }
    select, input {
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 12px;
        border: none;
        padding: 8px 15px;
        background: #ff66aa88;
        color: #fff;
        text-align: center;
        width: 140px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Currency Converter 💱</div>', unsafe_allow_html=True)

# Static rates relative to 1 USD
rates = {
    "USD": 1.0,
    "INR": 82.10,
    "EUR": 0.92,
    "GBP": 0.81,
    "JPY": 147.53,
    "AUD": 1.54,
    "CAD": 1.35,
    "CHF": 0.90,
    "CNY": 7.28,
    "SGD": 1.36
}

col1, col2, col3 = st.columns([1, 0.5, 1])

with col1:
    from_currency = st.selectbox("From Currency", list(rates.keys()), key="from")
    amount = st.number_input(
        "Amount",
        min_value=0.0,
        step=0.1,
        format="%.2f",
        key="amount",
    )

with col2:
    st.markdown("<h2 style='text-align:center; margin-top:40px;'>➜</h2>", unsafe_allow_html=True)

with col3:
    to_currency = st.selectbox("To Currency", list(rates.keys()), index=1, key="to")

if amount > 0:
    # Conversion
    in_usd = amount / rates[from_currency]
    converted_amount = in_usd * rates[to_currency]

    st.markdown(
        f"""<div class="converter-box" style="margin-top: 20px; text-align:center;">
        <h3>Conversion Result</h3>
        <p style="font-size: 2rem; font-weight: 900;">{amount:.2f} {from_currency} = <span style="color:#ffdd00;">{converted_amount:.2f} {to_currency}</span></p>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<p style='text-align:center; color:#fff9; font-weight:bold;'>Enter an amount to convert!</p>", unsafe_allow_html=True
    )
