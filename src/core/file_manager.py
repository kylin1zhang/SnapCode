import os
from PIL import Image
from typing import List, Tuple, Optional, Dict
from pathlib import Path, PureWindowsPath
import logging
import re

class FileManager:
    """文件管理类"""
    
    def __init__(self):
        # 初始化日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 语言扩展名映射
        self.language_extensions = {
            'python': '.py',
            'java': '.java',
            'csharp': '.cs',
            'cpp': '.cpp',
            'javascript': '.js',
            'sql': '.sql',
            'xml': '.xml'  # 添加XML扩展名
        }
        
        # 类名匹配模式
        self.class_patterns = {
            'java': r'public\s+class\s+(\w+)',
            'csharp': r'(?:public\s+)?class\s+(\w+)',
            'python': r'class\s+(\w+)',
            'cpp': r'class\s+(\w+)',
            'sql': r'CREATE\s+(?:TABLE|PROCEDURE|TRIGGER|VIEW)\s+(\w+)',
            'xml': r'<([a-zA-Z0-9_-]+)[^>]*>.*?</\1>'  # 添加XML根元素匹配
        }
    
    def import_files(self, file_paths: List[str]) -> List[str]:
        """导入文件并验证"""
        valid_files = []
        for path in file_paths:
            try:
                # 检查文件是否存在
                path_obj = Path(path)
                if not path_obj.exists():
                    self.logger.warning(f"文件不存在: {path}")
                    continue
                    
                # 检查是否为图片文件
                try:
                    with Image.open(path) as img:
                        # 验证是否为支持的图片格式
                        if img.format.lower() in ['jpeg', 'jpg', 'png', 'gif']:
                            self.logger.info(f"成功导入图片: {path}")
                            valid_files.append(path)
                        else:
                            self.logger.warning(f"不支持的图片格式: {path} ({img.format})")
                except Exception as e:
                    self.logger.warning(f"无效的图片文件: {path} ({str(e)})")
                    
            except Exception as e:
                self.logger.error(f"处理文件失败: {path} ({str(e)})")
        
        # 记录导入结果
        if not valid_files:
            self.logger.warning("没有有效的图片文件被导入")
        else:
            self.logger.info(f"成功导入 {len(valid_files)} 个文件")
        
        return valid_files
    
    def detect_code_info(self, code: str) -> Dict[str, str]:
        """检测代码信息（语言类型和类名）"""
        # 语言特征
        language_features = {
            'python': {
                'keywords': ['def ', 'import ', 'from ', 'class ', '.py'],
                'weight': 1
            },
            'csharp': {
                'keywords': [
                    'using System',
                    'namespace',
                    'public class',
                    'private static',
                    'string[]',
                    'void',
                    'EAP.Devhub',
                    '.CTC',
                    'AutoMapper'
                ],
                'weight': 1.2
            },
            'java': {
                'keywords': [
                    'public class',
                    'private static',
                    'String[]',
                    'void',
                    'package',
                    'import java'
                ],
                'weight': 1
            },
            'sql': {
                'keywords': [
                    'SELECT ',
                    'INSERT INTO',
                    'UPDATE ',
                    'DELETE FROM',
                    'CREATE TABLE',
                    'ALTER TABLE',
                    'EXEC ',
                    'EXECUTE ',
                    'DECLARE @',
                    'BEGIN TRANSACTION',
                    'MERGE INTO',
                    'WITH ',
                    'UNION ',
                    'JOIN '
                ],
                'weight': 1.5
            },
            'xml': {
                'keywords': [
                    '<?xml',
                    '</',
                    '/>',
                    'xmlns:',
                    'encoding=',
                    '<root>',
                    '</root>',
                    '<config',
                    '<project',
                    '<properties',
                    '<dependencies'
                ],
                'weight': 2.0  # XML的特征很明显，给更高的权重
            }
        }
        
        # 检测语言
        language_scores = {lang: 0 for lang in language_features}
        for lang, features in language_features.items():
            weight = features.get('weight', 1)
            for keyword in features['keywords']:
                if keyword in code:
                    language_scores[lang] += 1 * weight
        
        # 获取得分最高的语言
        detected_language = max(language_scores.items(), key=lambda x: x[1])[0]
        
        # 尝试查找类名
        class_name = None
        if detected_language in self.class_patterns:
            pattern = self.class_patterns[detected_language]
            matches = re.findall(pattern, code)
            if matches:
                class_name = matches[0]
        
        return {
            'language': detected_language,
            'class_name': class_name
        }
    
    def generate_smart_filename(self, code: str, original_path: str = None) -> str:
        """智能生成文件名"""
        try:
            # 检测代码信息
            code_info = self.detect_code_info(code)
            language = code_info['language']
            class_name = code_info['class_name']
            
            # 获取文件扩展名
            extension = self.language_extensions.get(language, '.txt')
            
            # 生成基础文件名
            if class_name:
                base_name = class_name
            else:
                # 如果没有类名，使用原始文件名或默认名
                if original_path:
                    base_name = Path(original_path).stem
                else:
                    base_name = f"code_{len(code)//100}"
            
            # 确保输出目录存在
            output_dir = Path(original_path).parent if original_path else Path.cwd()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理文件名冲突
            counter = 1
            file_path = output_dir / f"{base_name}{extension}"
            while file_path.exists():
                file_path = output_dir / f"{base_name}_{counter}{extension}"
                counter += 1
            
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"生成文件名失败: {str(e)}")
            # 返回默认文件名
            return str(Path(original_path).parent / "code_1.txt" if original_path else "code_1.txt")
    
    def save_code(self, code: str, original_path: str = None, custom_filename: str = None) -> Tuple[bool, str]:
        """保存代码到文件"""
        try:
            if custom_filename:
                # 使用自定义文件名
                output_path = Path(original_path).parent / custom_filename if original_path else Path(custom_filename)
            else:
                # 使用智能生成的文件名
                output_path = Path(self.generate_smart_filename(code, original_path))
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            self.logger.info(f"代码已保存到: {output_path}")
            return True, str(output_path)
            
        except Exception as e:
            error_msg = f"保存代码失败: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg 