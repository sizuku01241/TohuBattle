$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$comMojang = Split-Path -Parent $repoRoot
$behaviorSource = Join-Path $repoRoot "behavior_pack"
$resourceSource = Join-Path $repoRoot "resource_pack"
$behaviorTarget = Join-Path $comMojang "development_behavior_packs\behavior_pack"
$resourceTarget = Join-Path $comMojang "development_resource_packs\resource_pack"

if (-not (Test-Path -LiteralPath $behaviorSource)) { throw "behavior_packが見つかりません" }
if (-not (Test-Path -LiteralPath $resourceSource)) { throw "resource_packが見つかりません" }

if (Test-Path -LiteralPath $behaviorTarget) { Remove-Item -LiteralPath $behaviorTarget -Recurse -Force }
if (Test-Path -LiteralPath $resourceTarget) { Remove-Item -LiteralPath $resourceTarget -Recurse -Force }
Copy-Item -LiteralPath $behaviorSource -Destination $behaviorTarget -Recurse -Force
Copy-Item -LiteralPath $resourceSource -Destination $resourceTarget -Recurse -Force
Write-Output "Minecraft用Development Packへ同期しました。"
