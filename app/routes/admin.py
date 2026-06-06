from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import require_role, hash_password
from app.dependencies import templates

router = APIRouter(prefix="/admin", tags=["admin"])


# ========= СПИСОК ПОЛЬЗОВАТЕЛЕЙ =========

@router.get("/users")
def users_list(
    request: Request,
    role_filter: str = None,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    query = db.query(User)
    
    if role_filter and role_filter in ['student', 'teacher', 'admin']:
        query = query.filter(User.role == role_filter)
    
    # ПАГИНАЦИИЯ ТУУУТ
    per_page = 10
    offset = (page - 1) * per_page
    
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    users = query.order_by(User.full_name).offset(offset).limit(per_page).all()
    
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {
            "users": users,
            "role_filter": role_filter,
            "page": page,
            "total_pages": total_pages
        }
    )


# ========= СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ =========

@router.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    group_name: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    #уникальностЬ логина
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Логин уже занят")
    
    #валидация роли
    if role not in ['student', 'teacher', 'admin']:
        raise HTTPException(status_code=400, detail="Недопустимая роль")
    
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        group_name=group_name if group_name else None
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=303)


# ========= РЕДАКТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ =========

@router.post("/users/{user_id}/edit")
def edit_user(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    role: str = Form(...),
    group_name: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Валидация роли
    if role not in ['student', 'teacher', 'admin']:
        raise HTTPException(status_code=400, detail="Недопустимая роль")
    
    user.full_name = full_name
    user.role = role
    user.group_name = group_name if group_name else None
    
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


# ========= УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ =========

@router.post("/users/{user_id}/delete")
def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Нельзя удалить самого себя
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    db.delete(user)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=303)