import streamlit as st
import pandas as pd

st.set_page_config(page_title="Settle", page_icon="🤝", layout="wide")

st.title("🤝 Settle")
st.caption("AI agents that negotiate and settle freelancer invoices")

invoices = pd.DataFrame([
    {"Client": "Acme Studio", "Project": "Logo design", "Amount ($)": 800, "Days overdue": 12, "Status": "Overdue"},
    {"Client": "BrightPath Co", "Project": "Website copy", "Amount ($)": 450, "Days overdue": 0, "Status": "Unpaid"},
    {"Client": "Nova Labs", "Project": "Dashboard UI", "Amount ($)": 1200, "Days overdue": 5, "Status": "Overdue"},
    {"Client": "GreenLeaf", "Project": "Brand kit", "Amount ($)": 600, "Days overdue": 0, "Status": "Paid"},
    {"Client": "Pixel Park", "Project": "Poster set", "Amount ($)": 300, "Days overdue": 0, "Status": "Unpaid"},
])

outstanding = invoices.loc[invoices["Status"] != "Paid", "Amount ($)"].sum()
overdue_count = (invoices["Status"] == "Overdue").sum()
paid_total = invoices.loc[invoices["Status"] == "Paid", "Amount ($)"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Outstanding", f"${outstanding:,}")
c2.metric("Overdue invoices", int(overdue_count))
c3.metric("Paid this month", f"${paid_total:,}")

st.subheader("Your invoices")
st.dataframe(invoices, use_container_width=True, hide_index=True)
st.divider()
st.subheader("🤖 Settle agent")

open_invoices = invoices[invoices["Status"] != "Paid"].reset_index(drop=True)
labels = [
    f"{row['Client']} - {row['Project']} (${row['Amount ($)']})"
    for _, row in open_invoices.iterrows()
]
choice = st.selectbox("Pick an invoice", labels)
row = open_invoices.iloc[labels.index(choice)]


def late_risk(days_overdue, amount):
    score = 20 + days_overdue * 4 + amount / 40
    return min(int(score), 95)


risk = late_risk(row["Days overdue"], row["Amount ($)"])
discount = 5 if risk >= 60 else 3 if risk >= 40 else 2
offer = round(row["Amount ($)"] * (1 - discount / 100), 2)

st.metric("Late-payment risk", f"{risk}%")
st.progress(risk / 100)
st.info(f"Suggested offer: {discount}% discount if paid within 3 days → ${offer:,.2f}")

# Har client ki chhupi hui policy: kitna discount mile to jaldi pay karenge
CLIENT_POLICY = {"Acme Studio": 4, "BrightPath Co": 3, "Nova Labs": 6, "Pixel Park": 8}
MAX_DISCOUNT = 6  # guardrail: freelancer ka max discount limit (%)


def client_agent(client, offered):
    need = CLIENT_POLICY[client]
    if offered >= need:
        return "accept", offered
    return "counter", need


if st.button("✅ Approve & send offer"):
    client = row["Client"]
    amount = row["Amount ($)"]

    with st.chat_message("assistant", avatar="🧑‍💻"):
        st.write(f"**Freelancer agent:** Hi {client}! Pay within 3 days and get {discount}% off.")

    action, final = client_agent(client, discount)

    if action == "accept":
        with st.chat_message("user", avatar="🏢"):
            st.write(f"**Client agent:** Deal! {discount}% works for us.")
    else:
        with st.chat_message("user", avatar="🏢"):
            st.write(f"**Client agent:** We can pay fast, but we need {final}% off.")
        with st.chat_message("assistant", avatar="🧑‍💻"):
            if final <= MAX_DISCOUNT:
                st.write(f"**Freelancer agent:** {final}% is within your limit. Accepted!")
            else:
                st.write(f"**Freelancer agent:** {final}% is above your {MAX_DISCOUNT}% limit. I can't agree. Escalating to you.")
                final = None

    if final is None:
        st.warning("No deal. Needs your decision.")
    else:
        st.success(f"Deal settled: {final}% off → ${amount * (1 - final / 100):,.2f}. Next: create the PayPal invoice.")