# Cachuelos App – Full Stack Job Marketplace

Cachuelos App is a **full stack web application** that simulates a simple gig marketplace where:

- Employers can publish temporary jobs
- Workers can apply to available jobs
- Employers can manage applications

The project was built as a **portfolio project** to demonstrate backend API development, authentication systems, database design, and frontend interaction with REST APIs.

---

# Project Structure

```
cachuelos-api/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── crear-job.html
│   ├── mis-jobs.html
│   ├── mis-postulaciones.html
│   ├── postulantes.html
│   │
│   ├── js/
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   ├── jobs.js
│   │   ├── crear-job.js
│   │   ├── mis-jobs.js
│   │   ├── mis-postulaciones.js
│   │   ├── postulantes.js
│   │   ├── register.js
│
├── database/
│   ├── schema.sql
│
└── README.md
```
---
# Project Architecture

The application is composed of two main parts:

**Backend**

- FastAPI
- PostgreSQL (Supabase)
- psycopg2 for SQL queries
- JWT authentication

**Frontend**

- HTML
- Vanilla JavaScript
- Fetch API
- LocalStorage for token storage

The frontend communicates with the backend through **REST endpoints protected with JWT**.

---

# Features

### Authentication

- User registration
- Login with JWT
- Protected endpoints
- Token stored in `localStorage`
- Automatic redirect to login if token is missing or invalid

---

### Roles

Two user roles exist:

**Empleador**

Can:

- Create jobs
- View jobs they created
- View applicants for their jobs

**Trabajador**

Can:

- View available jobs
- Apply to jobs
- View their own applications

---

### Jobs

Employers can:

- Create new jobs
- Edit jobs
- Close jobs
- Delete jobs
- View applicants

Workers can:

- Browse available jobs
- Apply to jobs

---

### Applications

Workers can:

- Send an application message
- See jobs they applied to

Employers can:

- View all applicants for their jobs

The database prevents **duplicate applications**.

---

# Tech Stack

## Backend

- Python
- FastAPI
- PostgreSQL (Supabase)
- psycopg2
- JWT authentication
- Uvicorn server

## Frontend

- HTML
- JavaScript (Vanilla)
- Fetch API
- LocalStorage

---

# Backend Architecture

The backend API connects to **Supabase PostgreSQL** using a `DATABASE_URL`.

Important design choices:

- No ORM is used
- No Supabase client SDK
- SQL queries are executed directly using **psycopg2**
- Each endpoint:
  1. Opens a connection
  2. Executes SQL
  3. Commits when needed
  4. Closes the connection

Authentication uses **Bearer tokens**.

Example request header:

```
Authorization: Bearer <token>
```

Protected routes use:

```
Depends(get_current_user)
```

---

# Database Schema

## Users

```
users
```

| column | description |
|------|-------------|
| user_id | primary key |
| nombre | user name |
| nacionalidad | nationality |
| email | unique email |
| password_hash | hashed password |
| rol | trabajador / empleador |
| fecha_creacion | timestamp |

---

## Jobs

```
jobs
```

| column | description |
|------|-------------|
| job_id | primary key |
| user_id | job owner |
| titulo | job title |
| descripcion | description |
| pago | payment |
| ubicacion | location |
| fecha | job date |
| estado | abierto / cerrado |
| fecha_creacion | timestamp |

---

## Postulaciones

```
postulaciones
```

| column | description |
|------|-------------|
| postulacion_id | primary key |
| job_id | referenced job |
| user_id | applicant |
| mensaje | application message |
| fecha_postulacion | timestamp |

Constraint:

```
UNIQUE(job_id, user_id)
```

Prevents a worker from applying more than once to the same job.

---

# Backend API Endpoints

## System

```
GET /
GET /test-db
```

---

## Authentication

```
POST /auth/register
POST /auth/login
GET /me
```

---

## Jobs

```
POST /jobs
GET /jobs
GET /jobs/{job_id}
PATCH /jobs/{job_id}
PATCH /jobs/{job_id}/cerrar
DELETE /jobs/{job_id}
GET /users/{user_id}/jobs
GET /mis-jobs
```

---

## Applications

```
POST /postulaciones
PATCH /postulaciones/{postulacion_id}/aceptar
GET /jobs/{job_id}/postulaciones
GET /users/{user_id}/postulaciones
GET /mis-postulaciones
```

---

# Frontend Structure

```
frontend/

login.html
register.html
dashboard.html
crear-job.html
mis-jobs.html
mis-postulaciones.html
postulantes.html

auth.js
register.js
dashboard.js
jobs.js
crear-job.js
mis-jobs.js
mis-postulaciones.js
postulantes.js
```

The frontend uses **pure HTML and JavaScript** without frameworks.

Each page has its own JavaScript file responsible for API interaction.

---

# Authentication Flow (Frontend)

Login returns a JWT token.

The token is stored in:

```
localStorage.setItem("access_token", token)
```

Protected pages verify the token:

```
const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "login.html";
}
```

Authenticated requests include:

```
fetch(url, {
    headers: {
        "Authorization": "Bearer " + token
    }
})
```

---

# Logout

All pages include a logout function:

```
function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
}
```

Example button:

```
<button onclick="logout()">Cerrar sesión</button>
```

---

# Running the Backend

Start the server:

```
uvicorn main:app --reload
```

API will run at:

```
http://127.0.0.1:8000
```

Interactive documentation:

```
http://127.0.0.1:8000/docs
```

---

# Learning Goals

This project was built to practice:

- Building REST APIs with FastAPI
- Designing relational databases
- Implementing JWT authentication
- Writing SQL queries for backend logic
- Connecting a frontend to a backend API
- Managing user roles and permissions

---

# Future Improvements

- Modular backend architecture
- Frontend UI improvements
- Docker deployment
- Cloud hosting
- Notifications system
- Messaging between users
- Rating system for jobs and workers

---

# License

MIT License
