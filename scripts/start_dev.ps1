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

Write-Host "-> Applying migrations"
python manage.py migrate

Write-Host "-> Collecting static files"
python manage.py collectstatic --noinput

Write-Host "-> Starting development server on 0.0.0.0:8001"
python manage.py runserver 0.0.0.0:8001
