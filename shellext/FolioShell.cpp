// 稀疏包的清单里必须有一个 Application，这个小程序就是它（AppListEntry="none"，开始菜单里看不到）。
// 平时不会被启动；万一被启动，就把参数原样交给 Folio.exe。
// 位置：%LOCALAPPDATA%\Programs\Folio-shell\FolioShell.exe → %LOCALAPPDATA%\Programs\Folio\Folio.exe
#include <windows.h>
#include <shlwapi.h>

#include <string>

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    wchar_t self[MAX_PATH * 2];
    DWORD n = GetModuleFileNameW(nullptr, self, ARRAYSIZE(self));
    if (n == 0 || n >= ARRAYSIZE(self)) return 1;
    std::wstring dir(self, n);
    dir = dir.substr(0, dir.find_last_of(L'\\'));                    // Folio-shell
    std::wstring exe = dir.substr(0, dir.find_last_of(L'\\')) + L"\\Folio\\Folio.exe";
    std::wstring cmd = L"\"" + exe + L"\"";
    const wchar_t* args = PathGetArgsW(GetCommandLineW());
    if (args && *args) cmd += std::wstring(L" ") + args;
    STARTUPINFOW si = {};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {};
    if (!CreateProcessW(exe.c_str(), &cmd[0], nullptr, nullptr, FALSE, 0, nullptr, nullptr, &si, &pi)) return 1;
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return 0;
}
