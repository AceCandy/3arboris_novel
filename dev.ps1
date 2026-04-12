$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'

if (-not (Test-Path $BackendDir) -or -not (Test-Path $FrontendDir)) {
    throw 'backend or frontend directory not found.'
}

$backendProcess = $null
$frontendProcess = $null

try {
    $venvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
    if (Test-Path $venvPython) {
        $backendPython = $venvPython
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $backendPython = (Get-Command python).Source
    }
    elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        $backendPython = (Get-Command python3).Source
    }
    else {
        throw 'Python 3.10+ not found.'
    }

    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        throw 'npm.cmd not found. Please install Node.js 18+.'
    }

    $cmdExe = (Get-Command cmd.exe -ErrorAction Stop).Source

    if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
        throw 'frontend/node_modules not found. Run npm install in frontend first.'
    }

    if (-not (Test-Path (Join-Path $BackendDir '.env')) -and (Test-Path (Join-Path $BackendDir 'env.example'))) {
        Write-Host 'Hint: backend/.env not found. You can create it from backend/env.example.' -ForegroundColor Yellow
    }

    Write-Host 'Starting backend dev server...'
    $backendProcess = Start-Process -FilePath $backendPython -ArgumentList '-m', 'uvicorn', 'app.main:app', '--reload' -WorkingDirectory $BackendDir -PassThru

    Write-Host 'Starting frontend dev server...'
    $frontendProcess = Start-Process -FilePath $cmdExe -ArgumentList '/c', 'npm.cmd run dev' -WorkingDirectory $FrontendDir -PassThru

    Write-Host ''
    Write-Host 'Dev environment started:'
    Write-Host '- Backend: http://127.0.0.1:8000'
    Write-Host '- Frontend: http://127.0.0.1:5173'
    Write-Host 'Closing this window will try to stop both processes.'
    Write-Host ''

    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) {
            break
        }
    }
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }

    if ($frontendProcess -and -not $frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force
    }
}
