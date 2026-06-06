from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, Integer, Text, String, DateTime
from typing import Optional, List
from datetime import datetime

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) #student/teacher/admin
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created: Mapped[datetime] = mapped_column(server_default=func.now())

    assignments: Mapped[List["Assignment"]] = relationship(back_populates="student") #все назначения студента

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created: Mapped[datetime] = mapped_column(server_default=func.now())
    updated: Mapped[datetime] = mapped_column(server_default=func.now())

    assignments: Mapped[List["Assignment"]] = relationship(back_populates="task") #все студенты по заданию

class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending") #pending/submitted/verified/rejected 
    grade: Mapped[Optional[int]] = mapped_column(Integer) #0-100

    task: Mapped["Task"] = relationship(back_populates="assignments")
    student: Mapped["User"] = relationship(back_populates="assignments")

    #получить комментарии и файлы назначения
    comments: Mapped[List["Comment"]] = relationship(back_populates="assignment")
    files: Mapped[List["File"]] = relationship(back_populates="assignment")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    created: Mapped[datetime] = mapped_column(server_default=func.now())

    assignment: Mapped["Assignment"] = relationship(back_populates="comments")

class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    assignment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assignments.id"))
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    assignment: Mapped["Assignment"] = relationship(back_populates="files")