import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# 1. Load environment variables
load_dotenv()

# 2. Verify API Key
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY not found in .env file.")

def get_model():
    """
    Returns the configured Anthropic LLM.
    """
    return ChatAnthropic(
        model="claude-3-haiku-20240307",  # <--- The model we proved works
        temperature=0, 
        max_tokens=4096
    )