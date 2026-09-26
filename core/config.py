import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
MODEL_NAME: str = "openai/gpt-oss-120b"

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
# DATABASE_URL собирается из отдельных переменных
_db_user = os.environ.get("DB_USER", "postgres")
_db_password = os.environ.get("DB_PASSWORD", "postgres")
_db_host = os.environ.get("DB_HOST", "localhost")
_db_port = os.environ.get("DB_PORT", "5432")
_db_name = os.environ.get("DB_NAME", "fin_assist")

DATABASE_URL: str = (
    os.environ.get("DATABASE_URL")
    or f"postgresql+asyncpg://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
)

if not GROQ_API_KEY:
    raise RuntimeError(
        "Не задана переменная окружения GROQ_API_KEY. "
        "Проверь файл .env в корне проекта."
    )

if not BOT_TOKEN:
    raise RuntimeError(
        "Не задана переменная окружения BOT_TOKEN. "
        "Проверь файл .env в корне проекта."
    )
