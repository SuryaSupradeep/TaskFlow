TaskFlow - Enterprise Team Task Manager

A full-stack team task management application built with React on the frontend 
and FastAPI on the backend, deployed on Railway with PostgreSQL.


LIVE DEMO

Frontend : https://taskflow-production-441.up.railway.app
Backend  : https://backend-production-f073.up.railway.app/docs


FEATURES

- Signup and Login with email and password
- Role-based access for Admin and Member
- Create and manage projects
- Create, assign, update and delete tasks
- AI task breakdown on task creation
- Team chat for all members
- Per-project comment threads
- Dashboard with live task statistics
- Team panel showing members and their assigned tasks


TECH STACK

Frontend
  React 18, CSS, Tailwind utilities, deployed on Railway

Backend
  FastAPI, SQLAlchemy, PostgreSQL, Passlib with bcrypt, deployed on Railway


PROJECT STRUCTURE

Team_Manager/
  Backend/
    main.py           FastAPI app with all API endpoints
    models.py         SQLAlchemy database models
    schemas.py        Pydantic request and response schemas
    auth.py           Password hashing and verification
    database.py       Database connection and session management
    worker.py         Celery worker for background tasks
    requirements.txt  Python dependencies
    .python-version   Pins Python to 3.12
    railway.toml      Railway deployment config
  Frontend/
    src/
      App.jsx         Root component with sidebar navigation
      Login.jsx       Sign in and sign up pages
      Dashboard.jsx   Stats overview page
      Tasks.jsx       Task list and creation
      Projects.jsx    Project management and team panel
      api.js          All API calls with mock data fallback
      index.jsx       React entry point
      index.css       Global styles
    public/
    package.json
    railway.toml      Railway deployment config


API ENDPOINTS

POST    /api/users/register              Register new user
POST    /api/users/login                 Login user
GET     /api/users                       Get all users
POST    /api/projects                    Create project
GET     /api/projects                    Get all projects
POST    /api/tasks                       Create task with AI analysis
GET     /api/tasks                       Get all tasks
PATCH   /api/tasks/{id}                  Update task status
DELETE  /api/tasks/{id}                  Delete task (Admin only)
GET     /api/dashboard                   Get task statistics
GET     /api/team/messages               Get team chat messages
POST    /api/team/messages               Send team chat message
GET     /api/projects/{id}/comments      Get project comments
POST    /api/projects/{id}/comments      Add project comment


DATABASE MODELS

User           id, email, name, hashed_password, role
Project        id, name, description
Task           id, title, description, status, due_date, project_id, assignee_id, ai_insights
TeamMessage    id, text, timestamp, user_id
ProjectComment id, text, timestamp, project_id, user_id


REQUIREMENTS

fastapi
uvicorn
sqlalchemy
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart
psycopg2-binary
python-dotenv
celery

Note on bcrypt version: bcrypt is pinned to 4.0.1 and passlib to 1.7.4 because 
newer versions of bcrypt removed the __about__ module that passlib depends on. 
This caused 500 errors on all password operations. Version 4.0.1 is the last 
stable release that works correctly with passlib on Python 3.12 and Railway.


LOCAL SETUP

Backend

  cd Backend
  set DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/taskmanager //(provided in the railway postgressql database)//
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000

Frontend

  cd Frontend
  npm install
  npm start

  Open http://localhost:3000 in your browser.


ENVIRONMENT VARIABLES

DATABASE_URL    PostgreSQL connection string

On Railway, add DATABASE_URL = ${{Postgres.DATABASE_URL}} in the 
Backend service Variables tab.


RAILWAY DEPLOYMENT

Backend
  1. Connect GitHub repo to Railway
  2. Set Root Directory to Backend
  3. Set Build Command  to pip3 install -r requirements.txt
  4. Set Start Command  to uvicorn main:app --host 0.0.0.0 --port $PORT
  5. Add variable DATABASE_URL = ${{Postgres.DATABASE_URL}}

Frontend
  1. Connect GitHub repo to Railway
  2. Set Root Directory to Frontend
  3. Set Build Command  to npm install && npm run build
  4. Set Start Command  to npx serve -s build -l $PORT


ROLE BASED ACCESS

Feature               Admin    Member
Create tasks          Yes      No
Delete tasks          Yes      No
Create projects       Yes      No
View all tasks        Yes      No
View assigned tasks   Yes      Yes
Update task status    Yes      Yes
Team chat             Yes      Yes
Project comments      Yes      Yes


AI TASK ANALYSIS

When a task is created with a description longer than 10 characters the backend
automatically generates a breakdown including priority level (HIGH or MEDIUM),
estimated effort (2-4 hours, 1-2 days, or 3-5 days) and a step by step plan
tailored to the task type such as API development, frontend, database, deployment
or bug fixing. This runs directly on the backend with no external API required.

VALIDATION RULES

Registration
  - Full name is required
  - Email must contain @ symbol
  - Email must end with @taskflow.com
  - Password must be at least 4 characters
  - Duplicate emails are rejected with "Email already registered"

Login
  - Invalid email or password returns 401 Unauthorized

Tasks
  - Title is required
  - Project must be selected and must exist in the database
  - Assignee must exist in the database if provided
  - Description longer than 10 characters triggers AI analysis

Projects
  - Project name is required
  - Project must exist in database before tasks can be assigned to it

Team Messages
  - User must exist in database before sending a message
  - Empty messages are not accepted

Project Comments
  - Project must exist before adding a comment
  - User must exist before adding a comment


AUTHOR

Devaguptapu Surya Supradeep
GitHub: https://github.com/SuryaSupradeep/TaskFlow