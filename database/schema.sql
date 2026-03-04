-- Tipo para el rol del usuario
create type user_role as enum ('trabajador', 'empleador');

-- Tipo para el estado del trabajo
create type job_status as enum ('abierto', 'cerrado');

create table users (
    user_id integer generated always as identity primary key,
    nombre varchar(50) not null,
    nacionalidad varchar(50),
    email varchar(100) unique not null,
    password_hash varchar(255) not null,
    rol user_role not null,
    fecha_creacion timestamp default current_timestamp
);

create table jobs (
    job_id integer generated always as identity primary key,
    user_id integer not null references users(user_id) on delete cascade,
    titulo varchar(100) not null,
    descripcion text,
    pago numeric(10,2),
    ubicacion varchar(100),
    fecha date,
    estado job_status default 'abierto',
    fecha_creacion timestamp default current_timestamp
);

create table postulaciones (
    postulacion_id integer generated always as identity primary key,
    job_id integer not null references jobs(job_id) on delete cascade,
    user_id integer not null references users(user_id) on delete cascade,
    mensaje text,
    fecha_postulacion timestamp default current_timestamp,
    
    unique (job_id, user_id)
);


-- Añadir estado a postulaciones
-- Tipo para estado de postulacion
create type postulacion_status as enum ('pendiente', 'aceptada', 'rechazada');

-- Agregar columna a la tabla existente
alter table postulaciones
add column estado postulacion_status default 'pendiente';
