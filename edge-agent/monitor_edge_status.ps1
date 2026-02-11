param(
  [Parameter(Mandatory=$true)][string]$BASE,
  [Parameter(Mandatory=$true)][string]$EDGE_STORE_ID,
  [Parameter(Mandatory=$true)][string]$USER_TOKEN,
  [int]$EverySec = 20,
  [int]$TimeoutSec = 15,
  [string]$LogPath = ""
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptPath = Join-Path $repoRoot "scripts\\monitor_edge_status.ps1"
& $scriptPath `
  -BASE $BASE `
  -EDGE_STORE_ID $EDGE_STORE_ID `
  -USER_TOKEN $USER_TOKEN `
  -EverySec $EverySec `
  -TimeoutSec $TimeoutSec `
  -LogPath $LogPath
