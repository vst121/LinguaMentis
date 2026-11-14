[CmdletBinding()]
param(
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"

# Prevent PowerShell 7+ from turning native stderr output into terminating errors
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$ComposeFile = Join-Path $RootDir "docker-compose.yml"
$EnvFile = Join-Path $BackendDir ".env"
$EnvExampleFile = Join-Path $BackendDir ".env.example"

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-QuietNative([scriptblock]$Command) {
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Command 2>&1 | Out-Null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevPreference
    }
}

function Stop-ProcessTree([int]$ParentId) {
    if ($ParentId -le 0) {
        return
    }
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ParentId $child.ProcessId
    }
    Stop-Process -Id $ParentId -Force -ErrorAction SilentlyContinue
}

# Ensure uv is discoverable if installed in the default user bin directory
$UvLocalBin = Join-Path $env:USERPROFILE ".local\bin"
if ((Test-Path $UvLocalBin) -and ($env:Path -notlike "*$UvLocalBin*")) {
    $env:Path = "$UvLocalBin;$env:Path"
}

Write-Step "Checking required tools..."
foreach ($tool in @("docker", "uv", "node")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required tool '$tool' was not found in PATH. Install it and try again."
    }
}

$PkgManager = if (Get-Command "pnpm" -ErrorAction SilentlyContinue) {
    "pnpm"
} elseif (Get-Command "npm.cmd" -ErrorAction SilentlyContinue) {
    "npm"
} elseif (Get-Command "npm" -ErrorAction SilentlyContinue) {
    "npm"
} else {
    throw "Neither 'pnpm' nor 'npm' was found in PATH."
}

Write-Step "Checking backend environment configuration (.env)..."
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExampleFile) {
        Copy-Item $EnvExampleFile $EnvFile
        Write-Warning "Created backend\.env from .env.example. Set GEMINI_API_KEY before using AI features."
    } else {
        throw "Neither backend\.env nor backend\.env.example was found."
    }
}

$EnvLines = Get-Content $EnvFile -ErrorAction SilentlyContinue
$GeminiLine = $EnvLines | Where-Object { $_ -match "^\s*GEMINI_API_KEY\s*=" } | Select-Object -First 1
if (-not $GeminiLine -or $GeminiLine -match "your-gemini-api-key|=\s*$") {
    Write-Warning "GEMINI_API_KEY does not appear to be configured in backend\.env. AI challenges and evaluations will fail until a valid key is set."
}

Write-Step "Checking Docker daemon..."
if ((Invoke-QuietNative { docker info }) -ne 0) {
    throw "Docker is not running. Start Docker Desktop and try again."
}

Write-Step "Starting PostgreSQL container..."
$prevPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    docker compose -f $ComposeFile up -d postgres
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start the PostgreSQL container."
    }
} finally {
    $ErrorActionPreference = $prevPreference
}

Write-Host "Waiting for PostgreSQL to accept connections..." -ForegroundColor DarkGray
$PgReady = $false
for ($i = 0; $i -lt 30; $i++) {
    if ((Invoke-QuietNative { docker compose -f $ComposeFile exec -T postgres pg_isready -U linguamentis -d linguamentis }) -eq 0) {
        $PgReady = $true
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $PgReady) {
    throw "PostgreSQL did not become ready on port 5438 in time."
}

if (-not $SkipSync) {
    Write-Step "Syncing backend dependencies (uv sync)..."
    Push-Location $BackendDir
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        uv sync
        if ($LASTEXITCODE -ne 0) {
            throw "'uv sync' failed with exit code $LASTEXITCODE."
        }
    } finally {
        $ErrorActionPreference = $prevPreference
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Step "Installing frontend dependencies ($PkgManager install)..."
    Push-Location $FrontendDir
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PkgManager install
        if ($LASTEXITCODE -ne 0) {
            throw "'$PkgManager install' failed with exit code $LASTEXITCODE."
        }
    } finally {
        $ErrorActionPreference = $prevPreference
        Pop-Location
    }
}

$BackendProc = $null
$FrontendProc = $null

try {
    Write-Step "Starting Backend (FastAPI) and Frontend (Next.js)..."
    $BackendProc = Start-Process -FilePath "uv" `
        -ArgumentList @("run", "python", "-m", "uvicorn", "linguamentis.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -NoNewWindow `
        -PassThru

    $FrontendCmd = if ($PkgManager -eq "pnpm") { "pnpm dev" } else { "npm run dev" }
    $FrontendProc = Start-Process -FilePath "cmd.exe" `
        -ArgumentList @("/c", $FrontendCmd) `
        -WorkingDirectory $FrontendDir `
        -NoNewWindow `
        -PassThru

    Write-Host "`nLinguaMentis is running:" -ForegroundColor Green
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Green
    Write-Host "  - Backend:  http://127.0.0.1:8000/health" -ForegroundColor Green
    Write-Host "  - API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop Backend and Frontend (PostgreSQL will keep running in Docker).`n" -ForegroundColor Yellow

    while ($true) {
        if ($BackendProc.HasExited) {
            Write-Warning "Backend process exited unexpectedly (exit code $($BackendProc.ExitCode))."
            break
        }
        if ($FrontendProc.HasExited) {
            Write-Warning "Frontend process exited unexpectedly (exit code $($FrontendProc.ExitCode))."
            break
        }
        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host "`nStopping Backend and Frontend..." -ForegroundColor Yellow
    if ($FrontendProc -and -not $FrontendProc.HasExited) {
        Stop-ProcessTree -ParentId $FrontendProc.Id
    }
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-ProcessTree -ParentId $BackendProc.Id
    }
    Write-Host "Services stopped." -ForegroundColor Yellow
}
