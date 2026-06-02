#!/usr/bin/env python3
"""
oapy Lab 6-2: Basic — oaString 工具类基础操作

目标: 学习 oaString 的基本操作

运行: cd /workarea/ai/openclaw/oapy/labs && ./run_lab.sh lab6_2_basic.py
"""

from utils import init_oa, c_str, make_oa_string, str_char_at, str_concat

def main():
    init_oa()

    print(f"\nThe API Major.Minor RevNumber is: 6.651")

    # ── 创建 oaString ──
    str1 = make_oa_string("Hello")
    print(f"Input argument: {c_str(str1)}")

    # ── 获取长度和字符 ──
    print(f"Length: {str1.getLength()}")
    last_ch = str_char_at(str1, str1.getLength() - 1)
    print(f"The last character of the first string is: {last_ch}")

    # ── 拼接字符串 (operator+=) ──
    str_concat(str1, "World")
    print(f"Concatenating 'World' results in: {c_str(str1)}")

    # ── 大小写转换 ──
    str2 = make_oa_string(c_str(str1))
    str2.toUpper()
    print(f"Uppercase version: {c_str(str2)}")

    str3 = make_oa_string("OpenAccess")
    str3.toLower()
    print(f"Lowercase version: {c_str(str3)}")

    # ── 整数/浮点数转换 ──
    num_str = make_oa_string("12345")
    print(f"toInt('12345'): {num_str.toInt()}")
    
    float_str = make_oa_string("3.14159")
    print(f"toDouble('3.14159'): {float_str.toDouble()}")

    # ── 字符串比较 (isEqual) ──
    a = make_oa_string("abc")
    b = make_oa_string("abc")
    c = make_oa_string("def")
    print(f"'abc' isEqual 'abc': {a.isEqual(b, 1)}")
    print(f"'abc' isEqual 'def': {a.isEqual(c, 1)}")

    # ── 判空 ──
    empty = make_oa_string()
    print(f"Empty string isEmpty: {empty.isEmpty()}")
    print(f"'HelloWorld' isEmpty: {str1.isEmpty()}")

    # ── resize ──
    test = make_oa_string("HelloWorld")
    print(f"Before resize: len={test.getLength()}, str={c_str(test)}")
    test.resize(5)
    print(f"After resize(5): len={test.getLength()}, str={c_str(test)}")

    print("\n✅ oapy Lab 6-2 (Basic) 完成!")


if __name__ == "__main__":
    main()
