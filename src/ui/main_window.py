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
    QLineEdit,
    QApplication,
    QSystemTrayIcon,
    QMenu
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QKeySequence, QImage, QShortcut
from pathlib import Path
import tempfile
import os
from .long_screenshot_window import TransparentWindow
import time

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
        self.label = QLabel("拖拽图片文件到这里\n或者点击选择文件\n或按Ctrl+V粘贴图片")
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
        """鼠标点击事件 - 选择单个或多个文件"""
        self.clicked.emit()

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapCode - 代码图片识别工具")
        self.setMinimumSize(1000, 700)
        
        # 设置应用图标
        icon_path = Path(__file__).parent.parent.parent / 'resources' / 'icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建工具栏
        self.toolbar = self.addToolBar("工具栏")
        self.toolbar.setMovable(False)  # 禁止移动工具栏
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        
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
        self.drop_area.files_dropped.connect(self.handle_dropped_files)
        self.drop_area.clicked.connect(self.select_files)
        left_layout.addWidget(self.drop_area)
        
        # 添加剪贴板快捷键
        self.paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        self.paste_shortcut.activated.connect(self.handle_paste)
        
        # 文件列表
        self.file_list = QListWidget()
        left_layout.addWidget(QLabel("已导入文件:"))
        left_layout.addWidget(self.file_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入文件夹")
        self.import_btn.clicked.connect(self.import_folder)
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
                padding: 10px;
                font-family: Consolas, Monaco, "Courier New", monospace;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        preview_layout = QVBoxLayout(preview_section)
        
        # 添加标题
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("代码预览")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # 添加复制按钮
        self.copy_btn = QPushButton("复制代码")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_code)
        
        header_layout.addWidget(preview_label)
        header_layout.addStretch()
        header_layout.addWidget(self.copy_btn)
        
        preview_layout.addWidget(header_widget)
        
        # 代码编辑器
        self.code_preview = QTextEdit()
        self.code_preview.setMinimumHeight(400)
        self.code_preview.setPlaceholderText("识别的代码将显示在这里，您可以直接编辑...")
        
        # 添加行号显示（可选）
        self.code_preview.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 禁用自动换行
        
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
        
        # 添加一个标志来标识当前图片是否来自剪贴板
        self.is_from_clipboard = False
        
        # 添加长截图窗口
        self.long_screenshot_window = None
        
        # 创建系统托盘图标
        self.setup_system_tray()
        
    def setup_system_tray(self):
        """设置系统托盘图标"""
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置图标
        icon_path = Path(__file__).parent.parent.parent / 'resources' / 'icon.png'
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加菜单项
        long_screenshot_action = tray_menu.addAction("长截图")
        long_screenshot_action.triggered.connect(self.show_long_screenshot_window)
        
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("退出")
        exit_action.triggered.connect(QApplication.quit)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置托盘图标点击事件
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        """托盘图标被激活时的处理"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击
            # 单击直接进行长截图
            self.show_long_screenshot_window()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:  # 双击
            # 双击显示主窗口
            self.show_main_window()
    
    def show_main_window(self):
        """显示主窗口"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def closeEvent(self, event):
        """关闭窗口事件 - 最小化到托盘而不是退出"""
        if self.tray_icon.isVisible():
            # 显示提示消息
            self.tray_icon.showMessage(
                "SnapCode 已最小化到托盘",
                "程序将继续在后台运行。单击托盘图标进行长截图，双击显示主窗口。",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            # 隐藏主窗口
            self.hide()
            # 忽略关闭事件
            event.ignore()
        else:
            # 正常关闭
            event.accept()
            
    def show_long_screenshot_window(self):
        """显示长截图窗口"""
        if self.long_screenshot_window is None:
            self.long_screenshot_window = TransparentWindow(self)
        self.long_screenshot_window.show()

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
            
            # 设置来源标志
            self.is_from_clipboard = False
            
            # 启用处理按钮
            self.process_btn.setEnabled(len(self.file_paths) > 0)
            
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def select_files(self):
        """点击拖拽区域时的文件选择事件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg);;XML文件 (*.xml);;所有文件 (*.*)"
        )
        if files:
            self.handle_dropped_files(files)

    def import_folder(self):
        """导入文件夹按钮点击事件"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含代码图片的文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder_path:
            try:
                # 获取文件夹中的所有图片文件和XML文件
                image_files = []
                for ext in ['*.png', '*.jpg', '*.jpeg', '*.xml']:  # 添加XML扩展名
                    image_files.extend(Path(folder_path).glob(ext))
                
                # 按文件名自然排序
                image_files.sort(key=lambda x: self._natural_sort_key(x.name))
                
                # 转换为字符串路径列表
                file_paths = [str(f) for f in image_files]
                
                if file_paths:
                    self.handle_dropped_files(file_paths)
                else:
                    self.statusBar().showMessage("所选文件夹中没有找到支持的文件", 3000)
                    
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
            
            # 合并所有识别出的代码（只保留代码内容）
            all_code = []
            for result in results:
                if result['success']:
                    # 只添加代码文本，不添加文件名和语言信息
                    all_code.append(result['text'])
            
            # 合并代码（不添加分隔符）
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

    def handle_paste(self):
        """处理剪贴板粘贴事件"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # 从剪贴板获取图片
            image = QImage(clipboard.image())
            
            # 创建临时文件保存图片，不弹出保存对话框
            try:
                # 创建临时目录（如果不存在）
                temp_dir = Path(tempfile.gettempdir()) / "snapcode"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成临时文件路径
                file_path = str(temp_dir / f"clipboard_image_{int(time.time())}.png")
                
                # 保存图片到临时文件
                if image.save(file_path, 'PNG'):
                    self.statusBar().showMessage("已处理剪贴板图片")
                    # 设置来源标志
                    self.is_from_clipboard = True
                    # 处理图片
                    self.handle_dropped_files([file_path])
                else:
                    self.statusBar().showMessage("处理剪贴板图片失败", 3000)
            except Exception as e:
                self.statusBar().showMessage(f"处理剪贴板图片出错: {str(e)}", 3000)
                import traceback
                traceback.print_exc()
        else:
            self.statusBar().showMessage("剪贴板中没有图片", 3000)

    def save_code(self):
        """保存代码按钮点击事件"""
        code = self.code_preview.toPlainText()
        if not code:
            self.statusBar().showMessage("没有可保存的代码", 3000)
            return
        
        # 获取建议的文件名和路径
        from src.core.file_manager import FileManager
        file_manager = FileManager()
        
        # 检测代码信息以获取合适的文件扩展名
        code_info = file_manager.detect_code_info(code)
        extension = file_manager.language_extensions.get(code_info['language'], '.txt')
        
        # 使用当前文件名作为默认名称（如果有的话）
        suggested_name = self.filename_edit.text().strip()
        if not suggested_name:
            # 如果没有自定义文件名，使用智能生成的文件名
            if self.file_paths:
                suggested_name = Path(file_manager.generate_smart_filename(code, self.file_paths[0])).name
            else:
                suggested_name = f"code{extension}"
        
        # 确保文件名有正确的扩展名
        if not suggested_name.endswith(extension):
            suggested_name = suggested_name.split('.')[0] + extension
        
        # 确定默认保存路径
        if self.is_from_clipboard:
            # 如果是剪贴板图片，默认保存到下载文件夹
            default_save_path = str(Path.home() / "Downloads" / suggested_name)
        else:
            # 如果是拖拽或选择的文件，默认保存到原图片所在文件夹
            if self.file_paths:
                default_save_path = str(Path(self.file_paths[0]).parent / suggested_name)
            else:
                default_save_path = str(Path.home() / "Downloads" / suggested_name)
        
        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存代码文件",
            default_save_path,  # 使用确定的默认保存路径
            f"代码文件 (*{extension});;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                # 确保目标目录存在
                save_dir = Path(file_path).parent
                save_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                self.statusBar().showMessage(f"代码已保存到: {file_path}", 3000)
            except Exception as e:
                self.statusBar().showMessage(f"保存失败: {str(e)}", 3000)
        else:
            self.statusBar().showMessage("已取消保存", 3000)

    def copy_code(self):
        """复制代码到剪贴板"""
        code = self.code_preview.toPlainText()
        if code:
            clipboard = QApplication.clipboard()
            clipboard.setText(code)
            self.statusBar().showMessage("代码已复制到剪贴板", 3000)
            
            # 添加视觉反馈
            original_style = self.copy_btn.styleSheet()
            self.copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #218838;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 12px;
                }
            """)
            # 1秒后恢复原样式
            QTimer.singleShot(1000, lambda: self.copy_btn.setStyleSheet(original_style))
        else:
            self.statusBar().showMessage("没有可复制的代码", 3000)