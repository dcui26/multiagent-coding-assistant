import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

key = os.getenv("ANTHROPIC_API_KEY")
print(f"Key loaded: {key[:10]}... (Check if this looks right)")

client = anthropic.Anthropic(api_key=key)

try:
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("✅ SUCCESS! API is working.")
    print(message.content)
except Exception as e:
    print(f"❌ ERROR: {e}")