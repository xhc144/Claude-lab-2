; Windows 安装程序（Inno Setup 6）。先运行 packaging/build.py 生成 dist/Folio，再：
;     iscc /DAppVersion=0.2.2 packaging/installer.iss
; 生成 dist/Folio-Setup-<版本>.exe。
;
; 装到当前用户自己的目录（%LOCALAPPDATA%\Programs\Folio），不需要管理员权限：
; 自动更新会整体替换程序目录，必须对这个目录和它的上一级有写权限。
; 也因为这样，卸载程序不能放在程序目录里（更新时会被一起替换掉），单独放在旁边的 Folio-uninstall。
;
; Windows 11 第一层右键菜单（先运行 packaging/build_shell.py 生成 dist/Folio-shell）装到旁边的 Folio-shell：
; Explorer（dllhost）加载着的 DLL 会锁住它所在的目录，放进程序目录的话自动更新就改不了名。
; 安装后用 register.ps1 注册稀疏包；注册不上（Windows 10、证书不受信任等）时保留下面 [Registry] 里的旧菜单。

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define Root SourcePath + "\.."
#define ShellDir "{localappdata}\Programs\Folio-shell"
#define HaveShell FileExists(Root + "\dist\Folio-shell\register.ps1")

[Setup]
AppId={{6E2B3F4A-8C1D-4E7F-9A5B-F0110C0A2D01}
AppName=Folio
AppVersion={#AppVersion}
AppVerName=Folio {#AppVersion}
AppPublisher=Folio
AppPublisherURL=https://github.com/xhc144/Claude-lab-2
AppSupportURL=https://github.com/xhc144/Claude-lab-2/issues
AppUpdatesURL=https://github.com/xhc144/Claude-lab-2/releases
DefaultDirName={localappdata}\Programs\Folio
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UninstallFilesDir={localappdata}\Programs\Folio-uninstall
UninstallDisplayName=Folio
UninstallDisplayIcon={app}\Folio.exe
SetupIconFile={#Root}\packaging\icons\folio.ico
OutputDir={#Root}\dist
OutputBaseFilename=Folio-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
ChangesAssociations=yes

[Languages]
; Inno Setup 6 不自带简体中文，用的是官方仓库里的社区翻译（issrc 的 is-6_7_1 标签，Files/Languages/Unofficial）
Name: "zh"; MessagesFile: "{#SourcePath}ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他："
Name: "pdfassoc"; Description: "用 Folio 打开 PDF 文件（可在“打开方式”里选择）"; GroupDescription: "其他："

[Files]
Source: "{#Root}\dist\Folio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#if HaveShell
Source: "{#Root}\dist\Folio-shell\*"; DestDir: "{#ShellDir}"; Flags: ignoreversion
; DLL 在带版本号的子目录里；同一个版本重装时 DLL 可能正被 Explorer 加载着，已经有了就不覆盖
Source: "{#Root}\dist\Folio-shell\{#AppVersion}\*"; DestDir: "{#ShellDir}\{#AppVersion}"; Flags: onlyifdoesntexist
#endif

[Icons]
; 起始位置不能是程序目录（Inno Setup 默认就是 {app}）：Folio 的当前目录在程序目录里时，
; 自动更新的替换脚本没法给程序目录改名，更新会装不上
Name: "{userprograms}\Folio"; Filename: "{app}\Folio.exe"; WorkingDir: "{userdocs}"
Name: "{userdesktop}\Folio"; Filename: "{app}\Folio.exe"; WorkingDir: "{userdocs}"; Tasks: desktopicon

[InstallDelete]
; 手动安装时清掉上次没装上的自动更新残留
Type: filesandordirs; Name: "{localappdata}\Programs\.folio-update"
#if HaveShell
; 右键菜单的稀疏包以这次装进来的为准（0.2.3 的 Folio-Shell.msix 已经拆成每个命令一个包）
Type: files; Name: "{#ShellDir}\*.msix"
#endif

[Registry]
; 只把 Folio 加进 PDF 的“打开方式”列表，不抢默认程序
Root: HKCU; Subkey: "Software\Classes\Folio.PDF"; ValueType: string; ValueData: "PDF 文档"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\Folio.PDF\DefaultIcon"; ValueType: string; ValueData: """{app}\Folio.exe"",0"; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\Folio.PDF\shell\open\command"; ValueType: string; ValueData: """{app}\Folio.exe"" ""%1"""; Tasks: pdfassoc
Root: HKCU; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "Folio.PDF"; ValueData: ""; Flags: uninsdeletevalue; Tasks: pdfassoc
; 资源管理器右键菜单：右键 PDF「用 Folio 压缩」「用 Folio 合并」，右键图片「用 Folio 转为 PDF」。
; 和 folio/platform_win.py 的 CONTEXT_MENU 一致；程序启动时也会按「设置 → 常规」里的开关补上或删掉
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Compress"; ValueType: string; ValueName: "MUIVerb"; ValueData: "用 Folio 压缩"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Compress"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Folio.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Compress\command"; ValueType: string; ValueData: """{app}\Folio.exe"" --tool compress ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Merge"; ValueType: string; ValueName: "MUIVerb"; ValueData: "用 Folio 合并"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Merge"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Folio.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Folio.Merge\command"; ValueType: string; ValueData: """{app}\Folio.exe"" --tool merge ""%1"""
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\Folio.ImagesToPdf"; ValueType: string; ValueName: "MUIVerb"; ValueData: "用 Folio 转为 PDF"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\Folio.ImagesToPdf"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Folio.exe,0"
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\image\shell\Folio.ImagesToPdf\command"; ValueType: string; ValueData: """{app}\Folio.exe"" --tool images ""%1"""

[Run]
#if HaveShell
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{#ShellDir}\register.ps1"" -Action install -Dir ""{#ShellDir}"" -Version {#AppVersion}"; WorkingDir: "{tmp}"; StatusMsg: "正在注册右键菜单…"; Flags: runhidden waituntilterminated
#endif
Filename: "{app}\Folio.exe"; Description: "立即打开 Folio"; Flags: nowait postinstall skipifsilent

#if HaveShell
[UninstallRun]
; 不写 WorkingDir：它在安装时就展开并记进卸载日志，{tmp} 到卸载时已经不存在，会 CreateProcess 失败（267）
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{#ShellDir}\register.ps1"" -Action uninstall -Dir ""{#ShellDir}"""; Flags: runhidden waituntilterminated; RunOnceId: "FolioShell"
#endif

[UninstallDelete]
; 自动更新后程序目录里的文件不在安装记录里，整个目录一起删掉
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\Programs\.folio-update"
Type: filesandordirs; Name: "{#ShellDir}"
