
"""
Settle - Local LLM Integration

Supports:
1. Normal text responses from Ollama.
2. Structured JSON responses using JSON Schema.
3. Configurable local models.
4. Error handling for unavailable models and invalid responses.

Default model: qwen2.5:3b
"""

import os
import json
import requests

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

OLLAMA_URL = (
    os.getenv("OLLAMA_BASE_URL")
    or os.getenv("OLLAMA_URL")
    or "http://localhost:11434"
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b"
)


# --------------------------------------------------
# CUSTOM ERROR
# --------------------------------------------------

class LLMResponseError(Exception):
    """Raised when Ollama fails or returns an invalid response."""


# --------------------------------------------------
# INTERNAL OLLAMA REQUEST
# --------------------------------------------------

def _send_request(payload, timeout=120):
    """
    Send a chat request to the local Ollama server.
    """

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=timeout
        )

        response.raise_for_status()

    except requests.exceptions.Timeout as exc:
        raise LLMResponseError(
            "Ollama request timed out. Try again or check your model."
        ) from exc

    except requests.exceptions.ConnectionError as exc:
        raise LLMResponseError(
            "Cannot connect to Ollama. Make sure Ollama is running."
        ) from exc

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "Unknown"

        details = ""
        if exc.response is not None:
            details = exc.response.text[:500]

        raise LLMResponseError(
            f"Ollama returned HTTP {status}: {details}"
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise LLMResponseError(
            f"Ollama request failed: {exc}"
        ) from exc

    try:
        data = response.json()
        content = data["message"]["content"]

    except (ValueError, KeyError, TypeError) as exc:
        raise LLMResponseError(
            "Ollama returned an unexpected response format."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMResponseError(
            "Ollama returned an empty response."
        )

    return content.strip()


# --------------------------------------------------
# NORMAL TEXT RESPONSE
# --------------------------------------------------

def ask_llm(
    system_prompt,
    user_prompt,
    temperature=0.7,
    timeout=120
):
    """
    Generate a normal text response using Ollama.

    This maintains compatibility with the existing Settle app.
    """

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        "stream": False,

        "options": {
            "temperature": temperature
        }
    }

    return _send_request(
        payload,
        timeout=timeout
    )


# --------------------------------------------------
# STRUCTURED JSON RESPONSE
# --------------------------------------------------

def ask_llm_json(
    system_prompt,
    user_prompt,
    response_schema,
    temperature=0.1,
    timeout=120
):
    """
    Generate a structured JSON response using Ollama.

    response_schema must be a valid JSON Schema.

    This function is used by Settle's AI negotiation agents.
    """

    if not isinstance(response_schema, dict):
        raise ValueError(
            "response_schema must be a dictionary containing JSON Schema."
        )

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    system_prompt
                    + "\nReturn a response matching the supplied JSON schema."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        "stream": False,

        "format": response_schema,

        "options": {
            "temperature": temperature
        }
    }

    content = _send_request(
        payload,
        timeout=timeout
    )

    try:
        result = json.loads(content)

    except json.JSONDecodeError as exc:
        raise LLMResponseError(
            "Ollama did not return valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise LLMResponseError(
            "Expected a JSON object from Ollama."
        )

    return result


# --------------------------------------------------
# LOCAL TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("Settle LLM connection test")
    print("--------------------------")

    print(f"Model: {OLLAMA_MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")

    try:
        result = ask_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Reply with: Settle AI connection successful.",
            temperature=0.1
        )

        print("\nModel response:")
        print(result)

    except LLMResponseError as error:
        print("\nConnection error:")
        print(error)
