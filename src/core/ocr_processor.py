import pytesseract
from PIL import Image
import re
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import logging

class OCRProcessor:
    """OCR处理类"""
    
    def __init__(self):
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
                'weight': 1.2  # 给C#特征更高的权重
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
                'weight': 1.5  # 给SQL更高的权重，因为其关键词比较独特
            }
        }
        
        # OCR配置
        self.config = r'--oem 3 --psm 6'
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
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
            
            # OCR识别
            text = pytesseract.image_to_string(
                image,
                config=self.config
            )
            
            # 后处理
            text = self._postprocess_text(text)
            
            self.logger.info(f"Successfully processed {image_path}")
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
            
            success, text = self.extract_text(path)
            if success:
                # 检测代码语言和类名
                code_info = self.detect_language(text)
                results.append({
                    'path': path,
                    'text': text,
                    'language': code_info['language'],
                    'class_name': code_info['class_name'],
                    'file_ext': code_info['file_ext'],
                    'success': True
                })
            else:
                results.append({
                    'path': path,
                    'error': text,
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