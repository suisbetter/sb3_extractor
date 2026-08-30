# SB3 Converter & Extractor 🚀

A lightweight, open-source tool to extract Scratch 3 (`.sb3`) projects into clean, categorized directories and generate standalone, executable HTML players that run directly in any web browser.

---

## ✨ Features

- 🎮 **Executable HTML Player**: Generates a self-contained HTML file for every project powered by TurboWarp Scaffolding. Includes interactive controls (**▶ Start**, **⏹ Stop**, **⛶ Fullscreen**).
- 📁 **Organized Asset Extraction**: Automatically sorts project contents into structured folders:
  - `sb3/`: Contains `project.json` (and project metadata)
  - `sound/`: Audio files (`.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`, etc.)
  - `assets/`: Visual graphics and costumes (`.svg`, `.png`, `.jpg`, etc.)
- 🖥️ **Modern Desktop GUI**: Sleek dark-mode Tkinter application with High-DPI scaling for crisp display on Windows.
- 🌐 **Web Interface (`index.html`)**: Interactive browser-based project inspector with live sprite thumbnails, costume & sound counters, and one-click packaged ZIP downloads.

---

## 📂 Output Structure

When an `.sb3` file is converted, an extracted directory is created:

```text
<project_name>_extracted/
├── <project_name>.html   # <-- Standalone executable HTML player
├── sb3/
│   └── project.json      # Scratch 3 project data & scripts
├── sound/
│   ├── meow.wav          # Extracted audio files
│   └── bgm.mp3
└── assets/
    ├── cat.svg           # Extracted sprite & backdrop costumes
    └── backdrop.png
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher (with `tkinter` included)
- Any modern web browser (Chrome, Edge, Firefox, Safari)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/sb3_extractor.git
   cd sb3_extractor
   ```

2. (Optional) Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

### 1. Python Desktop App
Run the converter script:
```bash
python convert.py
```
- Click **"Browse & Convert .sb3"** to choose your `.sb3` file.
- The extracted folder with your assets and executable HTML player will be generated automatically.

### 2. Web App
Open [`index.html`](index.html) in your browser:
- Drag and drop any `.sb3` file or browse your computer.
- Preview sprites, sounds, and project statistics.
- Click **"Open"** to download the clean ZIP package or play immediately in your browser.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
