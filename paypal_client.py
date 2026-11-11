import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
_token = {"value": None, "expires_at": 0}


def _check(r):
    if not r.ok:
        raise RuntimeError(f"PayPal error {r.status_code}: {r.text}")
    return r


def get_token():
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]
    r = _check(requests.post(
        f"{BASE}/v1/oauth2/token",
        auth=(os.getenv("PAYPAL_CLIENT_ID"), os.getenv("PAYPAL_CLIENT_SECRET")),
        data={"grant_type": "client_credentials"},
        timeout=30,
    ))
    d = r.json()
    _token["value"] = d["access_token"]
    _token["expires_at"] = time.time() + d["expires_in"]
    return _token["value"]


def _headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}


def create_invoice(client_email, item_name, amount, note=""):
    body = {
        "detail": {
            "invoice_number": f"SETTLE-{int(time.time())}",
            "currency_code": "USD",
            "note": note,
        },
        "invoicer": {"email_address": os.getenv("PAYPAL_BUSINESS_EMAIL")},
        "primary_recipients": [{"billing_info": {"email_address": client_email}}],
        "items": [{
            "name": item_name,
            "quantity": "1",
            "unit_amount": {"currency_code": "USD", "value": f"{amount:.2f}"},
        }],
    }
    r = _check(requests.post(f"{BASE}/v2/invoicing/invoices", json=body, headers=_headers(), timeout=30))
    data = r.json()
    return data.get("id") or data["href"].rstrip("/").split("/")[-1]


def send_invoice(invoice_id):
    body = {"send_to_recipient": True, "send_to_invoicer": True}
    _check(requests.post(f"{BASE}/v2/invoicing/invoices/{invoice_id}/send", json=body, headers=_headers(), timeout=30))


def get_invoice(invoice_id):
    return _check(requests.get(f"{BASE}/v2/invoicing/invoices/{invoice_id}", headers=_headers(), timeout=30)).json()