param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $ComposeArgs
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example — set GEMINI_API_KEY inside .env" -ForegroundColor Yellow
    } else {
        Write-Host "Missing .env and .env.example — create .env with GEMINI_API_KEY=" -ForegroundColor Red
    }
}

$extra = @()
if ($ComposeArgs) { $extra = $ComposeArgs }
docker compose -p formsiq up --build @extra
