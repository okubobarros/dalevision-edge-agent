param(
    [int]$SinceHours = 24
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptRoot "eod.py"

if (-not (Test-Path $pythonScript)) {
    Write-Error "Nao encontrei scripts/eod.py. Rode a partir da raiz do repo."
    exit 1
}

python $pythonScript --since-hours $SinceHours
