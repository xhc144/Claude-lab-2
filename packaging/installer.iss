; Windows 安装程序（Inno Setup 6）。先运行 packaging/build.py 生成 dist/Folio，再：
;     iscc /DAppVersion=0.2.2 packaging/installer.iss
; 生成 dist/Folio-Setup-<版本>.exe。
;
; 装到当前用户自己的目录（%LOCALAPPDATA%\Programs\Folio），不需要管理员权限：
; 自动更新会整体替换程序目录，必须对这个目录和它的上一级有写权限。
; 也因为这样，卸载程序不能放在程序目录里（更新时会被一起替换掉），单独放在旁边的 Folio-uninstall。

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define Root SourcePath + "\.."

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

[Icons]
Name: "{userprograms}\Folio"; Filename: "{app}\Folio.exe"
Name: "{userdesktop}\Folio"; Filename: "{app}\Folio.exe"; Tasks: desktopicon

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
Filename: "{app}\Folio.exe"; Description: "立即打开 Folio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 自动更新后程序目录里的文件不在安装记录里，整个目录一起删掉
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\Programs\.folio-update"
