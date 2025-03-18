# SnapCode - 代码图片识别工具

SnapCode是一款代码图片识别工具，可以将代码截图转换为可编辑的文本，支持多种编程语言。

## 安装说明

SnapCode提供两种使用方式：

1. **便携版本** - 无需安装，包含所有依赖
2. **安装版本** - 通过安装包安装，方便系统集成

## 解决常见问题

### 图标缺失问题

如果程序运行时没有显示图标，可能是由于以下原因：

1. 资源文件未正确包含在打包中
2. 资源文件路径不正确

**解决方法**：

1. 确保`resources`目录存在且包含`icon.ico`和`icon.png`文件
2. 使用提供的`convert_icon.py`脚本生成图标:
   ```
   python convert_icon.py
   ```
3. 使用`build_portable.py`重新构建应用程序，它会自动处理图标问题

### Tesseract OCR不可用问题

如果OCR功能不可用，可能是由于以下原因：

1. Tesseract OCR未正确安装或打包
2. 程序无法找到Tesseract路径

**解决方法**：

1. 使用便携版本：便携版本已经内置了Tesseract，无需额外安装
2. 使用安装版本：需要单独安装Tesseract OCR，步骤如下：
   - 下载并安装[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - 确保安装English语言包
   - 将Tesseract安装路径添加到环境变量
3. 手动指定Tesseract路径：在应用设置中指定Tesseract可执行文件路径

## 构建便携版本

便携版SnapCode包含所有依赖，包括Tesseract OCR，无需额外安装。构建步骤：

1. 确保已安装Python 3.8或更高版本
2. 安装所需依赖：`pip install -r requirements.txt`
3. 运行构建脚本：`python build_portable.py`
4. 在`dist`目录下找到`SnapCode.exe`和`SnapCode_便携版.zip`

## 项目结构

- `src/` - 源代码目录
  - `core/` - 核心功能模块 
  - `ui/` - 用户界面相关代码
  - `utils/` - 工具函数
- `resources/` - 资源文件
- `convert_icon.py` - 图标转换工具
- `build_portable.py` - 便携版构建工具
- `onefile_build.spec` - PyInstaller打包配置

## 技术说明

- 使用PyQt6构建UI
- 使用Tesseract OCR进行文字识别
- 支持Windows原生OCR和Tesseract OCR双引擎
- 自动检测代码语言并格式化

## 许可证

MIT License

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

1. **Using the System Tray**
   - Single-click the SnapCode icon in the system tray to start long screenshot
   - Double-click the system tray icon to open the main window
   - Right-click the tray icon to see more options

2. **Operation Steps**
   - After starting the long screenshot, a transparent window appears
   - Drag with your mouse to select the area to capture
   - After releasing the mouse, the program automatically scrolls and captures content
   - When capture is complete, choose where to save the image
   - The saved long screenshot can be converted to text using SnapCode's main features

3. **Suitable Scenarios**
   - Capturing long documents or code files
   - Complete screenshots of web pages
   - Interfaces that require scrolling to see all content

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
    │   ├── long_screenshot.py   # Long screenshot feature
    │   └── ocr_processor.py     # OCR recognition
    ├── ui/            # UI related
    │   ├── long_screenshot_window.py  # Long screenshot window
    │   └── main_window.py       # Main window
    └── utils/         # Utilities
        ├── win32_utils.py       # Windows API utilities
        └── icon_generator.py    # Icon generation
```

## Technical Features

1. Core Functionality
   - PyTesseract for OCR recognition
   - Feature-based programming language detection
   - Intelligent code formatting and correction
   - Long screenshot auto-scrolling and image stitching

2. UI Design
   - Modern interface based on PyQt6
   - Drag & drop support
   - Real-time preview functionality
   - System tray integration

3. Performance Optimization
   - Multi-file parallel processing
   - Smart caching mechanism
   - Memory usage optimization
   - Special optimizations for remote desktop environments

## Notes

1. Image Requirements
   - Use clear code screenshots
   - Supports PNG, JPG formats
   - Higher resolution images yield better results

2. Usage Tips
   - Prefer light text on dark background
   - Ensure complete code sections
   - Review special characters after recognition
   - For long screenshots, select content area rather than entire window 