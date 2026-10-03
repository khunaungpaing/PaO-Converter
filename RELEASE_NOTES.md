# Pa-O Converter v1.0.0 — Initial Public Release 🎉

We are excited to announce the first official public release of **Pa-O Converter (v1.0.0)**! 

Pa-O Converter is a free and open-source desktop utility designed for the Pa-O language community to seamlessly convert legacy Win/ASCII encoded text and documents into standard Pa-O Unicode (including characters from the **Unicode 16 Extended-C** range).

---

## 🌟 Highlights & Features

### 1. ⚡ Live Text Conversion
- **Real-Time Conversion**: Type or paste legacy Win/ASCII text in one pane and instantly see standard Unicode text in the other (with smart debouncing).
- **Character Badges & Independent Font Controls**: Easily monitor character counts and adjust text sizes independently for both panels.
- **1-Click Copy**: Copy the converted Unicode text directly to your clipboard.

### 2. 📄 Batch & Document Conversion
- **Drag-and-Drop Support**: Simply drag `.docx`, `.txt`, or `.pdf` files straight into the app.
- **Microsoft Word (.docx)**: Preserves document structure and intelligently merges split font runs to prevent syllable breakage.
- **PDF Conversion**: Converts text-based PDFs either into a newly formatted **PDF (.pdf)** preserving visual layout or extracts it to **Plain Text (.txt)**.
- **Selective Font Conversion**: Target only specific legacy fonts (default: `kothupaoh1`) while leaving other Myanmar or English texts untouched.
- **Custom Font & Size Mapping**: Bundled with the official `KhamThaton-Exp` Unicode font, with support for any system-installed or custom font file (`.ttf` / `.otf`).

### 3. 🎨 Modern & Polished Interface
- **Dark / Light Theme Support**: Automatically matches your system preferences or looks great in both environments.
- **Native Experience**: Clean macOS and Windows desktop UI with responsive progress indicators and non-destructive cancellation.

### 4. 🔄 In-App Updates
- Built-in GitHub update checker that alerts you to newer versions and allows **1-click direct download and update** for future releases.

---

## 📥 Downloads

| Platform | Installer / Package | System Requirements |
|---|---|---|
| **macOS** | `PaOConverter_v1.0.0_macOS.dmg` | macOS 11 (Big Sur) or newer |
| **Windows** | `PaOConverter_v1.0.0_Windows_Setup.exe` | Windows 10 / 11 (64-bit) |

---

### ⚠️ First-Launch Security Notice (Open Source App)

Since this software is freshly released and community-built, your operating system may display a security prompt on the first launch:

- **macOS (Gatekeeper)**: If macOS says the app *"cannot be opened because it is from an unidentified developer"*, open **System Settings → Privacy & Security**, scroll down, and click **"Open Anyway"** (or run `xattr -cr /path/to/PaOConverter_v1.0.0_macOS.dmg` in Terminal).
- **Windows (SmartScreen)**: If Windows displays *"Windows protected your PC"*, click **"More info"** → **"Run anyway"**.

---

## 🤝 Open Source & Feedback

Pa-O Converter is completely open source under the [MIT License](LICENSE).
- **Source Code**: [GitHub Repository](https://github.com/khunaungpaing/PaO-Converter)
- **Feedback & Bug Reports**: If you encounter any conversion issues or have suggestions, please open an issue on [GitHub Issues](https://github.com/khunaungpaing/PaO-Converter/issues).
