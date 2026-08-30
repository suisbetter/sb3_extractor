# Imports
import base64
import ctypes
import json
import os
import subprocess
import sys
import zipfile as zp
import tkinter as tk
from tkinter import filedialog, messagebox

# Enable High-DPI awareness on Windows for crisp rendering
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Available asset and sound extensions that can be extracted from the .sb3 file
SOUND_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
ASSET_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


# Opens the dialog window and stores the selected file path
def extract_sb3():
    file_path = filedialog.askopenfilename(
        title="Select Scratch Project",
        initialdir=".",  # Starts in the current directory
        filetypes=[
            ("Scratch 3 Project / Zip", "*.sb3 *.zip"),
            ("Scratch Project (*.sb3)", "*.sb3"),
            ("Zip Archive (*.zip)", "*.zip"),
            ("All Files", "*.*"),
        ],
    )

    # Print the resulting file path if a file was chosen
    if file_path:
        print(f"Selected file: {file_path}")
    else:
        print("User cancelled the dialog.")
        return

    # Create extraction folder based on the file name
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.join(os.path.dirname(file_path), f"{base_name}_extracted")

    sb3_dir = os.path.join(output_dir, "sb3")
    sound_dir = os.path.join(output_dir, "sound")
    assets_dir = os.path.join(output_dir, "assets")

    try:
        os.makedirs(sb3_dir, exist_ok=True)
        os.makedirs(sound_dir, exist_ok=True)
        os.makedirs(assets_dir, exist_ok=True)

        counts = {"sb3": 0, "sound": 0, "assets": 0}

        # Extract archive contents into categorized folders
        with zp.ZipFile(file_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                if member.is_dir():
                    continue

                filename = os.path.basename(member.filename)
                ext = os.path.splitext(filename)[1].lower()

                # Clean this up by moving JSON to sb3, audio to sound, and visual files to assets
                if filename.lower() == "project.json" or ext == ".json":
                    target_folder = sb3_dir
                    counts["sb3"] += 1
                elif ext in SOUND_EXTENSIONS:
                    target_folder = sound_dir
                    counts["sound"] += 1
                else:
                    target_folder = assets_dir
                    counts["assets"] += 1

                target_path = os.path.join(target_folder, filename)
                with zip_ref.open(member) as source, open(target_path, "wb") as dest:
                    dest.write(source.read())

        # Generate self-contained executable HTML player
        with open(file_path, "rb") as f:
            project_base64 = base64.b64encode(f.read()).decode("ascii")

        executable_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_name}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            background: #111827;
            color: #f9fafb;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        #header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 480px;
            max-width: 95vw;
            margin-bottom: 12px;
            padding: 0 4px;
        }}
        #title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #e5e7eb;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        #controls {{
            display: flex;
            gap: 8px;
        }}
        .btn {{
            border: none;
            outline: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.1s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:active {{
            transform: scale(0.96);
        }}
        .btn-green {{
            background-color: #22c55e;
            color: #ffffff;
        }}
        .btn-stop {{
            background-color: #ef4444;
            color: #ffffff;
        }}
        .btn-fullscreen {{
            background-color: #374151;
            color: #ffffff;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        #player-wrapper {{
            position: relative;
            width: 480px;
            height: 360px;
            max-width: 95vw;
            max-height: calc(95vw * 0.75);
            background-color: #000;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
        }}
        #player-container {{
            width: 100%;
            height: 100%;
        }}
        #loading {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #1f2937;
            z-index: 10;
            font-size: 16px;
        }}
        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 12px;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
    <!-- TurboWarp Scaffolding player engine -->
    <script src="https://packager.turbowarp.org/scaffolding/scaffolding-min.js"></script>
</head>
<body>
    <div id="header">
        <div id="title">{base_name}</div>
        <div id="controls">
            <button id="greenflag" class="btn btn-green" title="Start">▶ Start</button>
            <button id="stop" class="btn btn-stop" title="Stop">⏹ Stop</button>
            <button id="fullscreen" class="btn btn-fullscreen" title="Fullscreen">⛶ Fullscreen</button>
        </div>
    </div>
    
    <div id="player-wrapper">
        <div id="loading">
            <div class="spinner"></div>
            <div>Loading Scratch Project...</div>
        </div>
        <div id="player-container"></div>
    </div>

    <script>
        const projectBase64 = "{project_base64}";

        async function initPlayer() {{
            try {{
                const binary = atob(projectBase64);
                const len = binary.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {{
                    bytes[i] = binary.charCodeAt(i);
                }}

                const scaffolding = new Scaffolding.Scaffolding();
                scaffolding.width = 480;
                scaffolding.height = 360;
                scaffolding.resizeMode = "preserve-ratio";
                scaffolding.setup();

                const container = document.getElementById("player-container");
                scaffolding.appendTo(container);

                await scaffolding.loadProject(bytes.buffer);

                document.getElementById("loading").style.display = "none";
                scaffolding.greenFlag();

                document.getElementById("greenflag").onclick = () => scaffolding.greenFlag();
                document.getElementById("stop").onclick = () => scaffolding.stopAll();
                document.getElementById("fullscreen").onclick = () => {{
                    const wrapper = document.getElementById("player-wrapper");
                    if (!document.fullscreenElement) {{
                        wrapper.requestFullscreen().catch(err => console.error(err));
                    }} else {{
                        document.exitFullscreen();
                    }}
                }};
            }} catch (err) {{
                document.getElementById("loading").innerHTML = '<div style="color:#ef4444;padding:20px;text-align:center;">Failed to load project: ' + err.message + '</div>';
            }}
        }}

        window.addEventListener("DOMContentLoaded", initPlayer);
    </script>
</body>
</html>"""

        # Save executable HTML player in the extracted directory
        html_player_path = os.path.join(output_dir, f"{base_name}.html")
        with open(html_player_path, "w", encoding="utf-8") as f:
            f.write(executable_html)

        # Success message box with extraction summary
        messagebox.showinfo(
            "Success",
            f"Extraction complete!\n\n"
            f"• Output folder: {output_dir}\n"
            f"• Executable HTML: {base_name}.html\n"
            f"• Project JSON (sb3/): {counts['sb3']} file(s)\n"
            f"• Sound files (sound/): {counts['sound']} file(s)\n"
            f"• Assets (assets/): {counts['assets']} file(s)",
        )
    except zp.BadZipFile:
        messagebox.showerror("Error", "The selected file is not a valid zip/sb3 archive.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract file: {e}")
    finally:
        root.destroy()


# Set up the main application window
root = tk.Tk()
root.title("SB3 Converter & Extractor")
root.geometry("480x320")
root.resizable(False, False)
root.configure(bg="#1e1e2e")

# Center the window on screen
root.update_idletasks()
win_w = 480
win_h = 320
pos_x = (root.winfo_screenwidth() // 2) - (win_w // 2)
pos_y = (root.winfo_screenheight() // 2) - (win_h // 2)
root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

# Outer card container
card = tk.Frame(root, bg="#252538", bd=0, highlightbackground="#363a4f", highlightthickness=1)
card.pack(fill="both", expand=True, padx=18, pady=18)

# Header Section
header_frame = tk.Frame(card, bg="#252538")
header_frame.pack(fill="x", padx=20, pady=(18, 8))

title_label = tk.Label(
    header_frame,
    text="SB3 Project Converter",
    font=("Segoe UI", 15, "bold"),
    fg="#ffffff",
    bg="#252538",
)
title_label.pack(anchor="w")

subtitle_label = tk.Label(
    header_frame,
    text="Extract assets, organize project data & generate standalone HTML",
    font=("Segoe UI", 9),
    fg="#a6adc8",
    bg="#252538",
)
subtitle_label.pack(anchor="w", pady=(2, 0))

# Action Area / Card
action_frame = tk.Frame(card, bg="#1e1e2e", bd=0, highlightbackground="#45475a", highlightthickness=1)
action_frame.pack(fill="both", expand=True, padx=20, pady=10)

icon_label = tk.Label(
    action_frame,
    text="📦",
    font=("Segoe UI Emoji", 22),
    bg="#1e1e2e",
    fg="#ff8c1a",
)
icon_label.pack(pady=(10, 2))

info_label = tk.Label(
    action_frame,
    text="Select a Scratch 3 project (.sb3) file to begin",
    font=("Segoe UI", 9),
    fg="#bac2de",
    bg="#1e1e2e",
)
info_label.pack(pady=(0, 10))

# Create a button to trigger the dialog
btn = tk.Button(
    action_frame,
    text="  Browse & Convert .sb3  ",
    command=extract_sb3,
    font=("Segoe UI", 10, "bold"),
    bg="#ff8c1a",
    fg="#ffffff",
    activebackground="#e67705",
    activeforeground="#ffffff",
    relief="flat",
    cursor="hand2",
    padx=16,
    pady=6,
    bd=0,
)
btn.pack(pady=(0, 12))


def on_btn_enter(e):
    btn.config(bg="#ffa03b")


def on_btn_leave(e):
    btn.config(bg="#ff8c1a")


btn.bind("<Enter>", on_btn_enter)
btn.bind("<Leave>", on_btn_leave)

root.mainloop()