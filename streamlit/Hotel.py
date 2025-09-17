import streamlit as st
import random
import os

# -------------------------
# Config / assets
# -------------------------
# Local filenames (put these files in same folder as this script)
LOCAL_SUCCESS_GIF = "vadivelu_success.gif"
LOCAL_FAIL_GIF    = "vadivelu_fail.gif"

# -------------------------
# Menu and dialogues
# -------------------------
menu = {
    "Biryani": 120,
    "Parotta": 50,
    "Chicken 65": 100,
    "Soda": 30
}

success_dialogues = [
    "Saamy! sooru poduthu! 😂",
    "Saptachu pa.. Ippo thanpa kannu bright ah Thariethu😎",
]

fail_dialogues = [
    "Dai ennakunay varuviegalada! 😤",
    "Kaasu illa pa 🙃"
]

# -------------------------
# Helper: display GIF (local preferred)
# -------------------------
def show_gif(local_path, caption=None, width=400):
    """
    Try to show local file `local_path`. If not present, show `fallback_url`.
    Streamlit will handle GIFs if they are accessible.
    """
    if os.path.exists(local_path):
        try:
            st.image(local_path, caption=caption, width=width)
            return
        except Exception:
            # fall through to try URL
            pass

# -------------------------
# App UI
# -------------------------
st.set_page_config(page_title="🍽️ Sangi Manki Hotel", page_icon="🍛")
st.title("🍽️ Sangi Manki Hotel 🍽️")
st.subheader("Vadivelu Special Hotel Ordering 🤩")

st.write("### Today's Menu")
for item_name, price in menu.items():
    st.write(f"- **{item_name}** : Rs.{price}")

col1, col2 = st.columns([2, 1])
with col1:
    money = st.number_input("Enter the amount you have 💰", min_value=0, step=10, value=100)
    item = st.selectbox("Choose the item you want to buy 🍛", list(menu.keys()))

if st.button("Place Order"):
    price = menu[item]
    st.write(f"### You ordered **{item}** - Rs.{price}")
    st.write(f"You have Rs.{money}")

    if money >= price:
        # success
        st.success(f"Vadivelu: {random.choice(success_dialogues)}")
        # show success GIF: local preferred, fallback to URL
        show_gif(LOCAL_SUCCESS_GIF, caption="Victory!")
    else:
        shortage = price - money
        st.error(f"Vadivelu: {random.choice(fail_dialogues)}  (Short by Rs.{shortage})")
        # show fail GIF
        show_gif(LOCAL_FAIL_GIF, caption="Ouch!")

#st.write("---")
#st.caption("Tip: For best results download small GIFs (~200–800 KB) and place them in the app folder with the filenames above.")
