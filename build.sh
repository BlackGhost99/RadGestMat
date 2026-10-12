#!/usr/bin/env bash
# Build Render : dépendances + fichiers statiques
set -o errexit

pip install -r requirements.txt
mkdir -p media
python manage.py collectstatic --noinput
