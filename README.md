# Staccato (断奏)

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Textual](https://img.shields.io/badge/TUI-Textual-orange.svg)

**Universal HCI Micro-Timing Analysis Terminal**

*A cyberpunk terminal for analyzing the signal hygiene between your brain and your fingers*

[中文文档](README_zh.md) | [Features](#-core-features) | [Installation](#-installation) | [Usage](#-usage)

</div>

---

## 🎯 Overview

**Staccato** is not just another typing speed tester. It's an **oscilloscope for your fingers** — a terminal-based tool that reveals the micro-timing relationship between neural commands and physical execution through millisecond-level analysis.

### First Principles: Signal Hygiene

- **Rejects superficial metrics** like WPM (Words Per Minute)
- **Reveals the signal-to-noise ratio** between brain commands and muscle execution
- **Solves the core problem**: **"Finger Adhesion"** — when one finger hasn't fully released (Key Up) before the next finger presses (Key Down), causing command ambiguity

## ✨ Core Features

### 1. Dynamic Folding Piano Roll

- **Adaptive Display**: Only shows key rows that were actually pressed, automatically hiding unused areas
- **Physical Sorting**: Even dynamically generated rows are sorted by keyboard physical layout (HHKB standard), top to bottom
- **Millisecond Precision**: Visualizes the complete press (Down) to release (Up) cycle, just like a DAW (Digital Audio Workstation)

### 2. Intelligent Adhesion Detection

- **Visual Error Highlighting**: When two keys that shouldn't overlap (like A and D during an "emergency stop") do overlap, the overlapping region is instantly marked in red
- **Noise Filtering**: Filters out Windows system-level Auto-Repeat (hold-to-repeat) interference, revealing true physical press duration

### 3. Simple Button-Based Control

- **Start/Stop Recording**: Use dedicated buttons to control capture
- **Save/Load Sessions**: Persistent storage for detailed analysis
- **Clear Data**: Reset to start fresh measurements
- **Real-time Visualization**: Live piano roll shows your keystrokes as they happen

## 🎨 Design Philosophy

**Aesthetic Style: Claude Code / Cyberpunk Terminal**

- Extreme dark mode (Dark Charcoal), borderless minimalism
- High-contrast neon colors (Neon Blue/Red) for data feedback
- Zero decorative elements — only essential information flow

## 🛠️ Technology Stack

- **Platform**: Windows 10/11 Native (deeply optimized for Win32 API)
- **Core Stack**:
  - Python 3.13+
  - [Textual](https://github.com/Textualize/textual) (TUI framework)
  - `keyboard` (Low-level keyboard hooks)
  - `loguru` (Structured logging)
- **Performance**: Smooth rendering with independent input monitoring daemon thread, zero UI blocking
- **Architecture**: Event-driven design with atomic snapshot rendering for state consistency

## 📦 Installation

### Prerequisites

- Windows 10/11
- Python 3.13 or higher
- Administrator privileges (required for low-level keyboard hooks)

### Install with uv (Recommended)

```bash
# Install uv if you haven't
pip install uv

# Clone the repository
git clone https://github.com/chengyongru/staccato.git
cd staccato

# Install dependencies
uv sync

# Run the application
uv run python main.py
```

### Install with pip

```bash
git clone https://github.com/chengyongru/staccato.git
cd staccato
pip install -e .
python main.py
```

## 🚀 Usage

### Basic Workflow

1. **Start the application**: Run `python main.py` (or `uv run python main.py`)
2. **Start Recording**: Click the "Start Recording" button to begin capturing keyboard input
3. **Type normally**: The piano roll will dynamically display your keystrokes in real-time
4. **Observe State**: Watch the key status indicators:
   - **● (green)**: Currently pressed with duration counter
   - **○ (dim)**: Released
5. **Stop Recording**: Click the "Stop Recording" button when done
6. **Analyze**: Review the visual timeline for adhesion detection (red blocks)
7. **Save Session**: Use "Save Session" to persist your data for later analysis

### UI Controls

| Button | Action |
|--------|--------|
| **Start Recording** | Begin capturing keyboard input (button hides during recording) |
| **Stop Recording** | Stop capturing and freeze the display |
| **Save Session** | Save current recording to file (JSON format) |
| **Load Session** | Load a previously saved session for analysis |
| **Clear** | Reset all data and start fresh |

### Understanding the Display

```
A            | ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ | ● 1.23s
```

- **Left label**: Key name (sorted by physical keyboard position)
- **Timeline bar**:
  - `█` (blue): Key press duration
  - `█` (red): Overlapping key press (potential adhesion issue)
  - `░` (dim): Empty timeline
- **Right status**:
  - `● 1.23s` (green): Key is currently pressed, showing duration
  - `○ released` (dim): Key has been released

## 📊 What Makes Staccato Different?

Traditional typing testers measure **output** (WPM, accuracy). Staccato measures **input signal quality**:

- **Micro-timing analysis**: See exactly when each key is pressed and released
- **Adhesion detection**: Identify when fingers overlap unintentionally
- **Signal hygiene**: Understand the gap between intention and execution
- **Visual feedback**: Real-time piano roll visualization

## 🎯 Roadmap & Vision

### Limitations

- **Platform**: Currently Windows-only due to low-level keyboard hook requirements
- **Remote Desktop**: Does not work over SSH/RDP as keyboard hooks require local console access
- **Administrator Privileges**: Required for global keyboard hook installation

### Open Core Model

- **Open Source TUI Version**: The terminal version is completely free and open source, aiming to provide a valuable tool for developers and keyboard enthusiasts
- **Future Plans**: Based on the core engine, we plan to develop a more visually powerful GUI version to serve a broader user base

### Future Features

- [ ] Advanced statistics and analytics dashboard
- [ ] Customizable keyboard layouts (DVORAK, COLEMAK, etc.)
- [ ] Heat map visualization for finger fatigue analysis
- [ ] Session comparison and diff view
- [ ] Export to CSV/JSON for external analysis
- [ ] GUI version for broader audience

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) - the TUI framework for Python
- Inspired by the need for better input signal analysis in gaming and programming

---

<div align="center">

**We're not building a typing practice app. We're building an oscilloscope for your fingers.**

Made with ❤️ for keyboard enthusiasts and precision seekers

[⭐ Star us on GitHub](https://github.com/chengyongru/staccato) | [🐛 Report Bug](https://github.com/chengyongru/staccato/issues) | [💡 Request Feature](https://github.com/chengyongru/staccato/issues)

</div>
