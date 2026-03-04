import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from backend root
load_dotenv()

# Read variables
api_key = os.getenv("NVIDIA_API_KEY")
base_url = os.getenv("NVIDIA_BASE_URL")

print("NVIDIA_API_KEY Loaded:", bool(api_key))
print("NVIDIA_BASE_URL:", base_url)

# If API key missing, do NOT crash backend
if not api_key:
    print("⚠️ WARNING: NVIDIA_API_KEY not found. AI disabled.")
    client = None
else:
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

SYSTEM_PROMPT = (
    "You are WellNest AI, a supportive mental health companion. "
    "Respond empathetically and briefly. "
    "You are not a medical professional."
)


def summarize_text(text: str) -> str:
    """
    Calls NVIDIA/OpenAI model.
    Always returns safe string.
    """

    # If API not configured
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

        if completion.choices and len(completion.choices) > 0:
            return completion.choices[0].message.content.strip()

        return "Thank you for sharing. I’m here to support you."

    except Exception as e:
        import traceback
        print("========== AI ERROR ==========")
        print(repr(e))
        traceback.print_exc()
        print("================================")
        return "AI service failed"
