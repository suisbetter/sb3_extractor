# sb3_converter/cli.py
"""
CLI entry point for the sb3-converter package.

When invoked via the `sb3-converter` or `sb3` console_scripts entry point,
this module decides whether to open the GUI (when tkinter + a display are
available) or fall back to a headless CLI mode.
"""
import argparse
import sys
import traceback

from .core import convert_sb3, GUI_AVAILABLE

__all__ = ["main"]


def main(argv=None):
    """Main entry point.  Accepts an optional argv list for testability."""
    parser = argparse.ArgumentParser(
        prog="sb3",
        description="Extract a Scratch 3 (.sb3) project into organised folders "
        "and generate a standalone HTML player.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the .sb3 (or .zip) file to convert. If omitted and a GUI "
        "is available, a file picker opens; otherwise you are prompted.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print the full Python traceback on error (useful for debugging).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force the headless CLI mode even when tkinter is available.",
    )
    args = parser.parse_args(argv)

    if GUI_AVAILABLE and not args.headless:
        _run_gui()
    else:
        _run_headless(file_path=args.file, verbose=args.verbose)


def _run_gui():
    """Launch the Tkinter GUI window."""
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import platform

    _SYSTEM = platform.system()
    if _SYSTEM == "Darwin":
        UI_FONT = "SF Pro Display"
    elif _SYSTEM == "Windows":
        UI_FONT = "Segoe UI"
    else:
        UI_FONT = "DejaVu Sans"

    def extract_sb3():
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
        if not file_path:
            print("User cancelled the dialog.")
            return
        try:
            convert_sb3(file_path)
        except Exception:
            # convert_sb3 already displayed the error to the user
            pass

    root = tk.Tk()
    root.title("SB3 Converter & Extractor")
    root.geometry("480x320")
    root.resizable(False, False)
    root.configure(bg="#1e1e2e")

    # Center on screen
    root.update_idletasks()
    win_w, win_h = 480, 320
    pos_x = (root.winfo_screenwidth() // 2) - (win_w // 2)
    pos_y = (root.winfo_screenheight() // 2) - (win_h // 2)
    root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

    # Outer card
    card = tk.Frame(
        root, bg="#252538", bd=0,
        highlightbackground="#363a4f", highlightthickness=1,
    )
    card.pack(fill="both", expand=True, padx=18, pady=18)

    # Header
    header_frame = tk.Frame(card, bg="#252538")
    header_frame.pack(fill="x", padx=20, pady=(18, 8))

    tk.Label(
        header_frame,
        text="SB3 Project Converter",
        font=(UI_FONT, 15, "bold"),
        fg="#ffffff", bg="#252538",
    ).pack(anchor="w")

    tk.Label(
        header_frame,
        text="Extract assets, organize project data & generate standalone HTML",
        font=(UI_FONT, 9),
        fg="#a6adc8", bg="#252538",
    ).pack(anchor="w", pady=(2, 0))

    # Action area
    action_frame = tk.Frame(
        card, bg="#1e1e2e", bd=0,
        highlightbackground="#45475a", highlightthickness=1,
    )
    action_frame.pack(fill="both", expand=True, padx=20, pady=10)

    tk.Label(
        action_frame,
        text="\U0001f4e6",
        font=(UI_FONT, 22),
        bg="#1e1e2e", fg="#ff8c1a",
    ).pack(pady=(10, 2))

    tk.Label(
        action_frame,
        text="Select a Scratch 3 project (.sb3) file to begin",
        font=(UI_FONT, 9),
        fg="#bac2de", bg="#1e1e2e",
    ).pack(pady=(0, 10))

    btn = tk.Button(
        action_frame,
        text="  Browse & Convert .sb3  ",
        command=extract_sb3,
        font=(UI_FONT, 10, "bold"),
        bg="#ff8c1a", fg="#ffffff",
        activebackground="#e67705", activeforeground="#ffffff",
        relief="flat", cursor="hand2",
        padx=16, pady=6, bd=0,
    )
    btn.pack(pady=(0, 12))

    btn.bind("<Enter>", lambda e: btn.config(bg="#ffa03b"))
    btn.bind("<Leave>", lambda e: btn.config(bg="#ff8c1a"))

    root.mainloop()


def _run_headless(file_path=None, verbose=False):
    """Accept a file path from argv or prompt for one, then convert."""
    if not file_path:
        if not sys.stdin.isatty():
            print("No file path provided and stdin is not a terminal. Exiting.", file=sys.stderr)
            sys.exit(1)
        file_path = input("Enter the path to your .sb3 file: ").strip()

    if not file_path:
        print("No file path provided. Exiting.", file=sys.stderr)
        sys.exit(1)

    try:
        out = convert_sb3(file_path)
        print(f"\nDone! Output folder: {out}")
    except SystemExit:
        raise
    except Exception:
        if verbose:
            traceback.print_exc()
        # Non-verbose: a one-line error was already surfaced by convert_sb3
        # (via stderr or a GUI messagebox); just exit non-zero here.
        sys.exit(1)


if __name__ == "__main__":
    main()
