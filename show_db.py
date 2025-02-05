from database.db import get_session
from database.classes import User, Habit, HabitCompletion

session = get_session()

print("\n=== Пользователи ===")
users = session.query(User).all()
for user in users:
    print(f"ID: {user.id}, Telegram ID: {user.telegram_id}, Username: {user.username}")

print("\n=== Привычки ===")
habits = session.query(Habit).all()
for habit in habits:
    print(f"ID: {habit.id}, Название: {habit.name}, Частота: {habit.frequency}, Время: {habit.reminder_time}, Активна: {habit.is_active}")

print("\n=== Выполнения ===")
completions = session.query(HabitCompletion).all()
for completion in completions:
    print(f"ID: {completion.id}, Привычка ID: {completion.habit_id}, Дата: {completion.completed_at}")

session.close() 