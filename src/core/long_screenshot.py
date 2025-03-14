from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QScreen, QCursor
from PyQt6.QtWidgets import QWidget, QApplication
import numpy as np
import cv2
import win32gui
import win32con
import win32api
import time
import copy

class LongScreenshotCapture:
    def __init__(self):
        self.screenshots = []
        self.is_capturing = False
        self.window_handle = None
        self.select_rect = None
        self.scroll_delay = 800  # 进一步增加滚动延迟（毫秒）
        self.max_scroll_count = 300  # 增加最大滚动次数
        self.current_scroll_count = 0
        self.result_image = None
        self.auto_scroll = True
        self.same_frame_count = 0  # 连续相同帧计数
        self.max_same_frames = 8   # 增加最大连续相同帧数，从5增加到8，提高对空白区域的容忍度
        self.is_remote_desktop = False  # 是否为远程桌面
        self.empty_frame_count = 0  # 连续空白帧计数
        self.max_empty_frames = 5  # 最大连续空白帧数
        
    def start_capture(self, window_handle, select_rect=None):
        """开始捕获长截图"""
        print(f"开始捕获长截图，窗口句柄: {window_handle}")
        self.window_handle = window_handle
        self.select_rect = select_rect
        self.screenshots = []
        self.is_capturing = True
        self.current_scroll_count = 0
        self.same_frame_count = 0
        self.result_image = None
        
        # 检查是否为远程桌面窗口
        try:
            class_name = win32gui.GetClassName(window_handle)
            self.is_remote_desktop = any(name in class_name for name in ["MKSEmbedded", "VMware", "Citrix", "Remote"])
            if self.is_remote_desktop:
                print(f"检测到远程桌面窗口: {class_name}，将使用增强捕获模式")
        except Exception as e:
            print(f"获取窗口类名失败: {str(e)}")
        
        # 确保窗口处于活动状态
        try:
            win32gui.SetForegroundWindow(window_handle)
            time.sleep(1.0)  # 进一步增加等待时间，确保窗口完全激活
        except Exception as e:
            print(f"激活窗口失败: {str(e)}")
        
        # 捕获第一帧
        self.capture_frame()
        
        # 如果启用自动滚动，开始滚动过程
        if self.auto_scroll:
            QTimer.singleShot(self.scroll_delay, self.scroll_and_capture)
        
    def capture_frame(self):
        """捕获当前帧"""
        try:
            # 获取屏幕截图
            screen = QApplication.primaryScreen()
            
            # 如果有选择区域，使用选择区域
            if self.select_rect:
                # 使用全局坐标
                capture_rect = self.select_rect
            else:
                # 使用窗口区域
                try:
                    window_rect = win32gui.GetWindowRect(self.window_handle)
                    x, y, right, bottom = window_rect
                    capture_rect = QRect(x, y, right - x, bottom - y)
                except Exception as e:
                    print(f"获取窗口位置失败: {str(e)}")
                    self.finish_capture()
                    return False
            
            # 捕获指定区域的截图
            screenshot = screen.grabWindow(
                0,  # 使用0表示整个屏幕
                capture_rect.x(),
                capture_rect.y(),
                capture_rect.width(),
                capture_rect.height()
            ).toImage()
            
            # 转换为numpy数组
            bits = screenshot.bits()
            bits.setsize(screenshot.sizeInBytes())
            arr = np.frombuffer(bits, np.uint8).reshape(
                screenshot.height(), screenshot.width(), 4
            )
            
            # 转换为BGR格式
            frame = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            
            # 保存截图
            self.screenshots.append(frame.copy())
            print(f"已捕获第 {len(self.screenshots)} 帧，大小: {frame.shape}")
            
            return True
        except Exception as e:
            print(f"捕获帧错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def scroll_and_capture(self):
        """滚动并捕获下一帧"""
        if not self.is_capturing:
            return
        
        # 检查是否达到最大滚动次数
        if self.current_scroll_count >= self.max_scroll_count:
            print(f"达到最大滚动次数 ({self.max_scroll_count})，完成截图")
            self.finish_capture()
            return
        
        # 执行滚动
        if self.perform_scroll():
            # 等待页面渲染
            wait_time = 0.5 if self.is_remote_desktop else 0.3  # 远程桌面等待更长时间
            time.sleep(wait_time)
            
            # 捕获当前帧
            if self.capture_frame():
                # 检查是否到达底部
                if self.check_end_of_scroll():
                    print("检测到已到达底部，完成截图")
                    self.finish_capture()
                    return
                
                # 继续滚动和捕获
                self.current_scroll_count += 1
                QTimer.singleShot(self.scroll_delay, self.scroll_and_capture)
            else:
                print("捕获帧失败，完成截图")
                self.finish_capture()
        else:
            print("滚动失败，完成截图")
            self.finish_capture()
    
    def perform_scroll(self):
        """执行滚动操作"""
        try:
            # 确保窗口处于活动状态
            try:
                win32gui.SetForegroundWindow(self.window_handle)
                time.sleep(0.2)  # 增加等待时间
            except Exception as e:
                print(f"设置前台窗口失败: {str(e)}，尝试继续滚动")
            
            # 获取窗口中心点或选区中心点
            if self.select_rect:
                center_x = self.select_rect.x() + self.select_rect.width() // 2
                center_y = self.select_rect.y() + self.select_rect.height() // 2
            else:
                rect = win32gui.GetWindowRect(self.window_handle)
                center_x = (rect[0] + rect[2]) // 2
                center_y = (rect[1] + rect[3]) // 2
            
            # 保存当前鼠标位置
            original_pos = QCursor.pos()
            
            # 移动鼠标到中心点
            QCursor.setPos(center_x, center_y)
            time.sleep(0.2)  # 增加等待时间
            
            # 模拟滚动 - 根据是否为远程桌面调整滚动力度
            if self.is_remote_desktop:
                # 远程桌面使用更强的滚动
                scroll_count = 5  # 更多滚动次数
                scroll_value = -240  # 更大滚动值
                scroll_interval = 0.15  # 更长滚动间隔
            else:
                # 普通窗口使用标准滚动
                scroll_count = 3
                scroll_value = -120
                scroll_interval = 0.1
                
            # 执行滚动
            for _ in range(scroll_count):
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_WHEEL,
                    0, 0,
                    scroll_value,
                    0
                )
                time.sleep(scroll_interval)
            
            # 恢复鼠标位置
            QCursor.setPos(original_pos)
            
            return True
        except Exception as e:
            print(f"滚动错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_end_of_scroll(self):
        """检查是否到达滚动底部"""
        # 至少需要两帧才能比较
        if len(self.screenshots) < 2:
            return False
        
        try:
            # 获取最后两帧
            current_frame = self.screenshots[-1]
            previous_frame = self.screenshots[-2]
            
            # 计算相似度
            similarity = self.calculate_image_similarity(current_frame, previous_frame)
            print(f"帧相似度: {similarity}")
            
            # 检查当前帧是否为空白帧（几乎全白或全黑）
            is_empty_frame = self.is_empty_frame(current_frame)
            if is_empty_frame:
                self.empty_frame_count += 1
                print(f"检测到空白帧 ({self.empty_frame_count}/{self.max_empty_frames})")
                # 如果连续空白帧数量未达到阈值，不认为已到达底部
                if self.empty_frame_count < self.max_empty_frames:
                    self.same_frame_count = 0  # 重置相似帧计数
                    return False
            else:
                self.empty_frame_count = 0  # 重置空白帧计数
            
            # 远程桌面使用更低的相似度阈值
            threshold = 0.90 if self.is_remote_desktop else 0.95
            
            # 如果相似度超过阈值，可能已到达底部
            if similarity > threshold:
                self.same_frame_count += 1
                print(f"检测到相似帧 ({self.same_frame_count}/{self.max_same_frames})")
                if self.same_frame_count >= self.max_same_frames:
                    return True
            else:
                self.same_frame_count = 0
            
            return False
        except Exception as e:
            print(f"检查滚动结束错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def calculate_image_similarity(self, img1, img2):
        """计算两个图像的相似度"""
        try:
            # 确保两个图像大小相同
            if img1.shape != img2.shape:
                # 调整大小以匹配
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # 对于远程桌面，使用更简单的相似度计算方法
            if self.is_remote_desktop:
                # 转换为灰度图像
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                
                # 计算绝对差异
                diff = cv2.absdiff(gray1, gray2)
                
                # 计算相似度（1 - 归一化差异）
                similarity = 1.0 - (np.sum(diff) / (255.0 * diff.size))
                return similarity
            else:
                # 使用模板匹配
                result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
                return result.max()
        except Exception as e:
            print(f"计算图像相似度错误: {str(e)}")
            return 0.0
    
    def is_empty_frame(self, frame):
        """检查帧是否为空白（几乎全白或全黑）"""
        try:
            # 转换为灰度图像
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 计算平均亮度和标准差
            mean, std = cv2.meanStdDev(gray)
            mean_value = mean[0][0]
            std_value = std[0][0]
            
            # 判断是否为空白帧
            # 1. 几乎全白: 平均亮度高且标准差低
            # 2. 几乎全黑: 平均亮度低且标准差低
            is_white = mean_value > 240 and std_value < 15
            is_black = mean_value < 15 and std_value < 15
            
            # 判断是否为低内容帧（内容很少）
            is_low_content = std_value < 25  # 低标准差表示内容变化少
            
            return is_white or is_black or is_low_content
        except Exception as e:
            print(f"检查空白帧错误: {str(e)}")
            return False
    
    def finish_capture(self):
        """完成捕获并拼接图像"""
        print(f"完成捕获，共 {len(self.screenshots)} 帧")
        self.is_capturing = False
        
        if not self.screenshots:
            print("没有捕获到任何截图")
            return None
        
        # 拼接图像
        self.result_image = self.stitch_images()
        return self.result_image
    
    def stitch_images(self):
        """拼接图像 - 使用 ShareX 的方法"""
        if not self.screenshots:
            return None
        
        try:
            print("开始拼接图像...")
            
            # 如果只有一帧，直接返回
            if len(self.screenshots) == 1:
                print("只有一帧，无需拼接")
                return self.screenshots[0]
            
            # 获取所有图像的尺寸
            frames = self.screenshots
            height, width = frames[0].shape[:2]
            
            # 使用 ShareX 的拼接方法
            # 1. 计算每帧的重叠区域
            # 2. 找到最佳匹配点
            # 3. 拼接图像
            
            # 初始化结果图像
            total_height = height  # 初始高度为第一帧的高度
            
            # 计算每帧的偏移量
            offsets = [0]  # 第一帧的偏移量为0
            
            # 对每一对相邻帧计算最佳匹配点
            for i in range(1, len(frames)):
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                # 计算最佳匹配点
                offset = self.find_best_match(prev_frame, curr_frame)
                
                # 累加偏移量
                offsets.append(offsets[-1] + offset)
                
                # 更新总高度
                total_height = max(total_height, offsets[-1] + height)
            
            print(f"计算的总高度: {total_height}")
            
            # 创建结果图像
            result = np.zeros((total_height, width, 3), dtype=np.uint8)
            
            # 拼接图像
            for i, frame in enumerate(frames):
                y_offset = offsets[i]
                
                # 计算目标区域
                y_end = min(y_offset + height, total_height)
                h = y_end - y_offset
                
                # 复制图像
                if h > 0 and y_offset < total_height:
                    result[y_offset:y_end, 0:width] = frame[:h, :]
            
            print(f"拼接完成，最终图像大小: {result.shape}")
            return result
        except Exception as e:
            print(f"拼接图像错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 如果拼接失败，至少返回第一张图片
            return self.screenshots[0]
    
    def find_best_match(self, prev_frame, curr_frame):
        """找到两帧之间的最佳匹配点"""
        try:
            # 获取图像尺寸
            h, w = prev_frame.shape[:2]
            
            # 定义搜索区域
            # 远程桌面使用更大的搜索区域
            search_height = min(h // 2, 300) if self.is_remote_desktop else min(h // 3, 200)
            
            # 提取搜索区域
            prev_bottom = prev_frame[-search_height:, :]
            
            # 使用模板匹配找到最佳匹配点
            result = cv2.matchTemplate(curr_frame, prev_bottom, cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc = cv2.minMaxLoc(result)
            
            # 计算偏移量
            offset = max_loc[1]
            
            # 限制偏移量在合理范围内
            offset = max(0, min(offset, h - search_height))
            
            # 返回偏移量
            return h - search_height - offset
        except Exception as e:
            print(f"查找最佳匹配点错误: {str(e)}")
            
            # 如果匹配失败，使用默认偏移量
            # 远程桌面使用更小的默认重叠
            default_overlap = 30 if self.is_remote_desktop else 50
            return h - default_overlap 