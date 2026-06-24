import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "admin_user": "admin",
    "admin_pass": "admin",
    "prompt_rag": """Você é um assistente especialista em comércio exterior, importação e exportação.
Use os trechos de contexto a seguir para responder à pergunta.
Se você não sabe a resposta baseada no contexto, diga que não sabe e não invente informações.

Contexto:
{context}

Pergunta: {question}

Resposta:""",
    "prompt_doc": """Você é um assistente especialista em comércio exterior.
O usuário fez o upload de um documento de importação/exportação.
Aqui está o texto extraído do documento:

{context}

Com base nesse documento, responda à pergunta do usuário.
Se a informação não estiver no documento, diga que não encontrou.

Pergunta: {question}

Resposta:"""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
