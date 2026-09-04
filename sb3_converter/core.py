# sb3_converter/core.py
"""
Core conversion logic for the SB3 Converter & Extractor.

This module is platform-agnostic and works in GUI and headless environments.
"""

import base64
import html
import os
import platform
import sys
import zipfile as zp

# ──────────────────────────────────────────────────────────────────────────────
# Platform setup
# ──────────────────────────────────────────────────────────────────────────────

# Enable High-DPI awareness on Windows for crisp rendering
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Detect whether a GUI (tkinter) is available (not available in Colab/headless).
# We must actually attempt to create a Tk root here (not just import tkinter):
# on systems where the tkinter module imports fine but no display/window
# system is available (headless Linux, CI runners, some Colab setups), only
# instantiating Tk() reveals that GUI usage is impossible.
GUI_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    _test_root = tk.Tk()
    _test_root.withdraw()
    _test_root.destroy()
    GUI_AVAILABLE = True
except Exception:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

SOUND_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
ASSET_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

# Decompression-bomb guard: skip any single archive member whose declared
# uncompressed size exceeds this many bytes. 512 MB is far above any
# legitimate Scratch asset. Exposed as a module constant so it can be
# overridden (e.g. in tests).
MAX_MEMBER_SIZE = 512 * 1024 * 1024

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _show_error(title, message):
    """Display an error via messagebox (GUI) or stderr (headless)."""
    if GUI_AVAILABLE:
        from tkinter import messagebox
        messagebox.showerror(title, message)
    else:
        print(f"[ERROR] {title}: {message}", file=sys.stderr)


def _show_info(title, message):
    """Display information via messagebox (GUI) or stdout (headless)."""
    if GUI_AVAILABLE:
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    else:
        print(f"[{title}] {message}")


# ──────────────────────────────────────────────────────────────────────────────
# Core conversion logic
# ──────────────────────────────────────────────────────────────────────────────

def convert_sb3(file_path):
    """Validate, extract, and convert a Scratch .sb3/.zip project.

    Works in both GUI and headless (Colab / CLI) environments.
    Returns the output directory path on success; raises an exception on failure.
    """
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

                    # Guard against decompression bombs: skip any single entry
                    # whose uncompressed size is unreasonably large.
                    if member.file_size > MAX_MEMBER_SIZE:
                        errors.append(
                            f"Skipped oversized entry '{member.filename}' "
                            f"({member.file_size} bytes)"
                        )
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
    <!-- TurboWarp Scaffolding player engine (loaded from packager.turbowarp.org).
         Requires an internet connection on first load; it is not bundled
         inline in this file. -->
    <script src="https://packager.turbowarp.org/scaffolding/scaffolding-min.js"
            onerror="window.__scaffoldingFailed = true;"></script>
    <script>
        // If the external engine failed to load (e.g. no internet), surface a
        // clear error instead of leaving the spinner spinning forever.
        window.addEventListener("DOMContentLoaded", function () {{
            if (window.__scaffoldingFailed) {{
                var loading = document.getElementById("loading");
                if (loading) {{
                    loading.innerHTML = "";
                    var t = document.createElement("div");
                    t.textContent = "Could not load the Scratch player engine";
                    t.style.cssText = "color:#ef4444;font-weight:600;margin-bottom:8px;";
                    var d = document.createElement("div");
                    d.textContent = "An internet connection is required on first load. " +
                        "Please check your connection and refresh this page.";
                    d.style.cssText = "color:#f9fafb;padding:0 20px;";
                    loading.appendChild(t);
                    loading.appendChild(d);
                }}
            }}
        }});
    </script>
</head>
<body>
    <div id="header">
        <div id="title">{safe_title}</div>
        <div id="controls">
            <button id="greenflag" class="btn btn-green" title="Start">&#9654; Start</button>
            <button id="stop" class="btn btn-stop" title="Stop">&#9209; Stop</button>
            <button id="fullscreen" class="btn btn-fullscreen" title="Fullscreen">&#x26F6; Fullscreen</button>
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
            f"\u2022 Output folder: {output_dir}\n"
            f"\u2022 Executable HTML: {base_name}.html\n"
            f"\u2022 Project JSON (sb3/): {counts['sb3']} file(s)\n"
            f"\u2022 Sound files (sound/): {counts['sound']} file(s)\n"
            f"\u2022 Assets (assets/): {counts['assets']} file(s)"
        )

        if errors:
            summary += (
                f"\n\n\u26a0 {len(errors)} file(s) could not be extracted."
                f"\nThe HTML player was still created."
            )
            print("\n".join(errors))

        _show_info("Success", summary)
        return output_dir

    except zp.BadZipFile as e:
        _show_error(
            "Invalid Scratch Project",
            f"The selected file is not a valid or complete ZIP/SB3 archive.\n\nDetails: {e}"
        )
        raise

    except PermissionError as e:
        _show_error(
            "Permission Error",
            f"Access to the selected file or output folder was denied.\n\nDetails: {e}"
        )
        raise

    except FileNotFoundError as e:
        _show_error(
            "File Not Found",
            f"The selected file could not be found.\n\nDetails: {e}"
        )
        raise

    except ValueError as e:
        _show_error("Invalid Scratch Project", str(e))
        raise

    except OSError as e:
        _show_error(
            "File System Error",
            f"A file system operation failed.\n\nDetails: {e}"
        )
        raise

    except Exception as e:
        # Catch unexpected errors so the app does not silently crash.
        print("Unexpected error:", repr(e))
        _show_error(
            "Unexpected Error",
            f"Something unexpected went wrong.\n\n"
            f"{type(e).__name__}: {e}\n\n"
            f"Check the terminal/console for more details."
        )
        raise
