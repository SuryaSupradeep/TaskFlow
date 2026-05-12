from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Team Task Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── AI Analysis (inline, no Celery needed) ─────────────────────
def generate_ai_insights(title: str, description: str) -> str:
    """
    Generate smart task breakdown based on title and description keywords.
    No external API needed — runs instantly on task creation.
    """
    title_lower = title.lower()
    desc_lower  = description.lower()
    combined    = title_lower + " " + desc_lower

    # Detect task type from keywords
    if any(k in combined for k in ["api", "endpoint", "rest", "fastapi", "backend"]):
        steps = [
            "1. Define request/response schemas",
            "2. Implement endpoint logic with validation",
            "3. Add error handling and status codes",
            "4. Write unit tests for the endpoint",
            "5. Test with Postman or Swagger UI",
        ]
        priority = "HIGH" if any(k in combined for k in ["auth", "login", "security"]) else "MEDIUM"

    elif any(k in combined for k in ["ui", "frontend", "react", "component", "page", "design"]):
        steps = [
            "1. Create component structure and props",
            "2. Implement UI layout and styling",
            "3. Add state management and event handlers",
            "4. Connect to backend API",
            "5. Test responsiveness across screen sizes",
        ]
        priority = "MEDIUM"

    elif any(k in combined for k in ["database", "db", "schema", "migration", "model", "table"]):
        steps = [
            "1. Design database schema and relationships",
            "2. Create migration scripts",
            "3. Add indexes for performance",
            "4. Validate constraints and foreign keys",
            "5. Test with sample data",
        ]
        priority = "HIGH"

    elif any(k in combined for k in ["test", "testing", "unit", "integration", "qa"]):
        steps = [
            "1. Identify test cases and edge cases",
            "2. Write unit tests for core logic",
            "3. Add integration tests",
            "4. Set up test data and mocks",
            "5. Ensure 80%+ code coverage",
        ]
        priority = "MEDIUM"

    elif any(k in combined for k in ["deploy", "railway", "docker", "ci", "cd", "pipeline"]):
        steps = [
            "1. Prepare environment variables and configs",
            "2. Dockerize the application",
            "3. Set up CI/CD pipeline",
            "4. Configure health checks",
            "5. Monitor logs after deployment",
        ]
        priority = "HIGH"

    elif any(k in combined for k in ["bug", "fix", "error", "crash", "issue", "broken"]):
        steps = [
            "1. Reproduce the bug consistently",
            "2. Identify root cause from logs",
            "3. Implement fix with minimal side effects",
            "4. Add regression test",
            "5. Verify fix in staging environment",
        ]
        priority = "HIGH"

    elif any(k in combined for k in ["auth", "login", "register", "password", "jwt", "token"]):
        steps = [
            "1. Implement authentication flow",
            "2. Secure password hashing",
            "3. Generate and validate JWT tokens",
            "4. Add session management",
            "5. Test security edge cases",
        ]
        priority = "HIGH"

    elif any(k in combined for k in ["report", "dashboard", "analytics", "chart", "stats"]):
        steps = [
            "1. Define metrics and KPIs to display",
            "2. Write optimized DB queries",
            "3. Build chart/visualization components",
            "4. Add date range filters",
            "5. Test with real data",
        ]
        priority = "MEDIUM"

    else:
        # Generic breakdown for any other task
        words = description.split()[:6]
        steps = [
            f"1. Analyze requirements: {' '.join(words[:3])}...",
            "2. Break down into subtasks",
            "3. Implement core functionality",
            "4. Test and validate output",
            "5. Review and document changes",
        ]
        priority = "MEDIUM"

    # Estimate effort based on description length
    if len(description) > 100:
        effort = "3-5 days"
    elif len(description) > 50:
        effort = "1-2 days"
    else:
        effort = "2-4 hours"

    return (
        f"Priority: {priority} | Estimated Effort: {effort}\n\n"
        + "\n".join(steps)
    )


# ── Users ──────────────────────────────────────────────────────

@app.post("/api/users/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(
        email=user.email,
        hashed_password=auth.get_password_hash(user.password),
        role=user.role,
        name=user.name or user.email.split("@")[0],
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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

    # Generate AI insights inline — no Celery needed
    ai_insights = None
    if task.description and len(task.description) > 10:
        ai_insights = generate_ai_insights(task.title, task.description)

    db_task = models.Task(
        title=task.title,
        description=task.description,
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
        ai_insights=ai_insights,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
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