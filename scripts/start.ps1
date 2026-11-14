[CmdletBinding()]
param(
    [switch]$SkipSync
)

$ErrorActionPreference = "Stop"

# Prevent PowerShell 7+ from turning native stderr output into terminating errors
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$RunningOnWindows = if ($PSVersionTable.PSEdition -eq "Core") { $IsWindows } else { $true }
$PathSep = [System.IO.Path]::PathSeparator

$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptsDir
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
    if ($RunningOnWindows) {
        $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue
        foreach ($child in $children) {
            Stop-ProcessTree -ParentId $child.ProcessId
        }
        Stop-Process -Id $ParentId -Force -ErrorAction SilentlyContinue
    } else {
        $prevPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $childPids = @()
            if (Get-Command "pgrep" -ErrorAction SilentlyContinue) {
                $childPids = pgrep -P $ParentId 2>$null
            } elseif (Get-Command "ps" -ErrorAction SilentlyContinue) {
                $childPids = ps -o pid= --ppid $ParentId 2>$null
            }
            foreach ($childPid in $childPids) {
                $parsed = 0
                if ([int]::TryParse(($childPid.ToString().Trim()), [ref]$parsed)) {
                    Stop-ProcessTree -ParentId $parsed
                }
            }
        } finally {
            $ErrorActionPreference = $prevPreference
        }
        Stop-Process -Id $ParentId -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-PostgresReady {
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
    for ($i = 0; $i -lt 30; $i++) {
        if ((Invoke-QuietNative { docker compose -f $ComposeFile exec -T postgres pg_isready -U linguamentis -d linguamentis }) -eq 0) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "PostgreSQL did not become ready on port 5438 in time."
}

function Restart-Postgres {
    Write-Step "Restarting PostgreSQL container..."
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        docker compose -f $ComposeFile restart postgres
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to restart the PostgreSQL container."
        }
    } finally {
        $ErrorActionPreference = $prevPreference
    }

    Write-Host "Waiting for PostgreSQL to accept connections..." -ForegroundColor DarkGray
    for ($i = 0; $i -lt 30; $i++) {
        if ((Invoke-QuietNative { docker compose -f $ComposeFile exec -T postgres pg_isready -U linguamentis -d linguamentis }) -eq 0) {
            Write-Host "PostgreSQL is ready." -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 1
    }
    throw "PostgreSQL did not become ready on port 5438 in time."
}

function Start-BackendProcess {
    return Start-Process -FilePath "uv" `
        -ArgumentList @("run", "python", "-m", "uvicorn", "linguamentis.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $BackendDir `
        -NoNewWindow `
        -PassThru
}

function Start-FrontendProcess([string]$PackageManager) {
    # Remove production build output if present so next dev does not mix manifests with vendor-chunks
    $nextDir = Join-Path $FrontendDir ".next"
    if (Test-Path (Join-Path $nextDir "BUILD_ID")) {
        Remove-Item -Recurse -Force $nextDir -ErrorAction SilentlyContinue
    }

    $nextBin = Join-Path $FrontendDir "node_modules" "next" "dist" "bin" "next"
    if (Test-Path $nextBin) {
        return Start-Process -FilePath "node" `
            -ArgumentList @($nextBin, "dev") `
            -WorkingDirectory $FrontendDir `
            -NoNewWindow `
            -PassThru
    }

    $cmdString = "$PackageManager run dev"
    if ($RunningOnWindows) {
        return Start-Process -FilePath "cmd.exe" `
            -ArgumentList @("/c", $cmdString) `
            -WorkingDirectory $FrontendDir `
            -NoNewWindow `
            -PassThru
    }
    return Start-Process -FilePath "sh" `
        -ArgumentList @("-c", $cmdString) `
        -WorkingDirectory $FrontendDir `
        -NoNewWindow `
        -PassThru
}

function Show-CommandsHelp {
    Write-Host "`nAvailable runtime commands (type command + Enter):" -ForegroundColor Yellow
    Write-Host "  r  | restart  - Restart both Backend and Frontend" -ForegroundColor Yellow
    Write-Host "  rb | backend  - Restart Backend only" -ForegroundColor Yellow
    Write-Host "  rf | frontend - Restart Frontend only" -ForegroundColor Yellow
    Write-Host "  db            - Restart PostgreSQL container" -ForegroundColor Yellow
    Write-Host "  s  | status   - Show process status and URLs" -ForegroundColor Yellow
    Write-Host "  h  | help     - Show this help" -ForegroundColor Yellow
    Write-Host "  q  | quit     - Stop Backend and Frontend and exit (or press Ctrl+C)`n" -ForegroundColor Yellow
}

function Show-ServiceStatus($BackendProc, $FrontendProc) {
    $bState = if ($BackendProc -and -not $BackendProc.HasExited) { "RUNNING (PID $($BackendProc.Id))" } else { "STOPPED" }
    $fState = if ($FrontendProc -and -not $FrontendProc.HasExited) { "RUNNING (PID $($FrontendProc.Id))" } else { "STOPPED" }
    Write-Host "`nService status:" -ForegroundColor Cyan
    Write-Host "  - Backend:  $bState -> http://127.0.0.1:8000/health"
    Write-Host "  - Frontend: $fState -> http://localhost:3000"
    Write-Host "  - API Docs: http://127.0.0.1:8000/docs`n"
}

# Ensure uv is discoverable if installed in the default user bin directory
$UserHome = if ($RunningOnWindows) { $env:USERPROFILE } else { $HOME }
$UvLocalBin = Join-Path $UserHome ".local" "bin"
if ((Test-Path $UvLocalBin) -and ($env:PATH -notlike "*$UvLocalBin*")) {
    $env:PATH = "$UvLocalBin$PathSep$env:PATH"
}

Write-Step "Checking required tools..."
foreach ($tool in @("docker", "uv", "node")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Required tool '$tool' was not found in PATH. Install it and try again."
    }
}

$PkgManager = if (Get-Command "pnpm" -ErrorAction SilentlyContinue) {
    "pnpm"
} elseif ($RunningOnWindows -and (Get-Command "npm.cmd" -ErrorAction SilentlyContinue)) {
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
        Write-Warning "Created backend/.env from .env.example. Set GEMINI_API_KEY before using AI features."
    } else {
        throw "Neither backend/.env nor backend/.env.example was found."
    }
}

$EnvLines = Get-Content $EnvFile -ErrorAction SilentlyContinue
$GeminiLine = $EnvLines | Where-Object { $_ -match "^\s*GEMINI_API_KEY\s*=" } | Select-Object -First 1
if (-not $GeminiLine -or $GeminiLine -match "your-gemini-api-key|=\s*$") {
    Write-Warning "GEMINI_API_KEY does not appear to be configured in backend/.env. AI challenges and evaluations will fail until a valid key is set."
}

Write-Step "Checking Docker daemon..."
if ((Invoke-QuietNative { docker info }) -ne 0) {
    throw "Docker is not running. Start Docker Desktop (or the Docker service) and try again."
}

Ensure-PostgresReady

if (-not $SkipSync) {
    Write-Step "Syncing backend dependencies (uv sync --all-extras)..."
    Push-Location $BackendDir
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        uv sync --all-extras
        if ($LASTEXITCODE -ne 0) {
            throw "'uv sync --all-extras' failed with exit code $LASTEXITCODE."
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
$UserRequestedExit = $false
$BackendWarned = $false
$FrontendWarned = $false
$InputBuffer = ""
$CanReadKeys = $false

try {
    $CanReadKeys = -not [Console]::IsInputRedirected
} catch {
    $CanReadKeys = $false
}

try {
    Write-Step "Starting Backend (FastAPI) and Frontend (Next.js)..."
    $BackendProc = Start-BackendProcess
    $FrontendProc = Start-FrontendProcess -PackageManager $PkgManager

    Write-Host "`nLinguaMentis is running:" -ForegroundColor Green
    Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Green
    Write-Host "  - Backend:  http://127.0.0.1:8000/health" -ForegroundColor Green
    Write-Host "  - API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
    Show-CommandsHelp

    while (-not $UserRequestedExit) {
        if ($BackendProc.HasExited -and -not $BackendWarned) {
            Write-Warning "Backend process exited unexpectedly (exit code $($BackendProc.ExitCode)). Type 'rb' or 'r' to restart, or 'q' to quit."
            $BackendWarned = $true
            if (-not $CanReadKeys) {
                break
            }
        }
        if ($FrontendProc.HasExited -and -not $FrontendWarned) {
            Write-Warning "Frontend process exited unexpectedly (exit code $($FrontendProc.ExitCode)). Type 'rf' or 'r' to restart, or 'q' to quit."
            $FrontendWarned = $true
            if (-not $CanReadKeys) {
                break
            }
        }

        if ($CanReadKeys) {
            try {
                while ([Console]::KeyAvailable) {
                    $key = [Console]::ReadKey($true)
                    if ($key.Key -eq [ConsoleKey]::Enter) {
                        $cmd = $InputBuffer.Trim().ToLowerInvariant()
                        $InputBuffer = ""
                        Write-Host ""

                        switch ($cmd) {
                            { $_ -in @("r", "restart") } {
                                Write-Step "Restarting Backend and Frontend..."
                                if ($FrontendProc -and -not $FrontendProc.HasExited) {
                                    Stop-ProcessTree -ParentId $FrontendProc.Id
                                }
                                if ($BackendProc -and -not $BackendProc.HasExited) {
                                    Stop-ProcessTree -ParentId $BackendProc.Id
                                }
                                $BackendProc = Start-BackendProcess
                                $FrontendProc = Start-FrontendProcess -PackageManager $PkgManager
                                $BackendWarned = $false
                                $FrontendWarned = $false
                                Write-Host "Backend and Frontend restarted." -ForegroundColor Green
                            }
                            { $_ -in @("rb", "backend") } {
                                Write-Step "Restarting Backend..."
                                if ($BackendProc -and -not $BackendProc.HasExited) {
                                    Stop-ProcessTree -ParentId $BackendProc.Id
                                }
                                $BackendProc = Start-BackendProcess
                                $BackendWarned = $false
                                Write-Host "Backend restarted." -ForegroundColor Green
                            }
                            { $_ -in @("rf", "frontend") } {
                                Write-Step "Restarting Frontend..."
                                if ($FrontendProc -and -not $FrontendProc.HasExited) {
                                    Stop-ProcessTree -ParentId $FrontendProc.Id
                                }
                                $FrontendProc = Start-FrontendProcess -PackageManager $PkgManager
                                $FrontendWarned = $false
                                Write-Host "Frontend restarted." -ForegroundColor Green
                            }
                            "db" {
                                Restart-Postgres
                            }
                            { $_ -in @("s", "status") } {
                                Show-ServiceStatus -BackendProc $BackendProc -FrontendProc $FrontendProc
                            }
                            { $_ -in @("h", "help") } {
                                Show-CommandsHelp
                            }
                            { $_ -in @("q", "quit", "exit") } {
                                $UserRequestedExit = $true
                                break
                            }
                            "" {
                                # Ignore empty Enter
                            }
                            default {
                                Write-Warning "Unknown command '$cmd'. Type 'h' for help."
                            }
                        }
                    } elseif ($key.Key -eq [ConsoleKey]::Backspace) {
                        if ($InputBuffer.Length -gt 0) {
                            $InputBuffer = $InputBuffer.Substring(0, $InputBuffer.Length - 1)
                            Write-Host -NoNewline "`b `b"
                        }
                    } elseif (-not [char]::IsControl($key.KeyChar)) {
                        $InputBuffer += $key.KeyChar
                        Write-Host -NoNewline $key.KeyChar
                    }
                }
            } catch {
                $CanReadKeys = $false
            }
        }

        Start-Sleep -Milliseconds 250
    }
} finally {
    Write-Host "`nStopping Backend and Frontend..." -ForegroundColor Yellow
    if ($FrontendProc -and -not $FrontendProc.HasExited) {
        Stop-ProcessTree -ParentId $FrontendProc.Id
    }
    if ($BackendProc -and -not $BackendProc.HasExited) {
        Stop-ProcessTree -ParentId $BackendProc.Id
    }
    Write-Host "Services stopped (PostgreSQL remains running in Docker)." -ForegroundColor Yellow
}
