// 右键菜单扩展的自检（CI 里运行），返回 0 表示全部通过。
//
//     FolioShellTest.exe <FolioShellExt.dll> <临时目录>   直接加载 DLL 测试：标题、图标、按文件类型显示/隐藏、
//                                                        设置里关掉后隐藏、多选文件时一条命令启动
//     FolioShellTest.exe --packaged <临时目录>           通过已注册的稀疏包（dllhost 代理）创建，确认注册生效
#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <shobjidl.h>

#include <cstdio>
#include <fstream>
#include <initializer_list>
#include <sstream>
#include <string>
#include <vector>

namespace {

const CLSID kCompress = {0x774dddcf, 0x8048, 0x41f5, {0xa5, 0xe3, 0x7a, 0xf8, 0x31, 0xc7, 0x11, 0x1f}};
const CLSID kMerge = {0x2bd5e5c0, 0x1a3c, 0x4f08, {0x9e, 0x8a, 0xdf, 0xfb, 0x7a, 0x85, 0x84, 0x1d}};
const CLSID kImages = {0xe4165ea7, 0x0ea4, 0x4bf6, {0xaf, 0x0a, 0xb6, 0xf0, 0x3a, 0x8f, 0x1d, 0xb3}};

int g_failures = 0;

void Check(bool ok, const char* what) {
    std::printf("%s %s\n", ok ? "[ok]  " : "[FAIL]", what);
    if (!ok) ++g_failures;
}

std::string Utf8(const std::wstring& s) {
    int len = WideCharToMultiByte(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), nullptr, 0, nullptr, nullptr);
    std::string out(static_cast<size_t>(len), '\0');
    WideCharToMultiByte(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), &out[0], len, nullptr, nullptr);
    return out;
}

typedef HRESULT(STDAPICALLTYPE* GetClassObjectFn)(REFCLSID, REFIID, LPVOID*);
GetClassObjectFn g_get_class_object = nullptr;

IExplorerCommand* Create(const CLSID& clsid) {
    IExplorerCommand* cmd = nullptr;
    if (g_get_class_object) {
        IClassFactory* factory = nullptr;
        if (FAILED(g_get_class_object(clsid, IID_IClassFactory, reinterpret_cast<void**>(&factory)))) return nullptr;
        factory->CreateInstance(nullptr, __uuidof(IExplorerCommand), reinterpret_cast<void**>(&cmd));
        factory->Release();
    } else {
        CoCreateInstance(clsid, nullptr, CLSCTX_LOCAL_SERVER, __uuidof(IExplorerCommand), reinterpret_cast<void**>(&cmd));
    }
    return cmd;
}

IShellItemArray* Items(const std::wstring& dir, std::initializer_list<const wchar_t*> names) {
    std::vector<PIDLIST_ABSOLUTE> pidls;
    std::vector<PCIDLIST_ABSOLUTE> ids;
    for (const wchar_t* name : names) {
        std::wstring path = dir + L"\\" + name;
        PIDLIST_ABSOLUTE pidl = nullptr;
        if (SUCCEEDED(SHParseDisplayName(path.c_str(), nullptr, &pidl, 0, nullptr))) {
            pidls.push_back(pidl);
            ids.push_back(pidl);
        }
    }
    IShellItemArray* items = nullptr;
    if (ids.size() == names.size()) SHCreateShellItemArrayFromIDLists(static_cast<UINT>(ids.size()), ids.data(), &items);
    for (PIDLIST_ABSOLUTE p : pidls) CoTaskMemFree(p);
    return items;
}

bool Shown(IExplorerCommand* cmd, IShellItemArray* items) {
    EXPCMDSTATE state = ECS_HIDDEN;
    return cmd && items && SUCCEEDED(cmd->GetState(items, TRUE, &state)) && state == ECS_ENABLED;
}

std::wstring Title(IExplorerCommand* cmd) {
    LPWSTR name = nullptr;
    if (!cmd || FAILED(cmd->GetTitle(nullptr, &name))) return std::wstring();
    std::wstring s(name);
    CoTaskMemFree(name);
    return s;
}

void SetMenuEnabled(DWORD value) {
    RegSetKeyValueW(HKEY_CURRENT_USER, L"Software\\Folio\\Shell", L"ContextMenu", REG_DWORD, &value, sizeof(value));
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
    if (argc < 3) {
        std::printf("usage: FolioShellTest.exe <FolioShellExt.dll | --packaged> <temp dir>\n");
        return 2;
    }
    const bool packaged = std::wstring(argv[1]) == L"--packaged";
    const std::wstring dir = argv[2];
    CreateDirectoryW(dir.c_str(), nullptr);
    for (const wchar_t* name : {L"b 第二个.pdf", L"a.PDF", L"photo.jpg", L"notes.txt"}) {
        HANDLE f = CreateFileW((dir + L"\\" + name).c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, 0, nullptr);
        CloseHandle(f);
    }
    CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (!packaged) {
        HMODULE dll = LoadLibraryW(argv[1]);
        Check(dll != nullptr, "load FolioShellExt.dll");
        if (!dll) return 1;
        g_get_class_object = reinterpret_cast<GetClassObjectFn>(
            reinterpret_cast<void*>(GetProcAddress(dll, "DllGetClassObject")));
        Check(g_get_class_object != nullptr && GetProcAddress(dll, "DllCanUnloadNow") != nullptr, "exports");
        if (!g_get_class_object) return 1;
    }

    IExplorerCommand* compress = Create(kCompress);
    IExplorerCommand* merge = Create(kMerge);
    IExplorerCommand* images = Create(kImages);
    Check(compress && merge && images, packaged ? "create via registered package (dllhost)" : "create in-proc");
    if (!compress || !merge || !images) return 1;

    Check(Title(compress) == L"用 Folio 压缩", "title: compress");
    Check(Title(merge) == L"用 Folio 合并", "title: merge");
    Check(Title(images) == L"用 Folio 转为 PDF", "title: images");
    LPWSTR icon = nullptr;
    Check(SUCCEEDED(compress->GetIcon(nullptr, &icon)) && icon && StrStrIW(icon, L"\\Folio\\Folio.exe,0"), "icon is Folio.exe,0");
    std::wstring exe = icon ? std::wstring(icon, wcslen(icon) - 2) : std::wstring();
    CoTaskMemFree(icon);

    IShellItemArray* pdfs = Items(dir, {L"b 第二个.pdf", L"a.PDF"});
    IShellItemArray* jpg = Items(dir, {L"photo.jpg"});
    IShellItemArray* mixed = Items(dir, {L"a.PDF", L"photo.jpg"});
    IShellItemArray* txt = Items(dir, {L"notes.txt"});
    Check(pdfs && jpg && mixed && txt, "build shell item arrays");

    DWORD old = 1, size = sizeof(old);
    bool had = RegGetValueW(HKEY_CURRENT_USER, L"Software\\Folio\\Shell", L"ContextMenu", RRF_RT_REG_DWORD, nullptr,
                            &old, &size) == ERROR_SUCCESS;
    SetMenuEnabled(1);
    Check(Shown(compress, pdfs) && Shown(merge, pdfs), "PDF: compress and merge shown");
    Check(!Shown(images, pdfs), "PDF: images hidden");
    Check(Shown(images, jpg) && !Shown(compress, jpg) && !Shown(merge, jpg), "image: only images shown");
    Check(!Shown(compress, mixed) && !Shown(images, mixed), "PDF + image: all hidden");
    Check(!Shown(compress, txt) && !Shown(images, txt), "other files: hidden");
    SetMenuEnabled(0);
    Check(!Shown(compress, pdfs) && !Shown(images, jpg), "turned off in settings: hidden");
    if (had) {
        SetMenuEnabled(old);
    } else {
        RegDeleteKeyValueW(HKEY_CURRENT_USER, L"Software\\Folio\\Shell", L"ContextMenu");
    }

    if (!packaged) {  // dllhost 拿不到这里的环境变量，只在直接加载时测试启动命令
        std::wstring out = dir + L"\\launched.txt";
        DeleteFileW(out.c_str());
        SetEnvironmentVariableW(L"FOLIO_SHELL_TEST_OUT", out.c_str());
        Check(SUCCEEDED(compress->Invoke(pdfs, nullptr)), "invoke compress");
        std::ifstream f(out.c_str(), std::ios::binary);
        std::stringstream got;
        got << f.rdbuf();
        std::string want = Utf8(L"\"" + exe + L"\" --tool compress \"" + dir + L"\\b 第二个.pdf\" \"" + dir + L"\\a.PDF\"\n");
        Check(got.str() == want, "one command line with all selected files");
        if (got.str() != want) std::printf("  got:  %s  want: %s", got.str().c_str(), want.c_str());
    }

    for (IUnknown* u : {static_cast<IUnknown*>(pdfs), static_cast<IUnknown*>(jpg), static_cast<IUnknown*>(mixed),
                        static_cast<IUnknown*>(txt), static_cast<IUnknown*>(compress), static_cast<IUnknown*>(merge),
                        static_cast<IUnknown*>(images)}) {
        if (u) u->Release();
    }
    CoUninitialize();
    std::printf(g_failures ? "%d check(s) failed\n" : "all checks passed\n", g_failures);
    return g_failures ? 1 : 0;
}
