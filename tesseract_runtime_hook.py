# -*- coding: utf-8 -*-
import os
import sys

def setup_environment():
    if getattr(sys, 'frozen', False):
        # 打包环境
        base_dir = sys._MEIPASS
        
        # 添加src目录到Python路径
        src_dir = os.path.join(base_dir, 'src')
        if os.path.exists(src_dir):
            sys.path.insert(0, src_dir)
            
        # 设置Tesseract路径
        tessdata_dir = os.path.join(base_dir, 'tessdata')
        if os.path.exists(tessdata_dir):
            os.environ['TESSDATA_PREFIX'] = tessdata_dir
            
        # 设置Tesseract可执行文件
        try:
            import pytesseract
            tesseract_exe = os.path.join(base_dir, 'tesseract.exe')
            if os.path.exists(tesseract_exe):
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
        except:
            pass
            
        # 创建logs目录
        logs_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir)
            except:
                pass

setup_environment()
