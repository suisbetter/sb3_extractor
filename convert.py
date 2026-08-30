# Imports
import base64
import ctypes
import json
import os
import subprocess
import sys
import zipfile as zp
import html
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
    """Select, validate, extract, and convert a Scratch .sb3/.zip project."""
    file_path = filedialog.askopenfilename(
        title="Select Scratch Project",
        initialdir=".",
        filetypes=[
            ("Scratch 3 Project / Zip", "*.sb3 *.zip"),
            ("Scratch Project (*.sb3)", "*.sb3"),
            ("Zip Archive (*.zip)", "*.zip"),
            ("All Files", "*.*"),
        ],
    )

    # The user cancelled; do not treat that as an error.
    if not file_path:
        print("User cancelled the dialog.")
        return

    print(f"Selected file: {file_path}")

    output_dir = None
    created_files = []

    try:
        # Validate that the selected path is a regular file.
        if not os.path.isfile(file_path):
            raise FileNotFoundError("The selected file does not exist or is not a regular file.")

        # Make sure the file is readable before doing any work.
        if not os.access(file_path, os.R_OK):
            raise PermissionError("The selected file cannot be read. Check its permissions.")

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        safe_title = html.escape(base_name, quote=True)

        output_dir = os.path.join(
            os.path.dirname(file_path),
            f"{base_name}_extracted"
        )

        sb3_dir = os.path.join(output_dir, "sb3")
        sound_dir = os.path.join(output_dir, "sound")
        assets_dir = os.path.join(output_dir, "assets")

        # Create output directories.
        for directory in (output_dir, sb3_dir, sound_dir, assets_dir):
            os.makedirs(directory, exist_ok=True)

        counts = {"sb3": 0, "sound": 0, "assets": 0}
        errors = []
        project_json_found = False

        # Open and validate the archive.
        try:
            with zp.ZipFile(file_path, "r") as zip_ref:
                bad_member = zip_ref.testzip()
                if bad_member is not None:
                    raise zp.BadZipFile(
                        f"The archive contains a corrupted file: {bad_member}"
                    )

                for member in zip_ref.infolist():
                    if member.is_dir():
                        continue

                    # Ignore unsafe/invalid archive paths and only use the filename.
                    filename = os.path.basename(member.filename)
                    if not filename:
                        errors.append(f"Skipped invalid archive entry: {member.filename}")
                        continue

                    ext = os.path.splitext(filename)[1].lower()

                    if filename.lower() == "project.json":
                        target_folder = sb3_dir
                        counts["sb3"] += 1
                        project_json_found = True
                    elif ext == ".json":
                        target_folder = sb3_dir
                        counts["sb3"] += 1
                    elif ext in SOUND_EXTENSIONS:
                        target_folder = sound_dir
                        counts["sound"] += 1
                    else:
                        target_folder = assets_dir
                        counts["assets"] += 1

                    # Avoid overwriting files when an archive contains duplicate
                    # basenames from different directories.
                    target_path = os.path.join(target_folder, filename)
                    if os.path.exists(target_path):
                        stem, extension = os.path.splitext(filename)
                        number = 2
                        while os.path.exists(
                            os.path.join(target_folder, f"{stem}_{number}{extension}")
                        ):
                            number += 1
                        target_path = os.path.join(
                            target_folder, f"{stem}_{number}{extension}"
                        )

                    try:
                        with zip_ref.open(member) as source, open(target_path, "wb") as dest:
                            while True:
                                chunk = source.read(1024 * 1024)
                                if not chunk:
                                    break
                                dest.write(chunk)

                        created_files.append(target_path)

                    except (OSError, RuntimeError, zp.BadZipFile) as member_error:
                        errors.append(
                            f"Could not extract '{member.filename}': {member_error}"
                        )

        except zp.BadZipFile as archive_error:
            raise zp.BadZipFile(str(archive_error))

        # A Scratch project should contain project.json.
        if not project_json_found:
            raise ValueError(
                "This archive does not contain project.json, so it does not "
                "appear to be a valid Scratch project."
            )

        # Read the original archive and encode it for the HTML player.
        try:
            with open(file_path, "rb") as f:
                project_base64 = base64.b64encode(f.read()).decode("ascii")
        except OSError as read_error:
            raise OSError(f"Could not read the Scratch project: {read_error}")

        # Generate self-contained executable HTML player.
        executable_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
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
            text-align: center;
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
        <div id="title">{safe_title}</div>
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

        function showPlayerError(message) {{
            const loading = document.getElementById("loading");
            if (!loading) return;

            loading.innerHTML = "";
            const errorTitle = document.createElement("div");
            errorTitle.textContent = "Failed to load project";
            errorTitle.style.color = "#ef4444";
            errorTitle.style.fontWeight = "600";
            errorTitle.style.marginBottom = "8px";

            const errorText = document.createElement("div");
            errorText.textContent = message || "An unknown error occurred.";
            errorText.style.color = "#f9fafb";
            errorText.style.padding = "0 20px";

            loading.appendChild(errorTitle);
            loading.appendChild(errorText);
        }}

        async function initPlayer() {{
            try {{
                if (typeof Scaffolding === "undefined" ||
                    typeof Scaffolding.Scaffolding !== "function") {{
                    throw new Error(
                        "The TurboWarp player engine could not be loaded. " +
                        "Check your internet connection and try again."
                    );
                }}

                if (!projectBase64) {{
                    throw new Error("The embedded Scratch project is empty.");
                }}

                let binary;
                try {{
                    binary = atob(projectBase64);
                }} catch (decodeError) {{
                    throw new Error("The embedded project data is corrupted.");
                }}

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
                if (!container) {{
                    throw new Error("The player container could not be found.");
                }}

                scaffolding.appendTo(container);

                await scaffolding.loadProject(bytes.buffer);

                const loading = document.getElementById("loading");
                if (loading) {{
                    loading.style.display = "none";
                }}

                scaffolding.greenFlag();

                document.getElementById("greenflag").onclick = () => {{
                    try {{
                        scaffolding.greenFlag();
                    }} catch (error) {{
                        console.error("Green flag error:", error);
                        showPlayerError("Could not start the project: " + error.message);
                    }}
                }};

                document.getElementById("stop").onclick = () => {{
                    try {{
                        scaffolding.stopAll();
                    }} catch (error) {{
                        console.error("Stop error:", error);
                        showPlayerError("Could not stop the project: " + error.message);
                    }}
                }};

                document.getElementById("fullscreen").onclick = async () => {{
                    try {{
                        const wrapper = document.getElementById("player-wrapper");

                        if (!document.fullscreenElement) {{
                            if (!wrapper.requestFullscreen) {{
                                throw new Error("Fullscreen is not supported by this browser.");
                            }}
                            await wrapper.requestFullscreen();
                        }} else {{
                            await document.exitFullscreen();
                        }}
                    }} catch (error) {{
                        console.error("Fullscreen error:", error);
                        showPlayerError("Fullscreen failed: " + error.message);
                    }}
                }};
            }} catch (error) {{
                console.error("Player initialization error:", error);
                showPlayerError(
                    error && error.message
                        ? error.message
                        : "An unknown error occurred."
                );
            }}
        }}

        window.addEventListener("error", (event) => {{
            console.error("Page error:", event.error || event.message);
        }});

        window.addEventListener("unhandledrejection", (event) => {{
            console.error("Unhandled promise rejection:", event.reason);
        }});

        window.addEventListener("DOMContentLoaded", initPlayer);
    </script>
</body>
</html>"""

        # Save the generated HTML player.
        html_player_path = os.path.join(output_dir, f"{base_name}.html")
        try:
            with open(html_player_path, "w", encoding="utf-8") as f:
                f.write(executable_html)
            created_files.append(html_player_path)
        except OSError as write_error:
            raise OSError(f"Could not create the HTML player: {write_error}")

        summary = (
            f"Extraction complete!\n\n"
            f"• Output folder: {output_dir}\n"
            f"• Executable HTML: {base_name}.html\n"
            f"• Project JSON (sb3/): {counts['sb3']} file(s)\n"
            f"• Sound files (sound/): {counts['sound']} file(s)\n"
            f"• Assets (assets/): {counts['assets']} file(s)"
        )

        if errors:
            summary += (
                f"\n\n⚠ {len(errors)} file(s) could not be extracted."
                f"\nThe HTML player was still created."
            )
            print("\n".join(errors))

        messagebox.showinfo("Success", summary)

    except zp.BadZipFile as e:
        messagebox.showerror(
            "Invalid Scratch Project",
            f"The selected file is not a valid or complete ZIP/SB3 archive.\n\nDetails: {e}"
        )

    except PermissionError as e:
        messagebox.showerror(
            "Permission Error",
            f"Windows denied access to the selected file or output folder.\n\nDetails: {e}"
        )

    except FileNotFoundError as e:
        messagebox.showerror(
            "File Not Found",
            f"The selected file could not be found.\n\nDetails: {e}"
        )

    except ValueError as e:
        messagebox.showerror(
            "Invalid Scratch Project",
            str(e)
        )

    except OSError as e:
        messagebox.showerror(
            "File System Error",
            f"A file system operation failed.\n\nDetails: {e}"
        )

    except Exception as e:
        # Catch unexpected errors so the GUI does not silently crash.
        print("Unexpected error:", repr(e))
        messagebox.showerror(
            "Unexpected Error",
            f"Something unexpected went wrong.\n\n"
            f"{type(e).__name__}: {e}\n\n"
            f"Check the terminal/console for more details."
        )


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
root.destroy()
root.mainloop()