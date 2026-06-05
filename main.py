from fastapi import FastAPI, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime

import models, schemas, auth
from database import engine, get_db

# Створення таблиць у БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conference Registration System")
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request, db: Session = Depends(get_db)):
    email = auth.get_current_user_email(request)
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    # Новий синтаксис TemplateResponse
    return templates.TemplateResponse(request=request, name="base.html", context={"user": None})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None})

@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    first_name: str = Form(...), last_name: str = Form(...),
    gender: str = Form(...), nationality: str = Form(...),
    organization: str = Form(...), position: str = Form(...),
    birth_date: str = Form(...), email: str = Form(...),
    password: str = Form(...), confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Паролі не збігаються", "user": None})
    
    if db.query(models.User).filter(models.User.email == email).first():
         return templates.TemplateResponse(request=request, name="register.html", context={"error": "Email вже зареєстровано", "user": None})

    hashed_pwd = auth.get_password_hash(password)
    try:
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Неправильний формат дати", "user": None})

    new_user = models.User(
        first_name=first_name, last_name=last_name, gender=gender,
        nationality=nationality, organization=organization, position=position,
        birth_date=birth_date_obj, email=email, hashed_password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None})

@app.post("/login")
async def login_user(
    request: Request, email: str = Form(...), password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Неправильний email або пароль", "user": None})
    
    access_token = auth.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    users = db.query(models.User).all()
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"user": user, "users": users})

@app.get("/edit", response_class=HTMLResponse)
async def edit_form(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="edit.html", context={"user": user})

@app.post("/edit", response_class=HTMLResponse)
async def edit_user(
    request: Request,
    first_name: str = Form(...), last_name: str = Form(...),
    gender: str = Form(...), nationality: str = Form(...),
    organization: str = Form(...), position: str = Form(...),
    birth_date: str = Form(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError:
         return templates.TemplateResponse(request=request, name="edit.html", context={"error": "Неправильний формат дати", "user": user})

    # Оновлення даних
    user.first_name = first_name
    user.last_name = last_name
    user.gender = gender
    user.nationality = nationality
    user.organization = organization
    user.position = position
    user.birth_date = birth_date_obj
    
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)