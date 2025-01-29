import telebot
import logging
from config.config import TOKEN, ADMIN_IDS
from handlers import habit_handlers, reminder_handlers, stats_handlers
from database.db import get_or_create_user, add_habit, get_user_habits, get_session, get_habit_stats, delete_habit, add_test_completions
from utils.keyboards import get_frequency_keyboard, get_time_keyboard, get_habit_management_keyboard
from utils.scheduler import HabitScheduler
from database.classes import Habit
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота и планировщика
bot = telebot.TeleBot(TOKEN)
scheduler = HabitScheduler(bot)

# Словарь для хранения временных данных при создании привычки
user_states = {}

# Базовые хендлеры
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    logging.info(f"Бот запущен пользователем с ID: {user_id}")
    
    # Создаем пользователя в БД при первом запуске
    get_or_create_user(message.from_user.id, message.from_user.username)
    
    bot.reply_to(message, 
        f"Привет, <b>{message.from_user.full_name}</b>!\n"
        f"Ваш Telegram ID: {user_id}\n"
        "Я бот для отслеживания привычек. Вот что я умею:\n"
        "/addhabit - Добавить новую привычку\n"
        "/habits - Посмотреть список привычек\n"
        "/progress - Посмотреть статистику",
        parse_mode='HTML'
    )

# Обработчики создания привычки
@bot.message_handler(commands=['addhabit'])
def add_habit_start(message):
    user_states[message.from_user.id] = {'state': 'waiting_name'}
    bot.reply_to(message, "Давайте создадим новую привычку! Как назовём?")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_name')
def handle_habit_name(message):
    user_states[message.from_user.id].update({
        'state': 'waiting_frequency',
        'name': message.text
    })
    bot.reply_to(message, 
        "Выберите частоту привычки:",
        reply_markup=get_frequency_keyboard()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_frequency')
def handle_habit_frequency(message):
    if message.text not in ["Ежедневно", "Еженедельно", "Отмена"]:
        bot.reply_to(message, "Пожалуйста, выберите один из предложенных вариантов.")
        return

    if message.text == "Отмена":
        del user_states[message.from_user.id]
        bot.reply_to(message, "Создание привычки отменено.", reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    user_states[message.from_user.id].update({
        'state': 'waiting_time',
        'frequency': message.text
    })
    bot.reply_to(message, 
        "Выберите время для напоминаний:",
        reply_markup=get_time_keyboard()
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_time')
def handle_habit_time(message):
    if message.text == "Отмена":
        del user_states[message.from_user.id]
        bot.reply_to(message, "Создание привычки отменено.", reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    state = user_states[message.from_user.id]
    
    # Сохраняем привычку в БД
    habit = add_habit(
        message.from_user.id,
        state['name'],
        state['frequency'],
        message.text
    )
    
    # Планируем напоминание
    scheduler.schedule_habit(habit)
    
    del user_states[message.from_user.id]
    
    bot.reply_to(message, 
        f"✅ Привычка '{state['name']}' успешно создана!\n"
        f"📅 Частота: {state['frequency']}\n"
        f"⏰ Время напоминания: {message.text}",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

# Просмотр списка привычек
@bot.message_handler(commands=['habits'])
def list_habits(message):
    habits = get_user_habits(message.from_user.id)
    
    if not habits:
        bot.reply_to(message, "У вас пока нет активных привычек.")
        return
        
    for habit in habits:
        habit_text = (
            f"🔷 <b>{habit.name}</b>\n"
            f"📅 Частота: {habit.frequency}\n"
            f"⏰ Время: {habit.reminder_time}"
        )
        bot.send_message(
            message.chat.id,
            habit_text,
            parse_mode='HTML',
            reply_markup=get_habit_management_keyboard(habit.id)
        )

# Регистрация обработчиков callback
@bot.callback_query_handler(func=lambda call: call.data.startswith('complete_'))
def complete_callback(call):
    reminder_handlers.handle_completion(bot, call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('postpone_'))
def postpone_callback(call):
    reminder_handlers.handle_postpone(bot, call)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = (
        "🤖 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/addhabit - Добавить новую привычку\n"
        "/habits - Посмотреть список привычек\n"
        "/progress - Посмотреть статистику привычек\n"
        "/help - Показать это сообщение\n\n"
        "<b>Как пользоваться ботом:</b>\n"
        "1. Создайте новую привычку командой /addhabit\n"
        "2. Выберите частоту напоминаний\n"
        "3. Установите время для напоминаний\n"
        "4. Отмечайте выполнение привычки по напоминаниям\n"
        "5. Отслеживайте прогресс командой /progress"
    )
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(commands=['progress'])
def show_progress(message):
    habits = get_user_habits(message.from_user.id)
    
    if not habits:
        bot.reply_to(message, "У вас пока нет привычек для отслеживания.")
        return

    # Общая статистика
    total_habits = len(habits)
    total_completions = 0
    current_streak = 0
    best_streak = 0

    # Создаем график
    plt.figure(figsize=(10, 6))
    plt.title("Выполнение привычек за последние 30 дней")
    
    for habit in habits:
        completions = get_habit_stats(habit.id)
        total_completions += len(completions)
        
        # Данные для графика
        dates = [c.completed_at.date() for c in completions]
        if dates:
            plt.plot(dates, [1] * len(dates), 'o', label=habit.name)

    plt.xlabel("Дата")
    plt.ylabel("Выполнение")
    plt.legend()
    plt.grid(True)

    # Сохраняем график
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Отправляем статистику и график
    stats_text = (
        "📊 <b>Общая статистика:</b>\n"
        f"📝 Всего привычек: {total_habits}\n"
        f"✅ Выполнено раз: {total_completions}\n"
        f"🔥 Текущая серия: {current_streak} дней\n"
        f"🏆 Лучшая серия: {best_streak} дней\n\n"
        "График выполнения привычек за последние 30 дней:"
    )
    
    bot.send_photo(
        message.chat.id,
        buf,
        caption=stats_text,
        parse_mode='HTML'
    )

# Добавим обработчик для удаления привычки
@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_habit(call):
    habit_id = int(call.data.split('_')[1])
    
    # Подтверждение удаления
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{habit_id}"),
        InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_delete_{habit_id}")
    )
    
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_'))
def handle_confirm_delete(call):
    habit_id = int(call.data.split('_')[2])
    
    if delete_habit(habit_id):
        # Отменяем напоминания
        scheduler.stop_habit(habit_id)
        
        bot.edit_message_text(
            "❌ Привычка удалена",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "Ошибка удаления привычки")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_delete_'))
def handle_cancel_delete(call):
    habit_id = int(call.data.split('_')[2])
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_habit_management_keyboard(habit_id)
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Бот запущен")
    
    # Временно: добавляем тестовые данные
    add_test_completions()
    
    try:
        # Инициализация напоминаний для существующих привычек
        session = get_session()
        habits = session.query(Habit).filter_by(is_active=True).all()
        for habit in habits:
            try:
                scheduler.schedule_habit(habit)
            except Exception as e:
                logging.error(f"Ошибка планирования привычки {habit.id}: {e}")
        session.close()
        
        # Запуск бота
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        scheduler.stop_all() 