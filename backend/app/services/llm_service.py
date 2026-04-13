import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL  = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def call_llm(prompt: str, max_tokens: int = 500) -> dict:
    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return {"raw_response": response.choices[0].message.content.strip()}
    except Exception as e:
        print("[WARNING] OpenAI Error:", e)
        return {"error": str(e)}