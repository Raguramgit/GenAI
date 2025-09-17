# bmi_buddy.py
import streamlit as st
from math import isfinite

# Page config
st.set_page_config(
    page_title="BMI Buddy",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Custom CSS (modern, minimal, mobile-friendly) ----------
CUSTOM_CSS = r"""
/* Import a clean font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

:root{
  --bg: #f6f8fb;
  --card: #ffffff;
  --muted: #6b7280;
  --accent: #0ea5a4;
  --success: #16a34a;
  --danger: #ef4444;
  --glass: rgba(255,255,255,0.6);
}

html, body, [class*="css"]  {
    font-family: 'Inter', system-ui, sans-serif;
    background: var(--bg) !important;
}

/* Top header */
.header {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom: 8px;
}
.title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
.subtitle {
  color: var(--muted);
  font-size: 13px;
}

/* Card look */
.card {
  background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(245,248,255,0.9));
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 30px rgba(15,23,42,0.06);
  border: 1px solid rgba(15,23,42,0.03);
}

/* compact inputs */
.stNumberInput>div>div {
  border-radius: 10px;
}

/* BMI big value */
.bmi-big {
  font-size: 44px;
  font-weight: 800;
  margin: 2px 0 0;
}
.bmi-sub {
  color: var(--muted);
  margin-top: 6px;
}

/* Category pill */
.pill {
  display:inline-block;
  padding: 8px 12px;
  border-radius: 999px;
  font-weight:700;
}

/* small responsive tweak */
@media (max-width: 640px) {
  .bmi-big { font-size: 34px; }
  .header { flex-direction: column; align-items: flex-start; gap:6px; }
}

/* Footer */
.footer {
  text-align:center;
  color: #94a3b8;
  font-size:13px;
  margin-top: 18px;
}
"""
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# ---------- Helper functions ----------
def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI (kg/m^2). Returns rounded 1 decimal place. Handles invalid input gracefully."""
    try:
        if height_cm <= 0 or weight_kg <= 0:
            return 0.0
        h_m = height_cm / 100.0
        bmi_raw = weight_kg / (h_m * h_m)
        # Round to 1 decimal - compute manually to be explicit
        bmi_rounded = round(bmi_raw * 10) / 10.0
        return bmi_rounded
    except Exception:
        return 0.0

def category_and_suggestion(bmi: float):
    """Return (category, emoji, color_hex, short_msg, detailed_list)"""
    if not isfinite(bmi) or bmi <= 0:
        return ("—", "❓", "#6b7280", "Enter valid height and weight to calculate.", [])
    if bmi < 18.5:
        return (
            "Underweight",
            "🍲",
            "#0ea5a4",
            "Consider a nutrient-rich diet with professional guidance.",
            [
                "Increase calorie-dense, nutritious foods (nuts, oats, avocado).",
                "Include protein at each meal — lean meats, eggs, legumes.",
                "Try resistance training to build muscle mass.",
                "Consult a dietitian for a tailored meal plan."
            ],
        )
    elif bmi < 25:
        return (
            "Normal",
            "💪",
            "#16a34a",
            "Maintain a balanced diet and regular exercise 👍",
            [
                "Keep a colorful plate: vegetables, lean protein, whole grains.",
                "Aim for 150 min/week moderate or 75 min/week vigorous activity.",
                "Maintain consistent sleep and hydration habits.",
                "Periodic check-ins with healthcare as needed."
            ],
        )
    else:
        return (
            "Overweight",
            "🏃‍♂️",
            "#ef4444",
            "Incorporate physical activity and healthy eating habits.",
            [
                "Swap processed snacks for whole foods and fiber-rich choices.",
                "Start with daily 20–30 minute walks, then increase intensity.",
                "Control portions and prefer lean proteins and vegetables.",
                "Consider behavior change coaching or medical guidance if needed."
            ],
        )

def bmi_to_progress_pct(bmi: float) -> int:
    """
    Map BMI onto 0..100 for progress bar visualization.
    We'll map BMI 12 -> 0% and 40 -> 100% (clamped).
    """
    try:
        low, high = 12.0, 40.0
        if bmi <= low:
            return 0
        if bmi >= high:
            return 100
        pct = int(round((bmi - low) / (high - low) * 100))
        return pct
    except Exception:
        return 0

# ---------- App UI ----------
# Header
st.markdown(
    """
    <div class="header">
      <div>
        <div class="title">BMI Buddy <span style="font-size:18px">⚖️</span></div>
        <div class="subtitle">A clean & playful BMI calculator — minimal, mobile-friendly.</div>
      </div>
      <div class="subtitle">Enter metrics — get instant feedback & tips</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Spacing
st.markdown("")

# Input card
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    left, right = st.columns([1.6, 1])

    with left:
        # Styled numeric inputs (height & weight)
        height = st.number_input(
            "Height (cm)",
            min_value=50.0,
            max_value=260.0,
            value=170.0,
            step=0.5,
            help="Enter your height in centimeters",
            format="%.1f",
        )
        weight = st.number_input(
            "Weight (kg)",
            min_value=20.0,
            max_value=300.0,
            value=60.0,
            step=0.1,
            help="Enter your weight in kilograms",
            format="%.1f",
        )
        age = st.number_input(
            "Age (optional)",
            min_value=5,
            max_value=120,
            value=30,
            help="This is optional — shown for context only",
        )

        st.write("")  # small gap
        # Allow instant calculation or button-based; we'll show immediate results but also provide a Calculate button for UX.
        calc = st.button("Calculate BMI")

    with right:
        # Small quick facts / tips in the input card
        st.markdown("**Quick tips**")
        st.markdown("- Use centimeters / kilograms.")
        st.markdown("- BMI is a general guide — not a diagnosis.")
        st.markdown("- For conditions or pregnancy, consult a professional.")

    st.markdown("</div>", unsafe_allow_html=True)

# Compute (compute instantly for smaller friction)
bmi = calculate_bmi(weight, height)
category, emoji, color_hex, short_msg, details = category_and_suggestion(bmi)
pct = bmi_to_progress_pct(bmi)

# Output area
st.markdown("")  # spacing

with st.container():
    # Two-column responsive layout for result + recommendation
    col1, col2 = st.columns([1.4, 1])

    # Left: main BMI card
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        # Top row: emoji + label
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
              <div style="display:flex; gap:12px; align-items:center;">
                <div style="font-size:36px; line-height:1.1;">{emoji}</div>
                <div>
                  <div style="font-weight:700; font-size:14px">Your BMI</div>
                  <div class="bmi-sub">Based on height {height} cm and weight {weight} kg</div>
                </div>
              </div>
              <div style="text-align:right">
                <div style="font-size:13px; color:var(--muted)">Age</div>
                <div style="font-weight:700">{age}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # Big BMI value + category pill
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;">
               <div>
                 <div class="bmi-big">{bmi if (bmi>0) else '—'}</div>
                 <div class="bmi-sub">Body Mass Index (kg/m²)</div>
               </div>
               <div>
                 <div class="pill" style="background: {color_hex}22; color:{color_hex};">
                   {category}
                 </div>
               </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

        # Progress bar visual
        st.markdown("<div style='font-size:13px; color:var(--muted); margin-bottom:6px'>BMI visual guide</div>", unsafe_allow_html=True)
        st.progress(pct)

        # Small legend showing ranges
        st.markdown(
            """
            <div style="display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;">
              <div style="font-size:12px; color:var(--muted)">Under: &lt; 18.5</div>
              <div style="font-size:12px; color:var(--muted)">Normal: 18.5–24.9</div>
              <div style="font-size:12px; color:var(--muted)">Over: ≥ 25</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Right: Recommendation card
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
              <div>
                <div style="font-weight:700; font-size:14px">Health Recommendation</div>
                <div style="color:var(--muted); font-size:13px; margin-top:4px">{short_msg}</div>
              </div>
              <div style="font-size:22px">⚕️</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

        # Show detailed actionable tips as list
        if details:
            for tip in details:
                st.markdown(f"- {tip}")
        else:
            st.markdown("Enter valid height & weight and press **Calculate BMI**.")

        st.markdown("<hr style='margin:12px 0'>", unsafe_allow_html=True)

        # Small CTA and metric summary
        st.markdown(f"**Quick summary**")
        st.markdown(f"- Height: **{height} cm**")
        st.markdown(f"- Weight: **{weight} kg**")
        st.markdown(f"- BMI: **{bmi if (bmi>0) else '—'}**")
        st.markdown("</div>", unsafe_allow_html=True)

# Extra full-width message for notable states
if bmi > 0:
    if bmi < 18.5:
        st.info("You're classified as *Underweight*. A dietitian can help you design a healthy weight-gain plan. 🍲")
    elif bmi < 25:
        st.success("Great — your BMI is in the *Normal* range. Keep up the balanced habits! 💪")
    else:
        st.warning("BMI indicates *Overweight*. Small, consistent changes lead to big improvements. 🏃‍♂️")

# Footer
st.markdown('<div class="footer">Made with ❤️ • BMI Buddy — For informational purposes only (not medical advice)</div>', unsafe_allow_html=True)
