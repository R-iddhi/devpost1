import streamlit as st
import pandas as pd
from llm import ask_llm

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
    f"{r['Client']} - {r['Project']} (${r['Amount ($)']})"
    for _, r in open_invoices.iterrows()
]
choice = st.selectbox("Pick an invoice", labels)
row = open_invoices.iloc[labels.index(choice)]


def late_risk(days_overdue, amount):
    score = 20 + days_overdue * 4 + amount / 40
    return min(int(score), 95)


risk = late_risk(row["Days overdue"], row["Amount ($)"])
discount = 5 if risk >= 60 else 3 if risk >= 40 else 2

st.metric("Late-payment risk", f"{risk}%")
st.progress(risk / 100)
st.info(f"Suggested offer: {discount}% discount if paid within 3 days → ${row['Amount ($)'] * (1 - discount / 100):,.2f}")

# Har client ki chhupi hui policy: kitna discount mile to jaldi pay karenge
CLIENT_POLICY = {"Acme Studio": 4, "BrightPath Co": 3, "Nova Labs": 6, "Pixel Park": 8}
MAX_DISCOUNT = 6  # guardrail: freelancer ka max discount limit (%)

FREELANCER_SYS = (
    "You are the AI assistant of a freelancer, negotiating an unpaid invoice politely. "
    "Write exactly 2 short sentences. Use only the numbers given to you."
)
CLIENT_SYS = (
    "You are the AI assistant of a business client replying to a freelancer's early-payment offer. "
    "Write exactly 2 short sentences. Use only the numbers given to you."
)


def say(system, prompt, fallback):
    try:
        return ask_llm(system, prompt)
    except Exception:
        return fallback


def client_agent(client, offered):
    need = CLIENT_POLICY[client]
    if offered >= need:
        return "accept", offered
    return "counter", need


if st.button("✅ Approve & send offer"):
    client = row["Client"]
    project = row["Project"]
    amount = row["Amount ($)"]
    action, final = client_agent(client, discount)

    with st.spinner("Agents are negotiating..."):
        msg1 = say(
            FREELANCER_SYS,
            f"Offer {client} a {discount}% discount on their ${amount} invoice for '{project}' if they pay within 3 days.",
            f"Hi {client}! Pay within 3 days and get {discount}% off.",
        )
        msg3 = None
        if action == "accept":
            msg2 = say(
                CLIENT_SYS,
                f"Accept the {discount}% discount offer and confirm you will pay within 3 days.",
                f"Deal! {discount}% works for us.",
            )
        else:
            msg2 = say(
                CLIENT_SYS,
                f"You cannot accept {discount}%. Counter-offer: you will pay within 3 days if the discount is {final}%.",
                f"We can pay fast, but we need {final}% off.",
            )
            if final <= MAX_DISCOUNT:
                msg3 = say(
                    FREELANCER_SYS,
                    f"Accept the client's counter-offer of {final}% discount and confirm the deal.",
                    f"{final}% is within my limit. Accepted!",
                )
            else:
                msg3 = say(
                    FREELANCER_SYS,
                    f"Politely say that {final}% is above the limit you are allowed to give, and that you must check with the freelancer first.",
                    f"{final}% is above my {MAX_DISCOUNT}% limit. Escalating to the freelancer.",
                )

    with st.chat_message("assistant", avatar="🧑‍💻"):
        st.write(f"**Freelancer agent:** {msg1}")
    with st.chat_message("user", avatar="🏢"):
        st.write(f"**Client agent:** {msg2}")
    if msg3:
        with st.chat_message("assistant", avatar="🧑‍💻"):
            st.write(f"**Freelancer agent:** {msg3}")

    if action == "counter" and final > MAX_DISCOUNT:
        st.warning(f"No deal: client wants {final}% but your limit is {MAX_DISCOUNT}%. Needs your decision.")
    else:
        st.success(f"Deal settled: {final}% off → ${amount * (1 - final / 100):,.2f}. Next: create the PayPal invoice.")