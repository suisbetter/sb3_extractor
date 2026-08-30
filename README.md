# SB3 Converter & Extractor 

A lightweight, open-source tool to extract Scratch 3 (`.sb3`) projects into clean, categorized directories

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

## Usage Instructions

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
