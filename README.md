# Settle

**AI agents that negotiate early-payment discounts on freelancer invoices, then settle them through PayPal.**

Built for the PayPal AI Hackathon (Devpost).

## The problem

Freelancers often wait weeks for payment and hate chasing clients. Large companies use "early-payment discounts" to solve this, but small freelancers have no tool for it.

## What Settle does

1. A **Freelancer agent** proposes an early-payment discount on an unpaid invoice.
2. A **Client agent** accepts, counters, or rejects, according to the client's own policy.
3. Python code, not the AI, enforces the money rules (maximum discount, payment window, round limits).
4. The freelancer must **explicitly approve** the final deal. The AI never moves money on its own.
5. After approval, Settle creates and sends a real **PayPal Sandbox invoice** for the settled amount, and tracks its status until it is paid.
6. Every step is written to an action log.

Settle is **not** an escrow service. PayPal does not hold money conditionally here; the invoice is a normal PayPal invoice.

## Tech stack

- Python and Streamlit (UI)
- Ollama with Qwen 2.5 3B (local LLM for the two agents)
- PayPal Invoicing REST API (Sandbox) with OAuth 2.0
- python-dotenv and requests
- unittest (negotiation logic tests)

## What is real and what is simulated

**Real**
- Two LLM agents generating negotiation messages locally with Qwen 2.5 3B
- Money calculations and limits enforced in Python
- Human approval before any invoice is created
- PayPal Sandbox: OAuth token, invoice creation, sending, and status checks. An invoice was created, sent, paid from a sandbox buyer account, and confirmed as PAID through the API.
- 11 unit tests for the negotiation logic

**Simulated (demo data)**
- The five invoices on the dashboard are hard-coded sample data, not the user's real PayPal invoices
- The late-payment risk score is a simple heuristic formula, not a trained ML model
- Client policies are simulated
- All invoices are sent to a single sandbox test buyer account

**Not built yet (future work)**
- Persistent database (state currently lives in the Streamlit session)
- Loading the freelancer's real PayPal invoice portfolio
- Webhooks for automatic payment updates
- Stronger validation of model output, retries, and a model evaluation benchmark
- A hosted deployment

## Known limitations

- The 3B model sometimes gives short or off-target messages. Money decisions do not depend on the model's wording.
- Client-side minimum-discount enforcement is still being hardened.
- PayPal does not allow sending invoices to customers inside India, so the sandbox buyer account must be a non-India (for example US) account.

## How to run it

**Requirements:** Python 3.10 or newer, [Ollama](https://ollama.com), a free PayPal Developer account.

1. Clone the repository and open the folder.
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install the packages:
   ```
   python -m pip install -r requirements.txt
   ```
4. Download the model once:
   ```
   ollama pull qwen2.5:3b
   ```
5. Create a PayPal sandbox setup:
   - Go to developer.paypal.com, switch to **Sandbox**
   - Under **Apps & Credentials**, use (or create) an app and copy its Client ID and Secret
   - Under **Testing Tools > Sandbox Accounts**, use a Business account (seller) and create a **US Personal** account (buyer)
6. Copy `.env.example` to `.env` and fill in your own sandbox values. Never commit `.env`.
7. Start the app:
   ```
   python -m streamlit run app.py
   ```

## Try the demo

1. Pick **Acme Studio - Logo design ($800)** and click **Approve & send offer**.
2. Watch the two agents negotiate. A settled deal shows the discounted amount.
3. Click **Create & send PayPal invoice**.
4. Open the client payment page, log in with the US sandbox buyer account, and pay.
5. Back in the app, click **Refresh payment status** to see **PAID**.

## Run the tests

```
python -m unittest discover -s tests -p "test_*.py" -v
```

The tests use simulated AI responses to check the negotiation rules (limits, rejection, round limits, invalid input). They do not call the model or PayPal.

## Security notes

- Only PayPal **Sandbox** is used. No real money moves.
- Secrets live in `.env`, which is git-ignored. Use `.env.example` as a template.

## AI assistance disclosure

This project was developed with the help of AI coding assistants (ChatGPT and Claude). I reviewed, ran, and tested the code, and I am responsible for the final submission.

## License

MIT