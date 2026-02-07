
# Mi Tools Lite 🚀

**Mi Tools Lite** is a powerful, modular, and modern desktop application designed for advanced management of Xiaomi (MIUI/HyperOS) and Android devices via ADB. Built with Python and CustomTkinter, it offers a sleek dark-mode interface to debloat, monitor, tweak, and manage your device without needing root access (for most features).

## ✨ Features

### 🔌 Connection & Monitoring
*   **One-Click Connection**: Automatically scans and connects to ADB devices.
*   **Real-Time Monitor**: Live updates for:
    *   **Battery**: Level, Voltage, Temperature.
    *   **RAM**: Total, Free, Available memory.
    *   **CPU**: Core count and architecture.
*   **Smart Polling**: Only updates stats when the relevant tab is active to save resources.

### 🗑️ Advanced Debloater
*   **Safe Debloating**: Remove system apps for the current user (`--user 0`) without bricking the device.
*   **Dual-Variant Intelligence**: Automatically detects and handles both **Old MIUI** (`com.miui.*`) and **New HyperOS** (`com.xiaomi.*`) package names.
*   **Categorized Lists**: Pre-defined lists for Xiaomi, Google, Facebook, and Microsoft bloatware.
*   **Multi-Select**: tick multiple apps or "Select All" to remove them in bulk.
*   **Robust Restore**: Easily re-enable or re-install apps if you change your mind.

### 📦 Package Manager
*   **Deep Filtering**: View apps by category:
    *   ✅ **System Apps**
    *   👤 **User Apps**
    *   🚫 **Disabled Apps**
    *   🗑️ **Uninstalled System Apps** (Apps you previously removed)
*   **Batch Actions**: Uninstall, Disable, Enable, or Restore multiple apps at once.
*   **Search**: Real-time filtering by package name.

### ⚡ Task Manager & Process Killer
*   **Live Process List**: View all running user processes with PIDs.
*   **Auto-Foreground Detection**: One-click button to **instantly find and select the app currently on your screen**.
*   **Kill Options**:
    *   🟧 **Force Stop**: Cleanly stop an app (standard method).
    *   🟥 **Kill (Hard)**: Send `SIGKILL` to freeze/hung apps.
    *   ⬛ **Crash**: Send `SIGSEGV` to force a crash (useful for testing).

### 🔋 Power & Performance
*   **Low Power Mode**: Toggle Android's built-in battery saver via ADB.
*   **Doze Mode**: Force the device into Deep Sleep / Idle state immediately.
*   **Game Booster**: Trigger MIUI's performance/game mode properties.

### 🛠️ Inspector & Shell
*   **Layout Inspector**: Dump the current window hierarchy (UI XML) for debugging.
*   **Manual Shell**: Execute **any** ADB shell command directly from the GUI and view the output.

### 🎨 Tweaks & Customization
*   **Animation Speed Slider**: Finely tune window/transition scales from **0.1x (Lightning fast)** to **10x (Slow motion)**.
*   **Resolution & DPI**: Change screen density (DPI) and resolution safely.

### 🔄 Reboot Menu
*   **Modes**:
    *   System (Normal)
    *   Recovery (TWRP/Stock)
    *   Bootloader (Fastboot)
    *   FastbootD
    *   EDL (Emergency Download Mode)

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.10+**
*   **ADB (Android Platform Tools)** installed and added to your System PATH.
*   **USB Debugging** enabled on your Android device.

### Installation
1.  Clone the repository or download the source.
2.  Install dependencies:
    ```bash
    pip install customtkinter
    ```
3.  Run the application:
    ```bash
    python mi_tools_lite.py
    ```
    *(Or use the provided `run.bat` on Windows)*

## ⚠️ Disclaimer
This tool uses standard ADB commands. While `pm uninstall --user 0` is generally safe (as it only hides apps for the current user), **always back up your data** before removing system packages. The developer is not responsible for any bootloops or data loss.

---
*Built with ❤️ for the Android enthusiast community.*
