"""
图像预处理工具 - 用于提高OCR识别效果
"""
import cv2
import numpy as np
from typing import Tuple, Optional, List

def preprocess_image(image, enhance_text=True):
    """
    图像预处理以提高OCR识别效果
    
    Args:
        image: 输入图像 (OpenCV格式，BGR)
        enhance_text: 是否增强文本
        
    Returns:
        预处理后的图像
    """
    # 如果是彩色图像，转换为灰度图像
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # 检查图像是否为浅色背景深色文字
    is_dark_text = is_dark_text_on_light_background(gray)
    
    # 如果需要增强文本
    if enhance_text:
        # 应用自适应阈值二值化
        if is_dark_text:
            # 深色文字浅色背景
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
        else:
            # 浅色文字深色背景 (反转)
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
        
        # 应用形态学操作增强文本
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 如果是代码文本，尝试移除背景噪声
        if detect_code_content(gray):
            binary = remove_background_noise(binary)
            
        # 转换回RGB (因为一些OCR引擎需要彩色图像作为输入)
        processed = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    else:
        # 如果不需要增强，只应用基本处理
        # 去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # 增强对比度
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
        
        # 转换回RGB
        processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    return processed

def is_dark_text_on_light_background(image):
    """
    检测图像是否为深色文字浅色背景
    
    Args:
        image: 灰度图像
        
    Returns:
        bool: 如果是深色文字浅色背景则为True，否则为False
    """
    # 计算图像平均亮度
    mean_value = np.mean(image)
    
    # 如果平均亮度大于127，则很可能是深色文字浅色背景
    return mean_value > 127

def detect_code_content(image):
    """
    检测图像内容是否包含代码
    主要通过检测矩形对齐的文本行和缩进模式
    
    Args:
        image: 灰度图像
        
    Returns:
        bool: 如果图像可能包含代码则为True
    """
    # 使用霍夫线变换检测水平线
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    # 如果找到了足够多的水平线，可能是代码
    if lines is not None and len(lines) > 5:
        # 统计水平线的数量
        horizontal_lines = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 如果线接近水平
            if abs(y2 - y1) < 5:
                horizontal_lines += 1
        
        # 如果水平线占一定比例，很可能是代码
        if horizontal_lines / len(lines) > 0.5:
            return True
    
    # 使用垂直投影分析检测缩进模式
    projection = np.sum(image < 128, axis=0)  # 假设深色像素值<128
    
    # 计算投影的标准差，代码通常有明显的缩进模式
    std_deviation = np.std(projection)
    
    # 如果标准差大于一定阈值，可能是代码
    return std_deviation > 50

def remove_background_noise(image):
    """
    移除图像背景噪声
    
    Args:
        image: 二值化图像
        
    Returns:
        处理后的图像
    """
    # 查找轮廓
    contours, _ = cv2.findContours(255 - image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 创建掩码
    mask = np.ones_like(image) * 255
    
    # 过滤掉太小的轮廓 (噪声)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 5:  # 面积太小，视为噪声
            cv2.drawContours(mask, [contour], -1, 0, -1)
    
    # 应用掩码
    result = cv2.bitwise_and(image, mask)
    
    return result

def deskew_image(image):
    """
    校正倾斜图像
    
    Args:
        image: 输入图像
        
    Returns:
        校正后的图像
    """
    # 转换为灰度图像
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 二值化
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # 查找所有轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # 计算每个轮廓的旋转角度
    angles = []
    for c in contours:
        # 跳过太小的轮廓
        if cv2.contourArea(c) < 100:
            continue
            
        # 计算最小外接矩形
        rect = cv2.minAreaRect(c)
        
        # 获取角度
        angle = rect[2]
        
        # 将角度调整到-45到45度范围内
        if angle < -45:
            angle = 90 + angle
        
        angles.append(angle)
    
    # 如果没有找到合适的轮廓，返回原图
    if len(angles) == 0:
        return image
    
    # 计算角度的中位数作为最佳角度
    median_angle = np.median(angles)
    
    # 旋转图像
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def crop_to_content(image):
    """
    裁剪图像只保留内容区域
    
    Args:
        image: 输入图像
        
    Returns:
        裁剪后的图像
    """
    # 转换为灰度图像
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 寻找非零点
    coords = cv2.findNonZero(binary)
    
    # 获取边界框
    x, y, w, h = cv2.boundingRect(coords)
    
    # 添加一些额外的边距
    padding = 10
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(gray.shape[1] - x, w + 2 * padding)
    h = min(gray.shape[0] - y, h + 2 * padding)
    
    # 裁剪图像
    cropped = image[y:y+h, x:x+w]
    
    return cropped

def enhance_for_reading(image):
    """
    增强图像可读性，适用于阅读而非OCR
    
    Args:
        image: 输入图像
        
    Returns:
        增强后的图像
    """
    # 转换为灰度图像
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # 自适应直方图均衡化提高对比度
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 锐化图像
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    # 转换回彩色
    result = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
    
    return result

# 下面的函数用于改进OCR结果

def clean_ocr_text(text):
    """
    清理OCR识别文本
    
    Args:
        text: OCR识别的文本
        
    Returns:
        清理后的文本
    """
    # 替换常见的OCR错误
    replacements = {
        # 中文标点替换为英文标点
        '；': ';',
        '：': ':',
        '，': ',',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '（': '(',
        '）': ')',
        '【': '[',
        '】': ']',
        '《': '<',
        '》': '>',
        
        # 常见OCR错误
        'l': 'I',  # 小写l容易被识别为大写I
        '0': 'O',  # 数字0容易被识别为大写O
        '1': 'l',  # 数字1容易被识别为小写l
    }
    
    # 执行替换
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 删除多余的空行
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    cleaned_text = '\n'.join(non_empty_lines)
    
    return cleaned_text 