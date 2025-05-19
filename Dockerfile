# Dockerfile para Django + PostgreSQL
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . /code/

# Crear directorios necesarios
RUN mkdir -p /code/static /code/media /code/app/static

# Exponer el puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "app/manage.py", "runserver", "0.0.0.0:8000"]
