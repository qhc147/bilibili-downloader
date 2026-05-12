# B站视频下载器

基于 Python + CustomTkinter 的 B站视频下载工具，支持扫码登录、多画质选择、实时进度显示。

## 功能

- 扫码登录 B站账号，解锁高画质
- 支持 360P ~ 4K 多种画质
- 下载进度、速度、剩余时间实时显示
- **一键检查更新 yt-dlp**（新增 v1.1.0）
- 暗色主题界面

## 打包指南

克隆仓库后，按以下步骤操作即可生成安装包。

### 前置要求

- Windows 10/11 64 位
- [Inno Setup 6](https://jrsoftware.org/isdl.php)（用于最终打包）

### 方式一：一键构建（推荐）

1. 双击运行 `build.bat`
2. 脚本会自动完成以下操作：
   - 下载 Python 3.13 嵌入式包 → `python/`
   - 安装 pip 和所有依赖库
   - 下载 ffmpeg → `ffmpeg/`
   - 编译启动器 → `B站视频下载器.exe`
3. 全部完成后，用 Inno Setup 打开 `setup.iss`，点击 **编译(Compile)**
4. 安装包会生成到 `output/` 文件夹

### 方式二：手动配置

如果 `build.bat` 某一步失败（比如网络问题），可以手动补全：

#### 1. Python 嵌入式环境

1. 前往 [Python 下载页](https://www.python.org/downloads/)
2. 找到 Python 3.13.x，下载 **Windows embeddable package (64-bit)**
3. 解压到项目根目录的 `python/` 文件夹
4. 编辑 `python/python313._pth`，确保内容如下：
   ```
   python313.zip
   .
   ..
   Lib

   import site
   ```
5. 安装 pip 和依赖：
   ```
   python\python.exe get-pip.py
   python\python.exe -m pip install -r requirements.txt
   ```
   > `get-pip.py` 可从 https://bootstrap.pypa.io/get-pip.py 下载

#### 2. ffmpeg

1. 前往 https://www.gyan.dev/ffmpeg/builds/
2. 下载 **ffmpeg-release-essentials.zip**
3. 解压后在 `bin/` 文件夹中找到 `ffmpeg.exe`
4. 将 `ffmpeg.exe` 复制到项目根目录的 `ffmpeg/` 文件夹（没有就新建一个）

最终目录结构：
```
ffmpeg/
  └── ffmpeg.exe
```

#### 3. 编译启动器

```
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:winexe /win32icon:logo\app.ico /out:B站视频下载器.exe launcher.cs
```

> 注意：`logo\app.ico` 已包含在仓库中，无需额外准备。

#### 4. 打包

用 Inno Setup 打开 `setup.iss`，点击编译即可。

## 作者

- **qhc147** — 开发者
- Claude — AI 辅助开发

## 目录结构

```
├── build.bat           # 一键构建脚本
├── launcher.cs         # C# 启动器源码
├── logo/               # 应用图标资源
│   └── app.ico         # 程序图标（exe/窗口/快捷方式）
├── requirements.txt    # Python 依赖清单
├── setup.iss           # Inno Setup 打包配置
├── src/                # Python 源代码
│   ├── main.py
│   ├── auth/           # B站登录认证
│   ├── downloader/     # 视频下载核心
│   ├── updater/        # yt-dlp 更新模块 (v1.1.0 新增)
│   └── ui/             # GUI 界面
├── python/             # (构建后生成) 嵌入式 Python
├── ffmpeg/             # (构建后生成) ffmpeg
└── output/             # (打包后生成) 安装包输出
```
