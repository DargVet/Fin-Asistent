# Финансовый ассистент — Telegram бот

AI-помощник по личным финансам для студентов. Отвечает на вопросы «Могу ли я потратить N рублей?», «Хватит ли денег до конца месяца?» и анализирует бюджет.

## Стек

- **LLM** — Groq API (gpt-oss-120b)
- **Бот** — aiogram 3
- **База данных** — PostgreSQL + SQLAlchemy (async) + Alembic
- **Планировщик** — APScheduler

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <url>
cd Fin-Asistent
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Создать файл `.env`

```env
GROQ_API_KEY=your_groq_api_key
BOT_TOKEN=your_telegram_bot_token

DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fin_assist
```

- **GROQ_API_KEY** — получить на [console.groq.com](https://console.groq.com)
- **BOT_TOKEN** — получить у [@BotFather](https://t.me/BotFather) в Telegram

### 4. Создать базу данных

В PostgreSQL создай базу с именем `fin_assist`:

```sql
CREATE DATABASE fin_assist;
```

### 5. Применить миграции

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 6. Запустить бота

```bash
python -m bot.main
```

## Структура проекта

```
├── ai/              # LLM-ядро: клиент, промпты, guardrails, tool calling
├── bot/             # Telegram бот (aiogram)
│   ├── handlers/    # /start, /setup, /goals, AI-чат
│   ├── keyboards/   # Клавиатуры
│   └── middlewares/ # DB-сессия на каждый апдейт
├── core/            # Конфигурация
├── db/              # SQLAlchemy модели и репозитории
├── migrations/      # Alembic
├── scheduler/       # APScheduler задачи
└── services/        # Бизнес-логика
```

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Начало работы |
| `/setup` | Настроить баланс, доходы и расходы |
| `/goals` | Список финансовых целей |
| `/add_goal` | Добавить цель |
