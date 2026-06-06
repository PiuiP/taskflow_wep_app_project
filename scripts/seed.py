from app.database import SessionLocal, engine, Base
from app.models import User, Task, Assignment, Comment, File
from app.auth import hash_password


Base.metadata.create_all(bind=engine)

db = SessionLocal()

admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    db.add(User(
        username="admin",
        password_hash=hash_password("admin123"),
        full_name="Администратор Системы",
        role="admin",
        group_name=None
    ))
    print("Админ создан")


teacher = db.query(User).filter(User.username == "teacher").first()
if not teacher:
    db.add(User(
        username="teacher",
        password_hash=hash_password("teacher123"),
        full_name="Кружалов Алексей Сергеевич",
        role="teacher",
        group_name="ИВТ-41"
    ))
    print("Преподаватель создан")


students_data = [
    {"username": "student1", "full_name": "Иванов Иван"},
    {"username": "student2", "full_name": "Петрова Мария"},
]

for s in students_data:
    if not db.query(User).filter(User.username == s["username"]).first():
        db.add(User(
            username=s["username"],
            password_hash=hash_password("student123"),
            full_name=s["full_name"],
            role="student",
            group_name="ИВТ-41"
        ))
        print("Студент создан")

try:
    db.commit()
    print("Все данные успешно сохранены в БД!")
except Exception as e:
    db.rollback()
    print(f"Ошибка при сохранении: {e}")
finally:
    db.close()