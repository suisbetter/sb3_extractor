# SB3 Converter & Extractor 

A lightweight, open-source tool to extract Scratch projects into directories for usage outside the Scratch environment.  
Works on **Windows**, **macOS**, **Linux**, and **Google Colab**.

---
# Project Structure

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

##  Usage Instructions

### 1. Python Desktop App (Windows / macOS / Linux)
Run the converter script:
```bash
python convert.py
```
- A GUI window opens. Click **"Browse & Convert .sb3"** to choose your `.sb3` file.
- The extracted folder with your assets and executable HTML player will be generated automatically.
- **macOS note:** tkinter ships with the official Python installer from python.org. If you installed Python via Homebrew, run `brew install python-tk` first.

### 2. Headless / CLI mode (Linux, Google Colab, servers)
When no display is available, the script automatically falls back to a command-line interface:

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

### 3. Web App
Open [`index.html`](index.html) in your browser:
- Drag and drop any `.sb3` file or browse your computer.
- Preview sprites, sounds, and project statistics.
- Click **"Open"** to download the clean ZIP package or play immediately in your browser.

---

## License

This project is open-source and available under the [MIT License](LICENSE).
