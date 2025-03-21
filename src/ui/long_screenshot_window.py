from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, QEvent, QThread
from PyQt6.QtGui import QPainter, QColor, QScreen, QCursor, QImage, QPen
from PyQt6.QtWidgets import QWidget, QApplication, QMessageBox, QPushButton, QVBoxLayout, QLabel, QFileDialog, QDialog, QHBoxLayout
from ..utils.win32_utils import get_window_under_cursor, simulate_scroll, bring_window_to_front
from ..core.long_screenshot import LongScreenshotCapture
import cv2
import time
import os
import win32con
import win32api
import ctypes
import threading

class TransparentWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置无边框、置顶窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # 设置透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 初始化变量
        self.start_pos = None
        self.current_pos = None
        self.is_capturing = False
        self.capture = LongScreenshotCapture()
        self.parent_window = parent
        
        # 设置全屏
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
            
        print("透明窗口已初始化")
        
        # 创建取消按钮
        self.cancel_button = QPushButton("取消截图 (ESC)", self)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff3333;
            }
        """)
        self.cancel_button.clicked.connect(self.terminate_capture)
        self.cancel_button.hide()  # 初始隐藏
        
        # 创建一个定时器来检查ESC键状态
        self.esc_check_timer = QTimer(self)
        self.esc_check_timer.timeout.connect(self.check_esc_key)
        
        # 确保窗口能够接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        # 创建一个全局快捷键处理器
        QApplication.instance().installEventFilter(self)
        
    def showEvent(self, event):
        """窗口显示时，隐藏主窗口"""
        print("显示透明窗口")
        if self.parent_window:
            print("隐藏主窗口")
            self.parent_window.hide()
        
        # 启动ESC键检查定时器
        self.esc_check_timer.start(50)  # 每50毫秒检查一次
            
    def hideEvent(self, event):
        """窗口隐藏时，停止定时器"""
        if hasattr(self, 'esc_check_timer') and self.esc_check_timer.isActive():
            self.esc_check_timer.stop()
            
    def check_esc_key(self):
        """检查ESC键是否被按下"""
        try:
            # 使用win32api直接检查ESC键状态
            if win32api.GetAsyncKeyState(0x1B) & 0x8000:  # 0x1B是ESC键的虚拟键码
                print("检测到ESC键被按下（通过GetAsyncKeyState）")
                self.terminate_capture()
                return
        except Exception as e:
            print(f"检查ESC键状态出错: {str(e)}")
            
    def paintEvent(self, event):
        """绘制半透明遮罩和选区"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 如果正在截图，只绘制选区边框
        if self.is_capturing and hasattr(self, 'capture_rect'):
            # 清除背景
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
            
            # 绘制选区边框 - 使用虚线框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen()
            pen.setColor(QColor(0, 255, 0))  # 绿色
            pen.setWidth(2)  # 线宽
            pen.setStyle(Qt.PenStyle.DashLine)  # 虚线样式
            painter.setPen(pen)
            painter.drawRect(self.capture_rect)
            
            # 绘制截图进度信息
            if hasattr(self.capture, 'current_scroll_count'):
                progress_text = f"截图进度: {self.capture.current_scroll_count}/{self.capture.max_scroll_count}"
                font = painter.font()
                font.setPointSize(10)
                painter.setFont(font)
                
                # 设置文本颜色为白色，带黑色描边以增强可读性
                text_rect = QRect(self.capture_rect.x(), self.capture_rect.y() - 25, 200, 20)
                painter.setPen(QColor(0, 0, 0))
                for dx in [-1, 1]:
                    for dy in [-1, 1]:
                        painter.drawText(text_rect.adjusted(dx, dy, dx, dy), Qt.AlignmentFlag.AlignLeft, progress_text)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, progress_text)
            
            # 显示取消按钮
            if not self.cancel_button.isVisible():
                # 计算按钮位置 - 放在选区的右上角
                button_x = self.capture_rect.right() - self.cancel_button.width() - 10
                button_y = self.capture_rect.top() - self.cancel_button.height() - 10
                if button_y < 10:  # 如果太靠上，放在选区下方
                    button_y = self.capture_rect.bottom() + 10
                self.cancel_button.move(button_x, button_y)
                self.cancel_button.show()
                self.cancel_button.raise_()  # 确保按钮在最上层
            
            return
        
        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # 如果正在选择区域，绘制选区
        if self.start_pos and self.current_pos:
            select_rect = self.get_select_rect()
            # 绘制选区（清除遮罩）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(select_rect, Qt.GlobalColor.transparent)
            
            # 绘制选区边框 - 使用虚线框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen()
            pen.setColor(QColor(0, 255, 0))  # 绿色
            pen.setWidth(2)  # 线宽
            pen.setStyle(Qt.PenStyle.DashLine)  # 虚线样式
            painter.setPen(pen)
            painter.drawRect(select_rect)
            
            # 绘制选区尺寸信息
            size_text = f"{select_rect.width()} × {select_rect.height()}"
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            # 设置文本颜色为白色，带黑色描边以增强可读性
            text_rect = QRect(select_rect.x(), select_rect.y() - 25, 150, 20)
            painter.setPen(QColor(0, 0, 0))
            for dx in [-1, 1]:
                for dy in [-1, 1]:
                    painter.drawText(text_rect.adjusted(dx, dy, dx, dy), Qt.AlignmentFlag.AlignLeft, size_text)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, size_text)
            
    def mousePressEvent(self, event):
        """鼠标按下时开始选择区域"""
        if event.button() == Qt.MouseButton.LeftButton:
            print("鼠标按下，开始选择区域")
            self.start_pos = event.pos()
            self.current_pos = self.start_pos
            self.update()
            
    def mouseMoveEvent(self, event):
        """鼠标移动时更新选区"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.current_pos = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放时开始截图"""
        if event.button() == Qt.MouseButton.LeftButton and self.start_pos:
            print("鼠标释放，准备开始截图")
            # 获取选区
            select_rect = self.get_select_rect()
            if select_rect.width() > 10 and select_rect.height() > 10:
                # 开始长截图过程
                self.start_capture(select_rect)
            else:
                print("选区太小，取消截图")
                self.cancel_capture()
                
    def get_select_rect(self):
        """获取选择区域"""
        if not self.start_pos or not self.current_pos:
            return QRect()
            
        return QRect(
            min(self.start_pos.x(), self.current_pos.x()),
            min(self.start_pos.y(), self.current_pos.y()),
            abs(self.current_pos.x() - self.start_pos.x()),
            abs(self.current_pos.y() - self.start_pos.y())
        )
        
    def start_capture(self, select_rect):
        """开始长截图过程"""
        print("开始长截图过程")
        # 保存选区信息，但不立即隐藏窗口
        self.capture_rect = select_rect
        
        # 获取目标窗口
        try:
            # 先保存当前鼠标位置
            original_cursor_pos = QCursor.pos()
            
            # 获取选区中心点
            center_x = select_rect.x() + select_rect.width() // 2
            center_y = select_rect.y() + select_rect.height() // 2
            
            # 将鼠标移动到选区中心
            QCursor.setPos(center_x, center_y)
            time.sleep(0.2)  # 等待鼠标移动
            
            # 获取鼠标下的窗口
            target_window = get_window_under_cursor()
            print(f"目标窗口句柄: {target_window}")
            
            # 恢复鼠标位置
            QCursor.setPos(original_cursor_pos)
            
            if not target_window:
                print("未找到目标窗口")
                self.show_error("未能获取目标窗口，请重试")
                self.cancel_capture()
                return
                
            # 开始截图
            self.is_capturing = True
            
            # 修改窗口样式，保持窗口可见但只显示选区边框
            self.setWindowOpacity(0.3)  # 降低透明度
            self.update()  # 刷新显示
            
            # 使用全局坐标作为选区
            global_select_rect = QRect(
                select_rect.x(),
                select_rect.y(),
                select_rect.width(),
                select_rect.height()
            )
            
            print(f"全局选区: {global_select_rect.x()}, {global_select_rect.y()}, {global_select_rect.width()}, {global_select_rect.height()}")
            
            # 使用ShareX风格的捕获方法
            self.capture.start_capture(target_window, global_select_rect)
            
            # 创建一个定时器来更新截图进度
            self.progress_timer = QTimer(self)
            self.progress_timer.timeout.connect(self.update_capture_progress)
            self.progress_timer.start(500)  # 每500毫秒更新一次
            
            # 使用简单的事件循环，确保能够响应ESC键
            # 创建一个单独的定时器来检查截图状态
            self.check_capture_timer = QTimer(self)
            self.check_capture_timer.timeout.connect(self.check_capture_status)
            self.check_capture_timer.start(100)  # 每100毫秒检查一次
            
        except Exception as e:
            print(f"截图过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"截图过程出错: {str(e)}")
            self.restore_parent_window()
        
    def update_capture_progress(self):
        """更新截图进度显示"""
        if self.is_capturing and hasattr(self, 'capture_rect'):
            # 更新窗口以显示最新的截图进度
            self.update()
            
    def check_capture_status(self):
        """检查截图状态"""
        # 如果截图已经停止，处理结果
        if not self.capture.is_capturing:
            # 停止检查定时器
            self.check_capture_timer.stop()
            
            # 停止进度更新定时器
            if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
                self.progress_timer.stop()
            
            # 隐藏窗口
            self.hide()
            
            # 获取结果并保存
            result = self.capture.result_image
            if result is not None and result.size > 0:
                print(f"截图完成，图像大小: {result.shape}")
                
                # 先恢复主窗口，再保存截图
                self.restore_parent_window()
                time.sleep(0.5)  # 等待主窗口完全显示
                
                # 保存截图
                self.save_screenshot(result)
            else:
                print("截图失败，未获取到有效图像")
                
                # 先恢复主窗口
                self.restore_parent_window()
                time.sleep(0.5)  # 等待主窗口完全显示
                
                # 如果有任何帧，尝试使用第一帧
                if len(self.capture.screenshots) > 0:
                    print(f"尝试使用第一帧，大小: {self.capture.screenshots[0].shape}")
                    # 保存截图
                    self.save_screenshot(self.capture.screenshots[0])
                else:
                    self.show_error("截图失败，未能获取图像")
            
            # 确保恢复主窗口状态
            self.is_capturing = False
        else:
            # 如果截图仍在进行，继续检查
            self.check_capture_timer.start(100)  # 继续检查
            
    def restore_parent_window(self):
        """恢复主窗口"""
        print("恢复主窗口")
        if self.parent_window:
            # 确保在主线程中执行
            QTimer.singleShot(100, lambda: self._show_parent())
            
    def _show_parent(self):
        """显示父窗口的实际操作"""
        if self.parent_window:
            try:
                self.parent_window.show()
                self.parent_window.activateWindow()  # 激活窗口
                self.parent_window.raise_()  # 将窗口提升到顶层
                
                # 尝试使用Windows API确保窗口可见
                if hasattr(self.parent_window, 'winId'):
                    hwnd = int(self.parent_window.winId())
                    bring_window_to_front(hwnd)
                    
                print("主窗口已恢复")
            except Exception as e:
                print(f"恢复主窗口出错: {str(e)}")
                import traceback
                traceback.print_exc()
            
    def cancel_capture(self):
        """取消截图"""
        print("取消截图")
        self.start_pos = None
        self.current_pos = None
        self.is_capturing = False
        self.hide()
        self.restore_parent_window()
            
    def keyPressEvent(self, event):
        """按ESC取消截图"""
        if event.key() == Qt.Key.Key_Escape:
            print("按下ESC键，立即取消截图")
            self.terminate_capture()
            
    def terminate_capture(self):
        """强制终止截图过程"""
        print("强制终止截图过程")
        
        # 停止所有定时器
        if hasattr(self, 'esc_check_timer') and self.esc_check_timer.isActive():
            self.esc_check_timer.stop()
            print("停止ESC检查定时器")
        
        if hasattr(self, 'check_capture_timer') and self.check_capture_timer.isActive():
            self.check_capture_timer.stop()
            print("停止截图状态检查定时器")
        
        if hasattr(self, 'progress_timer') and self.progress_timer.isActive():
            self.progress_timer.stop()
            print("停止进度更新定时器")
        
        # 强制停止截图过程
        if hasattr(self, 'capture'):
            print("调用截图捕获器的force_stop方法")
            result = self.capture.force_stop()
            print("截图捕获器已强制停止")
            
            # 如果有结果图像，处理它
            if result is not None and result.size > 0:
                print(f"截图已终止，但已获取部分图像，大小: {result.shape}")
                # 保存结果图像以便后续处理
                self.capture.result_image = result
        
        # 强制停止任何可能的滚动操作
        try:
            # 恢复鼠标位置到屏幕中心（避免滚动继续）
            screen = QApplication.primaryScreen()
            if screen:
                center = screen.geometry().center()
                QCursor.setPos(center)
                print(f"已将鼠标移动到屏幕中心: {center.x()}, {center.y()}")
        except Exception as e:
            print(f"恢复鼠标位置失败: {str(e)}")
        
        # 立即隐藏窗口并恢复主窗口
        print("隐藏截图窗口")
        self.hide()
        self.is_capturing = False
        self.start_pos = None
        self.current_pos = None
        
        # 隐藏取消按钮
        self.cancel_button.hide()
        
        # 恢复主窗口
        print("恢复主窗口")
        self.restore_parent_window()
        
        # 处理已捕获的帧（如果有）
        if hasattr(self, 'capture') and self.capture.result_image is not None and self.capture.result_image.size > 0:
            try:
                print("处理已捕获的图像")
                # 等待主窗口完全显示
                QTimer.singleShot(500, lambda: self.save_screenshot(self.capture.result_image))
            except Exception as e:
                print(f"处理已捕获帧时出错: {str(e)}")
                import traceback
                traceback.print_exc()
        
    def save_screenshot(self, image):
        """保存截图或复制到剪贴板"""
        try:
            # 创建QImage用于复制到剪贴板
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # 获取用户桌面路径作为默认保存位置
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            default_path = os.path.join(desktop_path, "长截图.png")
            
            # 确保默认路径存在
            if not os.path.exists(desktop_path):
                desktop_path = os.path.expanduser("~")  # 如果桌面路径不存在，使用用户主目录
                default_path = os.path.join(desktop_path, "长截图.png")
            
            # 创建一个自定义对话框，添加"复制到剪贴板"按钮
            dialog = QDialog(self.parent_window)
            dialog.setWindowTitle("长截图完成")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout()
            
            # 添加提示标签
            label = QLabel("长截图已完成，您可以保存或复制到剪贴板")
            layout.addWidget(label)
            
            # 按钮布局
            button_layout = QHBoxLayout()
            
            # 保存按钮
            save_button = QPushButton("保存图片")
            save_button.clicked.connect(lambda: self._save_image_to_file(image, dialog))
            
            # 复制按钮
            copy_button = QPushButton("复制到剪贴板")
            copy_button.clicked.connect(lambda: self._copy_image_to_clipboard(q_img, dialog))
            
            # 取消按钮
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_button)
            button_layout.addWidget(copy_button)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            
            # 显示对话框
            dialog.exec()
        except Exception as e:
            print(f"处理截图出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"处理截图出错: {str(e)}")

    def _save_image_to_file(self, image, parent_dialog=None):
        """保存图像到文件"""
        try:
            # 获取用户桌面路径作为默认保存位置
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            default_path = os.path.join(desktop_path, "长截图.png")
            
            # 确保默认路径存在
            if not os.path.exists(desktop_path):
                desktop_path = os.path.expanduser("~")  # 如果桌面路径不存在，使用用户主目录
                default_path = os.path.join(desktop_path, "长截图.png")
            
            # 使用模态对话框，确保不会导致主程序退出
            dialog = QFileDialog(self.parent_window, "保存长截图", default_path, "PNG图像 (*.png);;JPEG图像 (*.jpg *.jpeg)")
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            dialog.setDefaultSuffix("png")
            
            if dialog.exec() == QFileDialog.DialogCode.Accepted:
                file_path = dialog.selectedFiles()[0]
                print(f"保存截图到: {file_path}")
                
                # 确保文件扩展名正确
                if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path += '.png'
                
                # 确保目录存在
                save_dir = os.path.dirname(file_path)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                # 保存图像
                success = cv2.imwrite(file_path, image)
                
                if success:
                    print("截图保存成功")
                    QMessageBox.information(self.parent_window, "保存成功", f"长截图已保存到:\n{file_path}")
                    if parent_dialog:
                        parent_dialog.accept()
                else:
                    print("截图保存失败")
                    # 尝试使用备用方法保存
                    try:
                        # 转换为QImage并保存
                        height, width, channel = image.shape
                        bytes_per_line = 3 * width
                        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                        if q_img.save(file_path):
                            print("使用备用方法保存成功")
                            QMessageBox.information(self.parent_window, "保存成功", f"长截图已保存到:\n{file_path}")
                            if parent_dialog:
                                parent_dialog.accept()
                        else:
                            raise Exception("备用保存方法也失败了")
                    except Exception as e:
                        print(f"备用保存方法失败: {str(e)}")
                        self.show_error(f"保存截图失败，请检查文件路径和权限\n错误: {str(e)}")
            else:
                print("用户取消保存")
        except Exception as e:
            print(f"保存截图出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"保存截图出错: {str(e)}")

    def _copy_image_to_clipboard(self, q_img, parent_dialog=None):
        """复制图像到剪贴板"""
        try:
            # 获取剪贴板
            clipboard = QApplication.clipboard()
            
            # 复制图像到剪贴板
            clipboard.setImage(q_img)
            
            print("图像已复制到剪贴板")
            QMessageBox.information(self.parent_window, "复制成功", "长截图已复制到剪贴板")
            
            # 关闭父对话框
            if parent_dialog:
                parent_dialog.accept()
        except Exception as e:
            print(f"复制到剪贴板失败: {str(e)}")
            self.show_error(f"复制到剪贴板失败: {str(e)}")
            
    def show_error(self, message):
        """显示错误消息"""
        print(f"错误: {message}")
        # 确保在主线程中执行
        QTimer.singleShot(0, lambda: QMessageBox.critical(self.parent_window, "截图错误", message))

    def eventFilter(self, obj, event):
        """全局事件过滤器，用于捕获ESC键"""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                print("全局事件过滤器捕获到ESC键 - 立即终止截图")
                # 无论是否正在截图，都尝试终止
                self.terminate_capture()
                return True  # 事件已处理
        
        # 对于其他事件，继续传递
        return super().eventFilter(obj, event) 