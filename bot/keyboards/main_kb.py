from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💬 Спросить ассистента")],
        [KeyboardButton(text="📊 Моя ситуация"), KeyboardButton(text="🎯 Цели")],
        [KeyboardButton(text="⚙️ Настроить данные")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Задай вопрос или выбери действие",
)
