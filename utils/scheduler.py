import schedule
import threading
import time
from datetime import datetime
from database.classes import Habit
from database.db import get_session
from typing import Dict

class HabitScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.jobs: Dict[int, schedule.Job] = {}  # habit_id -> job
        self.running = True
        self.thread = threading.Thread(target=self._run_continuously)
        self.thread.start()

    def schedule_habit(self, habit: Habit):
        session = get_session()
        try:
            # Получаем свежую копию привычки из БД
            habit = session.merge(habit)
            
            habit_id = habit.id
            user_id = habit.user.telegram_id  # Сохраняем ID пользователя
            habit_name = habit.name  # Сохраняем имя привычки
            
            # Отменяем существующее напоминание, если есть
            if habit_id in self.jobs:
                schedule.cancel_job(self.jobs[habit_id])

            # Создаем функцию напоминания с сохраненными значениями
            def reminder_job():
                from handlers.reminder_handlers import send_reminder
                send_reminder(self.bot, user_id, habit_name)

            # Планируем напоминание в зависимости от частоты
            if habit.frequency == "Ежедневно":
                job = schedule.every().day.at(habit.reminder_time).do(reminder_job)
            elif habit.frequency == "Еженедельно":
                job = schedule.every().week.at(habit.reminder_time).do(reminder_job)
            
            self.jobs[habit_id] = job
        finally:
            session.close()

    def _run_continuously(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop_all(self):
        self.running = False
        self.thread.join()
        schedule.clear()

    def stop_habit(self, habit_id: int):
        """Остановка напоминаний для конкретной привычки"""
        if habit_id in self.jobs:
            schedule.cancel_job(self.jobs[habit_id])
            del self.jobs[habit_id] 