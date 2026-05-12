@echo off
REM encoding: GBK
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   B站视频下载器 - 一键构建脚本
echo ============================================
echo.
echo  此脚本将自动下载依赖并准备打包环境
echo  完成后使用 Inno Setup 打开 setup.iss 即可打包
echo.
pause

set PYTHON_VERSION=3.13.13
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set GETPIP_URL=https://bootstrap.pypa.io/get-pip.py
set FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
set CSC_PATH=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe

echo ============================================
echo  [1/4] 配置 Python 嵌入式环境
echo ============================================

if exist "python\python.exe" (
    echo  Python 已存在，跳过下载
    goto :install_pip
)

echo  正在下载 Python %PYTHON_VERSION% 嵌入式包...
curl -L --progress-bar -o python-embed.zip "%PYTHON_URL%"
if errorlevel 1 (
    echo.
    echo  错误：Python 下载失败，请检查网络连接
    echo  你也可以手动下载：%PYTHON_URL%
    echo  解压到项目根目录的 python\ 文件夹
    goto :fail
)

echo  正在解压 Python...
if not exist "python" mkdir python
powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath 'python' -Force"
del python-embed.zip

echo  正在配置 Python 路径...
(
    echo python313.zip
    echo .
    echo ..
    echo Lib
    echo.
    echo import site
) > python\python313._pth

mkdir python\Lib 2>nul
mkdir python\Lib\site-packages 2>nul

echo  Python 配置完成

:install_pip
echo.
echo ============================================
echo  [2/4] 安装 pip 和依赖包
echo ============================================

if not exist "python\Scripts\pip.exe" (
    echo  正在下载 get-pip.py...
    curl -L --progress-bar -o get-pip.py "%GETPIP_URL%"
    if errorlevel 1 (
        echo  错误：get-pip.py 下载失败
        goto :fail
    )

    echo  正在安装 pip...
    python\python.exe get-pip.py
    if errorlevel 1 (
        echo  错误：pip 安装失败
        goto :fail
    )
    del get-pip.py
    echo  pip 安装完成
) else (
    echo  pip 已存在，跳过安装
)

echo  正在安装项目依赖...
python\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo  错误：依赖包安装失败，请检查网络连接
    goto :fail
)
echo  依赖安装完成

echo.
echo ============================================
echo  [3/4] 配置 ffmpeg
echo ============================================

if exist "ffmpeg\ffmpeg.exe" (
    echo  ffmpeg 已存在，跳过下载
    goto :compile
)

echo  正在下载 ffmpeg（约80MB，请耐心等待）...
curl -L --progress-bar -o ffmpeg.zip "%FFMPEG_URL%"
if errorlevel 1 (
    echo  错误：ffmpeg 下载失败
    echo  你也可以手动下载 ffmpeg.exe 放到 ffmpeg\ 文件夹
    goto :fail
)

echo  正在解压 ffmpeg...
if not exist "ffmpeg" mkdir ffmpeg
powershell -Command ^
    "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg-temp' -Force; ^
     $exe = Get-ChildItem -Path 'ffmpeg-temp' -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1; ^
     if ($exe) { Copy-Item $exe.FullName 'ffmpeg\ffmpeg.exe' -Force } ^
     else { Write-Error 'ffmpeg.exe not found in archive' }; ^
     Remove-Item 'ffmpeg-temp' -Recurse -Force"
del ffmpeg.zip

if not exist "ffmpeg\ffmpeg.exe" (
    echo  错误：ffmpeg 解压失败
    echo  请手动下载 ffmpeg.exe 放到 ffmpeg\ 文件夹
    goto :fail
)
echo  ffmpeg 配置完成

:compile
echo.
echo ============================================
echo  [4/4] 编译启动器
echo ============================================

if not exist "launcher.cs" (
    echo  错误：找不到 launcher.cs
    goto :fail
)

if not exist "%CSC_PATH%" (
    echo  错误：未找到 C# 编译器
    echo  请确认已安装 .NET Framework 4.x
    echo  预期路径：%CSC_PATH%
    goto :fail
)

if not exist "logo\app.ico" (
    echo  错误：找不到 logo\app.ico，请先准备图标文件
    goto :fail
)

echo  正在编译 B站视频下载器.exe...
"%CSC_PATH%" /nologo /target:winexe /win32icon:logo\app.ico /out:"B站视频下载器.exe" launcher.cs
if errorlevel 1 (
    echo  错误：编译失败
    goto :fail
)
echo  编译完成

echo.
echo ============================================
echo  构建成功！
echo ============================================
echo.
echo  所有依赖已就绪，接下来：
echo  1. 安装 Inno Setup: https://jrsoftware.org/isinfo.php
echo  2. 打开 setup.iss
echo  3. 点击 编译(Compile) 即可生成安装包
echo  4. 安装包会输出到 output\ 文件夹
echo.
pause
exit /b 0

:fail
echo.
echo  构建中断，请解决上述错误后重试
echo.
pause
exit /b 1
