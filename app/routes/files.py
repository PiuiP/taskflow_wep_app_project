from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import File as FileModel, User, Assignment
from app.auth import get_current_user

router = APIRouter(tags=["files"])


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Проверка доступа:
    # - если файл условия (assignment_id is None) — доступен всем из группы
    # - если файл назначения — доступен только студенту-исполнителю и преподавателю-автору задачи
    
    if file.assignment_id is None:
        #файл условия — доступен всем
        pass
    else:
        assignment = db.query(Assignment).filter(Assignment.id == file.assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Назначение не найдено")
        
        # Студент-исполнитель или преподаватель-автор задачи
        if current_user.id != assignment.student_id:
            from app.models import Task
            task = db.query(Task).filter(Task.id == assignment.task_id).first()
            if not task or task.author_id != current_user.id:
                raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    import os
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    
    return FileResponse(
        file.file_path,
        filename=file.original_name,
        media_type=file.mime_type
    )