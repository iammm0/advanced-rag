Param(
  [int]$Port = 8000,
  [int]$GraceSeconds = 8
)

$ErrorActionPreference = "Stop"

function Wait-PortFree {
  param([int]$Port, [int]$Seconds)
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    $listen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listen) { return $true }
    Start-Sleep -Milliseconds 250
  }
  return $false
}

function Stop-PortListenersGracefully {
  param([int]$Port, [int]$GraceSeconds)

  $pids = @(
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique
  ) | Where-Object { $_ -and $_ -ne 0 }

  if (-not $pids -or $pids.Count -eq 0) {
    Write-Host "Port $Port is free."
    return
  }

  Write-Host "Port $Port is in use. PID(s): $($pids -join ', ')"
  foreach ($p in $pids) {
    try {
      Write-Host "Trying graceful stop PID=$p ..."
      # 先请求正常终止（不加 /F）
      cmd /c "taskkill /PID $p /T" | Out-Null
    } catch {
      Write-Host "Graceful stop PID=$p failed: $($_.Exception.Message)"
    }
  }

  if (Wait-PortFree -Port $Port -Seconds $GraceSeconds) {
    Write-Host "Port $Port is released."
    return
  }

  Write-Host "Port still in use after $GraceSeconds seconds, forcing termination..."
  $pids2 = @(
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique
  ) | Where-Object { $_ -and $_ -ne 0 }

  foreach ($p in $pids2) {
    try {
      Write-Host "Force killing PID=$p ..."
      cmd /c "taskkill /PID $p /T /F" | Out-Null
    } catch {
      Write-Host "Force kill PID=$p failed: $($_.Exception.Message)"
    }
  }

  if (-not (Wait-PortFree -Port $Port -Seconds 5)) {
    # If the port is still occupied but the PID cannot be found,
    # it usually means the system reports a stale OwningProcess (needs admin fix / reboot).
    $still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $stillPid = ($still | Select-Object -First 1 -ExpandProperty OwningProcess)
    $procExists = $false
    if ($stillPid) {
      $procExists = (Get-Process -Id $stillPid -ErrorAction SilentlyContinue) -ne $null
    }
    if ($stillPid -and -not $procExists) {
      throw "Port $Port is still in use but PID $stillPid is not found. Run PowerShell as Administrator to clear the listener (or reboot), then retry."
    }
    throw "Port $Port is still in use after force kill."
  }
  Write-Host "Port $Port force released."
}

# 1) 先优雅关闭旧后端
Stop-PortListenersGracefully -Port $Port -GraceSeconds $GraceSeconds

# 2) 启动新后端（固定端口）
Set-Location (Split-Path -Parent $PSScriptRoot)  # -> repo root
$env:PORT = "$Port"
Write-Host "启动后端：PORT=$env:PORT"
python main.py

