from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import uuid
import os

from app.database import get_db
from app.models import User, Task, Assignment, Comment, File as FileModel
from app.auth import require_role
from app.dependencies import templates
from app.config import settings

router = APIRouter(prefix="/student", tags=["student"])


# ========= МОИ ЗАДАЧИ =========

@router.get("/tasks")
def my_tasks(
    request: Request,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["student"]))
):
    query = db.query(Assignment).filter(Assignment.student_id == current_user.id)
    
    if status_filter and status_filter in ['pending', 'submitted', 'verified', 'rejected']:
        query = query.filter(Assignment.status == status_filter)
    
    assignments = query.all()
    
    tasks_info = []
    for assignment in assignments:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if task:
            is_overdue = task.deadline < datetime.now() and assignment.status in ['pending', 'submitted']
            tasks_info.append({
                'task': task,
                'assignment': assignment,
                'is_overdue': is_overdue
            })
    
    # Сортировка: просроченные сверху, потом по дедлайну
    tasks_info.sort(key=lambda x: (not x['is_overdue'], x['task'].deadline))
    
    return templates.TemplateResponse(
        request,
        "student/tasks.html",
        {
            "tasks_info": tasks_info,
            "status_filter": status_filter
        }
    )


# ========= ПРОСМОТР ЗАДАНИЯ =========

@router.get("/task/{assignment_id}")
def task_detail(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["student"]))
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.student_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    task = db.query(Task).filter(Task.id == assignment.task_id).first()
    
    #айлы условия задания (привязаны к задаче через uploaded_by_id преподавателя)
    condition_files = db.query(FileModel).filter(
        FileModel.uploaded_by_id == task.author_id,
        FileModel.assignment_id.is_(None)
    ).all()
    # На самом деле файлы условия привязаны к заданию через автора — но у нас в модели File
    # нет прямой связи с Task. Для простоты: файлы без assignment_id, загруженные автором задачи.
    
    #файлы студента
    student_files = db.query(FileModel).filter(
        FileModel.assignment_id == assignment.id,
        FileModel.uploaded_by_id == current_user.id
    ).all()
    
    #комментарии
    comments = db.query(Comment).filter(
        Comment.assignment_id == assignment.id
    ).order_by(Comment.created.asc()).all()
    
    comments_info = []
    for comment in comments:
        author = db.query(User).filter(User.id == comment.author_id).first()
        comments_info.append({
            'comment': comment,
            'author': author
        })
    
    is_overdue = task.deadline < datetime.now() and assignment.status in ['pending', 'submitted']
    
    return templates.TemplateResponse(
        request,
        "student/task_detail.html",
        {
            "task": task,
            "assignment": assignment,
            "condition_files": condition_files,
            "student_files": student_files,
            "comments_info": comments_info,
            "is_overdue": is_overdue
        }
    )


# ========= СДАЧА ЗАДАНИЯ =========

@router.post("/task/{assignment_id}/submit")
async def submit_task(
    request: Request,
    assignment_id: int,
    solution_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["student"]))
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id,
        Assignment.student_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    if assignment.status == 'verified':
        raise HTTPException(status_code=400, detail="Задание уже проверено")
    
    os.makedirs("uploads", exist_ok=True)
    file_ext = solution_file.filename.split(".")[-1]
    stored_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = f"uploads/{stored_name}"
    
    with open(file_path, "wb") as buffer:
        content = await solution_file.read()
        buffer.write(content)
    
    file = FileModel(
        original_name=solution_file.filename,
        stored_name=stored_name,
        file_path=file_path,
        file_size=len(content),
        mime_type=solution_file.content_type or "application/octet-stream",
        assignment_id=assignment.id,
        uploaded_by_id=current_user.id
    )
    db.add(file)
    
    #статус на submitted
    assignment.status = 'submitted'
    db.commit()
    
    return RedirectResponse(url=f"/student/task/{assignment.id}", status_code=303)


# ========= УСПЕВАЕМОСТЬ =========

@router.get("/progress")
def progress(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["student"]))
):
    assignments = db.query(Assignment).filter(
        Assignment.student_id == current_user.id
    ).all()
    
    #по статусам
    stats = {'pending': 0, 'submitted': 0, 'verified': 0, 'rejected': 0}
    for assignment in assignments:
        if assignment.status in stats:
            stats[assignment.status] += 1
    
    total = len(assignments)
    verified_count = stats['verified']
    progress = (verified_count / total * 100) if total > 0 else 0
    
    #средний балл
    grades = [a.grade for a in assignments if a.grade is not None and a.status == 'verified']
    avg_grade = sum(grades) / len(grades) if grades else 0
    
    #спиисок задач с оценкамиии
    tasks_info = []
    for assignment in assignments:
        task = db.query(Task).filter(Task.id == assignment.task_id).first()
        if task:
            tasks_info.append({
                'task': task,
                'assignment': assignment
            })
    
    tasks_info.sort(key=lambda x: x['task'].deadline, reverse=True)
    
    return templates.TemplateResponse(
        request,
        "student/progress.html",
        {
            "stats": stats,
            "total": total,
            "progress": round(progress, 1),
            "avg_grade": round(avg_grade, 1),
            "tasks_info": tasks_info
        }
    )