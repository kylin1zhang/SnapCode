import os
import sys
import pytesseract
from PIL import Image
import re
import logging
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import time
from datetime import datetime

class OCRProcessor:
    """OCR处理类 - 支持Tesseract OCR和Windows OCR"""
    
    def __init__(self):
        # 设置日志
        self._setup_logging()
        self.logger.info("初始化OCR处理器")
        
        # 语言特征定义
        self.language_features = {
            'python': {
                'keywords': ['def', 'class', 'import', 'from', 'if', 'for', 'while', 'try', 'except'],
                'patterns': [
                    r'def\s+\w+\s*\(',
                    r'class\s+\w+[:\(]',
                    r'import\s+[\w\s,]+',
                    r'from\s+[\w\.]+\s+import'
                ],
                'file_ext': '.py'
            },
            'csharp': {
                'keywords': ['public', 'private', 'class', 'void', 'string', 'int', 'var', 'using', 'namespace'],
                'patterns': [
                    r'public\s+class\s+\w+',
                    r'namespace\s+[\w\.]+',
                    r'using\s+[\w\.]+;',
                    r'public\s+(?:static\s+)?(?:void|string|int|bool)\s+\w+\s*\(',
                    r'private\s+(?:static\s+)?(?:void|string|int|bool)\s+\w+\s*\('
                ],
                'file_ext': '.cs',
                'weight': 1.2
            },
            'java': {
                'keywords': ['public', 'private', 'class', 'void', 'String', 'int', 'package'],
                'patterns': [
                    r'public\s+class\s+\w+',
                    r'package\s+[\w\.]+;',
                    r'import\s+[\w\.]+;',
                    r'public\s+(?:static\s+)?(?:void|String|int|boolean)\s+\w+\s*\('
                ],
                'file_ext': '.java'
            },
            'sql': {
                'keywords': [
                    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 
                    'JOIN', 'GROUP BY', 'ORDER BY', 'HAVING', 'CREATE TABLE',
                    'ALTER TABLE', 'DROP TABLE', 'EXEC', 'EXECUTE', 'PROCEDURE',
                    'DECLARE', 'SET', 'BEGIN', 'END', 'TRIGGER', 'VIEW'
                ],
                'patterns': [
                    r'SELECT\s+[\w\s,\*]+\s+FROM',
                    r'INSERT\s+INTO\s+\w+',
                    r'UPDATE\s+\w+\s+SET',
                    r'CREATE\s+(?:TABLE|PROCEDURE|TRIGGER|VIEW|INDEX)',
                    r'ALTER\s+TABLE\s+\w+',
                    r'EXEC(?:UTE)?\s+\w+',
                    r'BEGIN\s+TRANSACTION',
                    r'DECLARE\s+@\w+',
                ],
                'file_ext': '.sql',
                'weight': 1.5
            }
        }
        
        # OCR配置
        self.config = r'--oem 3 --psm 6'
        
        # 设置Tesseract
        self._setup_tesseract()
        
        # 尝试加载Windows OCR支持
        self.windows_ocr_available = False
        try:
            from src.core.windows_ocr import OCR
            self.windows_ocr = OCR()
            self.windows_ocr_available = self.windows_ocr.is_windows_ocr_available()
            if self.windows_ocr_available:
                self.logger.info("Windows OCR可用")
        except ImportError:
            self.logger.info("Windows OCR不可用")
    
    def _setup_logging(self):
        """设置日志"""
        # 创建logs目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        log_file = log_dir / "ocr_processor.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_tesseract(self):
        """设置Tesseract"""
        # 获取应用基础路径
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.logger.info(f"应用基础路径: {base_dir}")
        
        # 设置tessdata路径 - 尝试多种位置
        tessdata_paths = [
            os.path.join(base_dir, 'tessdata'),
            os.path.join(base_dir, '_internal', 'tessdata'),
        ]
        
        self.tessdata_path = None
        for path in tessdata_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # 检查是否包含语言文件
                eng_file = os.path.join(path, 'eng.traineddata')
                if os.path.exists(eng_file):
                    self.tessdata_path = path
                    break
        
        if self.tessdata_path:
            self.logger.info(f"找到tessdata路径: {self.tessdata_path}")
            os.environ['TESSDATA_PREFIX'] = self.tessdata_path
            
            # 列出可用的语言
            lang_files = []
            for file in os.listdir(self.tessdata_path):
                if file.endswith('.traineddata'):
                    lang_files.append(file.split('.')[0])
            self.logger.info(f"可用语言: {', '.join(lang_files)}")
        else:
            self.logger.warning("未找到有效的tessdata路径")
        
        # 设置Tesseract可执行文件路径
        tesseract_paths = [
            os.path.join(base_dir, 'tesseract.exe'),
            os.path.join(base_dir, '_internal', 'tesseract.exe'),
        ]
        
        self.tesseract_path = None
        for path in tesseract_paths:
            if os.path.exists(path):
                self.tesseract_path = path
                break
        
        if self.tesseract_path:
            self.logger.info(f"找到Tesseract可执行文件: {self.tesseract_path}")
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        else:
            self.logger.warning("未找到有效的Tesseract路径")
        
        # 检查Tesseract是否可用
        self.tesseract_available = self.check_tesseract()
    
    def check_tesseract(self):
        """检查Tesseract OCR是否可用"""
        try:
            # 尝试获取Tesseract版本
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"检测到Tesseract版本: {version}")
            return True
        except Exception as e:
            self.logger.error(f"检测Tesseract时出错: {e}")
            return False
    
    def process_image(self, image_path):
        """
        处理图像，包括OCR识别和语言检测
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            包含处理结果的字典
        """
        start_time = time.time()
        self.logger.info(f"开始处理图像: {image_path}")
        
        # 首先尝试Tesseract OCR
        if self.tesseract_available:
            try:
                # 提取文本
                success, text = self.extract_text(image_path)
                
                if success:
                    # 检测语言
                    code_info = self.detect_language(text)
                    
                    return {
                        'success': True,
                        'text': text,
                        'language': code_info['language'],
                        'class_name': code_info['class_name'],
                        'file_ext': code_info['file_ext'],
                        'confidence': code_info['confidence'],
                        'time_taken': time.time() - start_time,
                        'engine': 'Tesseract OCR'
                    }
            except Exception as e:
                self.logger.error(f"Tesseract处理失败: {e}")
        
        # 如果Tesseract失败或不可用，尝试Windows OCR
        if self.windows_ocr_available:
            try:
                self.logger.info("尝试使用Windows OCR")
                text = self.windows_ocr.recognize_text(image_path)
                
                if text and not text.startswith("Windows OCR不可用"):
                    # 检测语言
                    code_info = self.detect_language(text)
                    
                    return {
                        'success': True,
                        'text': text,
                        'language': code_info['language'],
                        'class_name': code_info['class_name'],
                        'file_ext': code_info['file_ext'],
                        'confidence': code_info['confidence'],
                        'time_taken': time.time() - start_time,
                        'engine': 'Windows OCR'
                    }
            except Exception as e:
                self.logger.error(f"Windows OCR处理失败: {e}")
        
        # 所有OCR方法都失败
        return {
            'success': False,
            'error': 'OCR处理失败，请确保Tesseract OCR已正确安装或Windows OCR可用',
            'time_taken': time.time() - start_time
        }
    
    def detect_language(self, code: str) -> Dict[str, any]:
        """检测代码语言和提取类名"""
        scores = {lang: 0 for lang in self.language_features}
        class_name = None
        
        # 对每种语言进行评分
        for lang, features in self.language_features.items():
            # 关键字匹配
            for keyword in features['keywords']:
                if keyword in code:
                    scores[lang] += 1
            
            # 模式匹配
            for pattern in features['patterns']:
                matches = re.findall(pattern, code)
                scores[lang] += len(matches)
                
                # 尝试提取类名
                if 'class' in pattern and matches:
                    class_match = re.search(r'class\s+(\w+)', matches[0])
                    if class_match:
                        class_name = class_match.group(1)
        
        # 获取得分最高的语言
        detected_lang = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[detected_lang] / sum(1 for s in scores.values() if s > 0) if any(scores.values()) else 0
        
        self.logger.info(f"检测到语言: {detected_lang} (置信度: {confidence:.2f})")
        if class_name:
            self.logger.info(f"检测到类名: {class_name}")
        
        return {
            'language': detected_lang,
            'confidence': confidence,
            'class_name': class_name,
            'file_ext': self.language_features[detected_lang]['file_ext']
        }
    
    def extract_text(self, image_path: str) -> Tuple[bool, str]:
        """从图片中提取文本"""
        try:
            image = Image.open(image_path)
            
            # 图片预处理
            image = self._preprocess_image(image)
            
            # 尝试使用中英文混合识别
            try:
                text = pytesseract.image_to_string(
                    image,
                    lang='chi_sim+eng',  # 同时使用简体中文和英文
                    config=self.config
                )
            except Exception as e:
                self.logger.warning(f"中英文混合识别失败，尝试仅英文: {e}")
                # 回退到仅英文
                text = pytesseract.image_to_string(
                    image,
                    lang='eng',  # 仅使用英文
                    config=self.config
                )
            
            # 后处理
            text = self._postprocess_text(text)
            
            self.logger.info(f"成功处理图像: {image_path}")
            return True, text
            
        except Exception as e:
            self.logger.error(f"OCR处理失败: {str(e)}")
            return False, str(e)
    
    def batch_process(self, image_paths: List[str], 
                     progress_callback=None) -> List[Dict]:
        """批量处理图片"""
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths, 1):
            # 更新进度
            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(progress)
            
            # 处理图片
            result = self.process_image(path)
            
            if result['success']:
                results.append({
                    'path': path,
                    'text': result['text'],
                    'language': result['language'],
                    'class_name': result.get('class_name'),
                    'file_ext': result['file_ext'],
                    'success': True,
                    'engine': result.get('engine', 'Unknown')
                })
            else:
                results.append({
                    'path': path,
                    'error': result.get('error', '未知错误'),
                    'success': False
                })
                
        return results

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """图片预处理"""
        # 转换为灰度图
        if image.mode != 'L':
            image = image.convert('L')
        return image
    
    def _postprocess_text(self, text: str) -> str:
        """文本后处理"""
        # 修复常见的OCR错误
        replacements = {
            '；': ';',  # 中文分号替换
            '：': ':',  # 中文冒号替换
            '"': '"',   # 中文引号替换
            '"': '"',   # 中文引号替换
            ''': "'",   # 中文单引号替换
            ''': "'",   # 中文单引号替换
            '（': '(',  # 中文括号替换
            '）': ')',  # 中文括号替换
            '【': '[',  # 中文方括号替换
            '】': ']',  # 中文方括号替换
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 删除多余的空行
        text = '\n'.join(line for line in text.splitlines() if line.strip())
        
        return text

class OCRError(Exception):
    """OCR处理异常"""
    pass 