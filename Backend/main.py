from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas, auth
from database import engine, get_db
import os
import uvicorn


# Import worker safely — app still works if Celery not running
try:
    from worker import process_ai_task_breakdown
    CELERY_AVAILABLE = True
except Exception:
    CELERY_AVAILABLE = False

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Team Task Manager")

origins = [
    "https://frontend-production-28aba.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Users ──────────────────────────────────────────────────────

@app.post("/api/users/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not user.email.lower().endswith("@taskflow.com"):
        raise HTTPException(status_code=400, detail="Only @taskflow.com emails are allowed.")
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(
        email=user.email,
        hashed_password=auth.get_password_hash(user.password),
        role=user.role,
        name=user.name or user.email.split("@")[0],  # use provided name or fallback
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/")
def root():
    return {"message": "API working"}

@app.post("/api/users/login", response_model=schemas.UserOut)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not db_user or not auth.verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return db_user

@app.get("/api/users", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# ── Projects ────────────────────────────────────────────────────

@app.post("/api/projects", response_model=schemas.ProjectOut)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/projects", response_model=list[schemas.ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

# ── Tasks ───────────────────────────────────────────────────────

@app.post("/api/tasks", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Validate project exists
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=400, detail=f"Project {task.project_id} does not exist")

    # Validate assignee exists if provided
    if task.assignee_id:
        assignee = db.query(models.User).filter(models.User.id == task.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=400, detail=f"User {task.assignee_id} does not exist")

    db_task = models.Task(
        title=task.title,
        description=task.description,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Trigger AI analysis if description is long enough
    if CELERY_AVAILABLE and task.description and len(task.description) > 10:
        try:
            process_ai_task_breakdown.delay(db_task.id, task.description)
        except Exception:
            pass  # Don't crash if Celery/RabbitMQ not running

    return db_task

@app.get("/api/tasks", response_model=list[schemas.TaskOut])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()

@app.patch("/api/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.status is not None:
        task.status = payload.status
    if payload.ai_insights is not None:
        task.ai_insights = payload.ai_insights
    if payload.assignee_id is not None:
        task.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Deleted"}

# ── Dashboard ───────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()
    now = datetime.now()
    return {
        "total":       len(tasks),
        "todo":        sum(1 for t in tasks if t.status == "todo"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "done":        sum(1 for t in tasks if t.status == "done"),
        "overdue":     sum(1 for t in tasks if t.due_date and t.due_date < now and t.status != "done"),
    }


# ── Chat & Comments ─────────────────────────────────────────────

@app.get("/api/projects/{project_id}/comments", response_model=list[schemas.CommentOut])
def get_project_comments(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.ProjectComment).filter(models.ProjectComment.project_id == project_id).order_by(models.ProjectComment.timestamp.asc()).all()

@app.post("/api/projects/{project_id}/comments", response_model=schemas.CommentOut)
def create_project_comment(project_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    db_comment = models.ProjectComment(text=comment.text, project_id=project_id, user_id=comment.user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@app.get("/api/team/messages", response_model=list[schemas.MessageOut])
def get_team_messages(db: Session = Depends(get_db)):
    return db.query(models.TeamMessage).order_by(models.TeamMessage.timestamp.asc()).all()

@app.post("/api/team/messages", response_model=schemas.MessageOut)
def create_team_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    db_message = models.TeamMessage(text=message.text, user_id=message.user_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message