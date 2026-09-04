FROM python:3.12-slim

# Instalar librerías de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY app/ app/
COPY migrations/ migrations/
COPY main.py .
COPY view_db.py .

# Variable de entorno para que Python reconozca los módulos internos
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Puerto por defecto (las plataformas como Render/Koyeb inyectan $PORT)
EXPOSE 8000

# Comando de inicio con soporte de puerto dinámico
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
