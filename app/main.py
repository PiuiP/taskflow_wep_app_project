from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from database import init_db
#from routes.auth import auth
#from routes.task import tasks
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

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#сюда потом роуты

@app.get("/")
def root():
    return RedirectResponse(url="/login")
