#!/usr/bin/env pwsh
<#
Backup the project's database.
Supports SQLite (default) or PostgreSQL if env vars present.
Run from repository root.
#>

param(
    [string]$BackupDir = ".\backups"
)

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir | Out-Null }

# Detect SQLite database file (common default)
$sqliteFile = 'db.sqlite3'
if (Test-Path $sqliteFile) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmm"
    $dest = Join-Path $BackupDir "db_sqlite_$timestamp.sqlite3"
    Copy-Item $sqliteFile $dest -Force
    Write-Host "SQLite DB backed up to: $dest"
    exit 0
}

# If not SQLite, attempt pg_dump using environment variables
if ($env:PGHOST -or $env:POSTGRES_HOST) {
    $pgHost = $env:PGHOST ? $env:PGHOST : $env:POSTGRES_HOST
    $pgUser = $env:PGUSER ? $env:PGUSER : ($env:POSTGRES_USER ? $env:POSTGRES_USER : 'postgres')
    $pgDb   = $env:PGDATABASE ? $env:PGDATABASE : ($env:POSTGRES_DB ? $env:POSTGRES_DB : 'radgestmat_db')
    $timestamp = Get-Date -Format "yyyyMMdd_HHmm"
    $dest = Join-Path $BackupDir "pg_dump_${pgDb}_$timestamp.dump"
    Write-Host "Running pg_dump against $pgHost/$pgDb as $pgUser"
    pg_dump -h $pgHost -U $pgUser -Fc -f $dest $pgDb
    if ($LASTEXITCODE -eq 0) { Write-Host "Postgres dump saved to: $dest" } else { Write-Error "pg_dump failed (exit $LASTEXITCODE)" }
    exit $LASTEXITCODE
}

Write-Warning "No known database found (neither $sqliteFile nor PG env vars). Provide manual backup steps or set env vars for Postgres."
