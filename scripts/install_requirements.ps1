#!/usr/bin/env pwsh
<#
Install dependencies into the project's virtual environment.
Run from repository root.
#>

Write-Host "-> Activating virtualenv if present"
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Warning ".venv not found. Please create a virtualenv or run inside your environment.";
}

Write-Host "-> Upgrading pip"
python -m pip install --upgrade pip

if (Test-Path requirements.txt) {
    Write-Host "-> Installing requirements.txt"
    python -m pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt not found in repository root.";
}

Write-Host "-> Done. You can run './scripts/start_dev.ps1' to start the dev server."
