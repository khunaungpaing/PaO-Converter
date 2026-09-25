# Pa-O ASCII → Unicode Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey.svg)](#download--install)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](#run-from-source)
[![GitHub Release](https://img.shields.io/github/v/release/khunaungpaing/PaO-Converter)](https://github.com/khunaungpaing/PaO-Converter/releases/latest)

A **free, open-source** desktop application that converts Pa-O legacy Win/ASCII encoded text to standard Pa-O Unicode — including Pa-O Ext-C characters. It supports live text conversion, drag-and-drop file conversion (`.txt`, `.docx`, `.pdf`), and selective font handling. Built for the Pa-O language community as a preservation and accessibility tool.

> **ပအိုဝ်ဘာသာ:** ဤ application သည် ပအိုဝ်စာဝေါဟာရများကို Win/ASCII encoding မှ Unicode သို့ ပြောင်းလဲပေးသော အခမဲ့ open-source ဆော့ဖ်ဝဲလ်ဖြစ်သည်။

---

## What it does

- **Live Text Conversion**: Converts Win/ASCII text to Unicode in real-time as you type or paste, with a 300ms debounce.
- **Drag-and-Drop File Conversion**: Converts `.txt`, `.docx`, and text-based `.pdf` files by dropping them directly into the window or selecting via file browser.
- **Smart PDF Handling**: When selecting a PDF, the app prompts you to choose between creating a converted **PDF (.pdf)** (preserving original layout and artwork) or extracting as **Text (.txt)**.
- **Selective Font Conversion**: Converts only text using a specified legacy font (default: `kothupaoh1`), leaving other languages or fonts untouched.
- **Flexible Font Selection**: Choose an output font by picking any font installed on your system or browsing for a custom `.ttf`/`.otf` file. Defaults to bundled `KhamThaton-Exp`.
- **Intelligent DOCX Run Merging**: Joins adjacent legacy-font runs before conversion to prevent syllable split errors across Word formatting runs.
- **Background Processing & Safe Cancellation**: Conversions run on background threads with responsive progress tracking and safe, non-destructive cancellation.
- **In-App About & Open-Source License**: View app version, features, author credits, and the full MIT license text directly from the UI.

---

## Download & Install

Download the latest pre-built installer from the [**Releases page**](https://github.com/khunaungpaing/PaO-Converter/releases/latest):

| Platform | File | Notes |
|---|---|---|
| macOS | `PaOConverter_vX.X.X_macOS.dmg` | Drag to Applications |
| Windows | `PaOConverter_vX.X.X_Windows_Setup.exe` | Run the Setup installer |

### ⚠️ First-Launch Security Warnings

These are expected on both platforms for unsigned open-source apps. No changes to your system are required.

**macOS — Gatekeeper:**
> "Pa-O Converter cannot be opened because it is from an unidentified developer."

Run this once in Terminal after downloading the DMG:
```bash
xattr -cr ~/Downloads/PaOConverter_vX.X.X_macOS.dmg
```
Or: **System Settings → Privacy & Security → scroll down → "Open Anyway"**

**Windows — SmartScreen:**
> "Windows protected your PC"

Click **More info → Run anyway**. Or right-click the `.exe` → **Properties → Unblock → OK** before running.

---

## Requirements

- Python 3.9 or newer
- macOS, Windows, or Linux desktop

Dependencies are listed in [`requirements.txt`](requirements.txt).

---

## Run from source

```bash
cd pao_converter
python3 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

---

## Using the converter

### 1. Text Convert Tab

1. Type or paste Win/ASCII text into the left editor.
2. Unicode text updates automatically in the right editor.
3. Live character count badges appear at the bottom of both panes.
4. Click **Copy Unicode Text** to copy the result, or **Clear** to reset both fields.
5. Font sizes can be adjusted independently via the spin boxes at the top.

### 2. File Convert Tab

1. **Select or Drop File**: Drag and drop a `.txt`, `.docx`, or `.pdf` file into the drop zone, or click **Select File…**.
2. **PDF Output Format**: If you selected a PDF file, choose whether to save as **PDF (.pdf)** or **Text (.txt)** in the pop-up prompt.
3. **Source Font Filter**: Set the legacy font name to convert (default: `kothupaoh1`). Leave empty to convert all fonts.
4. **Output Font**: The default font is `KhamThaton-Exp`. Click **Choose Font…** to pick from **System Fonts…** or browse a **Font File…**.
5. **Size Mapping**: Adjust source-to-output point size adjustments (default: `16:12, 18:14, 20:16`).
6. Click **Cancel** at any time during conversion to stop safely without saving corrupted files.

---

## Bundled assets

```
assets/
├── fonts/
│   ├── kothupaoh1.ttf                  # Bundled Pa-O legacy ASCII font
│   └── KhamThaton-Exp-Regular-0.2.ttf  # Bundled Pa-O Unicode font
└── img/
    ├── app.icns                        # macOS application & dock icon
    ├── app.ico                         # Windows executable & installer icon
    └── app.png                         # High-res app logo & Linux icon
```

---

## Architecture & Codebase

| Path | Purpose |
| --- | --- |
| [`core/engine.py`](core/engine.py) | ASCII-to-Unicode conversion pipeline and phonetic ordering rules |
| [`core/mapping.py`](core/mapping.py) | Character lookup tables and derived character sets |
| [`core/version.py`](core/version.py) | Application version (`v1.0.0`), author metadata, and license constants |
| [`core/file_options.py`](core/file_options.py) | Font-name normalization and size-mapping helpers |
| [`core/cancellation.py`](core/cancellation.py) | Thread-safe cooperative cancellation handling |
| [`ui/text_tab.py`](ui/text_tab.py) | Live text conversion interface with debounced preview |
| [`ui/file_tab.py`](ui/file_tab.py) | File conversion interface with font and size mapping controls |
| [`ui/about_dialog.py`](ui/about_dialog.py) | Tabbed About and Open Source MIT License dialog |
| [`ui/widgets.py`](ui/widgets.py) | `DropZoneWidget` (drag-and-drop) and `PlainTextFontEdit` |
| [`migration/docx_converter.py`](migration/docx_converter.py) | Word (.docx) document conversion and run grouping |
| [`migration/pdf_converter.py`](migration/pdf_converter.py) | PDF text span extraction, redaction, and shaped text insertion |
| [`workers/file_worker.py`](workers/file_worker.py) | `QThread` worker managing asynchronous file conversion |

---

## Building Installers & Distribution

Pre-configured scripts are available to build standalone distribution packages:

### macOS (.app & .dmg)
```bash
./scripts/build_macos.sh
```
Produces `dist/PaOConverter_v1.0.0_macOS.dmg` with a drag-to-Applications shortcut. Upgrades automatically prompt to replace previous versions.

### Windows (Inno Setup .exe)
```bat
scripts\build_windows.bat
```
Produces `Output\PaOConverter_v1.0.0_Windows_Setup.exe` with a fixed `AppId` for clean in-place upgrades.

### Automated GitHub Releases (CI/CD)
Pushing a version tag automatically triggers [`.github/workflows/build-release.yml`](.github/workflows/build-release.yml) to build both macOS and Windows installers:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Contributing

Contributions are welcome! This project exists for the Pa-O language community.

- **Bug reports & feature requests:** [Open an issue](https://github.com/khunaungpaing/PaO-Converter/issues)
- **Pull requests:** Fork the repository, make your changes, and submit a PR
- **Mapping corrections:** Pa-O character mapping improvements are especially valuable — see [`core/mapping.py`](core/mapping.py)

Please do not modify `core/engine.py` or `core/mapping.py` without thorough testing across all character combinations.

---

## License

This project is open-source software licensed under the **[MIT License](LICENSE)** — see the [LICENSE](LICENSE) file for details.

Free for personal, educational, community, and commercial use.

**Author:** Khun Aung Paing & Pa-O Language Community  
**Project:** [github.com/khunaungpaing/PaO-Converter](https://github.com/khunaungpaing/PaO-Converter)
