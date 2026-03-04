from fastapi import FastAPI
from fastapi import Query
from db import get_connection
from pydantic import BaseModel, EmailStr
from datetime import date, datetime, timedelta
import psycopg2
import os
from dotenv import load_dotenv

from jose import jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware


# -------------------
# Configuración
# -------------------

load_dotenv()
app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En desarrollo está bien
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------
# Seguridad (JWT + Password Hashing)
# -------------------

SECRET_KEY = "supersecretkey"  # cambiar luego
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password[:72], hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        print("TOKEN RECIBIDO:", credentials.credentials)

        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print("PAYLOAD:", payload)

        user_id = payload.get("user_id")
        rol = payload.get("rol")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        return {"user_id": user_id, "rol": rol}

    except Exception as e:
        print("ERROR AL DECODIFICAR:", e)
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )
# -------------------
# Modelos
# -------------------

class JobUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    pago: float | None = None
    ubicacion: str | None = None
    fecha: date | None = None

class UserCreate(BaseModel):
    nombre: str
    nacionalidad: str | None = None
    email: EmailStr
    password: str
    rol: str  # trabajador o empleador


class JobCreate(BaseModel):
    titulo: str
    descripcion: str | None = None
    pago: float
    ubicacion: str
    fecha: date

class PostulacionCreate(BaseModel):
    job_id: int
    mensaje: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    nombre: str
    nacionalidad: str | None = None
    email: EmailStr
    password: str
    rol: str

# -------------------
# Endpoints básicos
# -------------------

@app.get("/")
def home():
    return {"message": "API funcionando"}


@app.get("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {"database_time": result}

    except Exception as e:
        return {"error": str(e)}

        
@app.post("/jobs")
def create_job(job: JobCreate, user=Depends(get_current_user)):
    if user["rol"] != "empleador":
        raise HTTPException(status_code=403, detail="Solo empleadores pueden crear trabajos")

    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        INSERT INTO jobs (user_id, titulo, descripcion, pago, ubicacion, fecha)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING job_id;
        """

        cur.execute(query, (
            user["user_id"],   # 🔥 ahora viene del token
            job.titulo,
            job.descripcion,
            job.pago,
            job.ubicacion,
            job.fecha
        ))

        job_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return {
            "message": "Cachuelo creado",
            "job_id": job_id
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/jobs")
def get_jobs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ubicacion: str | None = None,
    pago_min: float | None = None,
    pago_max: float | None = None
):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Base de la consulta
        query = """
        SELECT 
            job_id,
            user_id,
            titulo,
            descripcion,
            pago,
            ubicacion,
            fecha,
            estado,
            fecha_creacion
        FROM jobs
        WHERE estado = 'abierto'
        """

        params = []

        # Filtros opcionales
        if ubicacion:
            query += " AND ubicacion ILIKE %s"
            params.append(f"%{ubicacion}%")

        if pago_min is not None:
            query += " AND pago >= %s"
            params.append(pago_min)

        if pago_max is not None:
            query += " AND pago <= %s"
            params.append(pago_max)

        # Orden + paginación
        query += """
        ORDER BY fecha_creacion DESC
        LIMIT %s OFFSET %s;
        """

        params.extend([limit, offset])

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        jobs = []
        for row in rows:
            jobs.append({
                "job_id": row[0],
                "user_id": row[1],
                "titulo": row[2],
                "descripcion": row[3],
                "pago": float(row[4]) if row[4] else None,
                "ubicacion": row[5],
                "fecha": str(row[6]) if row[6] else None,
                "estado": row[7],
                "fecha_creacion": str(row[8])
            })

        return {
            "limit": limit,
            "offset": offset,
            "count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        return {"error": str(e)}

@app.post("/postulaciones")
def create_postulacion(post: PostulacionCreate, user=Depends(get_current_user)):

    # Solo trabajadores pueden postular
    if user["rol"] != "trabajador":
        raise HTTPException(
            status_code=403,
            detail="Solo trabajadores pueden postular"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1️⃣ Verificar que el job exista y esté abierto
        cur.execute("""
            SELECT user_id, estado
            FROM jobs
            WHERE job_id = %s;
        """, (post.job_id,))

        job = cur.fetchone()

        if not job:
            cur.close()
            conn.close()
            return {"error": "Trabajo no encontrado"}

        owner_id, estado = job

        # 2️⃣ No puede postular a su propio job
        if owner_id == user["user_id"]:
            cur.close()
            conn.close()
            return {"error": "No puedes postular a tu propio trabajo"}

        # 3️⃣ El job debe estar abierto
        if estado != "abierto":
            cur.close()
            conn.close()
            return {"error": "El trabajo está cerrado"}

        # 4️⃣ Verificar si ya postuló (evita error de UNIQUE)
        cur.execute("""
            SELECT postulacion_id
            FROM postulaciones
            WHERE job_id = %s AND user_id = %s;
        """, (post.job_id, user["user_id"]))

        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            return {"error": "Ya postulaste a este trabajo"}

        # 5️⃣ Crear postulación
        cur.execute("""
            INSERT INTO postulaciones (job_id, user_id, mensaje)
            VALUES (%s, %s, %s)
            RETURNING postulacion_id;
        """, (
            post.job_id,
            user["user_id"],
            post.mensaje
        ))

        postulacion_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return {
            "message": "Postulación creada",
            "postulacion_id": postulacion_id
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/jobs/{job_id}")
def get_job_by_id(job_id: int):
    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT 
            job_id,
            user_id,
            titulo,
            descripcion,
            pago,
            ubicacion,
            fecha,
            estado,
            fecha_creacion
        FROM jobs
        WHERE job_id = %s;
        """

        cur.execute(query, (job_id,))
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return {"error": "Trabajo no encontrado"}

        job = {
            "job_id": row[0],
            "user_id": row[1],
            "titulo": row[2],
            "descripcion": row[3],
            "pago": float(row[4]) if row[4] else None,
            "ubicacion": row[5],
            "fecha": str(row[6]) if row[6] else None,
            "estado": row[7],
            "fecha_creacion": str(row[8])
        }

        return job

    except Exception as e:
        return {"error": str(e)}

@app.get("/users/{user_id}/postulaciones")
def get_postulaciones_by_user(user_id: int, user=Depends(get_current_user)):

    # Solo el propio usuario puede ver sus postulaciones
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver estas postulaciones"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT 
            postulacion_id,
            job_id,
            mensaje,
            fecha_postulacion
        FROM postulaciones
        WHERE user_id = %s
        ORDER BY fecha_postulacion DESC;
        """

        cur.execute(query, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        postulaciones = []
        for row in rows:
            postulaciones.append({
                "postulacion_id": row[0],
                "job_id": row[1],
                "mensaje": row[2],
                "fecha_postulacion": str(row[3])
            })

        return postulaciones

    except Exception as e:
        return {"error": str(e)}

@app.patch("/jobs/{job_id}/cerrar")
def cerrar_job(job_id: int, user=Depends(get_current_user)):

    if user["rol"] != "empleador":
        raise HTTPException(
            status_code=403,
            detail="Solo empleadores pueden cerrar trabajos"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Verificar que el job exista y sea del usuario
        cur.execute("""
            SELECT estado, user_id
            FROM jobs
            WHERE job_id = %s;
        """, (job_id,))

        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return {"error": "Trabajo no encontrado"}

        estado_actual, owner_id = row

        # Validar propietario
        if owner_id != user["user_id"]:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="No puedes cerrar un trabajo que no es tuyo"
            )

        if estado_actual == "cerrado":
            cur.close()
            conn.close()
            return {"message": "El trabajo ya está cerrado"}

        # Cerrar job
        cur.execute("""
            UPDATE jobs
            SET estado = 'cerrado'
            WHERE job_id = %s;
        """, (job_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Trabajo cerrado correctamente"}

    except Exception as e:
        return {"error": str(e)}


@app.patch("/postulaciones/{postulacion_id}/aceptar")
def aceptar_postulacion(postulacion_id: int, user=Depends(get_current_user)):

    if user["rol"] != "empleador":
        raise HTTPException(
            status_code=403,
            detail="Solo empleadores pueden aceptar postulaciones"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1️⃣ Obtener job_id y estado actual
        cur.execute("""
            SELECT job_id, estado
            FROM postulaciones
            WHERE postulacion_id = %s;
        """, (postulacion_id,))

        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return {"error": "Postulación no encontrada"}

        job_id, estado_actual = row

        if estado_actual == "aceptada":
            cur.close()
            conn.close()
            return {"message": "La postulación ya está aceptada"}

        # 2️⃣ Aceptar la postulación seleccionada
        cur.execute("""
            UPDATE postulaciones
            SET estado = 'aceptada'
            WHERE postulacion_id = %s;
        """, (postulacion_id,))

        # 3️⃣ Rechazar las demás
        cur.execute("""
            UPDATE postulaciones
            SET estado = 'rechazada'
            WHERE job_id = %s
            AND postulacion_id != %s;
        """, (job_id, postulacion_id))

        # 4️⃣ Cerrar el trabajo
        cur.execute("""
            UPDATE jobs
            SET estado = 'cerrado'
            WHERE job_id = %s;
        """, (job_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {
            "message": "Postulación aceptada, otras rechazadas y trabajo cerrado",
            "job_id": job_id
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/users/{user_id}/jobs")
def get_jobs_by_user(user_id: int, user=Depends(get_current_user)):

    # Validar que solo vea sus propios jobs
    if user["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver estos trabajos"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT 
            job_id,
            titulo,
            descripcion,
            pago,
            ubicacion,
            fecha,
            estado,
            fecha_creacion
        FROM jobs
        WHERE user_id = %s
        ORDER BY fecha_creacion DESC;
        """

        cur.execute(query, (user_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        jobs = []
        for row in rows:
            jobs.append({
                "job_id": row[0],
                "titulo": row[1],
                "descripcion": row[2],
                "pago": float(row[3]) if row[3] else None,
                "ubicacion": row[4],
                "fecha": str(row[5]) if row[5] else None,
                "estado": row[6],
                "fecha_creacion": str(row[7])
            })

        return jobs

    except Exception as e:
        return {"error": str(e)}

@app.post("/auth/register")
def register_user(data: RegisterRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        password_hash = hash_password(data.password)

        cur.execute("""
            INSERT INTO users (nombre, nacionalidad, email, password_hash, rol)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id;
        """, (
            data.nombre,
            data.nacionalidad,
            data.email,
            password_hash,
            data.rol
        ))

        user_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return {
            "message": "Usuario creado",
            "user_id": user_id
        }

    except Exception as e:
        return {"error": str(e)}


@app.post("/auth/login")
def login(data: LoginRequest):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, password_hash, rol
            FROM users
            WHERE email = %s;
        """, (data.email,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:
            return {"error": "Credenciales inválidas"}

        user_id, password_hash, rol = user

        if not verify_password(data.password, password_hash):
            return {"error": "Credenciales inválidas"}

        token = create_access_token({
            "user_id": user_id,
            "rol": rol
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/me")
def get_me(user=Depends(get_current_user)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT user_id, nombre, nacionalidad, email, rol, fecha_creacion
            FROM users
            WHERE user_id = %s;
        """, (user["user_id"],))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return {"error": "Usuario no encontrado"}

        return {
            "user_id": row[0],
            "nombre": row[1],
            "nacionalidad": row[2],
            "email": row[3],
            "rol": row[4],
            "fecha_creacion": str(row[5])
        }

    except Exception as e:
        return {"error": str(e)}

@app.patch("/jobs/{job_id}")
def update_job(
    job_id: int,
    job: JobUpdate,
    user=Depends(get_current_user)
):
    if user["rol"] != "empleador":
        raise HTTPException(
            status_code=403,
            detail="Solo empleadores pueden editar trabajos"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1️⃣ Verificar que el job existe y es del usuario
        cur.execute("""
            SELECT user_id, estado
            FROM jobs
            WHERE job_id = %s;
        """, (job_id,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return {"error": "Trabajo no encontrado"}

        owner_id, estado = row

        if owner_id != user["user_id"]:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="No eres el propietario de este trabajo"
            )

        if estado == "cerrado":
            cur.close()
            conn.close()
            return {"error": "No se puede editar un trabajo cerrado"}

        # 2️⃣ Construir UPDATE dinámico
        fields = []
        values = []

        if job.titulo is not None:
            fields.append("titulo = %s")
            values.append(job.titulo)

        if job.descripcion is not None:
            fields.append("descripcion = %s")
            values.append(job.descripcion)

        if job.pago is not None:
            fields.append("pago = %s")
            values.append(job.pago)

        if job.ubicacion is not None:
            fields.append("ubicacion = %s")
            values.append(job.ubicacion)

        if job.fecha is not None:
            fields.append("fecha = %s")
            values.append(job.fecha)

        if not fields:
            cur.close()
            conn.close()
            return {"message": "Nada para actualizar"}

        query = f"""
            UPDATE jobs
            SET {", ".join(fields)}
            WHERE job_id = %s;
        """

        values.append(job_id)

        cur.execute(query, values)

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Trabajo actualizado correctamente"}

    except Exception as e:
        return {"error": str(e)}

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, user=Depends(get_current_user)):
    if user["rol"] != "empleador":
        raise HTTPException(
            status_code=403,
            detail="Solo empleadores pueden eliminar trabajos"
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1️⃣ Verificar propietario
        cur.execute("""
            SELECT user_id
            FROM jobs
            WHERE job_id = %s;
        """, (job_id,))
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return {"error": "Trabajo no encontrado"}

        owner_id = row[0]

        if owner_id != user["user_id"]:
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=403,
                detail="No eres el propietario de este trabajo"
            )

        # 2️⃣ Eliminar postulaciones primero (FK)
        cur.execute("""
            DELETE FROM postulaciones
            WHERE job_id = %s;
        """, (job_id,))

        # 3️⃣ Eliminar job
        cur.execute("""
            DELETE FROM jobs
            WHERE job_id = %s;
        """, (job_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Trabajo eliminado correctamente"}

    except Exception as e:
        return {"error": str(e)}

@app.get("/jobs/{job_id}/postulaciones")
def ver_postulaciones(job_id: int, user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1️⃣ Verificar que el job existe
        cur.execute("""
            SELECT user_id
            FROM jobs
            WHERE job_id = %s
        """, (job_id,))
        
        job = cur.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")

        job_owner_id = job[0]

        # 2️⃣ Validar que el usuario sea el dueño
        if job_owner_id != user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver estas postulaciones"
            )

        # 3️⃣ Obtener postulaciones
        cur.execute("""
            SELECT 
                p.postulacion_id,
                p.user_id,
                u.nombre,
                u.nacionalidad,
                p.mensaje,
                p.fecha_postulacion,
                p.estado
            FROM postulaciones p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.job_id = %s
            ORDER BY p.fecha_postulacion DESC
        """, (job_id,))

        rows = cur.fetchall()

        postulaciones = []
        for row in rows:
            postulaciones.append({
                "postulacion_id": row[0],
                "user_id": row[1],
                "nombre": row[2],
                "nacionalidad": row[3],
                "mensaje": row[4],
                "fecha_postulacion": str(row[5]),
                "estado": row[6]
            })

        return {
            "job_id": job_id,
            "total_postulaciones": len(postulaciones),
            "postulaciones": postulaciones
        }

    finally:
        cur.close()
        conn.close()

@app.get("/mis-postulaciones")
def mis_postulaciones(user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Validar rol
        if user["rol"] != "trabajador":
            raise HTTPException(
                status_code=403,
                detail="Solo los trabajadores pueden ver sus postulaciones"
            )

        # Obtener postulaciones del usuario
        cur.execute("""
            SELECT 
                p.postulacion_id,
                p.mensaje,
                p.fecha_postulacion,
                j.job_id,
                j.titulo,
                j.pago,
                j.ubicacion,
                j.estado,
                j.fecha
            FROM postulaciones p
            JOIN jobs j ON p.job_id = j.job_id
            WHERE p.user_id = %s
            ORDER BY p.fecha_postulacion DESC
        """, (user["user_id"],))

        rows = cur.fetchall()

        postulaciones = []
        for row in rows:
            postulaciones.append({
                "postulacion_id": row[0],
                "mensaje": row[1],
                "fecha_postulacion": str(row[2]),
                "job": {
                    "job_id": row[3],
                    "titulo": row[4],
                    "pago": float(row[5]) if row[5] else None,
                    "ubicacion": row[6],
                    "estado": row[7],
                    "fecha": str(row[8]) if row[8] else None
                }
            })

        return {
            "total": len(postulaciones),
            "postulaciones": postulaciones
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cur.close()
        conn.close()

from fastapi import HTTPException, Depends

@app.get("/mis-jobs")
def mis_jobs(user=Depends(get_current_user)):
    try:
        # ✅ Validar que sea empleador
        if user["rol"] != "empleador":
            raise HTTPException(
                status_code=403,
                detail="Solo los empleadores pueden ver sus trabajos"
            )

        conn = get_connection()
        cur = conn.cursor()

        query = """
        SELECT 
            job_id,
            user_id,
            titulo,
            descripcion,
            pago,
            ubicacion,
            fecha,
            estado,
            fecha_creacion
        FROM jobs
        WHERE user_id = %s
        ORDER BY fecha_creacion DESC;
        """

        cur.execute(query, (user["user_id"],))
        rows = cur.fetchall()

        jobs = []
        for row in rows:
            jobs.append({
                "job_id": row[0],
                "user_id": row[1],
                "titulo": row[2],
                "descripcion": row[3],
                "pago": float(row[4]) if row[4] else None,
                "ubicacion": row[5],
                "fecha": str(row[6]) if row[6] else None,
                "estado": row[7],
                "fecha_creacion": str(row[8])
            })

        return {
            "count": len(jobs),
            "jobs": jobs
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass