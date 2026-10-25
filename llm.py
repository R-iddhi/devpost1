import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


def ask_llm(system_prompt, user_prompt, temperature=0.7):
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


if __name__ == "__main__":
    print(ask_llm(
        "You are a polite assistant for a freelancer. Reply in 2 short sentences.",
        "Write a message to client Acme Studio offering a 5% discount on an $800 invoice if paid within 3 days.",
    ))