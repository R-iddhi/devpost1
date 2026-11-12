
"""
SETTLE - AI-powered freelancer invoice negotiation

Features:
- Invoice overview
- Late-payment risk estimation
- Qwen-powered dual-agent negotiation
- Freelancer financial guardrails
- Explicit human approval
- PayPal Sandbox invoice creation
- PayPal payment-status synchronization

Pandas is deliberately not used.
"""

import os
from datetime import datetime
from decimal import Decimal

import streamlit as st
from dotenv import load_dotenv

from negotiation_engine import (
    negotiate_invoice,
    NegotiationError,
)

from paypal_client import (
    create_invoice,
    send_invoice,
    get_invoice,
)


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

st.set_page_config(
    page_title="Settle",
    page_icon="🤝",
    layout="wide",
)

import ui_theme
ui_theme.apply()

MAX_DISCOUNT = 6

FREELANCER_POLICY = {
    "max_discount_percent": MAX_DISCOUNT,
    "min_payment_window_days": 1,
    "max_payment_window_days": 3,
}


# ==================================================
# SESSION STATE
# ==================================================

DEFAULT_STATE = {
    "negotiation": None,
    "paypal_invoice": None,
    "approved_deal_key": None,
    "action_log": [],
}

for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


def log_event(event):
    st.session_state.action_log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "event": event,
    })


# ==================================================
# SIMULATED CLIENT PREFERENCES
# ==================================================

# These preferences are simulated for the demonstration.
# They are not real customer financial records.

CLIENT_PROFILES = {
    "Acme Studio": {
        "minimum_discount_to_accept": 4,
        "preferred_payment_window_days": 3,
        "payment_preference": (
            "Willing to settle an overdue invoice early "
            "for a reasonable discount."
        ),
    },

    "BrightPath Co": {
        "minimum_discount_to_accept": 3,
        "preferred_payment_window_days": 3,
        "payment_preference": (
            "Prefers smaller discounts and quick settlement."
        ),
    },

    "Nova Labs": {
        "minimum_discount_to_accept": 6,
        "preferred_payment_window_days": 3,
        "payment_preference": (
            "Requires a higher discount for early payment."
        ),
    },

    "Pixel Park": {
        "minimum_discount_to_accept": 8,
        "preferred_payment_window_days": 3,
        "payment_preference": (
            "Requests a large discount before agreeing."
        ),
    },
}


# ==================================================
# DEMO INVOICE DATA
# ==================================================

# These are illustrative dashboard records.
# They are not automatically retrieved from PayPal.

invoices = [
    {
        "client": "Acme Studio",
        "project": "Logo design",
        "amount": 800,
        "days_overdue": 12,
        "status": "Overdue",
    },

    {
        "client": "BrightPath Co",
        "project": "Website copy",
        "amount": 450,
        "days_overdue": 0,
        "status": "Unpaid",
    },

    {
        "client": "Nova Labs",
        "project": "Dashboard UI",
        "amount": 1200,
        "days_overdue": 5,
        "status": "Overdue",
    },

    {
        "client": "GreenLeaf",
        "project": "Brand kit",
        "amount": 600,
        "days_overdue": 0,
        "status": "Paid",
    },

    {
        "client": "Pixel Park",
        "project": "Poster set",
        "amount": 300,
        "days_overdue": 0,
        "status": "Unpaid",
    },
]


# ==================================================
# HELPER: DISPLAY INVOICES WITHOUT PANDAS
# ==================================================

def render_invoice_table(records):

    with st.container(border=True):

        headers = st.columns([1.3, 1.5, 0.8, 0.8, 0.8])

        header_names = [
            "Client",
            "Project",
            "Amount",
            "Overdue",
            "Status",
        ]

        for column, name in zip(headers, header_names):
            column.markdown(f"**{name}**")

        st.divider()

        for item in records:

            columns = st.columns(
                [1.3, 1.5, 0.8, 0.8, 0.8]
            )

            columns[0].write(item["client"])
            columns[1].write(item["project"])

            columns[2].write(
                f"${item['amount']:,.2f}"
            )

            columns[3].write(
                f"{item['days_overdue']} days"
            )

            columns[4].write(item["status"])


# ==================================================
# FINANCIAL OVERVIEW
# ==================================================

st.title("🤝 Settle")

st.caption(
    "AI-powered invoice negotiation "
    "and settlement through PayPal."
)

outstanding = sum(
    item["amount"]
    for item in invoices
    if item["status"] != "Paid"
)

overdue_count = sum(
    1
    for item in invoices
    if item["status"] == "Overdue"
)

paid_total = sum(
    item["amount"]
    for item in invoices
    if item["status"] == "Paid"
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Outstanding",
    f"${outstanding:,.2f}",
)

c2.metric(
    "Overdue invoices",
    overdue_count,
)

c3.metric(
    "Paid this month (demo data)",
    f"${paid_total:,.2f}",
)


# ==================================================
# INVOICE TABLE
# ==================================================

st.divider()

st.subheader("📄 Your invoices")

render_invoice_table(invoices)


# ==================================================
# SELECT AN INVOICE
# ==================================================

st.divider()

st.subheader("🤖 Settle AI negotiation")

open_invoices = [
    item
    for item in invoices
    if item["status"] != "Paid"
]

labels = [
    (
        f"{item['client']} - {item['project']} "
        f"(${item['amount']:,.2f})"
    )
    for item in open_invoices
]

choice = st.selectbox(
    "Select an invoice for negotiation",
    labels,
)

selected_index = labels.index(choice)

row = open_invoices[selected_index]

client = row["client"]
project = row["project"]
amount = row["amount"]
days_overdue = row["days_overdue"]

deal_key = f"{client}|{project}|{amount}"


# ==================================================
# LATE PAYMENT RISK
# ==================================================

def late_risk(days_overdue, amount):

    # Simple heuristic, not a trained ML prediction.

    score = 20 + days_overdue * 4 + amount / 40

    return min(int(score), 95)


risk = late_risk(
    days_overdue,
    amount,
)

suggested_discount = (
    5 if risk >= 60
    else 3 if risk >= 40
    else 2
)

risk_col1, risk_col2 = st.columns(2)

risk_col1.metric(
    "Estimated late-payment risk",
    f"{risk}%",
)

risk_col2.metric(
    "Suggested starting discount",
    f"{suggested_discount}%",
)

st.progress(risk / 100)

st.info(
    f"Suggested offer: {suggested_discount}% discount "
    "if paid within 3 days."
)


# ==================================================
# RUN AI NEGOTIATION
# ==================================================

st.markdown("### 🧠 Dual AI agents")

st.caption(
    "The freelancer agent and client agent "
    "negotiate using Qwen."
)

if st.button(
    "🤖 Run AI negotiation",
    type="primary",
    use_container_width=True,
):

    try:

        invoice_context = {
            "client": client,
            "project": project,
            "amount": amount,
            "days_overdue": days_overdue,
            "estimated_late_payment_risk": risk,
            "suggested_discount_percent": suggested_discount,
        }

        client_profile = CLIENT_PROFILES[client]

        with st.spinner(
            "AI agents are negotiating..."
        ):

            result = negotiate_invoice(
                invoice=invoice_context,
                freelancer_policy=FREELANCER_POLICY,
                client_profile=client_profile,
                max_rounds=3,
            )

        st.session_state.negotiation = {
            "key": deal_key,
            "result": result,
        }

        st.session_state.approved_deal_key = None
        st.session_state.paypal_invoice = None

        log_event(
            f"Negotiation completed for {client}: "
            f"{result['status']}"
        )

        st.rerun()

    except NegotiationError as error:

        st.error(f"Negotiation error: {error}")

    except Exception as error:

        st.error(f"Unexpected error: {error}")


# ==================================================
# DISPLAY NEGOTIATION
# ==================================================

negotiation_state = st.session_state.negotiation

if (
    negotiation_state
    and negotiation_state["key"] == deal_key
):

    result = negotiation_state["result"]

    st.divider()

    st.subheader("💬 Negotiation conversation")

    for item in result["messages"]:

        agent = item["agent"]

        if agent == "Freelancer Agent":
            role = "assistant"
            avatar = "🧑‍💻"
        else:
            role = "user"
            avatar = "🏢"

        with st.chat_message(role, avatar=avatar):

            st.write(f"**{agent}**")

            st.write(item["message"])

            with st.expander("Decision details"):

                st.write(
                    "Decision:",
                    item["decision"],
                )

                st.write(
                    "Proposed discount:",
                    f"{item['discount_percent']}%",
                )

                st.write(
                    "Payment window:",
                    f"{item['payment_window_days']} days",
                )

                st.write(
                    "Reason:",
                    item["reason"],
                )


    # ==================================================
    # AGREEMENT REACHED
    # ==================================================

    if result["status"] == "agreed":

        st.success(
            "Agreement reached between the AI agents!"
        )

        final_amount = Decimal(
            result["settlement_amount"]
        )

        discount = result["discount_percent"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Original invoice",
            f"${Decimal(str(amount)):.2f}",
        )

        col2.metric(
            "Agreed discount",
            f"{discount}%",
        )

        col3.metric(
            "Settlement amount",
            f"${final_amount:.2f}",
        )

        st.info(
            "The freelancer must approve this agreement "
            "before any PayPal invoice is created."
        )


        # ==================================================
        # HUMAN APPROVAL
        # ==================================================

        if (
            st.session_state.approved_deal_key
            != deal_key
        ):

            if st.button(
                "✅ Approve settlement terms",
                type="primary",
                use_container_width=True,
                key="approve_settlement",
            ):

                st.session_state.approved_deal_key = deal_key

                log_event(
                    f"Freelancer approved settlement for {client}"
                )

                st.rerun()

        else:

            st.success(
                "Settlement approved by the freelancer."
            )


        # ==================================================
        # CREATE PAYPAL INVOICE
        # ==================================================

        if (
            st.session_state.approved_deal_key
            == deal_key
        ):

            invoice_state = st.session_state.paypal_invoice

            if not (
                invoice_state
                and invoice_state["key"] == deal_key
            ):

                st.markdown("#### 💸 PayPal Sandbox")

                st.caption(
                    "Create a PayPal settlement invoice "
                    "using the agreed amount."
                )

                if st.button(
                    "Create PayPal settlement invoice",
                    use_container_width=True,
                    key="create_paypal_invoice",
                ):

                    client_email = os.getenv(
                        "CLIENT_TEST_EMAIL"
                    )

                    if not client_email:

                        st.error(
                            "CLIENT_TEST_EMAIL is missing "
                            "from your .env file."
                        )

                    else:

                        try:

                            with st.spinner(
                                "Creating PayPal invoice..."
                            ):

                                invoice_id = create_invoice(
                                    client_email,
                                    (
                                        f"{project} "
                                        "(early-payment settlement)"
                                    ),
                                    final_amount,
                                    (
                                        f"{discount}% early-payment "
                                        "discount agreed by Settle agents."
                                    ),
                                )

                            # Store immediately after creation.
                            # Do not create another invoice if
                            # a later operation fails.

                            st.session_state.paypal_invoice = {
                                "key": deal_key,
                                "id": invoice_id,
                                "status": "DRAFT",
                                "url": None,
                            }

                            log_event(
                                f"PayPal draft created: {invoice_id}"
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"PayPal creation failed: {error}"
                            )


            # ==================================================
            # SEND INVOICE AND CHECK STATUS
            # ==================================================

            invoice_state = st.session_state.paypal_invoice

            if invoice_state and invoice_state["key"] == deal_key:

                st.markdown(
                    "#### 💳 PayPal settlement invoice"
                )

                inv1, inv2 = st.columns(2)

                inv1.metric(
                    "PayPal Invoice ID",
                    invoice_state["id"],
                )

                inv2.metric(
                    "PayPal status",
                    invoice_state["status"],
                )

                if invoice_state["status"] == "DRAFT":

                    if st.button(
                        "📨 Send invoice to client",
                        use_container_width=True,
                        key="send_paypal_invoice",
                    ):

                        try:

                            with st.spinner(
                                "Sending PayPal invoice..."
                            ):

                                send_invoice(
                                    invoice_state["id"]
                                )

                            # Mark that the send was attempted
                            # before checking the invoice again.

                            invoice_state["status"] = (
                                "SEND_CHECK_REQUIRED"
                            )

                            log_event(
                                f"PayPal send attempted: "
                                f"{invoice_state['id']}"
                            )

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"PayPal send error: {error}"
                            )

                            st.warning(
                                "Check PayPal status before "
                                "retrying the send operation."
                            )

                elif invoice_state["status"] == "SEND_CHECK_REQUIRED":

                    st.warning(
                        "Invoice send result needs verification. "
                        "Refresh its PayPal status before retrying."
                    )

                if invoice_state["url"]:

                    st.link_button(
                        "🔗 Open client payment page",
                        invoice_state["url"],
                    )


                # ==================================================
                # REFRESH ACTUAL PAYPAL STATUS
                # ==================================================

                if st.button(
                    "🔄 Refresh PayPal payment status",
                    use_container_width=True,
                    key="refresh_paypal_status",
                ):

                    try:

                        with st.spinner(
                            "Checking the actual PayPal invoice..."
                        ):

                            details = get_invoice(
                                invoice_state["id"]
                            )

                        new_status = details.get(
                            "status",
                            "UNKNOWN",
                        )

                        metadata = (
                            details.get("detail", {})
                            .get("metadata", {})
                        )

                        recipient_url = metadata.get(
                            "recipient_view_url"
                        )

                        invoice_state.update({
                            "status": new_status,
                            "url": (
                                recipient_url
                                or invoice_state["url"]
                            ),
                        })

                        log_event(
                            f"PayPal invoice status: {new_status}"
                        )

                        if new_status == "PAID":
                            st.balloons()

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Unable to refresh PayPal status: {error}"
                        )


                # ==================================================
                # STATUS MESSAGES
                # ==================================================

                status = invoice_state["status"]

                if status == "PAID":

                    st.success(
                        "✅ Payment received through PayPal."
                    )

                elif status == "MARKED_AS_PAID":

                    st.info(
                        "Payment manually marked as paid. "
                        "This does not confirm PayPal checkout."
                    )

                elif status == "PARTIALLY_PAID":

                    st.warning(
                        "Partial payment recorded."
                    )

                elif status == "PAYMENT_PENDING":

                    st.warning(
                        "Payment is pending."
                    )

                elif status == "CANCELLED":

                    st.error(
                        "The PayPal invoice is cancelled."
                    )

                elif status == "REFUNDED":

                    st.info(
                        "The invoice has been refunded."
                    )


    elif result["status"] == "rejected":

        st.error(
            "The client agent rejected the settlement offer."
        )

    elif result["status"] == "escalated":

        st.warning(
            "The requested discount exceeds the freelancer's "
            "allowed limit. Decision escalated."
        )

    else:

        st.warning(
            "No agreement was reached within the allowed rounds."
        )


# ==================================================
# ACTION HISTORY
# ==================================================

if st.session_state.action_log:

    st.divider()

    st.subheader("📜 Settle action history")

    for entry in reversed(st.session_state.action_log):

        col1, col2 = st.columns([1, 4])

        col1.caption(entry["time"])
        col2.write(entry["event"])


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "Settle | AI-assisted invoice negotiation "
    "and PayPal Sandbox payment workflow"
)
