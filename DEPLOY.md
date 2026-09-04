# Guía Paso a Paso para Desplegar el Backend Gratis 🚀

Para desplegar este proyecto 100% gratis utilizaremos:
1. **Base de Datos (PostgreSQL en la Nube)**: **Supabase** (Free Tier: 500 MB, extensiones nativas `pg_trgm` y `unaccent`).
2. **Backend (FastAPI)**: **Render.com** (Free Web Service) o **Koyeb**.

---

## 🗄️ PASO 1: Crear la Base de Datos PostgreSQL en Supabase (Gratis)

1. Ve a [supabase.com](https://supabase.com/) e inicia sesión (con tu cuenta de GitHub o correo).
2. Crea una nueva organización y haz clic en **"New Project"**.
   - Nombre: `libros-bolivia`
   - Database Password: *(Guarda una contraseña segura)*
   - Región: Selecciona la más cercana (ej: `South America (São Paulo)` o `US East`).
3. Una vez creado el proyecto:
   - Ve a la pestaña **SQL Editor** (a la izquierda).
   - Abre el archivo [`migrations/001_schema.sql`](migrations/001_schema.sql), copia todo su contenido, pégalo en el editor de Supabase y haz clic en **Run**.
   - Haz lo mismo con el archivo [`migrations/002_seed_stores.sql`](migrations/002_seed_stores.sql) y haz clic en **Run**.
   - *¡Listo! Tu base de datos PostgreSQL ya tiene las extensiones pg_trgm, unaccent, tablas e índices listos.*
4. Obtén tu URL de conexión:
   - Ve a **Project Settings** (ícono de engranaje) $\rightarrow$ **Database**.
   - En la sección **Connection string**, selecciona la pestaña **URI**.
   - Copia la URL que luce así:
     `postgresql://postgres.[tu-id]:[tu-password]@aws-0-[region].pooler.supabase.com:6543/postgres`

---

## ⚡ PASO 2: Desplegar el Backend en Render.com (Gratis)

1. Ve a [render.com](https://render.com/) e inicia sesión con tu GitHub.
2. Haz clic en **New +** $\rightarrow$ **Web Service**.
3. Selecciona tu repositorio `librerias-bolivia-api`.
4. Completa la configuración:
   - **Name**: `librerias-bolivia-api`
   - **Language**: `Python 3`
   - **Region**: La misma de tu Supabase (ej: `US East` o `Frankfurt`).
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. En la sección **Environment Variables**, añade:
   - `DATABASE_URL` = *(Pega aquí la URI de Supabase del Paso 1)*
   - `USE_SQLITE_FALLBACK` = `false`
6. Haz clic en **Create Web Service**.

En 2 minutos Render compilará el contenedor y te entregará una URL pública con HTTPS activo:
👉 `https://librerias-bolivia-api.onrender.com/docs`
