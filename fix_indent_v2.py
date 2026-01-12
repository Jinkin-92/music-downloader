import sys


def fix_indentation():
    """修复main.py中的缩进问题"""
    file_path = "pyqt_ui/main.py"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 查找需要删除的重复代码块（第359-380行）
        # 第359-380行是第356-358行的重复
        lines_to_delete = lines[358:380]

        # 检查这些行是否确实是重复的
        print(f"检查要删除的 {len(lines_to_delete)} 行...")
        for i, line in enumerate(lines_to_delete, 358):
            print(f"  第{i + 359}行: {line[:50] if len(line) > 50 else line}")

        # 删除重复的行
        lines = lines[:358] + lines[380:]

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ 成功删除重复代码，文件已保存")
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False


if __name__ == "__main__":
    success = fix_indentation()
    sys.exit(0 if success else 1)
