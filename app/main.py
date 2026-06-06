from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.database import init_db
from app.dependencies import templates
from app.middleware import AuthMiddleware
from app.routes.auth import router as auth_router
from app.routes.teacher import router as teacher_router
#from routes.user import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("БД инициализирована, таблицы созданы")
    yield
    print("Сервер остановлен")

app = FastAPI(
    title="TaskFlow",
    description="Веб-приложение для управления учебными задачами",
    lifespan=lifespan
)

app.add_middleware(AuthMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


#сюда потом роуты
app.include_router(auth_router)
app.include_router(teacher_router)

@app.get("/")
def root():
    return RedirectResponse(url="/login")
