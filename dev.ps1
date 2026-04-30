$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'
$BackendHost = '0.0.0.0'
$BackendProxyHost = '127.0.0.1'
$BackendDefaultPort = 8000
$FrontendHost = '0.0.0.0'
$FrontendHmrHost = 'localhost'
$FrontendDefaultPort = 5173

if (-not (Test-Path $BackendDir) -or -not (Test-Path $FrontendDir)) {
    throw 'backend or frontend directory not found.'
}

$backendProcess = $null
$frontendProcess = $null
$BackendPython = $null
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    throw 'npm.cmd not found. Please install Node.js 18+.'
}

$cmdExe = (Get-Command cmd.exe -ErrorAction Stop).Source
$taskkillExe = (Get-Command taskkill.exe -ErrorAction SilentlyContinue).Source

function Resolve-VenvPython {
    $candidates = @(
        (Join-Path $BackendDir '.venv\Scripts\python.exe'),
        (Join-Path $BackendDir '.venv\bin\python')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Resolve-BootstrapPython {
    $venvPython = Resolve-VenvPython
    if ($venvPython) {
        return $venvPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return $python3.Source
    }

    throw 'Python 3.10+ not found.'
}

function Invoke-CheckedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @ArgumentList
        if ($LASTEXITCODE -ne 0) {
            throw $FailureMessage
        }
    }
    finally {
        Pop-Location
    }
}

function Ensure-FrontendDependencies {
    if (Test-Path (Join-Path $FrontendDir 'node_modules')) {
        return
    }

    Write-Host 'frontend/node_modules not found, running npm install...'
    Invoke-CheckedProcess -FilePath $npmCmd.Source -ArgumentList @('install') -WorkingDirectory $FrontendDir -FailureMessage 'npm install failed.'
}

function Ensure-BackendEnvironment {
    $bootstrapPython = Resolve-BootstrapPython
    $requirementsFile = Join-Path $BackendDir 'requirements.txt'

    if (-not (Test-Path (Join-Path $BackendDir '.venv'))) {
        Write-Host 'backend/.venv not found, creating virtual environment...'
        Invoke-CheckedProcess -FilePath $bootstrapPython -ArgumentList @('-m', 'venv', (Join-Path $BackendDir '.venv')) -WorkingDirectory $RootDir -FailureMessage 'Failed to create backend virtual environment.'
    }

    $script:BackendPython = Resolve-VenvPython
    if (-not $script:BackendPython) {
        $script:BackendPython = $bootstrapPython
    }

    & $script:BackendPython -c "import uvicorn" *> $null
    if ($LASTEXITCODE -eq 0) {
        return
    }

    if (-not (Test-Path $requirementsFile)) {
        throw 'backend/requirements.txt not found. Cannot install backend dependencies automatically.'
    }

    Write-Host 'Current Python environment is missing uvicorn, installing backend requirements...'
    Invoke-CheckedProcess -FilePath $script:BackendPython -ArgumentList @('-m', 'pip', 'install', '-r', $requirementsFile) -WorkingDirectory $BackendDir -FailureMessage 'Backend dependency installation failed.'
}

function Test-PortAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Host,
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listener = $null
    try {
        $address = [System.Net.IPAddress]::Parse($Host)
        $listener = [System.Net.Sockets.TcpListener]::new($address, $Port)
        $listener.Start()
        return $true
    }
    catch [System.Net.Sockets.SocketException] {
        return $false
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

function Find-AvailablePort {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Host,
        [Parameter(Mandatory = $true)]
        [int]$StartPort
    )

    for ($port = $StartPort; $port -le 65535; $port++) {
        if (Test-PortAvailable -Host $Host -Port $port) {
            return $port
        }
    }

    throw "No available port found in range ${Host}:${StartPort}-65535."
}

function Stop-TrackedProcess {
    param([System.Diagnostics.Process]$Process)

    if (-not $Process) {
        return
    }

    try {
        if ($Process.HasExited) {
            return
        }
    }
    catch {
        return
    }

    if ($taskkillExe) {
        & $taskkillExe /PID $Process.Id /T /F *> $null
        return
    }

    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
}

try {
    Ensure-FrontendDependencies
    Ensure-BackendEnvironment

    $BackendPort = Find-AvailablePort -Host $BackendHost -StartPort $BackendDefaultPort
    $FrontendPort = Find-AvailablePort -Host $FrontendHost -StartPort $FrontendDefaultPort

    if ($BackendPort -ne $BackendDefaultPort) {
        Write-Host "Detected backend default port $BackendDefaultPort in use, switching to $BackendPort."
    }

    if ($FrontendPort -ne $FrontendDefaultPort) {
        Write-Host "Detected frontend default port $FrontendDefaultPort in use, switching to $FrontendPort."
    }

    if (-not (Test-Path (Join-Path $BackendDir '.env')) -and (Test-Path (Join-Path $BackendDir 'env.example'))) {
        Write-Host 'Hint: backend/.env not found. You can create it from backend/env.example.' -ForegroundColor Yellow
    }

    Write-Host 'Starting backend dev server...'
    $backendProcess = Start-Process -FilePath $BackendPython -ArgumentList '-m', 'uvicorn', 'app.main:app', '--reload', '--host', $BackendHost, '--port', $BackendPort -WorkingDirectory $BackendDir -PassThru

    $frontendCommand = "set BACKEND_PROXY_HOST=$BackendProxyHost && set BACKEND_PORT=$BackendPort && set FRONTEND_HOST=$FrontendHost && set FRONTEND_PORT=$FrontendPort && set FRONTEND_HMR_HOST=$FrontendHmrHost && npm.cmd run dev"

    Write-Host 'Starting frontend dev server...'
    $frontendProcess = Start-Process -FilePath $cmdExe -ArgumentList '/c', $frontendCommand -WorkingDirectory $FrontendDir -PassThru

    Write-Host ''
    Write-Host 'Dev environment started:'
    Write-Host "- Backend listen address: http://$BackendHost`:$BackendPort"
    Write-Host "- Frontend listen address: http://$FrontendHost`:$FrontendPort"
    Write-Host "- Local frontend: http://127.0.0.1:$FrontendPort"
    Write-Host "- Local API proxy: http://$BackendProxyHost`:$BackendPort/api"
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
    Stop-TrackedProcess -Process $backendProcess
    Stop-TrackedProcess -Process $frontendProcess
}
