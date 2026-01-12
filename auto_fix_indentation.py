#!/usr/bin/env python3
"""
自动修复 pyqt_ui/main.py 的缩进错误
使用 tokenize 模块检测缩进问题并自动修复
"""

import re
import tokenize
from io import BytesIO


def fix_indentation_errors(file_path):
    """修复缩进错误"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed_count = 0
    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测以冒号结尾的控制流语句
        if re.match(r'^(\s*)(if|else|elif|for|while|def|class|try|except|finally|with|async).*:\s*$', line):
            # 获取当前缩进级别
            current_indent = len(line) - len(line.lstrip())
            base_indent = current_indent

            # 检查下一行的缩进
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_indent = len(next_line) - len(next_line.lstrip())

                # 如果下一行缩进不大于当前行，需要修复
                if next_line.strip() and next_indent <= base_indent:
                    # 检查是否是空行或注释
                    j = i + 1
                    while j < len(lines) and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                        j += 1

                    if j < len(lines):
                        actual_next_line = lines[j]
                        actual_indent = len(actual_next_line) - len(actual_next_line.lstrip())

                        # 如果实际代码行缩进不正确，修复从i+1到j的所有行
                        if actual_indent <= base_indent:
                            expected_indent = base_indent + 4
                            for k in range(i + 1, j + 1):
                                if lines[k].strip() and not lines[k].strip().startswith('#'):
                                    # 修复缩进
                                    original = lines[k]
                                    lines[k] = ' ' * expected_indent + lines[k].lstrip()
                                    if original != lines[k]:
                                        fixed_count += 1
                                        print(f"Fixed line {k + 1}: {repr(original.strip())} -> {repr(lines[k].strip())}")

        i += 1

    # 保存修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return fixed_count


if __name__ == '__main__':
    file_path = 'pyqt_ui/main.py'
    print(f"正在修复 {file_path} 的缩进错误...")
    print("-" * 60)

    fixed_count = fix_indentation_errors(file_path)

    print("-" * 60)
    print(f"✅ 修复完成！共修复 {fixed_count} 处缩进错误")

    # 验证语法
    print("\n正在验证Python语法...")
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        print("✅ 语法检查通过！")
    except py_compile.PyCompileError as e:
        print(f"❌ 语法错误仍然存在:")
        print(e)
