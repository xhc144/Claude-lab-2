# Folio 开发说明（给改代码的人和 AI）

Folio 是 PySide6（Qt）+ PyMuPDF 的 PDF 阅读器。Windows 用 PyInstaller 打包、Inno Setup 做安装程序，
装在 `%LOCALAPPDATA%\Programs\Folio`（不需要管理员权限）；macOS 是 `Folio.app`。默认分支 `main`。

## 基本约定

- 代码注释、界面文字、提交说明、文档都用中文，风格和周围的代码保持一致。
- 改完先跑测试：`QT_QPA_PLATFORM=offscreen python -m pytest -q`。Windows 专用的测试（替换脚本、注册表、命名管道）只在 Windows 上跑，CI 的 `windows-latest` 会跑。
- 不要直接推 `main`，在分支上改、开 PR。不要自己打 `v*` 标签或手动发布：推送 `v*` 标签或在 Actions 里填版本号运行，就会正式发布并推送给所有用户的自动更新。
- 版本号在 `folio/__init__.py`，发版说明写在 `docs/CHANGELOG.md` 对应的 `## 版本号` 一节（会原样进入更新提示和 Release 说明）。

## 自动更新的注意事项

代码在 `folio/update.py`，测试在 `tests/test_update.py`。**改动更新相关的任何代码（`update.py`、`WIN_SCRIPT`、`MAC_SCRIPT`、`ui/dialogs/update_dialog.py`、`packaging/installer.iss` 的快捷方式和目录、`packaging/make_manifest.py`、`packaging/update_key.py`）后必须跑 `tests/test_update.py`**，涉及 Windows 替换脚本的改动要在 Windows 上跑（CI 的 Windows 任务会跑）。

### 流程

1. **check**：读取 `latest.json`（GitHub Releases），程序内置了更新公钥时先验证清单的 Ed25519 签名，再比较版本号。
2. **prepare**：下载对应平台的 zip → 校验大小和 SHA-256 → 解压到程序目录旁边的 `.folio-update`（同一个磁盘，替换时只要改名）→ 当前程序有代码签名时，确认新版本是同一个签名者（同一张证书的指纹，或受信任证书的同一个 Subject）。解压目录里会写 `update.json` 记下要装的版本。
3. **launch_installer**：把替换脚本（Windows 是 PowerShell 的 `WIN_SCRIPT`，macOS 是 `MAC_SCRIPT`）写到临时目录并启动，然后 Folio 退出。
4. **替换脚本**：等旧进程退出 → 把程序目录改名成 `Folio.old-时间` → 把新版本移进来 → 重新启动 → 删掉旧目录和解压目录。改名失败会重试 20 秒；最终失败时写日志 `%TEMP%\folio-update-时间.log`，重新打开旧版本。
5. **下次启动**：`pending_failure()` 发现解压目录里还留着新版本（替换成功时它会被移走），就提示「更新没有装上」并给出手动下载地址，然后清理残留。

### 踩过的坑：当前目录会锁住程序目录（0.2.1 → 0.2.2 时真实发生过）

Windows 不允许给一个**正被某个进程当作当前目录**的文件夹（或者里面有文件被打开、DLL 被加载的文件夹）改名。从开始菜单或桌面快捷方式启动 Folio 时，它的当前目录就是程序目录（Inno Setup 的快捷方式默认「起始位置」是 `{app}`）；以前 `subprocess.Popen` 启动替换脚本时没传 `cwd`，PowerShell 继承了这个当前目录，自己把程序目录锁住了，`Rename-Item` 重试 40 次都失败，然后悄悄重新打开旧版本——用户看到的是「下载成功但重启后还是旧版本，`.folio-update` 一直留着」。

所以：

- **替换脚本和它的父进程都不能把当前目录放在程序目录里。** `launch_installer()` 的两个 `Popen` 都传 `cwd=tempfile.gettempdir()`；`WIN_SCRIPT` 一开头就 `Set-Location` 到临时目录，`MAC_SCRIPT` 一开头就 `cd` 到临时目录（双保险）。
- 快捷方式的起始位置是 `{userdocs}`（`packaging/installer.iss` 的 `[Icons]`），CI 试装时会检查。
- 同理，任何会长时间打开程序目录里文件的东西都不能放进程序目录。Windows 11 右键菜单的 DLL 会被 Explorer（dllhost.exe）加载，所以它装在旁边的 `Folio-shell`，不在 `Folio` 里。
- 新增要启动的子进程时，想一想它会不会在 Folio 退出后还活着、当前目录在哪里。

### 重要：执行替换的是「旧版本」的代码

`launch_installer()` 和替换脚本都来自**正在运行的旧版本**，新版本只是被下载的 zip。所以对更新逻辑的修复只对「从修复后的版本再往后更新」生效：

- 已经装了 0.2.2 及更早版本的用户，升级到 0.2.3 这一次仍然会失败，需要手动下载安装程序覆盖安装（或者先把快捷方式的「起始位置」改成别的目录，再从快捷方式启动、更新）。发版说明里要写清楚。
- 改 `update.py` / `WIN_SCRIPT` / `MAC_SCRIPT` 时，一定要想清楚**旧客户端会怎么跑新逻辑**：旧客户端会用它自己的代码下载、校验、解压、替换新版本。清单格式（`latest.json` 的字段）、zip 的目录结构（解压后顶层是 `Folio/Folio.exe` 或 `Folio.app`）、签名方式（换证书会让「同一签名者」检查失败）、更新公钥（换密钥后旧版本验证不了新清单）都要保持旧客户端能处理，否则所有用户都得手动更新一次。
- 需要改这些约定时，先发一个「能理解新旧两种格式」的过渡版本，等大部分用户更新到它之后再切换。

### 排查「更新下不来 / 装不上」

1. 看 `%LOCALAPPDATA%\Programs\.folio-update` 有没有残留：有 `Folio` 子目录说明下载、解压成功，但替换失败了；`update.json` 里是要装的版本。
2. 看 `%TEMP%\folio-update-*.log`（替换失败的原因、当时的当前目录、`$Error[0]`）和 `%TEMP%\folio-update-*.ps1`（实际运行的替换脚本，能看出用户的旧版本是哪一版逻辑）。
3. 看 `%LOCALAPPDATA%\Programs` 里有没有 `Folio.old-*`：改名成功但移入新版本失败时会改回去，残留说明中途出错。
4. 0.2.2 及更早版本没有日志，基本都是上面「当前目录」的问题：让用户手动下载安装。
5. 下载、校验阶段的错误会直接显示在更新窗口里（SHA-256 不一致、签名者不一致、清单签名无效等）。

## Windows 右键菜单

两套，详见 README「Windows 11 右键菜单」和 `folio/platform_win.py` 开头的注释：

- 新菜单：`shellext/`（C++ IExplorerCommand，三个 CLSID）+ `packaging/sparse/`（稀疏包清单、`register.ps1`），由 `packaging/build_shell.py` 构建。CLSID 在 `FolioShellExt.cpp`、`AppxManifest.xml`、`FolioShellTest.cpp` 三处要一致。
- 旧菜单：`folio/platform_win.py` 的 `CONTEXT_MENU`、`packaging/installer.iss` 的 `[Registry]`、`register.ps1` 的 `$Legacy` 三处要一致。
- 稀疏包的 Publisher 必须和签名证书的 Subject 完全一致；证书不受信任时注册会失败，自动退回旧菜单。
