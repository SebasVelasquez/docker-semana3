#!/usr/bin/env bash
# Se ejecuta una sola vez, cuando se crea el Codespace.
# Prepara el archivo .env, que nunca viaja dentro del repositorio.
set -e

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  echo "[preparar] Ya existe un .env; no se toca."
else
  cp .env.example .env
  # Reemplaza la clave de ejemplo por una aleatoria.
  CLAVE="$(openssl rand -hex 16)"
  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${CLAVE}/" .env
  echo "[preparar] .env creado con una contraseña aleatoria."
fi

chmod +x probar.sh 2>/dev/null || true

echo
echo "======================================================"
echo " Entorno listo. Ahora ejecuta:"
echo
echo "   docker compose up --build -d"
echo "   ./probar.sh"
echo "======================================================"
