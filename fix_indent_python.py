import sys


def fix_indentation():
    """修复main.py中的缩进问题"""
    file_path = "pyqt_ui/main.py"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 将13个空格替换为4个空格
        fixed_content = content.replace("            ", "    ")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        print("成功修复缩进问题")
        return True
    except Exception as e:
        print(f"修复失败: {e}")
        return False


if __name__ == "__main__":
    success = fix_indentation()
    sys.exit(0 if success else 1)
