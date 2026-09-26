from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as IKB


def _back(cb: str) -> list[IKB]:
    return [IKB(text="⬅️ Назад", callback_data=cb)]


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="💰 Доходы", callback_data="inc_m"),       IKB(text="💸 Расходы", callback_data="exp_m")],
        [IKB(text="📊 Общая информация", callback_data="info"), IKB(text="🏦 Накопить", callback_data="sav_m")],
        [IKB(text="🔄 Обновить баланс", callback_data="bal"), IKB(text="📜 История", callback_data="hist_m")],
        [IKB(text="⚙️ Настройки", callback_data="set_m")],
    ])


def prompt_kb(back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[*_back(back_cb)]])


# ── Доходы ───────────────────────────────────────────────────────────────────

def income_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="📌 Постоянные", callback_data="inc_r"), IKB(text="⚡️ Разовые", callback_data="inc_i")],
        [*_back("mm")],
    ])


def income_regular_kb(items) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(items), 2):
        row = [IKB(text=items[i].source, callback_data=f"inc_sel_{items[i].id}")]
        if i + 1 < len(items):
            row.append(IKB(text=items[i + 1].source, callback_data=f"inc_sel_{items[i + 1].id}"))
        rows.append(row)
    rows.append([IKB(text="➕ Новая категория", callback_data="inc_new")])
    rows.append([*_back("inc_m")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def income_item_kb(income_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="✏️ Изменить сумму", callback_data=f"inc_upd_{income_id}"),
         IKB(text="🗑 Удалить", callback_data=f"inc_del_{income_id}")],
        [*_back("inc_r")],
    ])


def income_irregular_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="➕ Добавить", callback_data="inc_i_add")],
        [*_back("inc_m")],
    ])


# ── Расходы ───────────────────────────────────────────────────────────────────

def expense_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="📌 Постоянные", callback_data="exp_r"), IKB(text="⚡️ Разовые", callback_data="exp_i")],
        [*_back("mm")],
    ])


def expense_regular_kb(items) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(items), 2):
        row = [IKB(text=items[i].name, callback_data=f"exp_sel_{items[i].id}")]
        if i + 1 < len(items):
            row.append(IKB(text=items[i + 1].name, callback_data=f"exp_sel_{items[i + 1].id}"))
        rows.append(row)
    rows.append([IKB(text="➕ Новая категория", callback_data="exp_new")])
    rows.append([*_back("exp_m")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def expense_item_kb(expense_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="✏️ Изменить сумму", callback_data=f"exp_upd_{expense_id}"),
         IKB(text="🗑 Удалить", callback_data=f"exp_del_{expense_id}")],
        [*_back("exp_r")],
    ])


def expense_irregular_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="➕ Добавить", callback_data="exp_i_add")],
        [*_back("exp_m")],
    ])


# ── Накопления ────────────────────────────────────────────────────────────────

def savings_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="🎯 Ввести цель", callback_data="sav_new"),
         IKB(text="📊 Посмотреть", callback_data="sav_view")],
        [IKB(text="➕ Пополнить", callback_data="sav_add"),
         IKB(text="🗑 Удалить цель", callback_data="sav_del")],
        [*_back("mm")],
    ])


def goals_list_kb(goals, action: str) -> InlineKeyboardMarkup:
    rows = [
        [IKB(text=f"{g.name} ({float(g.current_amount):,.0f} / {float(g.target_amount):,.0f} ₽)",
             callback_data=f"sav_{action}_{g.id}")]
        for g in goals
    ]
    rows.append([*_back("sav_m")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_goal_kb(goal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="✅ Да, удалить", callback_data=f"sav_del_ok_{goal_id}"),
         IKB(text="❌ Отмена", callback_data="sav_m")],
    ])


# ── История / Настройки ───────────────────────────────────────────────────────

def history_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="📅 Сегодня", callback_data="hist_t"),
         IKB(text="📆 Неделя", callback_data="hist_w")],
        [IKB(text="🗓 Месяц", callback_data="hist_mo")],
        [*_back("mm")],
    ])


def settings_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="🗑 Очистить все данные", callback_data="set_clr")],
        [*_back("mm")],
    ])


def confirm_clear_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [IKB(text="✅ Да, очистить", callback_data="set_clr_ok"),
         IKB(text="❌ Отмена", callback_data="set_m")],
    ])


def back_only_kb(back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[*_back(back_cb)]])
