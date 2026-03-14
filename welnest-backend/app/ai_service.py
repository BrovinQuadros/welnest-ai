import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Read API configuration
api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")

print("NVIDIA_API_KEY Loaded:", bool(api_key))
print("NVIDIA_BASE_URL:", base_url)

# Initialize AI client safely
client = None
if api_key:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
else:
    print("⚠️ WARNING: NVIDIA_API_KEY not found. AI disabled.")


# System prompt for the AI
SYSTEM_PROMPT = (
    "You are WellNest AI, a supportive mental health companion. "
    "Respond empathetically and briefly. "
    "You are not a medical professional."
)


def summarize_text(text: str) -> str:
    """
    Generate an AI response for journal entries.
    Always returns a safe string.
    """

    # If AI not configured
    if client is None:
        return "AI service is not configured properly."

    try:
        if not text or not text.strip():
            return "I’m here with you. Feel free to share whatever you’re feeling."

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text.strip()}
            ],
            max_tokens=200,
            temperature=0.7
        )

        if completion.choices:
            return completion.choices[0].message.content.strip()

        return "Thank you for sharing. I’m here to support you."

    except Exception as e:
        import traceback
        print("========== AI ERROR ==========")
        print(repr(e))
        traceback.print_exc()
        print("================================")

        return "AI service temporarily unavailable."