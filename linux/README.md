# 豆包语音输入 (Doubao Murmur) - Linux/SteamOS 版

使用豆包 ASR（自动语音识别）服务实现全局语音转文字输入。适用于 SteamOS Desktop Mode (Steam Deck) 和其他 Linux 发行版。

> **macOS 用户**: 请使用项目根目录的 macOS 版本。

## ✨ 功能

- ⌨️ **全局热键**: 右 `Alt` 开始/停止录音，`ESC` 取消（任何应用中均可用）
- 🎮 **手柄一键语音输入**: 在 Steam Input 桌面布局中把手柄按键映射为右 Alt 即可（见下文）
- 📝 **实时转写**: 说话时文字实时显示在屏幕顶部悬浮条中（不抢焦点、不挡输入）
- 📋 **自动粘贴**: 识别结果自动粘贴到当前输入框；终端自动改用 `Ctrl+Shift+V`
- 🔐 **登录一次**: 通过内置 WebView 登录豆包，凭证持久化存储
- 🫥 **静默驻留**: 启动后无窗口后台待命，再次启动应用可唤出控制面板

## 📋 系统要求

- **OS**: SteamOS 3 / Arch Linux / 其他支持 GTK4 的 Linux 发行版
- **音频**: PipeWire (SteamOS 默认) 或 PulseAudio
- **Python**: 3.11+
- **桌面环境**: KDE Plasma (推荐) 或 GNOME

## 🚀 安装

### 方法一: Flatpak (推荐)

从 [Releases](../../../../releases) 页面下载 `doubao-murmur.flatpak`：

```bash
flatpak install --user doubao-murmur.flatpak
flatpak run com.doubao.Murmur
```

WebKitGTK 等依赖打包在 GNOME runtime 中，**不受 SteamOS 系统更新影响**。

自动粘贴依赖宿主机的 `xdotool`（SteamOS 自带）。

也可以从源码自行构建：

```bash
cd linux
flatpak install flathub org.flatpak.Builder org.gnome.Platform//49 org.gnome.Sdk//49
make flatpak-install
```

### 方法二: 直接运行 (开发模式)

```bash
# 1. 安装系统依赖（SteamOS 需要先 sudo steamos-readonly disable）
sudo pacman -S python python-pip python-gobject gtk4 webkitgtk-6.0 xdotool

# 2. 安装 Python 依赖
cd linux
python3 -m venv --system-site-packages .venv
.venv/bin/pip install websockets sounddevice python-xlib

# 3. 运行
PYTHONPATH=src .venv/bin/python -m doubao_murmur
```

> ⚠️ SteamOS 系统更新会清除 pacman 安装的包，届时需重装 `webkitgtk-6.0`。推荐用 Flatpak。

## 🎮 使用方法

1. 首次启动会弹出控制面板，点击 **登录豆包**，在 WebView 中完成登录
2. 登录后应用静默驻留后台
3. 将光标放到任意输入框，按 **右 Alt**，屏幕顶部出现悬浮条，开始说话
4. 悬浮条实时显示识别文字（超长时自动滚动显示最新内容）
5. 再按一次 **右 Alt** 结束，文字自动粘贴到输入框
6. 录音期间屏幕底部会出现 ⏹ 按钮，点击它也可以停止

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| 右 Alt 键 | 开始 / 停止录音 |
| ESC 键 | 取消当前录音（不粘贴） |

### 🎮 手柄一键语音输入 (Steam Deck / 掌机)

桌面模式下 Steam 接管了手柄，原生按键事件不会透传，但可以让 Steam 把手柄按键转成键盘键：

1. 打开 **Steam → 设置 → 控制器 → 桌面布局 → 编辑**
2. 把 **R3（右摇杆按下）** 或任意顺手的按键 → 添加命令 → **键盘 → 右 Alt**
3. （可选）把 **B 键** → **键盘 → Escape**，用于取消录音

之后在任何应用里按 R3 即可开始/结束语音输入。应用通过 X11 层（XRecord）监听按键，
Steam 注入的按键和物理键盘都能识别，无需额外权限。

## 🏗 项目结构

```
linux/
├── src/doubao_murmur/
│   ├── __main__.py          # 入口点
│   ├── app.py               # 主 GtkApplication
│   ├── app_state.py         # 应用状态管理
│   ├── config.py            # 配置常量
│   ├── asr_client.py        # WebSocket ASR 客户端
│   ├── audio_capture.py     # 麦克风音频采集
│   ├── transcription.py     # 录音状态机
│   ├── params_store.py      # 凭证持久化
│   ├── hotkey/              # 输入管理
│   │   ├── manager.py       # 热键管理器（统一封送到 GTK 主线程）
│   │   ├── overlay_button.py # 屏幕 PTT 按钮
│   │   ├── x11_listener.py  # X11/XRecord 全局键监听（主用）
│   │   └── evdev_listener.py # /dev/input 监听（非 X11 后备）
│   ├── ui/                  # 用户界面
│   │   ├── overlay.py       # 录音悬浮窗
│   │   ├── windowing.py     # X11 置顶/定位/无焦点处理
│   │   ├── tray_icon.py     # 控制面板（GTK4 托盘后备）
│   │   └── login_window.py  # WebView 登录
│   ├── paste/               # 剪贴板/粘贴
│   │   └── paste_helper.py
│   └── resources/           # JS 注入脚本
├── flatpak/                 # Flatpak 打包
├── tests/                   # 单元测试
└── run.sh                   # 开发启动脚本
```

## 🔧 配置

配置文件存储在 `~/.config/doubao-murmur/asr_params.json`。

删除此文件可以强制重新登录：

```bash
rm ~/.config/doubao-murmur/asr_params.json
```

## ❓ 常见问题

### 启动后什么都没出现
- 这是正常的：已登录时应用静默驻留后台，按右 Alt 即可录音
- 想打开控制面板（登录/退出），再启动一次应用即可（单实例，会唤出面板）

### 没有声音/录音失败
- 检查麦克风权限: `arecord -l` 查看可用设备
- 检查 PipeWire: `pactl info` 确认音频系统正常
- 测试 Python 音频: `python3 -c "import sounddevice; print(sounddevice.query_devices())"`

### 自动粘贴不工作
- 确认宿主机有 `xdotool`（SteamOS 自带；其他发行版 `sudo pacman -S xdotool`）
- 文字始终会复制到剪贴板，粘贴失败时可手动 `Ctrl+V`（终端 `Ctrl+Shift+V`）

### 手柄按键不触发
- 确认是在 **桌面布局**（Desktop Layout）里设置的映射，不是某个游戏的布局
- 确认映射的目标是键盘的 **右 Alt**（Right Alt），不是左 Alt

### WebView 无法加载
- 安装 WebKitGTK: `sudo pacman -S webkitgtk-6.0`
- 确认网络连接正常

## 📝 开发

```bash
# 安装开发依赖
pip3 install --user -e ".[dev]"

# 运行测试
make test

# 运行应用
make run
```

## 📄 许可证

MIT License - 详见项目根目录的 LICENSE 文件。

## 🔗 相关链接

- [macOS 版本](../README.md)
- [豆包官网](https://www.doubao.com)
- [SteamOS](https://www.steamdeck.com)
