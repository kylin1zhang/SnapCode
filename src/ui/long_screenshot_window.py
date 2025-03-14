from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QScreen, QCursor, QImage
from PyQt6.QtWidgets import QWidget, QApplication, QMessageBox, QPushButton, QVBoxLayout, QLabel, QFileDialog
from ..utils.win32_utils import get_window_under_cursor, simulate_scroll, bring_window_to_front
from ..core.long_screenshot import LongScreenshotCapture
import cv2
import time
import os

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
            
    def showEvent(self, event):
        """窗口显示时，隐藏主窗口"""
        print("显示透明窗口")
        if self.parent_window:
            print("隐藏主窗口")
            self.parent_window.hide()
            
    def paintEvent(self, event):
        """绘制半透明遮罩和选区"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制半透明背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # 如果正在选择区域，绘制选区
        if self.start_pos and self.current_pos:
            select_rect = self.get_select_rect()
            # 绘制选区（清除遮罩）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(select_rect, Qt.GlobalColor.transparent)
            # 绘制选区边框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.setPen(QColor(0, 255, 0))
            painter.drawRect(select_rect)
            
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
        # 隐藏选择窗口
        self.hide()
        
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
            
            # 等待截图完成
            timeout = 120  # 增加最大等待时间（秒）
            start_time = time.time()
            
            while self.capture.is_capturing:
                QApplication.processEvents()
                time.sleep(0.1)
                
                # 检查是否超时
                if time.time() - start_time > timeout:
                    print("截图超时")
                    self.capture.is_capturing = False
                    break
                
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
        except Exception as e:
            print(f"截图过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error(f"截图过程出错: {str(e)}")
            self.restore_parent_window()
        finally:
            # 确保恢复主窗口状态
            self.is_capturing = False
            
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
            print("按下ESC键，取消截图")
            self.cancel_capture()
            
    def save_screenshot(self, image):
        """保存截图"""
        try:
            # 获取用户桌面路径作为默认保存位置
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            default_path = os.path.join(desktop_path, "长截图.png")
            
            # 确保默认路径存在
            if not os.path.exists(desktop_path):
                desktop_path = os.path.expanduser("~")  # 如果桌面路径不存在，使用用户主目录
                default_path = os.path.join(desktop_path, "长截图.png")
            
            # 注意：此时主窗口应该已经恢复，不需要再次恢复
            
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
            
    def show_error(self, message):
        """显示错误消息"""
        print(f"错误: {message}")
        # 确保在主线程中执行
        QTimer.singleShot(0, lambda: QMessageBox.critical(self.parent_window, "截图错误", message)) 