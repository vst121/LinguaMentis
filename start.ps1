[CmdletBinding()]
param(
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$ComposeFile = Join-Path $RootDir "docker-compose.yml"
$EnvFile = Join-Path $BackendDir ".env"
$EnvExampleFile = Join-Path $BackendDir ".env.example"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Stop-ProcessTree([int]$ParentId) {
    if ($ParentId -le 0) { return }
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ParentId $child.ProcessId
    }
    Stop-Process -Id $ParentId -Force -ErrorAction SilentlyContinue
}

# Ensure uv is discoverable if installed in the default user bin path
$UvLocalBin = Join-Path $env:USERPROFILE ".local\bin"
if ((Test-Path $UvLocalBin) -and ($env:Path -notlike "*$UvLocalBin*")) {
    $env:Path = "$UvLocalBin;$env:Path"
}

Write-Step "Verificando herramientas necesarias..."
foreach ($tool in @("docker", "uv", "node")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "No se encontró '$tool' en el PATH. Instálalo y vuelve a intentarlo."
    }
}

$PkgManager = if (Get-Command "pnpm" -ErrorAction SilentlyContinue) { "pnpm" }
elseif (Get-Command "npm.cmd" -ErrorAction SilentlyContinue) { "npm" }
else { Write-Error "No se encontró 'pnpm' ni 'npm' en el PATH." }

Write-Step "Comprobando configuración (.env)..."
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExampleFile) {
        Copy-Item $EnvExampleFile $EnvFile
        Write-Warning "Se creó backend\.env desde .env.example. Edita GEMINI_API_KEY antes de usar la IA."
    } else {
        Write-Error "No existe backend\.env ni backend\.env.example."
    }
}

$EnvLines = Get-Content $EnvFile -ErrorAction SilentlyContinue
$GeminiLine = $EnvLines | Where-Object { $_ -match "^\s*GEMINI_API_KEY\s*=" } | Select-Object -First 1
if (-not $GeminiLine -or $GeminiLine -match "your-gemini-api-key|\=\s*$") {
    Write-Warning "GEMINI_API_KEY no parece configurada en backend\.env. Los retos y evaluaciones con IA fallarán hasta que añadas una clave válida."
}

Write-Step "Verificando Docker..."
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker no está en ejecución. Abre Docker Desktop y vuelve a intentarlo."
}

Write-Step "Iniciando PostgreSQL..."
docker compose -f $ComposeFile up -d postgres
if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo iniciar el contenedor de PostgreSQL."
}

Write-Host "Esperando a que PostgreSQL acepte conexiones..." -ForegroundColor DarkGray
$PgReady = $false
for ($i = 0; $i -lt 30; $i++) {
    docker compose -f $ComposeFile exec -T postgres pg_isready -U linguamentis -d linguamentis *> $null
    if ($LASTEXITCODE -eq 0) {
        $PgReady = $true
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $PgReady) {
    Write-Error "PostgreSQL no respondió a tiempo en el puerto 5438."
}

if (-not $SkipSync) {
    Write-Step "Sincronizando dependencias del backend (uv sync)..."
    Push-Location $BackendDir
    try {
        uv sync
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falló 'uv sync'."
        }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Step "Instalando dependencias del frontend ($PkgManager install)..."
    Push-Location $FrontendDir
    try {
        & $PkgManager install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Falló '$PkgManager install'."
        }
    } finally {
        Pop-Location
    }
}

$BackendProc = $null
$FrontendProc = $null

try {
    Write-Step "Iniciando Backend (FastAPI) y Frontend (Next.js)..."
    $BackendProc = Start-Process -FilePath "uv" `
        -ArgumentList @("run", "uvicorn", "linguamentis.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -NoNewWindow `
        -PassThru

    $FrontendCmd = if ($PkgManager -eq "pnpm") { "pnpm dev" } else { "npm run dev" }
    $FrontendProc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/c", $FrontendCmd) `
        -WorkingDirectory $FrontendDir `
        -NoNewWindow `
        -PassThru

    Write-Host "`nLinguaMentis iniciado:" -ForegroundColor Green
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Green
    Write-Host "  - Backend:  http://127.0.0.1:8000/health" -ForegroundColor Green
    Write-Host "  - API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
    Write-Host "`nPulsa Ctrl+C para detener Backend y Frontend (PostgreSQL seguirá activo en Docker).`n" -ForegroundColor Yellow

    while ($true) {
        if ($BackendProc.HasExited) {
            Write-Warning "El proceso del Backend finalizó inesperadamente (código $($BackendProc.ExitCode))."
            break
        }
        if ($FrontendProc.HasExited) {
            Write-Warning "El proceso del Frontend finalizó inesperadamente (código $($FrontendProc.ExitCode))."
            break
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "`nDeteniendo Backend y Frontend..." -ForegroundColor Yellow
    if ($FrontendProc -and -not $FrontendProc.HasExited) {
        Stop-ProcessTree -ParentId $FrontendProc.Id
    }
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-ProcessTree -ParentId $BackendProc.Id
    }
    Write-Host "Servicios detenidos." -ForegroundColor Yellow
}
