import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.db import get_or_create_user, add_habit, get_user_habits

def add_habit(bot: telebot.TeleBot, message):
    user = get_or_create_user(message.from_user.id, message.from_user.username)
    bot.reply_to(message, "Давайте создадим новую привычку! Как назовём?")

def list_habits(bot: telebot.TeleBot, message):
    habits = get_user_habits(message.from_user.id)
    
    if not habits:
        bot.reply_to(message, "У вас пока нет активных привычек.")
        return
        
    response = "Ваши привычки:\n\n"
    for habit in habits:
        response += f"• {habit.name} ({habit.frequency})\n"
    
    bot.reply_to(message, response) 