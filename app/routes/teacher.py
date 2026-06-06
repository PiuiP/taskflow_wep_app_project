from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List
import uuid
import os

from app.database import get_db
from app.models import User, Task, Assignment, Comment, File as FileModel
from app.auth import require_role
from app.dependencies import templates

router = APIRouter(prefix="/teacher", tags=["teacher"])


# ========= ДАШБОРД ГРУППЫ =========

@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    #всех студентов, где группа студента == группе преподавателя
    students = db.query(User).filter(
        User.group_name == current_user.group_name,
        User.role == 'student'
    ).all()
    
    #статистика по статусам для группы
    stats_query = db.query(
        Assignment.status,
        func.count(Assignment.id)
    ).join(
        User, Assignment.student_id == User.id
    ).filter(
        User.group_name == current_user.group_name
    ).group_by(Assignment.status).all()
    
    stats = {s: 0 for s in ['pending', 'submitted', 'verified', 'rejected']}
    for status_val, count in stats_query:
        if status_val in stats:
            stats[status_val] = count
    
    total = sum(stats.values())
    
    #таблица успеваемости студентов
    students_progress = []
    for student in students:
        assignments = db.query(Assignment).filter(
            Assignment.student_id == student.id
        ).all()
        
        total_tasks = len(assignments)
        verified_count = sum(1 for a in assignments if a.status == 'verified')
        progress = (verified_count / total_tasks * 100) if total_tasks > 0 else 0
        
        grades = [a.grade for a in assignments if a.grade is not None and a.status == 'verified']
        avg_grade = sum(grades) / len(grades) if grades else 0
        
        students_progress.append({
            'student': student,
            'total': total_tasks,
            'verified': verified_count,
            'progress': round(progress, 1),
            'avg_grade': round(avg_grade, 1)
        })
    
    return templates.TemplateResponse(
        request,
        "teacher/dashboard.html",
        {
            "stats": stats,
            "total": total,
            "students_progress": students_progress
        }
    )

# ========= СПИСОК СТУДЕНТОВ ГРУППЫ =========

@router.get("/students")
def students_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    students = db.query(User).filter(
        User.group_name == current_user.group_name,
        User.role == 'student'
    ).order_by(User.full_name).all()
    
    #статистика для каждого студента
    students_info = []
    for student in students:
        assignments = db.query(Assignment).filter(
            Assignment.student_id == student.id
        ).all()
        
        total_tasks = len(assignments)
        verified_count = sum(1 for a in assignments if a.status == 'verified')
        submitted_count = sum(1 for a in assignments if a.status == 'submitted')
        progress = (verified_count / total_tasks * 100) if total_tasks > 0 else 0
        
        grades = [a.grade for a in assignments if a.grade is not None and a.status == 'verified']
        avg_grade = sum(grades) / len(grades) if grades else 0
        
        students_info.append({
            'student': student,
            'total': total_tasks,
            'verified': verified_count,
            'submitted': submitted_count,
            'progress': round(progress, 1),
            'avg_grade': round(avg_grade, 1)
        })
    
    return templates.TemplateResponse(
        request,
        "teacher/students.html",
        {"students_info": students_info}
    )

# ========= УСПЕВАЕМОСТЬ КОНКРЕТНОГО СТУДЕНТА =========

@router.get("/student/{student_id}")
def student_progress(
    request: Request,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    # Получаем студента
    student = db.query(User).filter(
        User.id == student_id,
        User.role == 'student'
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Проверяем, что студент из группы преподавателя
    if student.group_name != current_user.group_name:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    # Получаем все назначения студента
    assignments = db.query(Assignment).filter(
        Assignment.student_id == student.id
    ).all()
    
    # Статистика по статусам
    stats = {'pending': 0, 'submitted': 0, 'verified': 0, 'rejected': 0}
    for assignment in assignments:
        if assignment.status in stats:
            stats[assignment.status] += 1
    
    total = len(assignments)
    verified_count = stats['verified']
    progress = (verified_count / total * 100) if total > 0 else 0
    
    # Средний балл
    grades = [a.grade for a in assignments if a.grade is not None and a.status == 'verified']
    avg_grade = sum(grades) / len(grades) if grades else 0
    
    # Список задач с оценками
    tasks_info = []
    for assignment in assignments:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if task:
            tasks_info.append({
                'task': task,
                'assignment': assignment
            })
    
    # Сортируем по дедлайну (новые сверху)
    tasks_info.sort(key=lambda x: x['task'].deadline, reverse=True)
    
    return templates.TemplateResponse(
        request,
        "teacher/student_progress.html",
        {
            "student": student,
            "stats": stats,
            "total": total,
            "progress": round(progress, 1),
            "avg_grade": round(avg_grade, 1),
            "tasks_info": tasks_info
        }
    )

# ========= СПИСОК ЗАДАНИЙ ПРЕПОДАВАТЕЛЯ =========

@router.get("/tasks")
def tasks_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    tasks = db.query(Task).filter(
        Task.author_id == current_user.id
    ).order_by(Task.created.desc()).all()
    
    #считаем количество назначений и статусы
    tasks_info = []
    for task in tasks:
        assignments = db.query(Assignment).filter(Assignment.task_id == task.id).all()
        total = len(assignments)
        submitted = sum(1 for a in assignments if a.status == 'submitted')
        verified = sum(1 for a in assignments if a.status == 'verified')
        
        tasks_info.append({
            'task': task,
            'total': total,
            'submitted': submitted,
            'verified': verified
        })
    
    return templates.TemplateResponse(
        request,
        "teacher/tasks.html",
        {"tasks_info": tasks_info}
    )


# ========= СОЗДАНИЕ ЗАДАНИЯ =========

@router.get("/tasks/create")
def create_task_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    #группа студента == группе преподавателя
    students = db.query(User).filter(
        User.group_name == current_user.group_name,
        User.role == 'student'
    ).order_by(User.full_name).all()
    
    return templates.TemplateResponse(
        request,
        "teacher/create_task.html",
        {"students": students}
    )


@router.post("/tasks/create")
async def create_task_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    deadline: str = Form(...),
    student_ids: List[int] = Form(default=[]),
    condition_file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    if not student_ids:
        return templates.TemplateResponse(
            request,
            "teacher/create_task.html",
            {
                "students": db.query(User).filter(
                    User.group_name == current_user.group_name,
                    User.role == 'student'
                ).all(),
                "error": "Выберите хотя бы одного студента"
            }
        )

    task = Task(
        title=title,
        description=description,
        deadline=datetime.fromisoformat(deadline),
        author_id=current_user.id
    )
    db.add(task)
    db.flush()
    
    #назначения для выбранных студентов
    for student_id in student_ids:
        # Проверяем, что студент из группы преподавателя
        student = db.query(User).filter(
            User.id == student_id,
            User.group_name == current_user.group_name,
            User.role == 'student'
        ).first()
        
        if student:
            assignment = Assignment(
                task_id=task.id,
                student_id=student.id,
                status='pending'
            )
            db.add(assignment)
    
    #сохраняем файл условия если есть
    if condition_file and condition_file.filename:
        os.makedirs("uploads", exist_ok=True)
        file_ext = condition_file.filename.split(".")[-1]
        stored_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"uploads/{stored_name}"
        
        with open(file_path, "wb") as buffer:
            content = await condition_file.read()
            buffer.write(content)
        
        file = FileModel(
            original_name=condition_file.filename,
            stored_name=stored_name,
            file_path=file_path,
            file_size=len(content),
            mime_type=condition_file.content_type or "application/octet-stream",
            assignment_id=None,
            uploaded_by_id=current_user.id
        )
        db.add(file)
    
    db.commit()
    return RedirectResponse(url=f"/teacher/task/{task.id}", status_code=303)


# ========= СТРАНИЦА ЗАДАНИЯ (ПРОВЕРКА РАБОТ) =========

@router.get("/task/{task_id}")
def task_detail(
    request: Request,
    task_id: int,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    #преподаватель == автор?
    if task.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    # ПАГИНАЦИЯ ЗДЕЕЕЕСЬ
    per_page = 5
    offset = (page - 1) * per_page
    
    assignments = db.query(Assignment).filter(
        Assignment.task_id == task_id
    ).offset(offset).limit(per_page).all()
    
    total = db.query(Assignment).filter(Assignment.task_id == task_id).count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    #назначение -> студент, файл
    assignments_info = []
    for assignment in assignments:
        student = db.query(User).filter(User.id == assignment.student_id).first()
        files = db.query(FileModel).filter(
            FileModel.assignment_id == assignment.id
        ).all()
        
        assignments_info.append({
            'assignment': assignment,
            'student': student,
            'files': files
        })
    
    return templates.TemplateResponse(
        request,
        "teacher/task_detail.html",
        {
            "task": task,
            "assignments_info": assignments_info,
            "page": page,
            "total_pages": total_pages
        }
    )


# ========= БЫСТРАЯ СМЕНА СТАТУСА =========

@router.post("/task/{task_id}/quick_action")
def quick_action(
    request: Request,
    task_id: int,
    assignment_id: int = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    if action not in ['verified', 'rejected']:
        raise HTTPException(status_code=400, detail="Недопустимое действие")
    
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.task_id == task_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    
    assignment.status = action
    db.commit()
    
    return RedirectResponse(url=f"/teacher/task/{task_id}", status_code=303)


# ========= ПРОВЕРКА С ОЦЕНКОЙ И КОММЕНТАРИЕМ =========

@router.post("/task/{task_id}/check")
def check_assignment(
    request: Request,
    task_id: int,
    assignment_id: int = Form(...),
    grade: int = Form(...),
    comment: str = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["teacher"]))
):
    if action not in ['verified', 'rejected']:
        raise HTTPException(status_code=400, detail="Недопустимое действие")
    
    if grade < 0 or grade > 100:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 0 до 100")
    
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.task_id == task_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    
    assignment.status = action
    assignment.grade = grade
    
    new_comment = Comment(
        content=comment,
        assignment_id=assignment.id,
        author_id=current_user.id
    )
    db.add(new_comment)
    db.commit()
    
    return RedirectResponse(url=f"/teacher/task/{task_id}", status_code=303)