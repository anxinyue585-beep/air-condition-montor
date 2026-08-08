param(
  [string]$EvidenceRoot = "reports/platform_verification",
  [string]$PythonCommand = "python",
  [switch]$SkipDataGeneration
)

$ErrorActionPreference = "Stop"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$runDir = Join-Path $EvidenceRoot $runId
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$transcriptPath = Join-Path $runDir "full-transcript.log"
$summaryPath = Join-Path $runDir "verification-summary.json"
$startedAt = (Get-Date).ToUniversalTime().ToString("o")
$steps = [ordered]@{}

function Save-Summary {
  param([string]$Status, [string]$Message)
  $summary = [ordered]@{
    status = $Status
    message = $Message
    run_id = $runId
    started_at_utc = $startedAt
    completed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    evidence_directory = $runDir.Replace("\", "/")
    steps = $steps
  }
  $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
}

function Invoke-CapturedStep {
  param([string]$Name, [scriptblock]$Action)
  $logPath = Join-Path $runDir "$Name.log"
  New-Item -ItemType File -Force -Path $logPath | Out-Null
  Write-Host "`n=== $Name ==="
  $stepStarted = Get-Date
  try {
    $global:LASTEXITCODE = 0
    # Docker Compose v5 writes normal progress messages to stderr. Windows
    # PowerShell promotes those records to terminating errors when the global
    # preference is Stop, so capture both streams and judge native commands by
    # their exit code instead.
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
      & $Action 2>&1 | Tee-Object -FilePath $logPath
    }
    finally {
      $ErrorActionPreference = $previousErrorActionPreference
    }
    $nativeExitCode = $global:LASTEXITCODE
    if ($nativeExitCode -ne 0) {
      throw "Command exited with code $nativeExitCode"
    }
    $steps[$Name] = [ordered]@{
      status = "passed"
      duration_seconds = [math]::Round(((Get-Date) - $stepStarted).TotalSeconds, 2)
      log = $logPath.Replace("\", "/")
    }
  }
  catch {
    "ERROR: $($_.Exception.Message)" | Add-Content -LiteralPath $logPath -Encoding UTF8
    $steps[$Name] = [ordered]@{
      status = "failed"
      duration_seconds = [math]::Round(((Get-Date) - $stepStarted).TotalSeconds, 2)
      log = $logPath.Replace("\", "/")
      error = $_.Exception.Message
    }
    throw
  }
}

function Wait-DockerCommand {
  param([scriptblock]$Probe, [string]$Description, [int]$Attempts = 60, [int]$DelaySeconds = 5)
  for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    & $Probe *> $null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "$Description ready after attempt $attempt."
      return
    }
    Start-Sleep -Seconds $DelaySeconds
  }
  throw "$Description did not become ready after $($Attempts * $DelaySeconds) seconds."
}

Start-Transcript -LiteralPath $transcriptPath -Force | Out-Null
try {
  $cleanCsv = "data/processed/air_quality_clean.csv"
  if (-not (Test-Path -LiteralPath $cleanCsv)) {
    if ($SkipDataGeneration) {
      throw "Missing $cleanCsv and -SkipDataGeneration was supplied."
    }
    Invoke-CapturedStep "01-generate-dataset" {
      & $PythonCommand scripts/build_air_quality_dataset.py
    }
  }

  Invoke-CapturedStep "02-dataset-evidence" {
    Get-Item -LiteralPath $cleanCsv | Select-Object FullName, Length, LastWriteTimeUtc | Format-List
    Get-FileHash -Algorithm SHA256 -LiteralPath $cleanCsv | Format-List
    Get-Content -Raw -Encoding UTF8 data/processed/data_quality_report.json
  }

  Invoke-CapturedStep "03-docker-preflight" {
    $dockerCommand = Get-Command docker -ErrorAction Stop
    Write-Host "Docker CLI: $($dockerCommand.Source)"
    docker version
    docker compose version
  }

  Invoke-CapturedStep "04-platform-start" {
    docker compose -f platform/docker-compose.yml up -d
    docker compose -f platform/docker-compose.yml ps
  }

  Invoke-CapturedStep "05-service-readiness" {
    Wait-DockerCommand -Description "HDFS NameNode" -Probe { docker exec aq-namenode hdfs dfsadmin -report }
    Wait-DockerCommand -Description "HiveServer2" -Attempts 90 -Probe { docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "SELECT 1;" }
    Wait-DockerCommand -Description "Spark Master" -Probe { docker exec aq-spark-master /spark/bin/spark-submit --version }
  }

  Invoke-CapturedStep "06-hdfs-upload" {
    & powershell -ExecutionPolicy Bypass -File scripts/upload_to_hdfs.ps1
  }

  Invoke-CapturedStep "07-hive-queries" {
    & powershell -ExecutionPolicy Bypass -File scripts/run_hive_air_quality.ps1
  }

  Invoke-CapturedStep "08-spark-etl" {
    & powershell -ExecutionPolicy Bypass -File scripts/run_spark_air_quality.ps1
  }

  Invoke-CapturedStep "09-export-platform-results" {
    & powershell -ExecutionPolicy Bypass -File scripts/export_platform_results.ps1
  }

  Invoke-CapturedStep "10-final-acceptance" {
    docker compose -f platform/docker-compose.yml ps
    docker exec aq-namenode hdfs dfsadmin -report
    docker exec aq-namenode hdfs dfs -ls -h /warehouse/air_quality/clean
    docker exec aq-namenode hdfs dfs -ls -R /warehouse/air_quality/spark
    docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SELECT COUNT(*) AS total_rows FROM air_quality_clean_csv;"
    docker exec aq-hive-server beeline -u "jdbc:hive2://localhost:10000" -n root -e "USE air_quality; SELECT city, avg_aqi, good_rate FROM air_quality_city_topn LIMIT 10;"
    docker inspect aq-namenode aq-datanode aq-hive-server aq-spark-master --format "{{.Name}} {{.Config.Image}} {{.State.Status}}"
    Get-Item data/platform_exports/spark/air_quality_city_day.csv, data/platform_exports/hive/air_quality_city_month.csv | Select-Object FullName, Length, LastWriteTimeUtc
    Get-Content -Raw -Encoding UTF8 data/platform_exports/platform_run_manifest.json
  }

  Save-Summary -Status "passed" -Message "HDFS, Hive, and Spark acceptance checks completed successfully."
  Write-Host "`nPlatform acceptance passed. Evidence: $runDir"
}
catch {
  Save-Summary -Status "failed" -Message $_.Exception.Message
  Write-Error "Platform acceptance failed. Evidence: $runDir. $($_.Exception.Message)"
  exit 1
}
finally {
  Stop-Transcript | Out-Null
}
