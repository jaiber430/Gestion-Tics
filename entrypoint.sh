#!/bin/sh
# =============================================================================
# entrypoint.sh – Secuencia de arranque del contenedor app
# =============================================================================
# 1. Espera a que MySQL esté listo (hasta 60 intentos × 2 s = 2 min).
# 2. Ejecuta migraciones Django.
# 3. Recolecta archivos estáticos.
# 4. Crea/actualiza el usuario administrador inicial.
# 5. Arranca Gunicorn.
# =============================================================================
set -e

echo "[entrypoint] Esperando disponibilidad de MySQL..."
python - <<'PYEOF'
import socket, sys, time, os

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "3306"))

for attempt in range(90):
    try:
        with socket.create_connection((host, port), timeout=3):
            pass
        print(f"[entrypoint] Puerto MySQL abierto tras {attempt + 1} intento(s).")
        # Pequeña espera extra para que MySQL finalice el init SQL si aún corre.
        time.sleep(3)
        sys.exit(0)
    except OSError as exc:
        print(f"[entrypoint] Intento {attempt + 1}/90 - {exc}")
        time.sleep(2)

print("[entrypoint] MySQL no respondio en 3 minutos. Abortando.")
sys.exit(1)
PYEOF

echo "[entrypoint] Ejecutando migraciones..."
python manage.py migrate --noinput

echo "[entrypoint] Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "[entrypoint] Creando usuario administrador inicial (idempotente)..."
python manage.py create_admin

echo "[entrypoint] Iniciando Gunicorn..."
exec gunicorn Gestion.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
