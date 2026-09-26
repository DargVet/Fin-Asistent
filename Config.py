import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODEL_NAME = "openai/gpt-oss-120b"

if not GROQ_API_KEY:
    raise RuntimeError(
        "Не задана переменная окружения GROQ_API_KEY. "
        "Проверь файл .env в корне проекта."
    )