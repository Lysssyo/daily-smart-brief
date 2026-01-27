import sys


def load_text_file(filepath):
    """读取文本文件并返回其内容。"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"错误: 无法读取文件 {filepath}: {e}")
        sys.exit(1)
