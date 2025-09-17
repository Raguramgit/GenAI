# trip_splitter.py
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Trip Expense Splitter - Thailand", layout="centered")

st.title("💸 Trip Expense Splitter — Thailand Trip")
st.write(
    "Enter the total trip expense and number of people. Optionally provide each person's name and contribution. "
    "You can download a CSV / Excel settlement report."
)

# --- Inputs ---
total_amount = st.number_input("Total trip expense (currency)", min_value=0.0, step=100.0, format="%.2f")
num_people = st.number_input("Number of people", min_value=1, step=1, format="%d")

st.markdown("----")
st.subheader("Optional: Enter each person's name and contribution")
st.caption("If you don't enter any contributions, the app will split the *total amount* equally.")

# Use a DataFrame editor so users can quickly add/change rows
# Create default rows based on number of people
default_names = [f"Person {i+1}" for i in range(int(num_people))]
default_data = {"name": default_names, "contribution": [0.0] * int(num_people)}
df = pd.DataFrame(default_data)

# Let the user edit the table: experimental_data_editor on newer Streamlit, fallback to st.dataframe + inputs if unavailable
try:
    edited = st.experimental_data_editor(df, num_rows="dynamic")  # allows adding/removing rows
    contrib_df = edited.copy()
except Exception:
    st.info("Editor not available — using simple inputs for each person.")
    rows = []
    for i in range(int(num_people)):
        cols = st.columns([2, 1])
        name = cols[0].text_input(f"Name {i+1}", default_names[i], key=f"name_{i}")
        amt = cols[1].number_input(f"Contribution {i+1}", min_value=0.0, step=10.0, format="%.2f", key=f"amt_{i}")
        rows.append({"name": name, "contribution": amt})
    contrib_df = pd.DataFrame(rows)

# Ensure proper columns and types
if "name" not in contrib_df.columns:
    contrib_df = contrib_df.rename(columns={contrib_df.columns[0]: "name"})
if "contribution" not in contrib_df.columns:
    # If user added a column with a different name, try to heuristically find numeric column
    numeric_cols = contrib_df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        contrib_df = contrib_df.rename(columns={numeric_cols[0]: "contribution"})
    else:
        contrib_df["contribution"] = 0.0

contrib_df["contribution"] = pd.to_numeric(contrib_df["contribution"], errors="coerce").fillna(0.0)
contrib_df["name"] = contrib_df["name"].fillna("").astype(str)

st.markdown("---")

# --- Logic & Options ---
total_contributed = contrib_df["contribution"].sum()
st.write(f"Total of entered contributions: **{total_contributed:.2f}**")
st.write(f"Declared total expense: **{total_amount:.2f}**")

# If contributions exist and differ from total amount, give an option to reconcile
use_contributions_sum = False
if total_contributed > 0:
    if abs(total_contributed - total_amount) > 1e-6:
        st.warning(
            "The sum of individual contributions does not equal the declared total amount.\n\n"
            "Choose how to proceed:"
        )
        col1, col2 = st.columns(2)
        with col1:
            # Option 1: Use declared total_amount and proportionally scale contributions so they match total_amount
            scale_contrib = st.checkbox(
                "Scale individual contributions proportionally to match declared total amount",
                value=False,
            )
        with col2:
            # Option 2: Ignore declared total_amount and use sum(contributions) as the total split basis
            use_contributions_sum = st.checkbox(
                "Use sum of entered contributions as the actual total (ignore declared total)",
                value=False,
            )
    else:
        # they match closely
        use_contributions_sum = False

# Determine basis_total
if total_contributed == 0:
    basis_total = float(total_amount)
else:
    if use_contributions_sum:
        basis_total = float(total_contributed)
    else:
        basis_total = float(total_amount)

# If scaling requested, scale contributions so that sum == total_amount
if total_contributed > 0 and 'scale_contrib' in locals() and scale_contrib and not use_contributions_sum:
    # avoid division by zero
    if total_contributed > 0:
        scaling_factor = total_amount / total_contributed if total_contributed != 0 else 1.0
        contrib_df["contribution"] = contrib_df["contribution"] * scaling_factor
        total_contributed = contrib_df["contribution"].sum()
        st.success("Contributions scaled to match declared total amount.")
        basis_total = float(total_amount)

# Final equal share (split basis)
equal_share = basis_total / int(num_people)

# Build settlement table
# If there are more or fewer rows than num_people, we still compute settlement for provided rows and
# append placeholder people with zero contributions if needed to reach num_people for equal share distribution.
settlement_df = contrib_df.copy()

# If number of provided rows less than num_people, append placeholder rows
provided = len(settlement_df)
if provided < int(num_people):
    for i in range(provided, int(num_people)):
        settlement_df = pd.concat(
            [settlement_df, pd.DataFrame([{"name": f"Person {i+1}", "contribution": 0.0}])],
            ignore_index=True,
        )

# Compute share & balance
settlement_df["share"] = equal_share
settlement_df["balance"] = settlement_df["contribution"] - settlement_df["share"]
# Positive balance -> should receive money; Negative -> owes money

# Display results
st.subheader("📊 Settlement Summary")
st.metric("Equal share per person", f"{equal_share:.2f}")

# Show table with clear styling
def format_balance(v):
    if v > 0:
        return f"Receive {v:.2f}"
    elif v < 0:
        return f"Pay {abs(v):.2f}"
    return "Settled"

display_df = settlement_df[["name", "contribution", "share", "balance"]].copy()
display_df.columns = ["Name", "Contribution", "Share", "Balance"]
st.dataframe(display_df.style.format({"Contribution": "{:.2f}", "Share": "{:.2f}", "Balance": "{:.2f}"}), height=300)

# Group summary
total_contrib_final = settlement_df["contribution"].sum()
total_share = settlement_df["share"].sum()
st.write(f"**Total used for split:** {basis_total:.2f}")
st.write(f"**Total contributions (final):** {total_contrib_final:.2f}")
st.write(f"**Total shares (sum of equal shares):** {total_share:.2f}")

# Provide a friendly human-readable summary
st.markdown("**Per-person actions**")
for _, row in settlement_df.iterrows():
    name = row["name"] if row["name"].strip() else "(no name)"
    bal = row["balance"]
    if bal > 0:
        st.success(f"{name} should **receive ₹{bal:.2f}**")
    elif bal < 0:
        st.error(f"{name} should **pay ₹{abs(bal):.2f}**")
    else:
        st.info(f"{name} is settled up ✅")

st.markdown("---")

# --- Downloadable Reports ---
st.subheader("Download settlement report")

# Prepare CSV
csv_buf = io.StringIO()
report_df = display_df.copy()
report_df.to_csv(csv_buf, index=False)
csv_bytes = csv_buf.getvalue().encode("utf-8")

# Prepare Excel
excel_buf = io.BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    report_df.to_excel(writer, index=False, sheet_name="Settlement")
    # Optionally add a summary sheet
    summary = pd.DataFrame({
        "metric": ["basis_total", "total_contributions", "equal_share", "num_people"],
        "value": [basis_total, total_contrib_final, equal_share, int(num_people)]
    })
    summary.to_excel(writer, index=False, sheet_name="Summary")
excel_buf.seek(0)

st.download_button(
    label="📥 Download CSV",
    data=csv_bytes,
    file_name="trip_settlement.csv",
    mime="text/csv",
)

st.download_button(
    label="📥 Download Excel (.xlsx)",
    data=excel_buf,
    file_name="trip_settlement.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")
st.caption("Tip: If you want the app to automatically detect currency symbols or split uneven items (like one person paid for a taxi only used by some), I can add fields for 'apportioned items' and a more advanced settlement algorithm.")
