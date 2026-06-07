# 豆包语音输入 (Doubao Murmur) - Linux/SteamOS 版

使用豆包 ASR（自动语音识别）服务实现全局语音转文字输入。适用于 SteamOS Desktop Mode (Steam Deck) 和其他 Linux 发行版。

> **macOS 用户**: 请使用项目根目录的 macOS 版本。

## ✨ 功能

- 🎤 **一键录音**: 点击屏幕上的 🎤 按钮开始/停止录音
- 📝 **实时转写**: 说话时文字实时显示在悬浮窗中
- 📋 **自动粘贴**: 识别结果自动粘贴到当前输入框
- 🔐 **登录一次**: 通过内置 WebView 登录豆包，凭证持久化存储
- 🎮 **Steam Deck 优化**: 针对 1280×800 触摸屏优化

## 📋 系统要求

- **OS**: SteamOS 3 / Arch Linux / 其他支持 GTK4 的 Linux 发行版
- **音频**: PipeWire (SteamOS 默认) 或 PulseAudio
- **Python**: 3.11+
- **桌面环境**: KDE Plasma (推荐) 或 GNOME

## 🚀 快速开始

### 方法一: 直接运行 (开发模式)

```bash
# 1. 安装系统依赖
sudo pacman -S python python-pip python-gobject gtk4 webkitgtk-6.0 \
    portaudio wl-clipboard ydotool

# 2. 安装 Python 依赖
cd linux
pip3 install --user websockets sounddevice

# 3. 启用 ydotoold 守护进程 (用于自动粘贴)
sudo systemctl enable --now ydotoold
sudo usermod -aG input $USER
# 需要重新登录使 input 组生效

# 4. 运行
./run.sh
```

### 方法二: Flatpak (推荐)

```bash
# 构建并安装
make flatpak-install

# 设置权限
bash flatpak/setup-permissions.sh

# 运行
flatpak run com.doubao.Murmur
```

## 🎮 使用方法

1. 首次启动后，点击系统托盘图标 → **登录豆包**
2. 在弹出的 WebView 中完成豆包账号登录
3. 登录成功后 WebView 自动关闭，🎤 按钮出现在屏幕底部
4. 点击 🎤 按钮开始录音，对准麦克风说话
5. 再次点击 🎤 按钮停止录音
6. 识别结果自动粘贴到当前焦点输入框

### 快捷键 (需要 input 组权限)

| 快捷键 | 功能 |
|--------|------|
| 右 Alt 键 | 切换录音状态 |
| ESC 键 | 取消当前录音 |

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
│   │   ├── manager.py       # 热键管理器
│   │   ├── overlay_button.py # 屏幕 PTT 按钮
│   │   └── evdev_listener.py # /dev/input 监听
│   ├── ui/                  # 用户界面
│   │   ├── overlay.py       # 录音悬浮窗
│   │   ├── tray_icon.py     # 系统托盘
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

### 🎤 按钮没有出现
- 检查是否已登录豆包账号
- 检查 GTK4 是否正确安装: `gtk4-demo`

### 没有声音/录音失败
- 检查麦克风权限: `arecord -l` 查看可用设备
- 检查 PipeWire: `pactl info` 确认音频系统正常
- 测试 Python 音频: `python3 -c "import sounddevice; print(sounddevice.query_devices())"`

### 自动粘贴不工作
- 安装 ydotool: `sudo pacman -S ydotool`
- 启用守护进程: `sudo systemctl enable --now ydotoold`
- 加入 input 组: `sudo usermod -aG input $USER` (需重新登录)

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
