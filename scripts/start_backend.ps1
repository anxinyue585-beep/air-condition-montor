param(
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $venvPython) {
  $python = $venvPython
}
else {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pythonCommand) {
    throw "Python was not found. Create .venv and install backend/requirements.txt first."
  }
  $python = $pythonCommand.Source
}

Push-Location $projectRoot
try {
  & $python -m uvicorn backend.app:app --host $HostAddress --port $Port --reload
}
finally {
  Pop-Location
}
