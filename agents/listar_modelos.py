import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

import os, requests
from dotenv import load_dotenv
load_dotenv()

r = requests.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {os.getenv('LLM_API_KEY')}"},
    timeout=30,
)
print("status:", r.status_code)
for m in sorted(x["id"] for x in r.json()["data"]):
    print(" ", m)