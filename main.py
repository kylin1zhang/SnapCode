#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.ui.main_window import MainWindow

def main():
    """程序入口函数"""
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序名称
    app.setApplicationName("SnapCode")
    
    # 在PyQt6中，高DPI缩放默认已启用，不需要显式设置这些属性
    # 如果需要禁用高DPI缩放，可以使用以下代码：
    # app.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling, True)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 确保应用程序不会在最后一个窗口关闭时退出
    # 这样即使主窗口关闭，系统托盘图标仍然存在
    app.setQuitOnLastWindowClosed(False)
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 