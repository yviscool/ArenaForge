param(
    [string]$PackagesRoot = "C:\software\Sublime Text 4\Data\Packages",
    [string]$PackageName = "ArenaForge"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$packagePath = Join-Path $PackagesRoot $PackageName

if (-not (Test-Path -LiteralPath $PackagesRoot)) {
    throw "Packages root does not exist: $PackagesRoot"
}

if (Test-Path -LiteralPath $packagePath) {
    $existing = Get-Item -LiteralPath $packagePath
    if ($existing.LinkType -and $existing.LinkType -eq "Junction") {
        ([System.IO.DirectoryInfo]$existing).Delete()
    } else {
        throw "Refusing to replace non-junction path: $packagePath"
    }
}

New-Item -ItemType Junction -Path $packagePath -Target $repoRoot | Out-Null
Get-Item -LiteralPath $packagePath | Select-Object FullName, LinkType, Target | Format-List
