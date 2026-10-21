# Windows 11 资源管理器右键菜单扩展（x64）。由 packaging/build_shell.py 调用：
#     cmake -S shellext -B shellext/build -A x64 && cmake --build shellext/build --config Release
cmake_minimum_required(VERSION 3.20)
project(FolioShellExt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_compile_definitions(UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
if(MSVC)
  # 静态链接 C++ 运行库：用户电脑上不用另装 VC++ 运行库
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
  add_compile_options(/utf-8 /W4 /permissive-)
else()
  add_compile_options(-Wall -Wextra -municode)
  add_link_options(-municode -static)
endif()

add_library(FolioShellExt SHARED FolioShellExt.cpp FolioShellExt.def)
target_link_libraries(FolioShellExt PRIVATE shlwapi shell32 ole32 advapi32 uuid)

add_executable(FolioShell WIN32 FolioShell.cpp)
target_link_libraries(FolioShell PRIVATE shlwapi)

add_executable(FolioShellTest FolioShellTest.cpp)
target_link_libraries(FolioShellTest PRIVATE shlwapi shell32 ole32 advapi32 uuid)
