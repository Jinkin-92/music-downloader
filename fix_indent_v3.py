#!/usr/bin/env python3
"""
使用AST和tokenize完全重构缩进
"""

import ast
import re
from copy import deepcopy


def detect_and_fix_indent_issues(file_path):
    """检测并修复缩进问题"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines(keepends=True)

    # 尝试解析，收集错误信息
    try:
        ast.parse(content)
        print("File syntax is already correct!")
        return 0
    except IndentationError as e:
        print(f"Found IndentationError at line {e.lineno}: {e.msg}")
        error_line = e.lineno
    except SyntaxError as e:
        print(f"Found SyntaxError at line {e.lineno}: {e.msg}")
        error_line = e.lineno

    # 系统化地检查和修复常见缩进错误
    fixed_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测控制流语句（以冒号结尾）
        if re.match(r'^(\s*)(if|else|elif|for|while|def|class|try|except|finally|with|async).*:\s*$', line):
            base_indent = len(line) - len(line.lstrip())

            # 查找下一个非空行
            j = i + 1
            while j < len(lines) and (lines[j].strip() == '' or lines[j].lstrip().startswith('#')):
                j += 1

            if j < len(lines):
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip())

                # 检查是否需要增加缩进
                # 如果下一行的缩进 <= base_indent，且不是def/class（它们应该同级）
                is_structural = re.match(r'^\s*(def|class|else|elif|except|finally)\s', line)

                if not is_structural and next_indent <= base_indent:
                    # 需要增加缩进
                    expected_indent = base_indent + 4

                    # 检查是否有连续的代码块需要修复
                    k = j
                    while k < len(lines):
                        current_line = lines[k]
                        if current_line.strip() == '' or current_line.lstrip().startswith('#'):
                            k += 1
                            continue

                        current_indent = len(current_line) - len(current_line.lstrip())

                        # 如果缩进小于等于基础缩进，说明代码块结束
                        if current_indent <= base_indent:
                            break

                        # 修复这一行
                        if current_indent < expected_indent:
                            lines[k] = ' ' * expected_indent + current_line.lstrip()
                            print(f"Fixed line {k+1}")
                            fixed_count += 1
                        elif current_indent > expected_indent and current_indent < base_indent + 8:
                            # 缩进过大，调整到正确级别
                            lines[k] = ' ' * expected_indent + current_line.lstrip()
                            print(f"Adjusted line {k+1}")
                            fixed_count += 1

                        k += 1

        i += 1

    # 保存修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    return fixed_count


def iterative_fix(file_path, max_iterations=10):
    """迭代修复直到没有错误或达到最大迭代次数"""

    for iteration in range(max_iterations):
        print(f"\n=== Iteration {iteration + 1} ===")

        # 尝试解析
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            ast.parse(content)
            print("SUCCESS: File syntax is correct!")
            return True
        except (IndentationError, SyntaxError) as e:
            print(f"Error at line {e.lineno}: {e.msg}")

            # 尝试修复
            fixed = detect_and_fix_indent_issues(file_path)
            print(f"Fixed {fixed} issues in this iteration")

            if fixed == 0:
                print("No more fixes applied, but errors still exist.")
                return False

    print("Reached maximum iterations without success.")
    return False


if __name__ == '__main__':
    file_path = 'pyqt_ui/main.py'

    print("Starting iterative indentation fix...")
    success = iterative_fix(file_path)

    if success:
        print("\n" + "="*60)
        print("SUCCESS! File has been fixed.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("Could not automatically fix all errors.")
        print("Manual intervention may be required.")
        print("="*60)
