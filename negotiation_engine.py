
"""
SETTLE - Dual AI Negotiation Engine

Two AI agents negotiate early-payment settlements:

1. Freelancer Agent:
   Protects the freelancer's earnings and proposes discounts.

2. Client Agent:
   Evaluates offers and can accept, counter or reject.

IMPORTANT:
AI agents only propose negotiation terms.
Python validates all financial values.
A human must approve the final settlement before PayPal is used.
"""

import json

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from llm import ask_llm_json, LLMResponseError


# ==================================================
# CONFIGURATION
# ==================================================

CENT = Decimal("0.01")

VALID_DECISIONS = {
    "offer",
    "accept",
    "counter",
    "reject",
    "escalate"
}


# ==================================================
# CUSTOM ERROR
# ==================================================

class NegotiationError(Exception):
    """Raised when negotiation data or AI decisions are invalid."""


# ==================================================
# AI RESPONSE JSON SCHEMA
# ==================================================

NEGOTIATION_SCHEMA = {
    "type": "object",

    "properties": {
        "decision": {
            "type": "string",
            "enum": [
                "offer",
                "accept",
                "counter",
                "reject",
                "escalate"
            ]
        },

        "discount_percent": {
            "type": "number"
        },

        "payment_window_days": {
            "type": "integer"
        },

        "reason": {
            "type": "string"
        },

        "message": {
            "type": "string"
        }
    },

    "required": [
        "decision",
        "discount_percent",
        "payment_window_days",
        "reason",
        "message"
    ],

    "additionalProperties": False
}


# ==================================================
# FINANCIAL VALIDATION
# ==================================================

def to_decimal(value, field_name):
    """Safely convert a value into Decimal."""

    if isinstance(value, bool) or value is None:
        raise NegotiationError(
            f"{field_name} must be a valid number."
        )

    try:
        number = Decimal(str(value))

    except (InvalidOperation, ValueError, TypeError):
        raise NegotiationError(
            f"{field_name} must be a valid number."
        ) from None

    if not number.is_finite():
        raise NegotiationError(
            f"{field_name} must be finite."
        )

    return number


def calculate_settlement_amount(
    invoice_amount,
    discount_percent
):
    """
    Calculate the final invoice amount.

    Example:
    Original amount = $800
    Discount = 5%
    Final amount = $760
    """

    amount = to_decimal(
        invoice_amount,
        "Invoice amount"
    )

    discount = to_decimal(
        discount_percent,
        "Discount"
    )

    if amount <= 0:
        raise NegotiationError(
            "Invoice amount must be greater than zero."
        )

    if discount < 0 or discount > 100:
        raise NegotiationError(
            "Discount must be between 0 and 100."
        )

    final_amount = amount * (
        Decimal("1") - discount / Decimal("100")
    )

    return final_amount.quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


def validate_policy(policy):
    """Validate the freelancer's financial constraints."""

    if not isinstance(policy, dict):
        raise NegotiationError(
            "Freelancer policy must be a dictionary."
        )

    maximum_discount = to_decimal(
        policy.get("max_discount_percent"),
        "Maximum discount"
    )

    minimum_days = policy.get(
        "min_payment_window_days",
        1
    )

    maximum_days = policy.get(
        "max_payment_window_days",
        3
    )

    if not 0 <= maximum_discount <= 100:
        raise NegotiationError(
            "Maximum discount must be between 0 and 100."
        )

    if (
        isinstance(minimum_days, bool)
        or isinstance(maximum_days, bool)
        or not isinstance(minimum_days, int)
        or not isinstance(maximum_days, int)
    ):
        raise NegotiationError(
            "Payment window limits must be integers."
        )

    if minimum_days < 1 or maximum_days < minimum_days:
        raise NegotiationError(
            "Invalid payment window limits."
        )

    return maximum_discount, minimum_days, maximum_days


def validate_terms(discount, payment_days, policy):
    """Ensure an offer respects the freelancer's rules."""

    maximum_discount, minimum_days, maximum_days = (
        validate_policy(policy)
    )

    discount = to_decimal(
        discount,
        "Proposed discount"
    )

    if not 0 <= discount <= maximum_discount:
        raise NegotiationError(
            "AI proposed a discount outside the freelancer's limit."
        )

    if (
        isinstance(payment_days, bool)
        or not isinstance(payment_days, int)
    ):
        raise NegotiationError(
            "Payment window must be an integer."
        )

    if not minimum_days <= payment_days <= maximum_days:
        raise NegotiationError(
            "AI proposed a payment window outside the allowed range."
        )

    return discount


# ==================================================
# VALIDATE AI RESPONSE
# ==================================================

def validate_agent_response(response, allowed_decisions):
    """
    Validate the structure returned by an AI agent.

    Never trust an LLM response directly for financial decisions.
    """

    if not isinstance(response, dict):
        raise NegotiationError(
            "Agent response must be a JSON object."
        )

    decision = response.get("decision")

    if not isinstance(decision, str):
        raise NegotiationError(
            "Agent decision must be text."
        )

    decision = decision.strip().lower()

    if decision not in VALID_DECISIONS:
        raise NegotiationError(
            "Agent returned an unknown decision."
        )

    if decision not in allowed_decisions:
        raise NegotiationError(
            f"Decision '{decision}' is not allowed at this stage."
        )

    discount = to_decimal(
        response.get("discount_percent"),
        "Agent discount"
    )

    if not 0 <= discount <= 100:
        raise NegotiationError(
            "Agent discount must be between 0 and 100."
        )

    payment_days = response.get(
        "payment_window_days"
    )

    if (
        isinstance(payment_days, bool)
        or not isinstance(payment_days, int)
        or not 1 <= payment_days <= 30
    ):
        raise NegotiationError(
            "Agent returned an invalid payment window."
        )

    reason = response.get("reason")
    message = response.get("message")

    if (
        not isinstance(reason, str)
        or not reason.strip()
        or len(reason) > 600
    ):
        raise NegotiationError(
            "Agent returned an invalid explanation."
        )

    if (
        not isinstance(message, str)
        or not message.strip()
        or len(message) > 500
    ):
        raise NegotiationError(
            "Agent returned an invalid message."
        )

    return {
        "decision": decision,
        "discount_percent": discount,
        "payment_window_days": payment_days,
        "reason": reason.strip(),
        "message": message.strip()
    }


# ==================================================
# CALL AI AGENT
# ==================================================

def call_agent(
    system_prompt,
    user_prompt,
    allowed_decisions,
    agent_function=None
):
    """
    Request a structured decision from Qwen.

    agent_function is injectable so we can test the engine
    without requiring a running Ollama server.
    """

    model_function = agent_function or ask_llm_json

    try:
        response = model_function(
            system_prompt,
            user_prompt,
            NEGOTIATION_SCHEMA,
            temperature=0.1
        )

    except LLMResponseError as exc:
        raise NegotiationError(
            f"AI model error: {exc}"
        ) from exc

    except Exception as exc:
        raise NegotiationError(
            f"Agent execution failed: {exc}"
        ) from exc

    return validate_agent_response(
        response,
        allowed_decisions
    )


# ==================================================
# FREELANCER AI AGENT
# ==================================================

FREELANCER_SYSTEM_PROMPT = """
You are the AI negotiation representative of a freelancer.

Your objective:
Recover unpaid invoices quickly while protecting the
freelancer's earnings.

Rules:
1. Never exceed the freelancer's maximum discount.
2. Consider the invoice amount and overdue duration.
3. Prefer a reasonable early-payment agreement.
4. Do not invent financial facts.
5. Return only a decision matching the supplied JSON schema.
6. Explain your decision briefly.

You must distinguish between proposing an offer,
accepting a client counteroffer, rejecting it,
and escalating a decision to the freelancer.
"""


def freelancer_initial_offer(
    invoice,
    policy,
    agent_function=None
):
    """Ask the freelancer agent to generate its initial offer."""

    maximum_discount, min_days, max_days = (
        validate_policy(policy)
    )

    system_prompt = FREELANCER_SYSTEM_PROMPT

    user_prompt = f"""
Generate an initial early-payment discount offer.

Invoice:
{json.dumps(invoice, default=str)}

Freelancer policy:
Maximum discount: {maximum_discount}%
Allowed payment window: {min_days} to {max_days} days.

Return:
- decision = offer
- discount_percent
- payment_window_days
- reason
- message

Do not exceed the freelancer's policy.
"""

    response = call_agent(
        system_prompt,
        user_prompt,
        {"offer"},
        agent_function
    )

    validate_terms(
        response["discount_percent"],
        response["payment_window_days"],
        policy
    )

    return response


def freelancer_evaluate_counteroffer(
    invoice,
    policy,
    client_counter,
    agent_function=None
):
    """Ask the freelancer agent to evaluate a client's counteroffer."""

    maximum_discount, min_days, max_days = (
        validate_policy(policy)
    )

    system_prompt = FREELANCER_SYSTEM_PROMPT

    user_prompt = f"""
The client has made a counteroffer.

Invoice:
{json.dumps(invoice, default=str)}

Client counteroffer:
{json.dumps(client_counter, default=str)}

Freelancer policy:
Maximum discount: {maximum_discount}%
Allowed payment window: {min_days} to {max_days} days.

Decide whether to:

1. accept the client's exact counteroffer,
2. counter with a new offer,
3. reject the counteroffer,
4. escalate to the freelancer.

If accepting, your decision must be accept.

If countering, propose a discount at least as large as
the client's requested discount, but never exceed the
freelancer's maximum.

Return structured JSON only.
"""

    response = call_agent(
        system_prompt,
        user_prompt,
        {"accept", "counter", "reject", "escalate"},
        agent_function
    )

    if response["decision"] == "accept":
        # Acceptance means accepting the client's exact terms.
        response["discount_percent"] = (
            client_counter["discount_percent"]
        )

        response["payment_window_days"] = (
            client_counter["payment_window_days"]
        )

        # An accepted counteroffer must still pass Python guardrails.
        validate_terms(
            response["discount_percent"],
            response["payment_window_days"],
            policy
        )

    elif response["decision"] == "counter":
        validate_terms(
            response["discount_percent"],
            response["payment_window_days"],
            policy
        )

        if (
            response["discount_percent"]
            < client_counter["discount_percent"]
        ):
            raise NegotiationError(
                "Freelancer counteroffer is less favorable "
                "than the client's requested discount."
            )

    return response


# ==================================================
# CLIENT AI AGENT
# ==================================================

CLIENT_SYSTEM_PROMPT = """
You are the AI negotiation representative of a business client.

Your objective:
Obtain a reasonable early-payment discount while
maintaining a fair commercial agreement.

Evaluate the freelancer's offer against the client's
provided payment preferences.

You can:
1. accept the current offer,
2. counter with a different discount or payment window,
3. reject the offer.

Do not invent client preferences.
Do not invent invoice details.
Return only structured JSON matching the supplied schema.
"""


def client_evaluate_offer(
    invoice,
    current_offer,
    client_profile,
    agent_function=None
):
    """Ask the client agent to evaluate the freelancer's offer."""

    system_prompt = CLIENT_SYSTEM_PROMPT

    user_prompt = f"""
Evaluate the freelancer's early-payment offer.

Invoice:
{json.dumps(invoice, default=str)}

Freelancer offer:
{json.dumps(current_offer, default=str)}

Client preferences:
{json.dumps(client_profile, default=str)}

Decide whether to accept, counter or reject.

If countering, provide the discount you request and
the number of days within which you can pay.

If accepting, accept the freelancer's exact current offer.
Return structured JSON only.
"""

    return call_agent(
        system_prompt,
        user_prompt,
        {"accept", "counter", "reject"},
        agent_function
    )


# ==================================================
# MAIN NEGOTIATION WORKFLOW
# ==================================================

def negotiate_invoice(
    invoice,
    freelancer_policy,
    client_profile,
    max_rounds=3,
    agent_function=None
):
    """
    Run the complete two-agent negotiation.

    Returns a structured result.

    IMPORTANT:
    An agreed deal is NOT a PayPal payment authorization.
    Human approval is always required separately.
    """

    if not isinstance(invoice, dict):
        raise NegotiationError(
            "Invoice must be a dictionary."
        )

    amount = to_decimal(
        invoice.get("amount"),
        "Invoice amount"
    )

    if amount <= 0:
        raise NegotiationError(
            "Invoice amount must be greater than zero."
        )

    days_overdue = invoice.get("days_overdue", 0)

    if (
        isinstance(days_overdue, bool)
        or not isinstance(days_overdue, int)
        or days_overdue < 0
    ):
        raise NegotiationError(
            "Days overdue must be a non-negative integer."
        )

    if not isinstance(client_profile, dict):
        raise NegotiationError(
            "Client profile must be a dictionary."
        )

    if (
        isinstance(max_rounds, bool)
        or not isinstance(max_rounds, int)
        or not 1 <= max_rounds <= 5
    ):
        raise NegotiationError(
            "max_rounds must be between 1 and 5."
        )

    validate_policy(freelancer_policy)

    invoice_data = dict(invoice)
    invoice_data["amount"] = str(amount)

    history = []

    # ----------------------------------------------
    # 1. Freelancer generates the initial offer
    # ----------------------------------------------

    current_offer = freelancer_initial_offer(
        invoice_data,
        freelancer_policy,
        agent_function
    )

    history.append({
        "agent": "Freelancer Agent",
        **current_offer
    })

    # ----------------------------------------------
    # 2. Agents negotiate
    # ----------------------------------------------

    for round_number in range(1, max_rounds + 1):

        client_response = client_evaluate_offer(
            invoice_data,
            current_offer,
            client_profile,
            agent_function
        )

        history.append({
            "agent": "Client Agent",
            "round": round_number,
            **client_response
        })

        # Client accepted the freelancer's offer.
        if client_response["decision"] == "accept":

            final_discount = current_offer["discount_percent"]
            final_days = current_offer["payment_window_days"]

            final_amount = calculate_settlement_amount(
                amount,
                final_discount
            )

            return {
                "status": "agreed",
                "agreement_reached": True,
                "requires_human_approval": True,
                "invoice_amount": str(amount),
                "discount_percent": str(final_discount),
                "payment_window_days": final_days,
                "settlement_amount": str(final_amount),
                "messages": history
            }

        # Client rejected the offer.
        if client_response["decision"] == "reject":

            return {
                "status": "rejected",
                "agreement_reached": False,
                "requires_human_approval": False,
                "invoice_amount": str(amount),
                "discount_percent": None,
                "payment_window_days": None,
                "settlement_amount": None,
                "messages": history
            }

        # ------------------------------------------
        # 3. Freelancer evaluates client's counter
        # ------------------------------------------

        freelancer_response = freelancer_evaluate_counteroffer(
            invoice_data,
            freelancer_policy,
            client_response,
            agent_function
        )

        history.append({
            "agent": "Freelancer Agent",
            "round": round_number,
            **freelancer_response
        })

        decision = freelancer_response["decision"]

        # Freelancer accepts exact client counteroffer.
        if decision == "accept":

            final_discount = client_response["discount_percent"]
            final_days = client_response["payment_window_days"]

            final_amount = calculate_settlement_amount(
                amount,
                final_discount
            )

            return {
                "status": "agreed",
                "agreement_reached": True,
                "requires_human_approval": True,
                "invoice_amount": str(amount),
                "discount_percent": str(final_discount),
                "payment_window_days": final_days,
                "settlement_amount": str(final_amount),
                "messages": history
            }

        # Freelancer rejects or escalates.
        if decision in {"reject", "escalate"}:

            return {
                "status": (
                    "rejected"
                    if decision == "reject"
                    else "escalated"
                ),
                "agreement_reached": False,
                "requires_human_approval": False,
                "invoice_amount": str(amount),
                "discount_percent": None,
                "payment_window_days": None,
                "settlement_amount": None,
                "messages": history
            }

        # ------------------------------------------
        # 4. Freelancer makes a revised offer
        # ------------------------------------------

        current_offer = {
            "decision": "offer",
            "discount_percent": freelancer_response[
                "discount_percent"
            ],
            "payment_window_days": freelancer_response[
                "payment_window_days"
            ],
            "reason": freelancer_response["reason"],
            "message": freelancer_response["message"]
        }

    # ----------------------------------------------
    # 5. Negotiation limit reached
    # ----------------------------------------------

    return {
        "status": "no_agreement",
        "agreement_reached": False,
        "requires_human_approval": False,
        "invoice_amount": str(amount),
        "discount_percent": None,
        "payment_window_days": None,
        "settlement_amount": None,
        "messages": history
    }
