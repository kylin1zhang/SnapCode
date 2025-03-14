# SnapCode - Code Image Recognition Tool

SnapCode is an intelligent code image recognition tool that quickly converts code screenshots into editable text code. Whether it's code from online tutorials, video courses, or technical documentation, SnapCode makes it easy to convert code images into usable text.

[中文文档](README-CN.md)

## Key Features

1. Code Image Recognition
   - Drag & drop or select image files
   - Batch import processing
   - Automatic code text recognition
   - Smart handling of common OCR errors

2. Programming Language Detection
   - Automatic language identification
   - Support for Python, Java, C#, and other major languages
   - Intelligent analysis based on language features

3. Code Formatting
   - Automatic code formatting
   - Maintains code indentation and structure
   - Real-time preview and editing capabilities

4. File Management
   - Smart filename generation
   - Custom save path support
   - Batch file import/export

## New Feature: Long Screenshot

The new long screenshot feature allows you to:
- Capture long scrolling content (like documentation or code files)
- Use a transparent overlay window for precise positioning
- Auto-scroll and stitch images seamlessly
- Save the captured image to your preferred location

### How to Use Long Screenshot

1. Click the "Long Screenshot" button in the toolbar
2. Position the transparent window over the target content
3. Click "Start Capture" in the overlay window
4. Wait for the automatic scrolling and capture process
5. Choose where to save the resulting image
6. Use the captured image with SnapCode's main features to convert to text

## Usage

### Option 1: Direct Execution (No Installation)
1. Download the latest version of `SnapCode.exe` from the `dist` folder
2. Double-click to run the program
3. Drag & drop code images or click to select files
4. Edit and save after recognition is complete

### Option 2: Source Code Run
1. Clone the repository
```bash
git clone [repository URL]
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the program
```bash
python main.py
```

## Project Structure

```
SnapCode/
├── main.py              # Program entry
├── requirements.txt     # Dependencies
├── resources/          # Resource files
│   └── icon.png        # App icon
└── src/               # Source code
    ├── core/          # Core modules
    │   ├── code_processor.py    # Code processing
    │   ├── file_manager.py      # File management
    │   └── ocr_processor.py     # OCR recognition
    ├── ui/            # UI related
    │   └── main_window.py       # Main window
    └── utils/         # Utilities
        └── icon_generator.py    # Icon generation
```

## Technical Features

1. Core Functionality
   - PyTesseract for OCR recognition
   - Feature-based programming language detection
   - Intelligent code formatting and correction

2. UI Design
   - Modern interface based on PyQt6
   - Drag & drop support
   - Real-time preview functionality

3. Performance Optimization
   - Multi-file parallel processing
   - Smart caching mechanism
   - Memory usage optimization

## Notes

1. Image Requirements
   - Use clear code screenshots
   - Supports PNG, JPG formats
   - Higher resolution images yield better results

2. Usage Tips
   - Prefer light text on dark background
   - Ensure complete code sections
   - Review special characters after recognition 