import re
import sys


def fix_indentation():
    """修复main.py中的缩进问题"""
    file_path = "pyqt_ui/main.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 查找并修复缩进问题：将13个空格替换为4个空格
    content = re.sub(r"^(\s{13})", "    ", content, flags=re.MULTILINE)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"已修复 {file_path} 中的缩进问题")


if __name__ == "__main__":
    fix_indentation()
