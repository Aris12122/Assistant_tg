import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import matplotlib.pyplot as plt
import io
from database.db import get_user_habits, get_habit_stats
from datetime import datetime, timedelta

def show_progress(bot: telebot.TeleBot, message):
    habits = get_user_habits(message.from_user.id)
    
    if not habits:
        bot.reply_to(message, "У вас пока нет привычек для отслеживания.")
        return
    
    total_completions = 0
    current_streak = 0
    best_streak = 0
    
    for habit in habits:
        completions = get_habit_stats(habit.id)
        total_completions += len(completions)
        # TODO: Подсчет серий выполнения
    
    bot.reply_to(message,
        "📊 Общая статистика:\n"
        f"✅ Выполнено привычек: {total_completions}\n"
        f"📅 Текущая серия: {current_streak} дней\n"
        f"🏆 Лучшая серия: {best_streak} дней"
    )

def show_habit_stats(bot: telebot.TeleBot, call):
    habit_id = int(call.data.split("_")[1])
    
    # Создание графика (пример)
    plt.figure(figsize=(10, 5))
    # Здесь будет построение графика
    
    # Сохранение графика в байтовый поток
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    bot.send_photo(
        call.message.chat.id,
        buf,
        caption="📈 Статистика выполнения привычки за последний месяц"
    ) 