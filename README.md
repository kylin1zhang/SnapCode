# SnapCode - Code Image Recognition Tool

SnapCode is a powerful tool that converts code screenshots into editable text. It supports multiple programming languages and provides accurate code recognition.

## Key Features

1. **Code Image Recognition**
   - Drag & drop image files containing code
   - Batch processing support
   - Smart handling of OCR errors
   - Auto-detection of programming languages
   - Integrated OCR capabilities

2. **Long Screenshot Capture**
   - Capture scrolling content with auto-scroll
   - Smart image stitching
   - Transparent overlay for precise selection
   - System tray integration for quick access
   - Support for high DPI displays

3. **Smart Code Processing**
   - Automatic language detection (Python, C#, Java, SQL, etc.)
   - Code formatting and structure preservation
   - Special character correction
   - Support for both English and Chinese code recognition

4. **User-Friendly Interface**
   - Modern PyQt6-based UI
   - System tray integration
   - Clipboard support (Ctrl+V to paste images)
   - Real-time preview and editing

## Installation

### Option 1: Direct Execution
1. Download the latest `SnapCode.exe` from releases
2. Install Tesseract OCR if not already installed
3. Run the program

### Option 2: From Source
1. Clone the repository
```bash
git clone https://github.com/kylin1zhang/SnapCode.git
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Run the application
```bash
python main.py
```

## System Requirements

- Windows 10 or higher
- 100MB free disk space
- 2GB RAM (recommended)
- Tesseract OCR installed

## Using Long Screenshot Feature

1. **Quick Access**
   - Single click system tray icon for instant long screenshot
   - Double click to show main window
   - Right-click for more options

2. **Capture Process**
   - Select area with transparent overlay
   - Auto-scrolling and capture
   - Smart image stitching
   - Save or copy to clipboard

3. **Tips**
   - Select content area rather than entire window
   - Wait for scrolling to complete
   - Press ESC to cancel at any time

## Recent Updates

- Improved long screenshot stability
- Enhanced OCR accuracy for code recognition
- Added system tray integration
- Fixed high DPI display issues
- Improved Chinese language support

## Project Structure

```
SnapCode/
├── main.py              # Program entry
├── requirements.txt     # Dependencies
├── resources/          # Resource files
│   └── icon.png        # Application icon
└── src/               # Source code
    ├── core/          # Core modules
    │   ├── code_processor.py    # Code processing
    │   ├── file_manager.py      # File management
    │   ├── long_screenshot.py   # Long screenshot
    │   └── ocr_processor.py     # OCR recognition
    ├── ui/            # UI related
    │   ├── long_screenshot_window.py  # Long screenshot window
    │   └── main_window.py       # Main window
    └── utils/         # Utilities
        ├── win32_utils.py       # Windows API tools
        └── icon_generator.py    # Icon generation
```

## License

MIT License

[中文文档](README-CN.md) 