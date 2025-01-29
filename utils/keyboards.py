from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_habit_keyboard(habit_name: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления привычкой"""
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Выполнено", callback_data=f"complete_{habit_name}"),
        InlineKeyboardButton("⏰ Отложить на 1 час", callback_data=f"postpone_{habit_name}")
    )
    return keyboard

def get_frequency_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора частоты привычки"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.row(
        KeyboardButton("Ежедневно"),
        KeyboardButton("Еженедельно")
    )
    keyboard.row(KeyboardButton("Отмена"))
    return keyboard

def get_time_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора времени напоминания"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    times = ["09:00", "12:00", "15:00", "18:00", "21:00"]
    for time in times:
        keyboard.row(KeyboardButton(time))
    keyboard.row(KeyboardButton("Отмена"))
    return keyboard

def get_habit_management_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{habit_id}"),
        InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{habit_id}")
    )
    return keyboard 