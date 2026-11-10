# Imagen base: Python 3.12 en su versión "slim" (ligera).
FROM python:3.12-slim

# Carpeta de trabajo dentro del contenedor. Todo lo que sigue ocurre aquí.
WORKDIR /app

# Se copia primero SOLO requirements.txt y se instala.
# Así Docker guarda en caché la instalación: si luego cambias app.py,
# no vuelve a descargar las librerías y la construcción es más rápida.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora sí, el código de la aplicación.
COPY app.py .

# Python escribe los print() de inmediato en vez de guardarlos en
# memoria: sin esto, "docker compose logs" se vería vacío.
ENV PYTHONUNBUFFERED=1

# Documenta que el contenedor escucha en el 5000 (no publica nada por
# sí solo; la publicación se hace en docker-compose.yml).
EXPOSE 5000

# Comando que se ejecuta al arrancar el contenedor.
CMD ["python", "app.py"]
