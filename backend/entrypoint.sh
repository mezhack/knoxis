#!/bin/sh
set -e

echo "Aguardando banco de dados..."
python manage.py wait_for_db 2>/dev/null || sleep 3

echo "Rodando migrations..."
python manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "Iniciando Gunicorn..."
exec gunicorn knoxis.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 60 \
  --log-level info
