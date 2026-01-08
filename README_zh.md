# Staccato (断奏)

<div align="center">

![Python 版本](https://img.shields.io/badge/python-3.13+-blue.svg)
![平台](https://img.shields.io/badge/平台-Windows-lightgrey.svg)
![许可证](https://img.shields.io/badge/许可证-MIT-green.svg)
![状态](https://img.shields.io/badge/状态-活跃中-success.svg)
![Textual](https://img.shields.io/badge/TUI-Textual-orange.svg)

**通用型人机交互时序分析终端**

*一个赛博朋克风格的终端工具，用于分析大脑与手指之间的信号净度*

[English](README.md) | [核心功能](#-核心功能) | [安装](#-安装) | [使用](#-使用)

</div>

---

## 🎯 项目概述

**Staccato** 不仅仅是一个打字速度测试工具。它是**给手指用的示波器**——一个基于终端的工具，通过毫秒级分析揭示神经指令与物理执行之间的微观时序关系。

### 第一性原理：信号净度 (Signal Hygiene)

- **摒弃肤浅指标**：拒绝传统的"打字速度(WPM)"等表面指标
- **揭示信噪比**：透过微观毫秒级数据，揭示大脑指令与肌肉执行之间的信噪比
- **解决核心痛点**：**"手指粘连 (Finger Adhesion)"** —— 即前一个手指未完全抬起（Key Up），下一个手指已经按下（Key Down）导致的指令模糊

## ✨ 核心功能

### 1. 动态折叠钢琴卷帘 (Dynamic Folding Piano Roll)

- **自适应显示**：屏幕上只显示"由于操作而产生"的按键行，自动隐藏无用区域
- **物理排序**：即使是动态生成的行，也严格按照键盘物理布局（HHKB 标准）从上到下排序，符合直觉
- **毫秒级精度**：像音乐制作软件（DAW）一样，直观展示按下（Down）到抬起（Up）的全过程长条

### 2. 智能重叠判定 (Adhesion Detection)

- **可视化报错**：当不该重叠的两个键（如"急停"时的 A 和 D）发生重叠，重叠区域瞬间标红
- **去伪存真**：能够过滤掉 Windows 系统底层的 Auto-Repeat（长按连发）干扰，还原真实的物理按压时长

### 3. 简单的按钮控制

- **开始/停止录制**：使用专用按钮控制捕获
- **保存/加载会话**：持久化存储，便于详细分析
- **清除数据**：重置状态，开始新的测量
- **实时可视化**：钢琴卷帘实时显示按键操作

## 🎨 设计理念

**美学风格：Claude Code / 赛博朋克终端**

- 极致的深色模式（Dark Charcoal），无边框极简主义
- 高对比度的荧光色（Neon Blue/Red）作为数据反馈
- 摒弃一切多余装饰，只保留核心信息流

## 🛠️ 技术架构

- **平台**：Windows 10/11 原生（针对 Win32 API 深度优化）
- **核心技术栈**：
  - Python 3.13+
  - [Textual](https://github.com/Textualize/textual)（TUI 框架）
  - `keyboard`（底层键盘钩子）
  - `loguru`（结构化日志）
- **性能要求**：60fps 丝滑渲染，独立的输入监听守护线程，零阻塞 UI
- **架构设计**：事件驱动设计，原子快照渲染保证状态一致性

## 📦 安装

### 前置要求

- Windows 10/11
- Python 3.13 或更高版本
- 管理员权限（底层键盘钩子需要）

### 使用 uv 安装（推荐）

```bash
# 如果还没有安装 uv
pip install uv

# 克隆仓库
git clone https://github.com/chengyongru/staccato.git
cd staccato

# 安装依赖
uv sync

# 运行应用
uv run python main.py
```

### 使用 pip 安装

```bash
git clone https://github.com/chengyongru/staccato.git
cd staccato
pip install -e .
python main.py
```

## 🚀 使用

### 基本工作流

1. **启动应用**：运行 `python main.py`（或 `uv run python main.py`）
2. **开始录制**：点击"Start Recording"按钮开始捕获键盘输入
3. **正常输入**：钢琴卷帘会实时动态显示你的按键操作
4. **观察状态**：查看按键状态指示器：
   - **● (绿色)**：当前按下的按键，显示持续时间
   - **○ (灰色)**：已释放的按键
5. **停止录制**：点击"Stop Recording"按钮完成录制
6. **分析**：观察可视化反馈，查看粘连检测（红色区块）和时序分析
7. **保存会话**：使用"Save Session"保存数据供后续分析

### UI 控制按钮

| 按钮 | 功能 |
|------|------|
| **Start Recording** | 开始捕获键盘输入（录制时按钮隐藏） |
| **Stop Recording** | 停止捕获并冻结显示 |
| **Save Session** | 将当前录制保存到文件（JSON 格式） |
| **Load Session** | 加载之前保存的会话供分析 |
| **Clear** | 清除所有数据，重新开始 |

### 理解显示界面

```
A            | ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ | ● 1.23s
```

- **左侧标签**：按键名称（按物理键盘位置排序）
- **时间轴条形图**：
  - `█` (蓝色)：按键按下持续时间
  - `█` (红色)：重叠的按键按下（潜在的粘连问题）
  - `░` (灰色)：空白时间轴
- **右侧状态**：
  - `● 1.23s` (绿色)：按键当前被按下，显示持续时间
  - `○ released` (灰色)：按键已释放

## 📊 Staccato 的独特之处

传统的打字测试器测量**输出**（WPM、准确率）。Staccato 测量**输入信号质量**：

- **微观时序分析**：精确查看每个按键的按下和释放时间
- **粘连检测**：识别手指意外重叠的情况
- **信号净度**：理解意图与执行之间的差距
- **可视化反馈**：实时钢琴卷帘可视化

## 🎯 路线图与愿景

### 限制说明

- **平台限制**：目前仅支持 Windows，因为底层键盘钩子要求
- **远程桌面**：不支持 SSH/RDP 连接，因为键盘钩子需要本地控制台访问
- **管理员权限**：安装全局键盘钩子需要管理员权限

### 开源核心模式

- **开源 TUI 版本**：终端版本完全免费开源，希望为开发者和键盘爱好者提供有价值的工具
- **未来规划**：基于核心引擎，计划开发可视化更强的 GUI 版本，为更广泛的用户群体提供服务

### 未来功能

- [ ] 高级统计和分析仪表板
- [ ] 可自定义键盘布局（DVORAK、COLEMAK 等）
- [ ] 手指疲劳分析的热力图可视化
- [ ] 会话对比和差异视图
- [ ] 导出为 CSV/JSON 供外部分析
- [ ] 面向更广泛受众的 GUI 版本

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建你的功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交你的更改（`git commit -m '添加一些 AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启一个 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 使用 [Textual](https://github.com/Textualize/textual) 构建 - Python 的 TUI 框架
- 灵感来源于游戏和编程中对更好输入信号分析的需求

---

<div align="center">

**我们不是在做一个练打字的软件，我们是在做一个给手指用的示波器。**

用 ❤️ 为键盘爱好者和精度追求者打造

[⭐ 在 GitHub 上给我们点星](https://github.com/chengyongru/staccato) | [🐛 报告 Bug](https://github.com/chengyongru/staccato/issues) | [💡 请求功能](https://github.com/chengyongru/staccato/issues)

</div>
