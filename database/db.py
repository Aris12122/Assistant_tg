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

def get_habit_by_id(habit_id: int) -> Habit:
    session = Session()
    try:
        habit = session.query(Habit).filter_by(id=habit_id, is_active=True).first()
        return habit
    finally:
        session.close()

def calculate_streak(habit_id: int) -> int:
    session = Session()
    try:
        completions = session.query(HabitCompletion)\
            .filter_by(habit_id=habit_id)\
            .order_by(HabitCompletion.completed_at.desc())\
            .all()
        
        if not completions:
            return 0
            
        streak = 0
        last_date = None
        
        for completion in completions:
            current_date = completion.completed_at.date()
            if last_date is None:
                last_date = current_date
                streak = 1
            elif (last_date - current_date).days == 1:
                streak += 1
                last_date = current_date
            else:
                break
                
        return streak
    finally:
        session.close() 