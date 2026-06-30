$ErrorActionPreference = "Stop"

$python = "python"
if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
  $bundled = "C:\Users\aruto\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  if (Test-Path $bundled) {
    $python = $bundled
  }
}

& $python scripts\run_data_analysis_algorithms.py
