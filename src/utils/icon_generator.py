from PIL import Image, ImageDraw, ImageFont, ImageFilter
import colorsys
from pathlib import Path
import math
import os

def create_gradient(width, height, color1, color2, color3):
    """创建三色渐变背景"""
    image = Image.new('RGBA', (width, height))
    pixels = image.load()
    
    for y in range(height):
        for x in range(width):
            # 计算当前位置在渐变中的比例
            dx = x / width
            dy = y / height
            # 使用极坐标来创建径向渐变
            angle = math.atan2(dy - 0.5, dx - 0.5)
            dist = math.sqrt((dx - 0.5) ** 2 + (dy - 0.5) ** 2) * 2
            
            # 根据角度和距离混合三种颜色
            t = (angle + math.pi) / (2 * math.pi)
            s = min(1.0, dist)
            
            if t < 0.33:
                ratio1 = 1 - (t * 3)
                ratio2 = t * 3
                ratio3 = 0
            elif t < 0.66:
                ratio1 = 0
                ratio2 = 1 - ((t - 0.33) * 3)
                ratio3 = (t - 0.33) * 3
            else:
                ratio1 = (t - 0.66) * 3
                ratio2 = 0
                ratio3 = 1 - ((t - 0.66) * 3)
                
            # 混合颜色
            r = int(color1[0] * ratio1 + color2[0] * ratio2 + color3[0] * ratio3)
            g = int(color1[1] * ratio1 + color2[1] * ratio2 + color3[1] * ratio3)
            b = int(color1[2] * ratio1 + color2[2] * ratio2 + color3[2] * ratio3)
            
            pixels[x, y] = (r, g, b, 255)
    
    return image

def generate_icon():
    # 创建一个256x256的RGBA图像
    size = 256
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # 定义渐变颜色
    blue = (41, 128, 255)      # 亮蓝色
    purple = (147, 51, 234)    # 紫色
    pink = (255, 79, 216)      # 粉色
    
    # 创建渐变背景
    gradient = create_gradient(size, size, blue, purple, pink)
    
    # 创建圆形蒙版
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = 10
    mask_draw.ellipse([margin, margin, size-margin, size-margin], fill=255)
    
    # 应用圆形蒙版到渐变背景
    output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    output.paste(gradient, mask=mask)
    
    # 创建绘图对象
    draw = ImageDraw.Draw(output)
    
    # 绘制代码图案
    # 计算中心和大小
    center_x = size // 2
    center_y = size // 2
    symbol_size = 80  # 符号大小
    line_width = 12   # 线条宽度
    gap = 20         # 符号之间的间隔
    
    # 绘制代码符号 < >
    # 左箭头 <
    left_points = [
        (center_x - symbol_size//2, center_y),  # 尖端
        (center_x - symbol_size//4, center_y - symbol_size//2),  # 上边
        (center_x - symbol_size//4, center_y + symbol_size//2)   # 下边
    ]
    
    # 右箭头 >
    right_points = [
        (center_x + symbol_size//2, center_y),  # 尖端
        (center_x + symbol_size//4, center_y - symbol_size//2),  # 上边
        (center_x + symbol_size//4, center_y + symbol_size//2)   # 下边
    ]
    
    # 绘制符号（使用白色，半透明）
    symbol_color = (255, 255, 255, 230)
    
    # 绘制左箭头
    draw.line([left_points[0], left_points[1]], fill=symbol_color, width=line_width)
    draw.line([left_points[0], left_points[2]], fill=symbol_color, width=line_width)
    
    # 绘制右箭头
    draw.line([right_points[0], right_points[1]], fill=symbol_color, width=line_width)
    draw.line([right_points[0], right_points[2]], fill=symbol_color, width=line_width)
    
    # 在箭头之间添加一个小圆点
    dot_radius = 6
    draw.ellipse([
        center_x - dot_radius, 
        center_y - dot_radius,
        center_x + dot_radius, 
        center_y + dot_radius
    ], fill=symbol_color)
    
    # 添加光晕效果
    for i in range(3):
        glow = output.copy()
        glow = glow.filter(ImageFilter.GaussianBlur(2 + i*2))
        output = Image.alpha_composite(glow, output)
    
    # 保存图标
    icon_path = Path(__file__).parent.parent.parent / 'resources' / 'icon.png'
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(str(icon_path), 'PNG')

if __name__ == '__main__':
    generate_icon() 