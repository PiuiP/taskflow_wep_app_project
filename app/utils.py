from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

def validate_file_type(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")
    
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый тип файла. Разрешены: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )