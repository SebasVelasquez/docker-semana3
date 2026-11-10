# Semana 3 — Dos contenedores Docker comunicados entre sí

> 📄 **¿Vienes a calificar la actividad?** El documento de entrega, con el
> paso a paso y las capturas de evidencia, está en **[ENTREGA.md](ENTREGA.md)**.

Proyecto de ejemplo con **dos contenedores** que se comunican por una red
privada de Docker:

| Contenedor | Servicio | Qué hace | Imagen |
|---|---|---|---|
| `semana3-api` | `api` | API en Python/Flask que guarda y consulta mensajes | se construye con `api/Dockerfile` |
| `semana3-db` | `db` | Base de datos PostgreSQL que almacena esos mensajes | `postgres:16-alpine` (oficial) |

---

## 1. Qué hace cada contenedor

### Contenedor 1 — la API (`api`)

Una aplicación Flask muy pequeña con cuatro rutas:

| Método y ruta | Para qué sirve |
|---|---|
| `GET /` | Página de bienvenida; confirma que la API responde |
| `GET /salud` | Le pregunta la versión a PostgreSQL: **prueba que los dos contenedores se hablan** |
| `POST /mensajes` | Guarda un mensaje en la base de datos |
| `GET /mensajes` | Devuelve todos los mensajes guardados |

Se construye a partir de `api/Dockerfile`, que parte de la imagen oficial
de Python 3.12, instala Flask y el conector de PostgreSQL, copia `app.py`
y lo ejecuta.

### Contenedor 2 — la base de datos (`db`)

PostgreSQL 16 con la imagen oficial, sin modificar. Al arrancar por
primera vez crea el usuario, la contraseña y la base de datos que le
indican las variables de entorno. Los datos se guardan en un **volumen**
llamado `datos-db`, así que sobreviven aunque borres el contenedor.

La API crea sola la tabla al arrancar:

```sql
CREATE TABLE IF NOT EXISTS mensajes (
    id         SERIAL PRIMARY KEY,
    texto      TEXT NOT NULL,
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 2. Cómo se comunican los contenedores

Esta es la parte central de la entrega.

```
            tu PC (Windows)
                  │
                  │  http://localhost:5000      ← único puerto publicado
                  ▼
   ┌──────────────────────────────────────────────┐
   │   red de Docker:  red-app  (driver bridge)   │
   │                                              │
   │   ┌───────────────┐      ┌────────────────┐  │
   │   │  semana3-api  │─────▶│   semana3-db   │  │
   │   │  Flask :5000  │ 5432 │ PostgreSQL     │  │
   │   └───────────────┘      └────────────────┘  │
   │         "api"                   "db"         │
   └──────────────────────────────────────────────┘
```

**Tres ideas para explicar en la sustentación:**

1. **Red común.** En `docker-compose.yml` se declara la red `red-app` y
   los dos servicios se conectan a ella. Solo los contenedores de esa red
   se ven entre sí.

2. **Se llaman por el nombre del servicio, no por `localhost`.** Docker
   tiene un DNS interno: dentro de la red, el nombre `db` resuelve a la
   dirección IP del contenedor de PostgreSQL. Por eso la API se configura
   con `DB_HOST: db`.

   > ⚠️ `localhost` **no** funcionaría: dentro de un contenedor,
   > `localhost` es *ese mismo contenedor*. La API se estaría buscando a
   > sí misma en el puerto 5432, donde no hay nada.

3. **La base de datos no se publica al exterior.** El contenedor `db` no
   tiene sección `ports:`, así que su puerto 5432 **solo** es alcanzable
   desde dentro de `red-app`. El único puerto abierto hacia tu PC es el
   5000 de la API. Eso es, a la vez, buena práctica de seguridad y la
   prueba de que la comunicación ocurre por la red interna de Docker.

### Orden de arranque

PostgreSQL tarda unos segundos en aceptar conexiones. El proyecto lo
resuelve por partida doble:

- `healthcheck` en `db` + `depends_on: condition: service_healthy` en
  `api`: Compose no arranca la API hasta que PostgreSQL responde.
- La función `esperar_base_de_datos()` en `app.py` reintenta hasta 30
  veces, por si acaso.

---

## 3. Variables de entorno (`.env`)

Las credenciales **no van escritas en el código ni en el compose**. Viven
en un archivo `.env` que Docker Compose lee solo y que `.gitignore`
excluye del repositorio.

| Archivo | ¿Se sube a GitHub? | Para qué |
|---|---|---|
| `.env` | ❌ No | Credenciales reales de tu máquina |
| `.env.example` | ✅ Sí | Plantilla: dice qué variables hacen falta, sin revelar valores |

Variables usadas:

| Variable | Para qué |
|---|---|
| `POSTGRES_USER` | Usuario de la base de datos |
| `POSTGRES_PASSWORD` | Su contraseña |
| `POSTGRES_DB` | Nombre de la base de datos |
| `API_PORT` | Puerto de tu PC por donde verás la API |

---

## 4. Cómo levantar el proyecto

### Opción A — GitHub Codespaces (recomendada, no instala nada)

El repositorio trae un `.devcontainer/` que prepara Docker
automáticamente, así que no necesitas instalar nada en tu computador.

1. En GitHub, botón verde **`<> Code`** → pestaña **Codespaces** →
   **Create codespace on main**.
2. Espera 2–3 minutos a que termine de construirse. Al final verás en la
   terminal el mensaje `Entorno listo`.
3. En la terminal del Codespace:

```bash
docker compose up --build -d   # levanta los dos contenedores
./probar.sh                    # ejecuta todas las pruebas
```

El archivo `.env` se genera solo, con una contraseña aleatoria.

### Opción B — En tu propio computador

**Requisito:** tener instalado Docker Desktop (incluye `docker compose`).

```bash
# 1. Clonar el repositorio y entrar en la carpeta
git clone <URL-DEL-REPOSITORIO>
cd docker-semana3

# 2. Crear tu archivo .env a partir de la plantilla
cp .env.example .env        # en PowerShell: copy .env.example .env

# 3. Editar .env y poner una contraseña propia

# 4. Construir las imágenes y levantar los dos contenedores
docker compose up --build
```

Para dejarlo corriendo en segundo plano, añade `-d`:

```bash
docker compose up --build -d
```

### Comprobar que ambos contenedores están arriba

```bash
docker ps
```

Debes ver **dos** contenedores: `semana3-api` y `semana3-db`, ambos en
estado `Up` (el de la base de datos, además, como `healthy`).

### Ver los registros

```bash
docker compose logs -f api
```

### Apagar

```bash
docker compose down          # detiene y borra los contenedores
docker compose down -v       # además borra el volumen con los datos
```

---

## 5. Cómo probar la comunicación

### Todas las pruebas de una vez

El proyecto incluye un script que ejecuta las nueve comprobaciones
seguidas, con la salida ordenada:

```bash
./probar.sh
```

Si prefieres hacerlas una por una, aquí están:

### a) Prueba de vida con la base de datos

```bash
curl http://localhost:5000/salud
```

La API abre una conexión contra el host `db` y le pregunta su versión.
Si responde `"base_de_datos": "ok"` junto con la versión de PostgreSQL,
**los dos contenedores se están comunicando**.

### b) Guardar un mensaje (escribe en PostgreSQL)

```bash
curl -X POST http://localhost:5000/mensajes \
  -H "Content-Type: application/json" \
  -d "{\"texto\": \"Hola desde la Semana 3\"}"
```

Responde `201` con el registro guardado, incluidos el `id` que generó
PostgreSQL y la marca de tiempo `creado_en`.

### c) Consultar los mensajes (lee de PostgreSQL)

```bash
curl http://localhost:5000/mensajes
```

Devuelve el total y la lista de mensajes almacenados.

### d) Comprobarlo directamente en la base de datos

Para ver que el dato quedó de verdad en PostgreSQL y no en la memoria de
la API:

```bash
docker compose exec db psql -U usuario_app -d semana3 -c "SELECT * FROM mensajes;"
```

### e) Prueba opcional: la red por dentro

Desde el contenedor de la API, resolver el nombre `db`:

```bash
docker compose exec api python -c "import socket; print(socket.gethostbyname('db'))"
```

Imprime la IP privada del contenedor de PostgreSQL dentro de `red-app`.

---

## 6. Estructura del proyecto

```
docker-semana3/
├── .devcontainer/
│   ├── devcontainer.json   # prepara Docker dentro de GitHub Codespaces
│   └── preparar.sh         # genera el .env al crear el Codespace
├── api/
│   ├── Dockerfile          # receta de la imagen de la API
│   ├── app.py              # la aplicación Flask
│   └── requirements.txt    # Flask + psycopg2-binary
├── .env                    # credenciales reales (NO se sube)
├── .env.example            # plantilla de credenciales (sí se sube)
├── .gitattributes          # fuerza finales de línea LF
├── .gitignore              # ignora .env, __pycache__, etc.
├── docker-compose.yml      # define los 2 servicios, la red y el volumen
├── probar.sh               # ejecuta todas las pruebas de la entrega
└── README.md
```

---

## 7. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `connection refused` al hacer curl | Los contenedores aún no terminan de arrancar. Espera unos segundos y mira `docker compose logs api` |
| `could not translate host name "db"` | El servicio no está en la misma red. Revisa la sección `networks:` de ambos servicios |
| `port is already allocated` | El puerto 5000 está ocupado en tu PC. Cambia `API_PORT` en `.env` (por ejemplo a `5001`) y vuelve a levantar |
| `password authentication failed` | Cambiaste la contraseña en `.env` pero el volumen conserva la antigua. Ejecuta `docker compose down -v` y vuelve a levantar |
| La API arranca y se cae | Mira `docker compose logs api`; normalmente es que `.env` no existe o le falta una variable |
