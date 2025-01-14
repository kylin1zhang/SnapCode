import black
from typing import Tuple, Dict

class CodeProcessor:
    """代码处理类"""
    
    def format_code(self, code: str) -> Tuple[bool, str]:
        """格式化代码"""
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
            return True, formatted_code
        except Exception as e:
            return False, str(e)
    
    def check_syntax(self, code: str) -> Tuple[bool, Dict]:
        """检查代码语法"""
        try:
            compile(code, '<string>', 'exec')
            return True, {}
        except SyntaxError as e:
            return False, {
                'line': e.lineno,
                'offset': e.offset,
                'message': str(e)
            } 