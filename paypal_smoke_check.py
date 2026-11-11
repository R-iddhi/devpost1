import os
from dotenv import load_dotenv
from paypal_client import create_invoice, send_invoice, get_invoice

load_dotenv()

inv_id = create_invoice(
    os.getenv("CLIENT_TEST_EMAIL"),
    "Logo design (early-pay settlement)",
    760,
    "5% early-payment discount",
)
print("Draft created:", inv_id)
send_invoice(inv_id)
print("Status:", get_invoice(inv_id)["status"])