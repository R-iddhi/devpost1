
"""
Settle - Automated Negotiation Engine Tests

These tests use simulated AI responses.
They do not call Ollama or PayPal.
"""

import unittest

from negotiation_engine import (
    negotiate_invoice,
    calculate_settlement_amount,
    NegotiationError,
)


# --------------------------------------------------
# TEST DATA
# --------------------------------------------------

INVOICE = {
    "client": "Acme Studio",
    "project": "Logo Design",
    "amount": 800,
    "days_overdue": 12,
}

FREELANCER_POLICY = {
    "max_discount_percent": 6,
    "min_payment_window_days": 1,
    "max_payment_window_days": 3,
}

CLIENT_PROFILE = {
    "preferred_discount_percent": 4,
    "preferred_payment_window_days": 3,
}


# --------------------------------------------------
# SIMULATED AI RESPONSES
# --------------------------------------------------

def make_response(
    decision,
    discount,
    days=3,
    reason="Test negotiation decision.",
    message="Test negotiation message.",
):
    return {
        "decision": decision,
        "discount_percent": discount,
        "payment_window_days": days,
        "reason": reason,
        "message": message,
    }


def mock_agent(*responses):
    """
    Returns simulated AI responses in sequence.

    Each call to this function represents one agent response.
    """

    response_queue = list(responses)

    def fake_ai(
        system_prompt,
        user_prompt,
        response_schema,
        temperature=0.1,
    ):
        if not response_queue:
            raise AssertionError(
                "Unexpected additional AI call."
            )

        return response_queue.pop(0)

    return fake_ai


# --------------------------------------------------
# TEST 1: INITIAL OFFER ACCEPTED
# --------------------------------------------------

class NegotiationWorkflowTests(unittest.TestCase):

    def test_client_accepts_initial_offer(self):

        ai = mock_agent(
            make_response("offer", 5),
            make_response("accept", 5),
        )

        result = negotiate_invoice(
            INVOICE,
            FREELANCER_POLICY,
            CLIENT_PROFILE,
            agent_function=ai,
        )

        self.assertEqual(result["status"], "agreed")
        self.assertTrue(result["agreement_reached"])
        self.assertTrue(result["requires_human_approval"])

        self.assertEqual(
            result["settlement_amount"],
            "760.00",
        )

        self.assertEqual(
            result["discount_percent"],
            "5",
        )


# --------------------------------------------------
# TEST 2: CLIENT COUNTEROFFER ACCEPTED
# --------------------------------------------------

    def test_freelancer_accepts_client_counteroffer(self):

        ai = mock_agent(
            make_response("offer", 5),

            make_response("counter", 4),

            make_response("accept", 5),
        )

        result = negotiate_invoice(
            INVOICE,
            FREELANCER_POLICY,
            CLIENT_PROFILE,
            agent_function=ai,
        )

        self.assertEqual(result["status"], "agreed")

        # The accepted terms must be the client's
        # exact counteroffer, not another AI-generated value.

        self.assertEqual(
            result["discount_percent"],
            "4",
        )

        self.assertEqual(
            result["settlement_amount"],
            "768.00",
        )


# --------------------------------------------------
# TEST 3: CLIENT REJECTS OFFER
# --------------------------------------------------

    def test_client_rejects_offer(self):

        ai = mock_agent(
            make_response("offer", 5),
            make_response("reject", 0),
        )

        result = negotiate_invoice(
            INVOICE,
            FREELANCER_POLICY,
            CLIENT_PROFILE,
            agent_function=ai,
        )

        self.assertEqual(result["status"], "rejected")
        self.assertFalse(result["agreement_reached"])

        self.assertIsNone(
            result["settlement_amount"]
        )


# --------------------------------------------------
# TEST 4: DISCOUNT EXCEEDS FREELANCER LIMIT
# --------------------------------------------------

    def test_blocks_excessive_initial_discount(self):

        ai = mock_agent(
            make_response("offer", 8),
        )

        with self.assertRaises(NegotiationError):

            negotiate_invoice(
                INVOICE,
                FREELANCER_POLICY,
                CLIENT_PROFILE,
                agent_function=ai,
            )


# --------------------------------------------------
# TEST 5: CLIENT ASKS FOR EXCESSIVE DISCOUNT
# --------------------------------------------------

    def test_freelancer_can_escalate_excessive_counteroffer(self):

        ai = mock_agent(
            make_response("offer", 5),

            make_response("counter", 8),

            make_response("escalate", 8),
        )

        result = negotiate_invoice(
            INVOICE,
            FREELANCER_POLICY,
            CLIENT_PROFILE,
            agent_function=ai,
        )

        self.assertEqual(result["status"], "escalated")

        self.assertFalse(
            result["agreement_reached"]
        )


# --------------------------------------------------
# TEST 6: NEGOTIATION ROUND LIMIT
# --------------------------------------------------

    def test_negotiation_stops_after_round_limit(self):

        ai = mock_agent(
            make_response("offer", 5),

            make_response("counter", 4),

            make_response("counter", 5),
        )

        result = negotiate_invoice(
            INVOICE,
            FREELANCER_POLICY,
            CLIENT_PROFILE,
            max_rounds=1,
            agent_function=ai,
        )

        self.assertEqual(
            result["status"],
            "no_agreement",
        )

        self.assertFalse(
            result["agreement_reached"]
        )


# --------------------------------------------------
# TEST 7: INVALID INVOICE AMOUNT
# --------------------------------------------------

    def test_rejects_invalid_invoice_amount(self):

        invalid_invoice = {
            **INVOICE,
            "amount": -800,
        }

        ai = mock_agent()

        with self.assertRaises(NegotiationError):

            negotiate_invoice(
                invalid_invoice,
                FREELANCER_POLICY,
                CLIENT_PROFILE,
                agent_function=ai,
            )


# --------------------------------------------------
# TEST 8: INVALID FREELANCER POLICY
# --------------------------------------------------

    def test_rejects_invalid_discount_policy(self):

        invalid_policy = {
            "max_discount_percent": 150,
            "min_payment_window_days": 1,
            "max_payment_window_days": 3,
        }

        ai = mock_agent()

        with self.assertRaises(NegotiationError):

            negotiate_invoice(
                INVOICE,
                invalid_policy,
                CLIENT_PROFILE,
                agent_function=ai,
            )


# --------------------------------------------------
# TEST 9: FINANCIAL CALCULATION
# --------------------------------------------------

class FinancialCalculationTests(unittest.TestCase):

    def test_eight_hundred_at_five_percent(self):

        result = calculate_settlement_amount(
            800,
            5,
        )

        self.assertEqual(
            str(result),
            "760.00",
        )

    def test_eight_hundred_at_four_percent(self):

        result = calculate_settlement_amount(
            800,
            4,
        )

        self.assertEqual(
            str(result),
            "768.00",
        )

    def test_rejects_negative_discount(self):

        with self.assertRaises(NegotiationError):

            calculate_settlement_amount(
                800,
                -5,
            )


# --------------------------------------------------
# RUN TESTS
# --------------------------------------------------

if __name__ == "__main__":

    unittest.main(verbosity=2)
