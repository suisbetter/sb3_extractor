# tests/test_convert.py
"""
Functional tests for sb3_converter.core.convert_sb3 using a synthetic .sb3
project (no Scratch project needed on disk).

Run with:  pytest -q
"""
import json
import os
import re
import zipfile

import pytest

from sb3_converter.core import convert_sb3, MAX_MEMBER_SIZE


@pytest.fixture(autouse=True)
def disable_gui(monkeypatch):
    """Ensure tests run in headless mode so messagebox dialogs don't block."""
    monkeypatch.setattr("sb3_converter.core.GUI_AVAILABLE", False)


def make_sb3(tmp_path, name="test_project.sb3", include_project_json=True,
             extra_files=None, project_json_override=None):
    """Build a minimal but realistic Scratch 3 (.sb3) archive and return its path."""
    project = project_json_override or {
        "targets": [
            {
                "isStage": True,
                "name": "Stage",
                "costumes": [
                    {"name": "backdrop1", "assetId": "aaa",
                     "dataFormat": "svg", "md5ext": "aaa.svg"}
                ],
                "sounds": [],
                "currentCostume": 0,
            },
            {
                "isStage": False,
                "name": "Sprite1",
                "costumes": [
                    {"name": "costume1", "assetId": "bbb",
                     "dataFormat": "svg", "md5ext": "bbb.svg"}
                ],
                "sounds": [
                    {"name": "meow", "assetId": "ccc",
                     "dataFormat": "wav", "md5ext": "ccc.wav"}
                ],
                "currentCostume": 0,
            },
        ],
        "monitors": [],
        "extensions": [],
        "meta": {"semver": "3.0.0"},
    }

    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as z:
        if include_project_json:
            z.writestr("project.json", json.dumps(project))
        # Sample assets matching the project.json references.
        z.writestr("aaa.svg", "<svg></svg>")
        z.writestr("bbb.svg", "<svg></svg>")
        z.writestr("ccc.wav", b"RIFF\x00\x00\x00\x00FAKEWAV")
        if extra_files:
            for member_name, content in extra_files.items():
                z.writestr(member_name, content)
    return str(path)


# ─── Happy path ──────────────────────────────────────────────────────────────

def test_convert_creates_expected_folder_structure(tmp_path):
    sb3 = make_sb3(tmp_path)
    out = convert_sb3(sb3)

    assert os.path.isdir(out)
    assert os.path.isfile(os.path.join(out, "test_project.html"))
    assert os.path.isfile(os.path.join(out, "sb3", "project.json"))
    assert os.path.isfile(os.path.join(out, "sound", "ccc.wav"))
    assert os.path.isfile(os.path.join(out, "assets", "aaa.svg"))
    assert os.path.isfile(os.path.join(out, "assets", "bbb.svg"))


def test_convert_returns_output_dir(tmp_path):
    sb3 = make_sb3(tmp_path)
    out = convert_sb3(sb3)
    assert out.endswith("test_project_extracted")


def test_generated_html_embeds_base64_project(tmp_path):
    sb3 = make_sb3(tmp_path)
    out = convert_sb3(sb3)
    html_path = os.path.join(out, "test_project.html")
    content = open(html_path, encoding="utf-8").read()

    match = re.search(r'const projectBase64 = "([^"]+)"', content)
    assert match, "embedded base64 payload not found"
    import base64
    decoded = base64.b64decode(match.group(1))
    # The decoded payload should itself be a valid zip containing project.json.
    assert zipfile.is_zipfile(__import__("io").BytesIO(decoded))


def test_generated_html_escapes_project_title(tmp_path):
    # Use a filename with HTML special chars valid on all OSes (like & and ')
    # to confirm the title is escaped in output.
    import html
    raw = "x&amp'test.sb3"
    # html.escape(base_name, quote=True) where base_name is the file stem:
    safe = html.escape("x&amp'test", quote=True)
    sb3 = make_sb3(tmp_path, name=raw)
    out = convert_sb3(sb3)
    html_path = os.path.join(out, "x&amp'test.html")
    content = open(html_path, encoding="utf-8").read()
    assert safe in content
    assert "<title>" + safe + "</title>" in content


# ─── Error handling ─────────────────────────────────────────────────────────

def test_missing_file_raises(tmp_path):
    missing = str(tmp_path / "does_not_exist.sb3")
    with pytest.raises(FileNotFoundError):
        convert_sb3(missing)


def test_missing_project_json_raises(tmp_path):
    sb3 = make_sb3(tmp_path, include_project_json=False)
    with pytest.raises(ValueError):
        convert_sb3(sb3)


def test_not_a_zip_raises(tmp_path):
    not_a_zip = tmp_path / "fake.sb3"
    not_a_zip.write_text("this is definitely not a zip file")
    with pytest.raises((zipfile.BadZipFile, Exception)):
        convert_sb3(str(not_a_zip))


# ─── Robustness ──────────────────────────────────────────────────────────────

def test_duplicate_basenames_get_unique_names(tmp_path):
    # Two different subfolders each containing an identically-named file.
    extra = {
        "subdirA/dup.svg": "<svg>A</svg>",
        "subdirB/dup.svg": "<svg>B</svg>",
    }
    sb3 = make_sb3(tmp_path, extra_files=extra)
    out = convert_sb3(sb3)

    assets = os.listdir(os.path.join(out, "assets"))
    # Both copies should survive (one renamed to dup_2.svg).
    assert "dup.svg" in assets
    assert "dup_2.svg" in assets


def test_skips_oversized_zip_member(tmp_path, monkeypatch):
    """A decompression-bomb-sized member should be skipped, not extracted."""
    sb3 = make_sb3(tmp_path)
    huge_path = tmp_path / "with_huge.sb3"
    with zipfile.ZipFile(huge_path, "w") as z:
        with zipfile.ZipFile(sb3) as src:
            for item in src.infolist():
                z.writestr(item.filename, src.read(item.filename))
        # A genuinely small member, but we lower MAX_MEMBER_SIZE to something
        # between the size of project.json and this member's size, so the
        # guard triggers without writing real megabytes.
        z.writestr("big.bin", b"x" * 5000)
    monkeypatch.setattr("sb3_converter.core.MAX_MEMBER_SIZE", 1000)
    out = convert_sb3(str(huge_path))
    assert not os.path.exists(os.path.join(out, "assets", "big.bin"))
