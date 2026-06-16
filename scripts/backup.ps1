# QuoteFlow 数据库备份脚本 (Windows)
# 用法: 任务计划程序中每日执行
# powershell -File "D:\Projects\product-tool\scripts\backup.ps1"

$projectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$backupDir = Join-Path $projectDir "backups"
$retentionDays = 7

New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$date = Get-Date -Format "yyyyMMdd"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "[$timestamp] Starting backup..."

$dbs = @(
    (Join-Path $projectDir "backend\app.db"),
    (Join-Path $HOME "\.product_tool\products.db")
)

foreach ($db in $dbs) {
    if (Test-Path $db) {
        $name = [IO.Path]::GetFileNameWithoutExtension($db)
        $dest = Join-Path $backupDir "${name}-${date}.db"
        Copy-Item $db $dest -Force
        $size = (Get-Item $dest).Length
        Write-Host "  Backed up: $db -> $dest ($([math]::Round($size/1KB,1))KB)"
    } else {
        Write-Host "  Skipped (not found): $db"
    }
}

# Env backup
$envFile = Join-Path $projectDir "backend\.env"
if (Test-Path $envFile) {
    Copy-Item $envFile (Join-Path $backupDir "env-${date}.env") -Force
    Write-Host "  Backed up: .env"
}

# Clean old backups
$cutoff = (Get-Date).AddDays(-$retentionDays)
$deleted = Get-ChildItem $backupDir -Filter "*.db" | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -PassThru
Write-Host "  Cleaned $($deleted.Count) old backups (>${retentionDays}d)"

Write-Host "[$timestamp] Backup complete."
