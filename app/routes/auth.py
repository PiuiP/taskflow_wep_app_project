from fastapi import Depends, APIRouter, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import check_password, create_JWT, hash_password
from app.dependencies import templates

router = APIRouter()


#=========LOGIN=========

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(request: Request,
                 username: str = Form(...), 
                 password: str = Form(...), 
                 db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Пользователь не найден"}
        )
    
    if not check_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный пароль"}
        )
    token = create_JWT(user.username, user.role)

    if user.role == 'admin':
        redirect_url = "/admin/users" #на страницу со всеми пользователями для просмотра и управления
    elif user.role == "teacher":
        redirect_url = "/teacher/dashboard" #на страницу с дашбордом группы
    elif user.role == "student":
        redirect_url = "/student/tasks" #на страницу со всеми заданями конкретного ученика
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неизвестная роль пользователя"
        )
    
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="access_token", 
        value=token,
        httponly=True,
        max_age=86400, #24*60*60
        samesite="lax"
    )
    
    return response

#=========REGISTRATION=========

@router.get("/register")
def registration_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

#регистрациия только для учеников, учителем становятся через администратора
@router.post("/register")
def registration_submit(request: Request,
                        db: Session = Depends(get_db),
                        username: str = Form(...),
                        password: str = Form(...),
                        password_repeat: str = Form(...),
                        group_name: str = Form(...), #если такой группы нет -> ошибка
                        fullname: str = Form(...),):
    
    user = db.query(User).filter(User.username == username).first()
    group = db.query(User).filter(User.group_name == group_name).first() #должен быть хотябы одиин юзер с такой же группой (учитель первый, потом добавляются ученики)
    if user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь уже существует"}
        )
    if password != password_repeat:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароли не совпадают"}
        )
    if not group:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Указанной группы не существует"}
        )
    
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=fullname,
        role="student",  #регистрация только для студентов
        group_name=group_name
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


#=========LOGOUT========= 
@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

