"""
Lista os modelos disponiveis na chave de API configurada em LLM_API_KEY.

Util sempre que um modelo usado no projeto sai de catalogo: ja aconteceu duas
vezes com modelos do Groq (meta/llama-3.3-70b-instruct e openai/gpt-oss-120b,
descontinuados com poucos dias de diferenca). Chama a API REST direto, sem
passar pelo langchain_openai, porque o objetivo aqui e so ver a lista.
"""

import os
import requests
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
