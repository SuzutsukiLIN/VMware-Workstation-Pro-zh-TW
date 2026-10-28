#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Uninstall')][string]$Action = 'Install',
    [switch]$Elevated
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# The public repository intentionally omits VMware proprietary files.
$projectRoot = Split-Path -Parent $PSScriptRoot
$dataRoot = Join-Path $env:ProgramData 'VMware-Workstation-zh-TW-ES-Compat'
$stateFile = Join-Path $dataRoot 'install-state.json'
$files = @('vmappsdk-es.dll', 'vmui-es.dll', 'vmware.vmsg')
$nativeHash = @{
    'vmappsdk-es.dll' = 'e4439165a3b9b11b3321297c0a55d4d92bf832b5f03a10ee7e00063ac0014b20'
    'vmui-es.dll' = 'fd5154dbbcf04eeca18eb3928319c3479427edb33b615820a65624f198dea73d'
    'vmware.vmsg' = 'acf2c68d3dc38c5476b8874f5728c014810c66fc964e858fbcce4c9de717ebab'
}
$v10Hash = @{
    'vmappsdk-es.dll' = 'cd9cfd6d6b7a134ac9c91c8aebc939484071c8065df81d9ad6bd392bdb054227'
    'vmui-es.dll' = '320cb4ccbcf7f8118e4855ab7352d9fc6ccf03599f459333fbc0fe3e458fe0b8'
    'vmware.vmsg' = '70ad3f5e22511a0cabcd56bf6df125fafbfe01bbc427339e6baed9ddfccbbd90'
}
$v11Hash = @{
    'vmappsdk-es.dll' = '3f19def65c3eae70620aa31deecedc74ae7bf334e88bbe35e0b1f9479b0a52dc'
    'vmui-es.dll' = $v10Hash['vmui-es.dll']
    'vmware.vmsg' = 'f5567d6a39873053c0e25d694366e25230a1c9e201418a939345cf7aa602606e'
}
$v12Hash = @{
    'vmappsdk-es.dll' = $v11Hash['vmappsdk-es.dll']
    'vmui-es.dll' = $v11Hash['vmui-es.dll']
    'vmware.vmsg' = '895d68bbbdf1701b4526ed831bdc5d61a3f47fd21896455fe8d6ce9c48748798'
}

function Get-Hash([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "找不到檔案：$Path" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Test-HashSet([string]$Directory, [System.Collections.IDictionary]$Expected) {
    foreach ($name in $files) {
        $path = Join-Path $Directory $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $false }
        if ((Get-Hash $path) -ne [string]$Expected[$name]) { return $false }
    }
    return $true
}
function Get-CurrentState([string]$Directory) {
    foreach ($state in @(@{Name='native'; Hash=$nativeHash}, @{Name='v1.0'; Hash=$v10Hash}, @{Name='v1.1'; Hash=$v11Hash}, @{Name='v1.2'; Hash=$v12Hash})) {
        if (Test-HashSet $Directory $state.Hash) { return $state.Name }
    }
    return 'unknown'
}
function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Get-VMwareRoot {
    $locations = New-Object System.Collections.Generic.List[string]
    $locations.Add((Join-Path $env:ProgramFiles 'VMware\VMware Workstation'))
    foreach ($k in @('HKLM:\SOFTWARE\VMware, Inc.\VMware Workstation','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')) {
        if ($k -like '*Uninstall') {
            if (Test-Path $k) {
                foreach ($item in (Get-ChildItem $k -ErrorAction SilentlyContinue)) {
                    $v = Get-ItemProperty -LiteralPath $item.PSPath -ErrorAction SilentlyContinue
                    if ($null -ne $v -and $null -ne $v.PSObject.Properties['DisplayName'] -and
                        $null -ne $v.PSObject.Properties['InstallLocation'] -and
                        [string]$v.DisplayName -match '^VMware Workstation' -and $v.InstallLocation) {
                        $locations.Add([string]$v.InstallLocation)
                    }
                }
            }
        } elseif (Test-Path $k) {
            $v = Get-ItemProperty -Path $k -ErrorAction SilentlyContinue
            if ($null -ne $v -and $null -ne $v.PSObject.Properties['InstallPath'] -and $v.InstallPath) {
                $locations.Add([string]$v.InstallPath)
            }
        }
    }
    foreach ($root in $locations) {
        if (-not [string]::IsNullOrWhiteSpace($root) -and (Test-Path -LiteralPath (Join-Path $root 'vmware.exe') -PathType Leaf)) {
            return $root.TrimEnd('\')
        }
    }
    throw '找不到 VMware Workstation Pro 安裝目錄。請確認 VMware 已安裝。'
}
function Assert-VMwareVersion([string]$Root) {
    $exe = Join-Path $Root 'vmware.exe'
    $ver = (Get-Item -LiteralPath $exe).VersionInfo.FileVersion
    if ($ver -notmatch '^26\.0\.1(?:\D|$)' -or $ver -notmatch '25688693') {
        throw "不支援 VMware 版本：$ver。本安裝器僅適用 26.0.1 build-25688693。"
    }
    return $exe
}
function Assert-VMwareClosed {
    if (Get-Process -Name vmware -ErrorAction SilentlyContinue) {
        throw 'VMware Workstation 仍在執行。請先完全關閉 VMware 再重試。'
    }
}
function Get-ShortcutPath {
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory)
    if ([string]::IsNullOrWhiteSpace($desktop)) { throw '無法取得公用桌面目錄。' }
    return (Join-Path $desktop 'VMware Workstation Pro - 繁體中文.lnk')
}
function Set-Shortcut([string]$ExePath) {
    $lnk = Get-ShortcutPath
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($lnk)
    $sc.TargetPath = $ExePath
    $sc.Arguments = '--locale=es'
    $sc.WorkingDirectory = Split-Path -Parent $ExePath
    $sc.IconLocation = "$ExePath,0"
    $sc.Description = 'VMware Workstation Pro - 繁體中文（ES 相容模式）'
    $sc.Save()
    $test = $shell.CreateShortcut($lnk)
    if ($test.TargetPath -ne $ExePath -or $test.Arguments -ne '--locale=es') {
        throw '桌面捷徑驗證失敗。'
    }
    Write-Host "桌面捷徑已建立：$lnk" -ForegroundColor Green
}
function Remove-Shortcut([string]$ExePath) {
    $lnk = Get-ShortcutPath
    if (-not (Test-Path -LiteralPath $lnk)) { return }
    $sc = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
    if ($sc.TargetPath -eq $ExePath -and $sc.Arguments -eq '--locale=es') {
        Remove-Item -LiteralPath $lnk -Force
        Write-Host '已移除本工具建立的桌面捷徑。'
    } else {
        Write-Warning '桌面捷徑內容已被變更，為避免誤刪，已保留。'
    }
}
function Find-LegacyNativeBackup {
    $legacy = Join-Path $env:ProgramData 'VMware\LocalePatchBackups'
    if (-not (Test-Path -LiteralPath $legacy -PathType Container)) { return $null }
    $folders = @(Get-ChildItem -LiteralPath $legacy -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'VMware26.0.1_es_*' } | Sort-Object Name -Descending)
    foreach ($f in $folders) {
        if (Test-HashSet $f.FullName $nativeHash) { return $f.FullName }
    }
    return $null
}
function Copy-Three([string]$From, [string]$To) {
    foreach ($n in $files) {
        Copy-Item -LiteralPath (Join-Path $From $n) -Destination (Join-Path $To $n) -Force -ErrorAction Stop
    }
}
function Get-ExistingInstallState {
    if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) { return $null }
    return (Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Save-InstallState([string]$InstallRoot, [string]$Backup, [string]$BackupKind) {
    $data = [ordered]@{
        schema=1
        package='v1.2'
        installedAt=(Get-Date).ToString('o')
        vmwareRoot=$InstallRoot
        baselineFolder=$Backup
        baselineKind=$BackupKind
    }
    $data | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $stateFile -Encoding UTF8
}
function Invoke-Install([string]$Root, [string]$Exe) {
    $target=Join-Path $Root 'messages\es'
    $payload=Join-Path $projectRoot 'payload\es'
    $current=Get-CurrentState $target
    Write-Host "偵測到 ES 語系：$current"
    if ($current -eq 'unknown') { throw '語系檔 SHA-256 不符合已知基準，為避免覆蓋其他修補或新版檔案，已停止。' }
    if ($current -ne 'v1.2' -and -not (Test-HashSet $payload $v12Hash)) {
        throw '安裝包缺少完整 v1.2 語系檔，或檔案雜湊不符。請先執行本機資源建置。'
    }
    New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
    $existing = Get-ExistingInstallState
    $baseline = $null
    $baselineKind = 'none'
    if ($null -ne $existing -and $existing.vmwareRoot -eq $Root -and
        (Test-Path -LiteralPath ([string]$existing.baselineFolder) -PathType Container)) {
        $baseline=[string]$existing.baselineFolder
        $baselineKind=[string]$existing.baselineKind
    } else {
        $vendor=Find-LegacyNativeBackup
        if ($vendor) { $baseline=$vendor; $baselineKind='native' }
    }
    $rollback=$null
    try {
        if ($current -ne 'v1.2') {
            $rollback = Join-Path $dataRoot ('Backups\BeforeInstall_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
            New-Item -ItemType Directory -Path $rollback -Force | Out-Null
            Copy-Three $target $rollback
            $allowedBefore=@{'native'=$nativeHash;'v1.0'=$v10Hash;'v1.1'=$v11Hash}
            if (-not (Test-HashSet $rollback $allowedBefore[$current])) {
                throw '安裝前備份 SHA-256 驗證失敗。'
            }
            if (-not $baseline) {
                $baseline=$rollback
                $baselineKind = if ($current -eq 'native') { 'native' } else { 'prior-patch' }
            }
            Copy-Three $payload $target
            if (-not (Test-HashSet $target $v12Hash)) { throw '安裝後 SHA-256 驗證失敗，準備還原。' }
            Write-Host 'v1.2 繁體中文資源安裝完成。' -ForegroundColor Green
        } else {
            Write-Host 'v1.2 已經安裝，只需確認桌面捷徑。' -ForegroundColor Green
        }
        Set-Shortcut $Exe
        if ($baseline) { Save-InstallState $Root $baseline $baselineKind }
        else { Write-Warning '未找到原廠備份；已建立捷徑，但解除安裝無法保證還原原廠 ES 語系。' }
        Write-Host '請由桌面的「VMware Workstation Pro - 繁體中文」啟動。' -ForegroundColor Cyan
    } catch {
        $reason=$_.Exception.Message
        if ($rollback -and (Test-Path -LiteralPath $rollback -PathType Container)) {
            Write-Warning "安裝失敗，嘗試從 $rollback 還原..."
            try { Copy-Three $rollback $target } catch { Write-Warning ('自動還原失敗：'+$_.Exception.Message) }
        }
        throw $reason
    }
}
function Invoke-Uninstall([string]$Root, [string]$Exe) {
    $target=Join-Path $Root 'messages\es'
    $current=Get-CurrentState $target
    if ($current -ne 'v1.2') { throw "目前 ES 語系狀態為 $current，非本工具的 v1.2；拒絕覆寫。" }
    $state=Get-ExistingInstallState
    if ($null -eq $state -or $state.vmwareRoot -ne $Root) {
        throw '找不到這台 VMware 的安裝紀錄。為保護原檔，無法自動還原。'
    }
    $baseline=[string]$state.baselineFolder
    if (-not (Test-Path -LiteralPath $baseline -PathType Container)) { throw '找不到原始語系備份。' }
    $backupHash=$null
    switch ([string]$state.baselineKind) {
        'native' {$backupHash=$nativeHash}
        'prior-patch' {
            foreach ($hash in @($v10Hash,$v11Hash)) {
                if (Test-HashSet $baseline $hash) {$backupHash=$hash;break}
            }
        }
    }
    if ($null -eq $backupHash -or -not (Test-HashSet $baseline $backupHash)) { throw '備份的 SHA-256 不符合預期，為避免資料損壞，已停止還原。' }
    $rollback=Join-Path $dataRoot ('Backups\BeforeRestore_'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
    New-Item -ItemType Directory -Path $rollback -Force | Out-Null
    Copy-Three $target $rollback
    try {
        Copy-Three $baseline $target
        if (-not (Test-HashSet $target $backupHash)) { throw '還原檢查失敗' }
        Remove-Shortcut $Exe
        Remove-Item -LiteralPath $stateFile -Force -ErrorAction SilentlyContinue
        Write-Host ('已還原：'+[string]$state.baselineKind+'；備份保留在 '+$dataRoot) -ForegroundColor Green
    } catch {
        Write-Warning '還原過程失敗，正在恢復 v1.2 狀態...'
        Copy-Three $rollback $target
        throw
    }
}

try {
    Write-Host '=== VMware Workstation Pro 26.0.1 繁體中文一鍵安裝器 ===' -ForegroundColor Cyan
    if (-not (Test-Admin)) {
        if ($Elevated) { throw '系統管理員權限不足。' }
        Write-Host '正在要求 Windows 系統管理員權限（UAC）...'
        $psExe=Join-Path $PSHOME 'powershell.exe'
        $args='-NoProfile -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Action '+$Action+' -Elevated'
        $child=Start-Process -FilePath $psExe -ArgumentList $args -Verb RunAs -PassThru -Wait
        if ($null -eq $child) { throw '無法啟動系統管理員程序。' }
        exit $child.ExitCode
    }
    Assert-VMwareClosed
    $root=Get-VMwareRoot
    $exe=Assert-VMwareVersion $root
    Write-Host "VMware 路徑：$root"
    if ($Action -eq 'Install') { Invoke-Install $root $exe }
    else { Invoke-Uninstall $root $exe }
    exit 0
} catch {
    Write-Host ('錯誤：'+$_.Exception.Message) -ForegroundColor Red
    exit 1
}
