#!/usr/bin/env pwsh
<#
Start the development server for RadGestMat.
Run from repository root. Assumes virtualenv exists at ./.venv
#>

Write-Host "-> Activating virtualenv"
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Warning ".venv not found. Activate your environment manually.";
}

# Keep local development isolated from the production .env and database.
$env:ENVIRONMENT = "development"
$env:DJANGO_SETTINGS_MODULE = "radgestmat.settings.development"
$env:DB_ENGINE = "django.db.backends.sqlite3"
$env:DB_NAME = Join-Path (Get-Location) "db.dev.sqlite3"
$env:DEBUG = "True"

Write-Host "-> Applying migrations"
python manage.py migrate

Write-Host "-> Collecting static files"
python manage.py collectstatic --noinput

Write-Host "-> Starting development server on 0.0.0.0:8001"
python manage.py runserver 0.0.0.0:8001
