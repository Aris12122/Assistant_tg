import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import time
from utils.keyboards import get_habit_keyboard
import logging

def send_reminder(bot: telebot.TeleBot, user_id: int, habit_name: str):
    keyboard = get_habit_keyboard(habit_name)
    try:
        bot.send_message(
            user_id,
            f"🔔 Напоминание: пора выполнить привычку '{habit_name}'!",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Ошибка отправки напоминания: {e}")

def handle_completion(bot: telebot.TeleBot, call):
    habit_name = call.data.split("_")[1]
    # Здесь будет логика сохранения выполнения в БД
    bot.edit_message_text(
        f"✅ Отлично! Привычка '{habit_name}' отмечена как выполненная!",
        call.message.chat.id,
        call.message.message_id
    )

def handle_postpone(bot: telebot.TeleBot, call):
    habit_name = call.data.split("_")[1]
    # Здесь будет логика переноса напоминания
    bot.edit_message_text(
        f"⏰ Хорошо, я напомню о '{habit_name}' через час",
        call.message.chat.id,
        call.message.message_id
    ) 