#!/usr/bin/env python3
"""完全重写缩进修复策略"""

import re


def get_line_indent(line):
    """获取行缩进级别"""
    return len(line) - len(line.lstrip())


def fix_file_indentation(file_path):
    """修复文件缩进"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    fixes = []

    while i < len(lines):
        line = lines[i]

        # 检测控制流关键字
        stripped = line.strip()
        if (stripped.endswith(':') and
            any(stripped.startswith(kw) for kw in
                ['if ', 'else', 'elif', 'for ', 'while ', 'def ', 'class ', 'try:', 'except',
                 'finally', 'with ', 'async def', 'async for'])):

            base_indent = get_line_indent(line)
            expected_next_indent = base_indent + 4

            # 查找下一个非空、非注释行
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() and not next_line.strip().startswith('#'):
                    break
                j += 1

            if j < len(lines):
                next_indent = get_line_indent(lines[j])

                # 如果下一行缩进不足，需要修复
                if next_indent <= base_indent:
                    # 修复从j开始到遇到同级或更小缩进的所有行
                    k = j
                    while k < len(lines):
                        current_line = lines[k]
                        if not current_line.strip() or current_line.strip().startswith('#'):
                            k += 1
                            continue

                        current_indent = get_line_indent(current_line)

                        # 遇到同级或更小缩进，停止
                        if current_indent <= base_indent:
                            break

                        # 修复缩进
                        if current_indent < expected_next_indent:
                            lines[k] = ' ' * expected_next_indent + current_line.lstrip()
                            fixes.append((k + 1, current_line.strip(), lines[k].strip()))
                        elif current_indent > expected_next_indent and current_indent < expected_next_indent + 4:
                            # 缩进在中间，调整到正确位置
                            lines[k] = ' ' * expected_next_indent + current_line.lstrip()
                            fixes.append((k + 1, current_line.strip(), lines[k].strip()))

                        k += 1

        i += 1

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return fixes


if __name__ == '__main__':
    import sys

    file_path = 'pyqt_ui/main.py'
    print(f"Fixing {file_path}...")

    total_fixes = 0
    iteration = 0

    while iteration < 20:
        print(f"\n--- Iteration {iteration + 1} ---")

        # 测试语法
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, file_path, 'exec')
            print("SUCCESS: File is now syntactically correct!")
            break
        except (IndentationError, SyntaxError) as e:
            print(f"Syntax error: line {e.lineno}: {e.msg}")

        # 尝试修复
        fixes = fix_file_indentation(file_path)
        print(f"Applied {len(fixes)} fixes")
        for line_num, before, after in fixes[:5]:
            print(f"  Line {line_num}")
        if len(fixes) > 5:
            print(f"  ... and {len(fixes) - 5} more")

        total_fixes += len(fixes)

        if len(fixes) == 0:
            print("No fixes applied, but errors remain.")
            sys.exit(1)

        iteration += 1

    print(f"\nTotal fixes applied: {total_fixes}")
