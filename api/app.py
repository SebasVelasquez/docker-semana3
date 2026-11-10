"""API mínima en Flask que guarda y consulta mensajes en PostgreSQL.

Esta API corre dentro de un contenedor y se conecta a la base de datos
que corre en OTRO contenedor. La conexión no usa "localhost": usa el
nombre del servicio definido en docker-compose.yml (por defecto "db").
"""

import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

# Los datos de conexión llegan como variables de entorno desde
# docker-compose.yml, que a su vez las lee del archivo .env.
# Fíjate en DB_HOST: vale "db", el NOMBRE DEL SERVICIO del contenedor
# de PostgreSQL. Docker resuelve ese nombre dentro de la red interna.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": os.environ.get("DB_PORT", "5432"),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "dbname": os.environ["DB_NAME"],
}


@contextmanager
def conexion_db():
    """Abre una conexión y garantiza que se cierre al terminar."""
    conexion = psycopg2.connect(**DB_CONFIG)
    try:
        yield conexion
    finally:
        conexion.close()


def esperar_base_de_datos(intentos=30, espera=2):
    """PostgreSQL tarda unos segundos en aceptar conexiones al arrancar.

    Sin esta espera, la API se cae en el primer intento y el contenedor
    muere antes de que la base de datos esté lista.
    """
    for intento in range(1, intentos + 1):
        try:
            with conexion_db() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute("SELECT 1")
            print(f"[api] Base de datos lista en el intento {intento}", flush=True)
            return
        except psycopg2.OperationalError as error:
            print(
                f"[api] Esperando a la base de datos ({intento}/{intentos}): {error}",
                flush=True,
            )
            time.sleep(espera)
    raise RuntimeError("No se pudo conectar a la base de datos")


def crear_tabla():
    """Crea la tabla 'mensajes' si todavía no existe."""
    with conexion_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS mensajes (
                    id         SERIAL PRIMARY KEY,
                    texto      TEXT NOT NULL,
                    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        conexion.commit()
    print("[api] Tabla 'mensajes' lista", flush=True)


@app.get("/")
def inicio():
    """Página de bienvenida: confirma que la API responde."""
    return jsonify(
        {
            "servicio": "api",
            "mensaje": "API de la Semana 3 funcionando",
            "se_conecta_a": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}",
            "endpoints": {
                "GET  /salud": "verifica la conexión con PostgreSQL",
                "POST /mensajes": "guarda un mensaje; cuerpo: {\"texto\": \"hola\"}",
                "GET  /mensajes": "lista los mensajes guardados",
            },
        }
    )


@app.get("/salud")
def salud():
    """Prueba de vida: pregunta su versión a PostgreSQL."""
    try:
        with conexion_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
        return jsonify(
            {
                "api": "ok",
                "base_de_datos": "ok",
                "host_base_de_datos": DB_CONFIG["host"],
                "version_postgres": version,
            }
        )
    except psycopg2.Error as error:
        return (
            jsonify({"api": "ok", "base_de_datos": "error", "detalle": str(error)}),
            503,
        )


@app.post("/mensajes")
def crear_mensaje():
    """Guarda un mensaje en PostgreSQL (el contenedor vecino)."""
    datos = request.get_json(silent=True) or {}
    texto = str(datos.get("texto", "")).strip()
    if not texto:
        return jsonify({"error": "Falta el campo 'texto' en el cuerpo JSON"}), 400

    with conexion_db() as conexion:
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO mensajes (texto) VALUES (%s) "
                "RETURNING id, texto, creado_en",
                (texto,),
            )
            fila = cursor.fetchone()
        conexion.commit()

    return jsonify({"guardado": True, "mensaje": fila}), 201


@app.get("/mensajes")
def listar_mensajes():
    """Lee de PostgreSQL todos los mensajes guardados."""
    with conexion_db() as conexion:
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, texto, creado_en FROM mensajes ORDER BY id")
            filas = cursor.fetchall()

    return jsonify({"total": len(filas), "mensajes": filas})


if __name__ == "__main__":
    esperar_base_de_datos()
    crear_tabla()
    # host="0.0.0.0" es obligatorio dentro de un contenedor: con el valor
    # por defecto (127.0.0.1) la API solo se oiría a sí misma y no
    # responderían ni tu navegador ni el otro contenedor.
    app.run(host="0.0.0.0", port=5000)
