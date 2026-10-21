// Folio 的 Windows 11 资源管理器右键菜单（第一层新菜单里的「用 Folio 压缩」「用 Folio 合并」「用 Folio 转为 PDF」）。
//
// Windows 11 的新菜单只显示两种条件都满足的扩展：实现了 IExplorerCommand 的 COM 类，并且由带包标识的清单注册。
// 这个 DLL 由稀疏包（packaging/sparse/AppxManifest.xml）注册成 COM 代理服务器，在 dllhost.exe 里加载。
// 三个命令各是一个顶层菜单项（各有一个 CLSID），GetState 按选中文件的扩展名决定显不显示。
//
// 位置：%LOCALAPPDATA%\Programs\Folio-shell\<版本>\FolioShellExt.dll，Folio.exe 在 %LOCALAPPDATA%\Programs\Folio\。
// 不放进程序目录：自动更新会给整个程序目录改名，而 dllhost 加载着的 DLL 会锁住它所在的目录，更新就会失败。
//
// 只用 Windows 自带的头文件和库，手写 COM，不依赖 WRL/ATL；用 MSVC 或 MinGW 都能编译。
#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <shobjidl.h>

#include <new>
#include <string>
#include <vector>

namespace {

HMODULE g_module = nullptr;
LONG g_objects = 0;  // 还活着的命令和类工厂对象
LONG g_locks = 0;    // IClassFactory::LockServer 计数

enum class Kind { Pdf, Image };

struct CommandInfo {
    CLSID clsid;
    const wchar_t* title;
    const wchar_t* tool;  // 传给 Folio.exe --tool 的工具名（folio/app.py 的 TOOL_KEYS）
    Kind kind;
};

// CLSID 要和 packaging/sparse/AppxManifest.xml、folio/platform_win.py 里的一致
const CommandInfo kCommands[] = {
    // {774DDDCF-8048-41F5-A5E3-7AF831C7111F}
    {{0x774dddcf, 0x8048, 0x41f5, {0xa5, 0xe3, 0x7a, 0xf8, 0x31, 0xc7, 0x11, 0x1f}}, L"用 Folio 压缩", L"compress", Kind::Pdf},
    // {2BD5E5C0-1A3C-4F08-9E8A-DFFB7A85841D}
    {{0x2bd5e5c0, 0x1a3c, 0x4f08, {0x9e, 0x8a, 0xdf, 0xfb, 0x7a, 0x85, 0x84, 0x1d}}, L"用 Folio 合并", L"merge", Kind::Pdf},
    // {E4165EA7-0EA4-4BF6-AF0A-B6F03A8F1DB3}
    {{0xe4165ea7, 0x0ea4, 0x4bf6, {0xaf, 0x0a, 0xb6, 0xf0, 0x3a, 0x8f, 0x1d, 0xb3}}, L"用 Folio 转为 PDF", L"images", Kind::Image},
};

const wchar_t* const kImageExts[] = {L".png", L".jpg", L".jpeg", L".bmp", L".gif", L".tif", L".tiff", L".webp"};

// 命令行最长 32767 个字符；文件特别多时分几批启动，Folio 的单实例机制会把它们合到同一个窗口里
const size_t kMaxCommandLine = 30000;

std::wstring Parent(const std::wstring& path) {
    size_t k = path.find_last_of(L'\\');
    return k == std::wstring::npos ? path : path.substr(0, k);
}

std::wstring ModulePath(HMODULE module) {
    std::wstring buf(MAX_PATH, L'\0');
    for (;;) {
        DWORD n = GetModuleFileNameW(module, &buf[0], static_cast<DWORD>(buf.size()));
        if (n == 0) return std::wstring();
        if (n < buf.size()) {
            buf.resize(n);
            return buf;
        }
        buf.resize(buf.size() * 2);
    }
}

// Folio-shell\<版本>\FolioShellExt.dll → Programs\Folio\Folio.exe
std::wstring FolioExe() {
    return Parent(Parent(Parent(ModulePath(g_module)))) + L"\\Folio\\Folio.exe";
}

bool FileExists(const std::wstring& path) {
    DWORD a = GetFileAttributesW(path.c_str());
    return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}

// 「设置 → 常规 → 资源管理器右键菜单」关掉时，Folio 会把这个值写成 0（folio/platform_win.py）
bool MenuEnabled() {
    DWORD value = 1;
    DWORD size = sizeof(value);
    if (RegGetValueW(HKEY_CURRENT_USER, L"Software\\Folio\\Shell", L"ContextMenu", RRF_RT_REG_DWORD, nullptr, &value,
                     &size) != ERROR_SUCCESS) {
        return true;  // 没设置过：默认显示
    }
    return value != 0;
}

bool Matches(const std::wstring& path, Kind kind) {
    const wchar_t* ext = PathFindExtensionW(path.c_str());
    if (kind == Kind::Pdf) return _wcsicmp(ext, L".pdf") == 0;
    for (const wchar_t* e : kImageExts) {
        if (_wcsicmp(ext, e) == 0) return true;
    }
    return false;
}

// 取出选中的全部文件路径；有不在磁盘上的项目（例如压缩包里的文件）时失败
HRESULT SelectedPaths(IShellItemArray* items, std::vector<std::wstring>& out) {
    if (!items) return E_INVALIDARG;
    DWORD count = 0;
    HRESULT hr = items->GetCount(&count);
    if (FAILED(hr)) return hr;
    for (DWORD i = 0; i < count; ++i) {
        IShellItem* item = nullptr;
        hr = items->GetItemAt(i, &item);
        if (FAILED(hr)) return hr;
        PWSTR path = nullptr;
        hr = item->GetDisplayName(SIGDN_FILESYSPATH, &path);
        item->Release();
        if (FAILED(hr)) return hr;
        out.emplace_back(path);
        CoTaskMemFree(path);
    }
    return count ? S_OK : E_INVALIDARG;
}

// 测试时（shellext/FolioShellTest.cpp）设置 FOLIO_SHELL_TEST_OUT，只把命令行追加到这个文件里，不真的启动
HRESULT WriteTestOutput(const wchar_t* file, const std::wstring& cmd) {
    HANDLE f = CreateFileW(file, FILE_APPEND_DATA, FILE_SHARE_READ, nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (f == INVALID_HANDLE_VALUE) return HRESULT_FROM_WIN32(GetLastError());
    std::wstring line = cmd + L"\n";
    int len = WideCharToMultiByte(CP_UTF8, 0, line.c_str(), static_cast<int>(line.size()), nullptr, 0, nullptr, nullptr);
    std::string utf8(static_cast<size_t>(len), '\0');
    WideCharToMultiByte(CP_UTF8, 0, line.c_str(), static_cast<int>(line.size()), &utf8[0], len, nullptr, nullptr);
    DWORD written = 0;
    BOOL ok = WriteFile(f, utf8.data(), static_cast<DWORD>(utf8.size()), &written, nullptr);
    CloseHandle(f);
    return ok ? S_OK : HRESULT_FROM_WIN32(GetLastError());
}

HRESULT Launch(const std::wstring& exe, std::wstring cmd) {
    wchar_t test_out[MAX_PATH * 2];
    DWORD n = GetEnvironmentVariableW(L"FOLIO_SHELL_TEST_OUT", test_out, ARRAYSIZE(test_out));
    if (n > 0 && n < ARRAYSIZE(test_out)) return WriteTestOutput(test_out, cmd);
    STARTUPINFOW si = {};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi = {};
    // 当前目录用 dllhost 自己的（系统目录），不用文件所在的文件夹：Folio 开着时那个文件夹会因此不能改名
    if (!CreateProcessW(exe.c_str(), &cmd[0], nullptr, nullptr, FALSE, 0, nullptr, nullptr, &si, &pi)) {
        return HRESULT_FROM_WIN32(GetLastError());
    }
    AllowSetForegroundWindow(pi.dwProcessId);  // 让 Folio 的窗口能切到前台
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return S_OK;
}

class Command final : public IExplorerCommand {
public:
    explicit Command(const CommandInfo& info) : info_(info) { InterlockedIncrement(&g_objects); }

    // IUnknown
    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (!ppv) return E_POINTER;
        if (IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, __uuidof(IExplorerCommand))) {
            *ppv = static_cast<IExplorerCommand*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override { return static_cast<ULONG>(InterlockedIncrement(&refs_)); }
    IFACEMETHODIMP_(ULONG) Release() override {
        LONG n = InterlockedDecrement(&refs_);
        if (n == 0) delete this;
        return static_cast<ULONG>(n);
    }

    // IExplorerCommand
    IFACEMETHODIMP GetTitle(IShellItemArray*, LPWSTR* name) override { return SHStrDupW(info_.title, name); }
    IFACEMETHODIMP GetIcon(IShellItemArray*, LPWSTR* icon) override {
        return SHStrDupW((FolioExe() + L",0").c_str(), icon);
    }
    IFACEMETHODIMP GetToolTip(IShellItemArray*, LPWSTR* tip) override {
        *tip = nullptr;
        return E_NOTIMPL;
    }
    IFACEMETHODIMP GetCanonicalName(GUID* guid) override {
        *guid = info_.clsid;
        return S_OK;
    }
    IFACEMETHODIMP GetState(IShellItemArray* items, BOOL, EXPCMDSTATE* state) override {
        *state = Visible(items) ? ECS_ENABLED : ECS_HIDDEN;
        return S_OK;
    }
    IFACEMETHODIMP Invoke(IShellItemArray* items, IBindCtx*) override {
        std::vector<std::wstring> paths;
        HRESULT hr = SelectedPaths(items, paths);
        if (FAILED(hr)) return hr;
        // 一次把所有选中的文件交给一个 Folio 进程：Folio.exe --tool <工具> "文件1" "文件2" …
        const std::wstring exe = FolioExe();
        const std::wstring head = L"\"" + exe + L"\" --tool " + info_.tool;
        std::wstring cmd = head;
        for (const std::wstring& p : paths) {
            std::wstring arg = L" \"" + p + L"\"";  // Windows 的文件名里不会有双引号
            if (cmd.size() + arg.size() > kMaxCommandLine && cmd.size() > head.size()) {
                hr = Launch(exe, cmd);
                if (FAILED(hr)) return hr;
                cmd = head;
            }
            cmd += arg;
        }
        return Launch(exe, cmd);
    }
    IFACEMETHODIMP GetFlags(EXPCMDFLAGS* flags) override {
        *flags = ECF_DEFAULT;
        return S_OK;
    }
    IFACEMETHODIMP EnumSubCommands(IEnumExplorerCommand** commands) override {
        *commands = nullptr;
        return E_NOTIMPL;
    }

private:
    ~Command() { InterlockedDecrement(&g_objects); }

    // 选中的文件全部是这个命令处理的类型时才显示（PDF 和图片混选时都不显示）
    bool Visible(IShellItemArray* items) const {
        if (!MenuEnabled() || !FileExists(FolioExe())) return false;
        std::vector<std::wstring> paths;
        if (FAILED(SelectedPaths(items, paths))) return false;
        for (const std::wstring& p : paths) {
            if (!Matches(p, info_.kind)) return false;
        }
        return true;
    }

    const CommandInfo& info_;
    LONG refs_ = 1;
};

class Factory final : public IClassFactory {
public:
    explicit Factory(const CommandInfo& info) : info_(info) { InterlockedIncrement(&g_objects); }

    IFACEMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (!ppv) return E_POINTER;
        if (IsEqualIID(riid, IID_IUnknown) || IsEqualIID(riid, IID_IClassFactory)) {
            *ppv = static_cast<IClassFactory*>(this);
            AddRef();
            return S_OK;
        }
        *ppv = nullptr;
        return E_NOINTERFACE;
    }
    IFACEMETHODIMP_(ULONG) AddRef() override { return static_cast<ULONG>(InterlockedIncrement(&refs_)); }
    IFACEMETHODIMP_(ULONG) Release() override {
        LONG n = InterlockedDecrement(&refs_);
        if (n == 0) delete this;
        return static_cast<ULONG>(n);
    }

    IFACEMETHODIMP CreateInstance(IUnknown* outer, REFIID riid, void** ppv) override {
        if (!ppv) return E_POINTER;
        *ppv = nullptr;
        if (outer) return CLASS_E_NOAGGREGATION;
        Command* cmd = new (std::nothrow) Command(info_);
        if (!cmd) return E_OUTOFMEMORY;
        HRESULT hr = cmd->QueryInterface(riid, ppv);
        cmd->Release();
        return hr;
    }
    IFACEMETHODIMP LockServer(BOOL lock) override {
        if (lock) {
            InterlockedIncrement(&g_locks);
        } else {
            InterlockedDecrement(&g_locks);
        }
        return S_OK;
    }

private:
    ~Factory() { InterlockedDecrement(&g_objects); }

    const CommandInfo& info_;
    LONG refs_ = 1;
};

}  // namespace

extern "C" BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        g_module = instance;
        DisableThreadLibraryCalls(instance);
    }
    return TRUE;
}

STDAPI DllGetClassObject(REFCLSID clsid, REFIID riid, LPVOID* ppv) {
    if (!ppv) return E_POINTER;
    *ppv = nullptr;
    for (const CommandInfo& info : kCommands) {
        if (IsEqualCLSID(clsid, info.clsid)) {
            Factory* factory = new (std::nothrow) Factory(info);
            if (!factory) return E_OUTOFMEMORY;
            HRESULT hr = factory->QueryInterface(riid, ppv);
            factory->Release();
            return hr;
        }
    }
    return CLASS_E_CLASSNOTAVAILABLE;
}

STDAPI DllCanUnloadNow() {
    return (g_objects == 0 && g_locks == 0) ? S_OK : S_FALSE;
}
