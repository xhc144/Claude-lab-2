# 注册 / 移除 Folio 的 Windows 11 右键菜单（稀疏包 Folio.Shell.<命令>，每个命令一个包，
# 见 packaging/build_shell.py 的 PACKAGES；0.2.3 只有一个包 Folio.Shell，安装时一起移除）。由安装程序调用（packaging/installer.iss）：
#     register.ps1 -Action install   -Dir %LOCALAPPDATA%\Programs\Folio-shell -Version 0.2.3
#     register.ps1 -Action uninstall -Dir %LOCALAPPDATA%\Programs\Folio-shell
# 任何失败都不能中断安装：注册不上时保留旧的注册表右键菜单（Windows 10、证书不受信任等情况），原因写进
# %TEMP%\folio-shell.log。注册成功后删掉旧的注册表菜单，免得在「显示更多选项」里重复出现。
param([ValidateSet('install', 'uninstall')][string]$Action, [string]$Dir, [string]$Version = '')
# 不占用任何安装目录（Set-Location 只改 PowerShell 的位置，进程的当前目录要另外设）
Set-Location -LiteralPath ([System.IO.Path]::GetTempPath())
[System.IO.Directory]::SetCurrentDirectory([System.IO.Path]::GetTempPath())
# 从 PowerShell 7 里启动安装程序时会继承它的 PSModulePath，Windows PowerShell 5.1 就加载不了 Appx 模块
$env:PSModulePath = "$env:ProgramFiles\WindowsPowerShell\Modules;$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules"
$ErrorActionPreference = 'Stop'
$Key = 'HKCU:\Software\Folio\Shell'
# 和 folio/platform_win.py 的 CONTEXT_MENU 一致
$Legacy = @('SystemFileAssociations\.pdf\shell\Folio.Compress', 'SystemFileAssociations\.pdf\shell\Folio.Merge',
            'SystemFileAssociations\image\shell\Folio.ImagesToPdf')
$Log = Join-Path ([System.IO.Path]::GetTempPath()) 'folio-shell.log'

function Write-Log([string]$Text) {
  try { Add-Content -LiteralPath $Log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Action] $Text" -Encoding UTF8 } catch {}
}

# 这次要注册的包（目录里的 Folio-Shell-<命令>.msix；0.2.3 留下的 Folio-Shell.msix 不匹配）
$Msix = @(Get-ChildItem -LiteralPath $Dir -Filter 'Folio-Shell-*.msix' -ErrorAction SilentlyContinue | Sort-Object Name)

# Folio 的所有右键菜单包：现在的 Folio.Shell.<命令>，和 0.2.3 的 Folio.Shell
function Get-FolioPackages {
  @(Get-AppxPackage -Name 'Folio.Shell*' | Where-Object { $_.Name -eq 'Folio.Shell' -or $_.Name -like 'Folio.Shell.*' })
}

function Remove-Package {
  Get-FolioPackages | ForEach-Object { Remove-AppxPackage -Package $_.PackageFullName }
}

function Stop-Dllhost {
  # Explorer 用过右键菜单后，dllhost 还会加载着 DLL 一段时间：它在包里运行时移除不了包，也删不掉文件
  Get-Process dllhost -ErrorAction SilentlyContinue | Where-Object {
    try { @($_.Modules | Where-Object { $_.FileName -like "$Dir\*" }).Count -gt 0 } catch { $false }
  } | Stop-Process -Force -ErrorAction SilentlyContinue
}

if ($Action -eq 'uninstall') {
  # 先结束 dllhost 再移除包；移除失败时重试几次（dllhost 刚退出时包可能还标记为使用中）
  for ($i = 1; $i -le 5; $i++) {
    Stop-Dllhost
    try {
      Remove-Package
      if (-not (Get-FolioPackages)) { Write-Log 'packages removed'; break }
      Write-Log "attempt ${i}: package still registered"
    } catch { Write-Log "attempt ${i}: remove failed: $_" }
    Start-Sleep -Seconds 2
  }
  Stop-Dllhost
  Remove-Item -LiteralPath $Key -Recurse -Force -ErrorAction SilentlyContinue
  exit 0
}

$build = [Environment]::OSVersion.Version.Build
if ($build -lt 22000) {
  Write-Log "Windows build $build has no new context menu, keeping the classic one"
  exit 0
}
try {
  if (-not $Msix) { throw "no Folio-Shell-*.msix in $Dir" }
  Stop-Dllhost
  Remove-Package
  foreach ($m in $Msix) { Add-AppxPackage -Path $m.FullName -ExternalLocation $Dir }
  $pkgs = @(Get-FolioPackages)
  if ($pkgs.Count -ne $Msix.Count) { throw "registered $($pkgs.Count) of $($Msix.Count) packages" }
  New-Item -Path $Key -Force | Out-Null
  # folio/platform_win.py 的 new_menu_active() 只看这一个包是否还在（几个包总是一起注册、一起移除）
  Set-ItemProperty -Path $Key -Name PackageFamily -Value $pkgs[0].PackageFamilyName
  foreach ($k in $Legacy) {
    Remove-Item -LiteralPath "HKCU:\Software\Classes\$k" -Recurse -Force -ErrorAction SilentlyContinue
  }
  Write-Log "registered $(($pkgs | ForEach-Object { $_.PackageFullName }) -join ', ')"
} catch {
  # 最常见：签名证书不受这台电脑信任（自签名证书）。保留旧菜单；已经注册上的包也移除，不留半套新菜单
  Write-Log "register failed, keeping the classic context menu: $_"
  try { Remove-Package } catch { Write-Log "cleanup failed: $_" }
  if (Test-Path $Key) { Remove-ItemProperty -Path $Key -Name PackageFamily -ErrorAction SilentlyContinue }
}
# 清掉旧版本的 DLL 目录（还被 dllhost 加载着的删不掉，下次安装再删）
if ($Version) {
  Get-ChildItem -LiteralPath $Dir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne $Version } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
exit 0
