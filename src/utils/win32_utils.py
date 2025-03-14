import win32gui
import win32con
import win32api
import win32ui
import time
import traceback
from ctypes import windll, byref, c_ubyte, Structure, c_long, c_int, c_void_p, POINTER
from ctypes.wintypes import RECT, HWND, POINT, DWORD
from PyQt6.QtGui import QCursor

# 定义一些 Windows API 常量
WM_MOUSEWHEEL = 0x020A
MOUSEEVENTF_WHEEL = 0x0800
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77

# 远程桌面相关常量
GW_CHILD = 5
GW_HWNDNEXT = 2
WS_VISIBLE = 0x10000000

def get_window_under_cursor():
    """获取鼠标指针下的窗口句柄，增强对远程桌面的支持"""
    try:
        cursor_pos = win32gui.GetCursorPos()
        print(f"当前鼠标位置: {cursor_pos}")
        
        # 获取鼠标下的窗口
        hwnd = win32gui.WindowFromPoint(cursor_pos)
        print(f"获取到窗口句柄: {hwnd}")
        
        # 检查是否是远程桌面窗口
        class_name = win32gui.GetClassName(hwnd)
        if "MKSEmbedded" in class_name or "VMware" in class_name or "Citrix" in class_name or "Remote" in class_name:
            print(f"检测到远程桌面窗口: {class_name}")
            # 对于远程桌面，我们直接使用顶层窗口
            # 因为远程桌面内部的窗口无法直接访问
        else:
            # 尝试获取真正的内容窗口（有时顶层窗口不是我们想要的）
            child_hwnd = get_child_window_at_point(hwnd, cursor_pos)
            if child_hwnd and child_hwnd != hwnd:
                print(f"找到子窗口: {child_hwnd}")
                hwnd = child_hwnd
        
        # 获取窗口信息
        window_info = get_window_info(hwnd)
        if window_info:
            print(f"窗口信息: 标题='{window_info['title']}', 类名='{window_info['class']}'")
        
        return hwnd
    except Exception as e:
        print(f"获取鼠标下窗口失败: {str(e)}")
        traceback.print_exc()
        return None

def get_child_window_at_point(parent_hwnd, point):
    """获取指定点上的子窗口，增强对远程桌面的支持"""
    try:
        # 尝试获取子窗口
        child_hwnd = win32gui.ChildWindowFromPoint(parent_hwnd, point)
        if child_hwnd and child_hwnd != parent_hwnd:
            # 检查子窗口是否可见
            if win32gui.IsWindowVisible(child_hwnd):
                # 递归查找更深层次的子窗口
                deeper_child = get_child_window_at_point(child_hwnd, point)
                if deeper_child:
                    return deeper_child
                return child_hwnd
        
        # 如果没有找到合适的子窗口，尝试枚举所有子窗口
        try:
            def enum_child_windows(hwnd, param):
                rect = win32gui.GetWindowRect(hwnd)
                x, y = point
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    if win32gui.IsWindowVisible(hwnd):
                        param.append(hwnd)
                return True
            
            child_windows = []
            win32gui.EnumChildWindows(parent_hwnd, enum_child_windows, child_windows)
            
            if child_windows:
                # 返回最后一个找到的子窗口（通常是最上层的）
                return child_windows[-1]
        except Exception as e:
            print(f"枚举子窗口失败: {str(e)}")
        
        return parent_hwnd
    except Exception as e:
        print(f"获取子窗口失败: {str(e)}")
        return parent_hwnd

def get_window_info(hwnd):
    """获取窗口信息"""
    if not hwnd:
        return None
        
    try:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        return {
            'handle': hwnd,
            'title': title,
            'class': class_name,
            'rect': rect
        }
    except Exception as e:
        print(f"获取窗口信息失败: {str(e)}")
        traceback.print_exc()
        return None

def simulate_scroll(hwnd, amount=1, delay=50):
    """模拟滚动事件 - 增强对远程桌面的支持"""
    if not hwnd:
        print("无效的窗口句柄，无法滚动")
        return False
        
    try:
        print(f"模拟滚动窗口 {hwnd}，滚动量: {amount}")
        # 确保窗口处于活动状态
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)
        except Exception as e:
            print(f"设置前台窗口失败: {str(e)}，尝试继续滚动")
        
        # 获取窗口中心点
        rect = win32gui.GetWindowRect(hwnd)
        center_x = (rect[0] + rect[2]) // 2
        center_y = (rect[1] + rect[3]) // 2
        
        # 保存当前鼠标位置
        original_pos = QCursor.pos()
        
        # 将鼠标移动到窗口中心
        QCursor.setPos(center_x, center_y)
        time.sleep(0.05)
        
        # 对于远程桌面，使用更强的滚动方法
        class_name = win32gui.GetClassName(hwnd)
        if "MKSEmbedded" in class_name or "VMware" in class_name or "Citrix" in class_name or "Remote" in class_name:
            print(f"检测到远程桌面窗口: {class_name}，使用增强滚动")
            # 对远程桌面使用更多的滚动次数和更大的滚动值
            for _ in range(5):  # 增加滚动次数
                win32api.mouse_event(
                    MOUSEEVENTF_WHEEL,
                    0, 0,
                    -240,  # 增加滚动值
                    0
                )
                time.sleep(delay / 1000 * 2)  # 增加延迟
        else:
            # 普通窗口使用标准滚动
            for _ in range(3):
                win32api.mouse_event(
                    MOUSEEVENTF_WHEEL,
                    0, 0,
                    -120,
                    0
                )
                time.sleep(delay / 1000)
        
        # 恢复鼠标位置
        QCursor.setPos(original_pos)
        print("滚动完成")
        return True
    except Exception as e:
        print(f"模拟滚动失败: {str(e)}")
        traceback.print_exc()
        return False

def set_window_transparency(hwnd, alpha):
    """设置窗口透明度"""
    if not hwnd:
        print("无效的窗口句柄，无法设置透明度")
        return False
        
    try:
        print(f"设置窗口 {hwnd} 的透明度为 {alpha}")
        # 获取当前窗口样式
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        # 添加透明窗口样式
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                             style | win32con.WS_EX_LAYERED)
        # 设置透明度
        win32gui.SetLayeredWindowAttributes(hwnd, 0,
                                          int(alpha * 255),
                                          win32con.LWA_ALPHA)
        print("透明度设置完成")
        return True
    except Exception as e:
        print(f"设置窗口透明度失败: {str(e)}")
        traceback.print_exc()
        return False

def get_foreground_window():
    """获取当前前台窗口"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        print(f"当前前台窗口: {hwnd}")
        window_info = get_window_info(hwnd)
        if window_info:
            print(f"窗口信息: 标题='{window_info['title']}', 类名='{window_info['class']}'")
        return hwnd
    except Exception as e:
        print(f"获取前台窗口失败: {str(e)}")
        traceback.print_exc()
        return None

def get_screen_bounds():
    """获取屏幕边界 - ShareX 使用此方法获取全屏范围"""
    try:
        # 获取虚拟屏幕的尺寸（包括所有显示器）
        width = win32api.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = win32api.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        left = win32api.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = win32api.GetSystemMetrics(SM_YVIRTUALSCREEN)
        
        return {
            'left': left,
            'top': top,
            'width': width,
            'height': height,
            'right': left + width,
            'bottom': top + height
        }
    except Exception as e:
        print(f"获取屏幕边界失败: {str(e)}")
        traceback.print_exc()
        return None

def bring_window_to_front(hwnd):
    """将窗口置于前台 - 增强版本，处理SetForegroundWindow错误"""
    if not hwnd:
        return False
        
    try:
        print(f"尝试将窗口 {hwnd} 置于前台")
        
        # 检查窗口是否有效
        if not win32gui.IsWindow(hwnd):
            print(f"窗口 {hwnd} 无效")
            return False
            
        # 检查窗口是否最小化
        if win32gui.IsIconic(hwnd):
            # 恢复窗口
            print("窗口已最小化，正在恢复")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)
        
        # 尝试使用多种方法将窗口置于前台
        try:
            # 方法1: 标准SetForegroundWindow
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"SetForegroundWindow失败: {str(e)}，尝试备用方法")
            try:
                # 方法2: 使用AttachThreadInput
                current_thread = win32api.GetCurrentThreadId()
                foreground_window = win32gui.GetForegroundWindow()
                foreground_thread = win32api.GetWindowThreadProcessId(foreground_window)[0]
                
                if current_thread != foreground_thread:
                    win32api.AttachThreadInput(current_thread, foreground_thread, True)
                    win32gui.SetForegroundWindow(hwnd)
                    win32api.AttachThreadInput(current_thread, foreground_thread, False)
            except Exception as e2:
                print(f"备用方法也失败: {str(e2)}，尝试最后方法")
                try:
                    # 方法3: 使用ShowWindow
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                except Exception as e3:
                    print(f"所有方法都失败: {str(e3)}")
        
        # 确保窗口可见
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        print(f"窗口 {hwnd} 已尝试置于前台")
        return True
    except Exception as e:
        print(f"将窗口置于前台失败: {str(e)}")
        traceback.print_exc()
        return False 