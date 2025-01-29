from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.classes import Base, User, Habit, HabitCompletion
from datetime import datetime

# Создаем подключение к БД
engine = create_engine('sqlite:///habits.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_or_create_user(telegram_id: int, username: str) -> User:
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        session.commit()
    
    session.close()
    return user

def add_habit(telegram_id: int, name: str, frequency: str, reminder_time: str) -> Habit:
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        habit = Habit(
            user_id=user.id,
            name=name,
            frequency=frequency,
            reminder_time=reminder_time
        )
        session.add(habit)
        session.commit()
        
        # Обновляем объект перед возвратом
        session.refresh(habit)
        return habit
    finally:
        session.close()

def get_user_habits(telegram_id: int) -> list:
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    habits = session.query(Habit).filter_by(user_id=user.id, is_active=True).all()
    session.close()
    return habits

def complete_habit(habit_id: int):
    session = Session()
    completion = HabitCompletion(habit_id=habit_id)
    session.add(completion)
    session.commit()
    session.close()

def get_habit_stats(habit_id: int, days: int = 30) -> list:
    session = Session()
    completions = session.query(HabitCompletion)\
        .filter_by(habit_id=habit_id)\
        .order_by(HabitCompletion.completed_at.desc())\
        .limit(days)\
        .all()
    session.close()
    return completions

def get_session():
    return Session()

def delete_habit(habit_id: int):
    session = Session()
    try:
        habit = session.query(Habit).filter_by(id=habit_id).first()
        if habit:
            habit.is_active = False
            session.commit()
            return True
        return False
    finally:
        session.close()

def add_test_completions():
    """Добавляет тестовые данные выполнения привычек"""
    session = Session()
    try:
        # Получаем все активные привычки
        habits = session.query(Habit).filter_by(is_active=True).all()
        
        # Для каждой привычки добавляем случайные выполнения за последний месяц
        from datetime import datetime, timedelta
        import random
        
        for habit in habits:
            # Создаем от 10 до 25 выполнений за последний месяц
            for _ in range(random.randint(10, 25)):
                # Случайная дата в последние 30 дней
                random_days = random.randint(0, 30)
                completion_date = datetime.now() - timedelta(days=random_days)
                
                completion = HabitCompletion(
                    habit_id=habit.id,
                    completed_at=completion_date
                )
                session.add(completion)
        
        session.commit()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении тестовых данных: {e}")
        return False
    finally:
        session.close() 