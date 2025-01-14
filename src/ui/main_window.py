from PyQt6.QtWidgets import (
    QMainWindow, 
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QLabel,
    QFileDialog,
    QListWidget,
    QFrame,
    QLineEdit
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path

class DropArea(QWidget):
    """自定义拖拽区域"""
    
    # 定义信号
    files_dropped = pyqtSignal(list)
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 提示标签
        self.label = QLabel("拖拽图片文件到这里\n或者点击选择文件")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                border: 2px dashed #999;
                border-radius: 5px;
                background: #f0f0f0;
                min-height: 100px;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽释放事件"""
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        self.files_dropped.emit(file_paths)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.clicked.emit()

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapCode - 代码图片识别工具")
        self.setMinimumSize(1000, 700)
        
        # 初始化文件路径列表
        self.file_paths = []
        
        # 设置中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 拖拽区域
        self.drop_area = DropArea(self)
        self.drop_area.files_dropped.connect(self.handle_dropped_files)  # 连接信号
        self.drop_area.clicked.connect(self.import_files)  # 连接点击信号
        left_layout.addWidget(self.drop_area)
        
        # 文件列表
        self.file_list = QListWidget()
        left_layout.addWidget(QLabel("已导入文件:"))
        left_layout.addWidget(self.file_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入文件夹")
        self.import_btn.clicked.connect(self.import_files)
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.process_files)
        self.process_btn.setEnabled(False)
        
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.process_btn)
        left_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 1. 代码预览区域 - 设置更大的比例
        preview_section = QWidget()
        preview_section.setStyleSheet("""
            QLabel { 
                font-weight: bold; 
                font-size: 14px; 
                margin-bottom: 5px; 
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff;
                padding: 5px;
            }
        """)
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.addWidget(QLabel("代码预览"))
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setMinimumHeight(400)  # 设置最小高度
        preview_layout.addWidget(self.code_preview)
        right_layout.addWidget(preview_section, stretch=4)  # 设置更大的拉伸因子
        
        # 2. 文件保存区域 - 设置更小的比例
        save_section = QWidget()
        save_section.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        save_section.setMaximumHeight(100)  # 限制最大高度
        
        save_layout = QVBoxLayout(save_section)
        save_layout.setContentsMargins(10, 10, 10, 10)
        save_layout.setSpacing(10)
        
        # 文件名输入区域
        filename_container = QWidget()
        filename_layout = QHBoxLayout(filename_container)
        filename_layout.setContentsMargins(0, 0, 0, 0)
        
        self.filename_edit = QLineEdit()
        self.filename_edit.setMinimumHeight(30)
        self.filename_edit.setPlaceholderText("文件名将根据代码自动生成")
        self.filename_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
                font-size: 13px;
            }
        """)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.setMinimumWidth(80)
        self.save_btn.clicked.connect(self.save_code)
        
        filename_layout.addWidget(self.filename_edit, stretch=3)
        filename_layout.addWidget(self.save_btn, stretch=1)
        save_layout.addWidget(filename_container)
        
        right_layout.addWidget(save_section, stretch=1)  # 设置更小的拉伸因子
        
        # 添加左右面板到主布局
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
    
    def handle_dropped_files(self, file_paths: list):
        """处理拖拽的文件"""
        try:
            from src.core.file_manager import FileManager
            
            file_manager = FileManager()
            valid_files = file_manager.import_files(file_paths)
            
            # 更新文件列表
            self.file_paths = valid_files
            self.file_list.clear()
            self.file_list.addItems([Path(path).name for path in self.file_paths])
            
            # 启用处理按钮
            self.process_btn.setEnabled(len(self.file_paths) > 0)
            
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def import_files(self):
        """导入文件夹按钮点击事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含代码图片的文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            try:
                # 获取文件夹中的所有图片文件
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_files.extend(Path(folder_path).glob(ext))
                
                # 按文件名自然排序
                image_files.sort(key=lambda x: self._natural_sort_key(x.name))
                
                # 转换为字符串路径列表
                file_paths = [str(f) for f in image_files]
                
                if file_paths:
                    self.handle_dropped_files(file_paths)
                else:
                    self.statusBar().showMessage("所选文件夹中没有找到图片文件", 3000)
                    
            except Exception as e:
                self.statusBar().showMessage(f"导入文件夹失败: {str(e)}", 3000)
                import traceback
                traceback.print_exc()

    def _natural_sort_key(self, s: str) -> list:
        """生成用于自然排序的键"""
        import re
        # 将字符串分割成数字和非数字部分
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split('([0-9]+)', s)]

    def process_files(self):
        """处理文件按钮点击事件"""
        from src.core.ocr_processor import OCRProcessor
        from src.core.file_manager import FileManager
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            # 创建处理器
            processor = OCRProcessor()
            file_manager = FileManager()
            
            # 处理文件
            results = processor.batch_process(
                self.file_paths,
                progress_callback=self.update_progress
            )
            
            # 合并所有识别出的代码
            all_code = []
            for result in results:
                if result['success']:
                    all_code.append(f"# 文件: {Path(result['path']).name}")
                    if result['language']:
                        all_code.append(f"# 语言: {result['language']}")
                    all_code.append(result['text'])
                    all_code.append("\n" + "="*50 + "\n")
            
            # 合并代码
            merged_code = '\n'.join(all_code)
            
            # 显示在预览区域
            self.code_preview.setText(merged_code)
            
            # 生成并设置默认文件名
            if merged_code:
                default_filename = file_manager.generate_smart_filename(
                    merged_code,
                    self.file_paths[0] if self.file_paths else None
                )
                # 只显示文件名，不显示完整路径
                filename = Path(default_filename).name
                self.filename_edit.setText(filename)
                self.filename_edit.setToolTip(f"完整路径: {default_filename}")
                
        except Exception as e:
            self.statusBar().showMessage(f"处理失败: {str(e)}", 3000)
            import traceback
            traceback.print_exc()
        finally:
            # 恢复按钮状态
            self.process_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
            # 隐藏进度条
            self.progress_bar.setVisible(False)

    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def save_code(self):
        """保存代码按钮点击事件"""
        if not self.code_preview.toPlainText():
            return
        
        code = self.code_preview.toPlainText()
        custom_filename = self.filename_edit.text().strip()
        
        # 获取第一个图片文件的路径作为参考
        original_path = self.file_paths[0] if self.file_paths else None
        
        from src.core.file_manager import FileManager
        file_manager = FileManager()
        
        success, message = file_manager.save_code(
            code=code,
            original_path=original_path,
            custom_filename=custom_filename
        )
        
        if success:
            self.statusBar().showMessage(f"代码已保存到: {message}", 3000)
        else:
            self.statusBar().showMessage(f"保存失败: {message}", 3000)