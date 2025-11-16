FROM python:3.11-slim

# Ver logs en tiempo real
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY . .

# Arranca el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
