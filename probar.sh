#!/usr/bin/env bash
# Ejecuta todas las pruebas de la entrega y muestra la evidencia
# ordenada, lista para tomar capturas de pantalla.
#
#   Uso:   ./probar.sh
#
# Antes de correrlo, los contenedores deben estar arriba:
#   docker compose up --build -d

cd "$(dirname "$0")"

# Lee las credenciales del .env para no escribirlas aquí.
set -a
# shellcheck disable=SC1091
. ./.env
set +a

PUERTO="${API_PORT:-5000}"
URL="http://localhost:${PUERTO}"

titulo() {
  echo
  echo "=================================================================="
  echo "  $1"
  echo "=================================================================="
}

titulo "1. LOS DOS CONTENEDORES ESTAN CORRIENDO  (docker ps)"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

titulo "2. LA RED QUE COMPARTEN  (docker network inspect)"
RED="$(docker network ls --filter name=red-app --format '{{.Name}}' | head -1)"
echo "Red: ${RED}"
docker network inspect "${RED}" \
  --format '{{range .Containers}}  {{.Name}}  ->  {{.IPv4Address}}{{"\n"}}{{end}}'

titulo "3. LA API RESPONDE  (GET /)"
curl -s "${URL}/" | python3 -m json.tool

titulo "4. LA API ALCANZA A POSTGRESQL  (GET /salud)"
echo ">>> Si 'base_de_datos' dice 'ok', los dos contenedores se comunican."
curl -s "${URL}/salud" | python3 -m json.tool

titulo "5. GUARDAR UN MENSAJE EN LA BASE DE DATOS  (POST /mensajes)"
curl -s -X POST "${URL}/mensajes" \
  -H "Content-Type: application/json" \
  -d '{"texto": "Hola desde la Semana 3"}' | python3 -m json.tool

curl -s -X POST "${URL}/mensajes" \
  -H "Content-Type: application/json" \
  -d '{"texto": "Segundo mensaje de prueba"}' | python3 -m json.tool

titulo "6. CONSULTAR LOS MENSAJES GUARDADOS  (GET /mensajes)"
curl -s "${URL}/mensajes" | python3 -m json.tool

titulo "7. VALIDACION: un mensaje vacio se rechaza  (debe dar error 400)"
curl -s -o /tmp/resp.json -w "Codigo HTTP: %{http_code}\n" \
  -X POST "${URL}/mensajes" \
  -H "Content-Type: application/json" \
  -d '{"texto": "   "}'
cat /tmp/resp.json | python3 -m json.tool

titulo "8. EL DATO ESTA DE VERDAD EN POSTGRESQL  (consulta directa)"
echo ">>> Esto entra al OTRO contenedor y consulta la tabla directamente."
docker compose exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
  -c "SELECT id, texto, creado_en FROM mensajes ORDER BY id;"

titulo "9. EL NOMBRE 'db' SE RESUELVE DENTRO DE LA RED  (DNS de Docker)"
echo ">>> Prueba de que NO se usa localhost sino el nombre del servicio."
docker compose exec -T api \
  python -c "import socket; print('El nombre db apunta a la IP:', socket.gethostbyname('db'))"

echo
echo "=================================================================="
echo "  PRUEBAS TERMINADAS"
echo "=================================================================="
echo
