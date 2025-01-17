import os
import requests
from pathlib import Path

def download_font():
    # 字体文件URL（使用更可靠的CDN源）
    font_url = "https://fonts.googleapis.com/css2?family=Pacifico&display=swap"
    
    # 目标路径
    font_dir = Path(__file__).parent / 'fonts'
    font_path = font_dir / 'Pacifico-Regular.ttf'
    
    # 确保目录存在
    font_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 获取字体CSS
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(font_url, headers=headers)
        response.raise_for_status()
        
        # 从CSS中提取字体URL
        css_content = response.text
        font_url_start = css_content.find("src: url(") + 9
        font_url_end = css_content.find(")", font_url_start)
        actual_font_url = css_content[font_url_start:font_url_end]
        
        # 下载实际的字体文件
        font_response = requests.get(actual_font_url, headers=headers)
        font_response.raise_for_status()
        
        # 保存文件
        with open(font_path, 'wb') as f:
            f.write(font_response.content)
        
        print(f"字体文件已下载到: {font_path}")
        return True
    except Exception as e:
        print(f"下载字体文件失败: {str(e)}")
        return False

if __name__ == '__main__':
    download_font() 