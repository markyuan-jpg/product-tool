# -*- coding: utf-8 -*-
"""
图片文件名匹配器 - 根据产品型号匹配图片
"""
import os
import re
import glob
import logging
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 常见图片文件夹名
IMAGE_FOLDERS = ['images', 'imgs', 'pics', 'img', 'photo', 'photos']
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']


def normalize_model(model: str) -> str:
    """
    标准化型号 (用于匹配)
    
    处理:
    - 转小写
    - 移除空格和特殊字符
    - 移除常见前缀
    """
    if not model:
        return ''
    
    model = str(model).lower().strip()
    
    # 移除常见前缀
    prefixes = ['model', 'item', 'no.', 'sku', 'code', '型号', '编号']
    for p in prefixes:
        if model.startswith(p):
            model = model[len(p):].strip()
    
    # 移除非字母数字
    model = re.sub(r'[^a-z0-9]', '', model)
    
    return model


def extract_keywords(model: str, min_len: int = 3) -> List[str]:
    """
    从型号提取匹配关键词
    
    例如: "ABC-1234" → ["abc", "abc123", "1234", "abc-1234"]
    """
    if not model:
        return []
    
    model = str(model).strip().lower()
    keywords = []
    
    # 完整型号
    keywords.append(model)
    
    # 移除特殊字符的版本
    clean = re.sub(r'[^a-z0-9]', '', model)
    if clean:
        keywords.append(clean)
    
    # 数字部分
    numbers = re.findall(r'\d+', model)
    for n in numbers:
        if len(n) >= min_len:
            keywords.append(n)
    
    # 字母部分
    letters = re.findall(r'[a-z]+', model)
    for l in letters:
        if len(l) >= min_len:
            keywords.append(l)
    
    # 分割的部分
    parts = re.split(r'[-_\s]+', model)
    for p in parts:
        if len(p) >= min_len:
            keywords.append(p)
    
    return list(set(keywords))


def find_image_folder(file_path: str) -> Optional[str]:
    """
    查找图片文件夹
    
    检查位置:
    1. 同目录 images/
    2. 同目录 imgs/
    3. 同目录 pics/
    4. 子目录 (递归搜索)
    """
    file_dir = os.path.dirname(file_path)
    
    # 1. 同目录
    for folder in IMAGE_FOLDERS:
        path = os.path.join(file_dir, folder)
        if os.path.isdir(path):
            return path
    
    # 2. 子目录
    for root, dirs, files in os.walk(file_dir):
        for folder in dirs:
            if folder.lower() in IMAGE_FOLDERS:
                return os.path.join(root, folder)
    
    return None


def get_image_files(folder: str) -> List[str]:
    """获取文件夹中所有图片文件"""
    if not folder or not os.path.isdir(folder):
        return []
    
    files = []
    for ext in IMAGE_EXTS:
        files.extend(glob.glob(os.path.join(folder, '*' + ext)))
    
    return sorted(files)


def match_image_by_filename(model: str, image_files: List[str]) -> Optional[str]:
    """
    根据型号匹配图片
    
    匹配策略 (优先级):
    1. 完全匹配 (含型号的文件名)
    2. 数字匹配 (型号中的数字)
    3. 前缀匹配
    
    Args:
        model: 产品型号
        image_files: 图片文件列表
    
    Returns:
        str: 匹配的图片路径, 无匹配返回None
    """
    if not model or not image_files:
        return None
    
    keywords = extract_keywords(model)
    if not keywords:
        return None
    
    # 优先: 完全匹
    for img in image_files:
        img_name = os.path.basename(img).lower()
        for kw in keywords:
            if kw == img_name.replace(os.path.splitext(img_name)[1], ''):
                return img
    
    # 次优: 包含关键词
    for img in image_files:
        img_name = os.path.basename(img).lower()
        for kw in keywords:
            if kw in img_name:
                return img
    
    return None


def batch_match_images(models: List[str], image_folder: str) -> Dict[str, str]:
    """
    批量匹配图片
    
    Args:
        models: 产品型号列表
        image_folder: 图片文件夹
    
    Returns:
        dict: {model: image_path}
    """
    image_files = get_image_files(image_folder)
    
    result = {}
    for model in models:
        if model:
            img = match_image_by_filename(model, image_files)
            if img:
                result[model] = img
    
    return result


def match_images_for_excel(excel_path: str, df) -> List[str]:
    """
    为Excel数据匹配图片
    
    Args:
        excel_path: Excel文件路径
        df: 产品DataFrame
    
    Returns:
        list: 图片路径列表 (与行对应)
    """
    # 查找图片文件夹
    img_folder = find_image_folder(excel_path)
    if not img_folder:
        logging.info(f'No image folder found for: {excel_path}')
        return [None] * len(df)
    
    image_files = get_image_files(img_folder)
    logging.info(f'Found {len(image_files)} images in: {img_folder}')
    
    # 提取型号列
    if 'model' not in df.columns:
        return [None] * len(df)
    
    models = df['model'].tolist()
    
    # 匹配
    results = []
    for model in models:
        img = match_image_by_filename(model, image_files)
        results.append(img)
    
    return results


# ============ 单元测试 ============

if __name__ == '__main__':
    # 测试关键词提取
    test_models = ['ABC-1234', 'Model X001', '产品编号-001', 'SKU12345']
    
    print('=== Keyword Extraction ===')
    for model in test_models:
        keywords = extract_keywords(model)
        print(f'{model} → {keywords}')
    
    # 测试匹配
    print('\n=== Image Matching ===')
    
    # 创建测试图片
    test_folder = 'test_images'
    os.makedirs(test_folder, exist_ok=True)
    
    test_imgs = [
        'abc-1234.jpg',
        '1234.png',
        'model_x001.jpg',
        'unrelated.jpg'
    ]
    
    for img in test_imgs:
        Path(os.path.join(test_folder, img)).touch()
    
    models = ['ABC-1234', 'Model X001', 'UNKNOWN-999']
    results = batch_match_images(models, test_folder)
    
    for model, img in results.items():
        print(f'{model} → {img}')
    
    # 清理
    import shutil
    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)