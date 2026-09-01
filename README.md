# SB3 Converter & Extractor

A lightweight, open-source tool to extract Scratch 3 projects and generate a
standalone HTML player.  Works on **Windows**, **macOS**, **Linux**, and
**Google Colab** — no Scratch account required.

---

## Features

- 📦 Drag-and-drop `.sb3` / `.zip` project support
- 🗂 Organises assets into `sb3/`, `sound/`, and `assets/` folders
- 🌐 Generates a self-contained HTML file that plays the project offline
- 🖥 Native desktop app (Electron) — no Python or browser required
- 🐍 pip-installable Python package with `sb3-converter` CLI command
- ⚡ PyInstaller single-file executable for every platform

---

## Project Structure

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

## Installation & Usage

### Option 1 — Electron Desktop App (Windows / macOS / Linux)

> No Python required.  Download the pre-built installer for your platform from
> the [**Releases**](https://github.com/suisbetter/sb3_extractor/releases) page.

| Platform | File |
|----------|------|
| Windows  | `SB3Converter-Setup-*.exe` (NSIS installer) |
| macOS    | `SB3Converter-*.dmg` |
| Linux    | `SB3Converter-*.AppImage` or `.deb` |

Launch the app, drag your `.sb3` file onto the window (or click **Browse**),
then click **Extract & Open**.

#### Build from source

```bash
# Copy the Electron manifest and install dependencies
cp electron-package.json package.json
npm install

# Run in dev mode
npm start

# Build distributable for the current platform
npm run build
```

---

### Option 2 — pip Package (Python 3.8+)

```bash
pip install sb3-converter          # install from PyPI (once published)
# or install directly from the repo:
pip install git+https://github.com/suisbetter/sb3_extractor.git

# Launch the GUI (or fall back to CLI on headless systems)
sb3-converter

# Convert a file directly from the terminal
sb3 /path/to/my_project.sb3
```

**macOS note:** tkinter ships with the official Python installer from
python.org.  If you installed Python via Homebrew, run
`brew install python-tk` first.

---

### Option 3 — PyInstaller Standalone Executable

Build a single-file native executable (no Python installation needed on the
target machine):

```bash
pip install pyinstaller
pyinstaller sb3_converter.spec

# Windows → dist/SB3Converter.exe
# macOS   → dist/SB3Converter.app   (zipped for distribution)
# Linux   → dist/SB3Converter
```

Or download the pre-built binary from the
[Releases](https://github.com/suisbetter/sb3_extractor/releases) page.

---

### Option 4 — Browser / Web App

Open [`index.html`](index.html) in any modern browser:

- Drag and drop any `.sb3` file or click **Browse .sb3 File**.
- Preview sprites, sounds, and project statistics.
- Click **Extract & Open** to download the organised ZIP package.

---

### Option 5 — Headless / CLI / Google Colab

When no display is available, the Python script automatically falls back to a
command-line interface:

```bash
# Pass the file path as an argument
python convert.py /path/to/project.sb3

# Or run without arguments and type the path when prompted
python convert.py
```

**Google Colab example:**

```python
# Upload your .sb3 in the Colab sidebar, then run:
!python convert.py /content/my_project.sb3
```

---

## Development

```bash
git clone https://github.com/suisbetter/sb3_extractor.git
cd sb3_extractor

# Python (editable install)
pip install -e ".[dev]"

# Electron
cp electron-package.json package.json
npm install
npm start
```

---

## License

This project is open-source and available under the [MIT License](LICENSE).
