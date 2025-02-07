# SnapCode - 代码图片识别工具

SnapCode 是一个智能代码图片识别工具，可以快速将代码截图转换为可编辑的文本代码。无论是来自在线教程、视频课程还是技术文档的代码，SnapCode 都能轻松将代码图片转换为可用的文本。

[English](README.md)

## 主要特性

1. 代码图片识别
   - 拖放或选择图片文件
   - 批量导入处理
   - 自动代码文本识别
   - 智能处理常见OCR错误

2. 编程语言检测
   - 自动语言识别
   - 支持Python、Java、C#等主流语言
   - 基于语言特征的智能分析

3. 代码格式化
   - 自动代码格式化
   - 保持代码缩进和结构
   - 实时预览和编辑功能

4. 文件管理
   - 智能文件名生成
   - 自定义保存路径
   - 批量文件导入/导出

## 使用方法

### 方式一：直接运行（无需安装）
1. 从`dist`目录下载最新版本的`SnapCode.exe`
2. 双击运行程序
3. 拖拽代码图片或点击选择文件
4. 识别完成后编辑并保存

### 方式二：源码运行
1. 克隆仓库
```bash
git clone [repository URL]
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python main.py
```

## 项目结构

```
SnapCode/
├── main.py              # 程序入口
├── requirements.txt     # 依赖项
├── resources/          # 资源文件
│   └── icon.png        # 应用图标
└── src/               # 源代码
    ├── core/          # 核心模块
    │   ├── code_processor.py    # 代码处理
    │   ├── file_manager.py      # 文件管理
    │   └── ocr_processor.py     # OCR识别
    ├── ui/            # UI相关
    │   └── main_window.py       # 主窗口
    └── utils/         # 工具类
        └── icon_generator.py    # 图标生成
```

## 技术特性

1. 核心功能
   - 使用PyTesseract进行OCR识别
   - 基于特征的编程语言检测
   - 智能代码格式化和纠正

2. UI设计
   - 基于PyQt6的现代界面
   - 支持拖放操作
   - 实时预览功能

3. 性能优化
   - 多文件并行处理
   - 智能缓存机制
   - 内存使用优化

## 注意事项

1. 图片要求
   - 使用清晰的代码截图
   - 支持PNG、JPG格式
   - 分辨率越高识别效果越好

2. 使用技巧
   - 优先使用浅色背景深色文字
   - 确保代码段完整
   - 识别后检查特殊字符 