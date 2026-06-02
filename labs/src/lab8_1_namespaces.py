#!/usr/bin/env python3
"""
oapy Lab 8-1: Namespaces — 命名空间与名称映射

目标: 测试不同 NameSpace 下的名称创建和映射

运行: cd /workarea/ai/openclaw/oapy/labs && ./run_lab.sh lab8_1_namespaces.py
"""

from utils import init_oa, c_str, make_oa_string, make_oa_name, get_namespace

def main():
    init_oa()

    # 测试名称
    test_names = [
        "Bus[3:0]",
        "clk",
        "rst_n",
        "data_in[7:0]",
        "my_sig",
    ]

    # 命名空间列表 (跳过 def — oaDefNS 无构造函数)
    namespaces = [
        ("native", get_namespace("native")),
        ("unix", get_namespace("unix")),
        ("win", get_namespace("win")),
        ("lef", get_namespace("lef")),
        ("verilog", get_namespace("verilog")),
        ("vhdl", get_namespace("vhdl")),
    ]

    print("=" * 60)
    print("oapy Lab 8-1: Namespace 名称映射测试")
    print("=" * 60)

    for test_name in test_names:
        print(f"\n--- 输入名称: '{test_name}' ---")
        for ns_name, ns in namespaces:
            try:
                name = make_oa_name(ns, test_name)
                # 获取名称的字符串表示
                name_str = c_str(make_oa_string(str(name))) if hasattr(name, '__str__') else str(type(name))
                print(f"  {ns_name:10s} → oaScalarName created")
            except Exception as e:
                print(f"  {ns_name:10s} → ERROR: {e}")

    # 测试特殊字符
    print(f"\n--- 特殊字符测试 ---")
    special_names = ["a;b", "c$d", "e^f", "g#h"]
    ns = get_namespace("native")
    for sn in special_names:
        try:
            name = make_oa_name(ns, sn)
            print(f"  'native' + '{sn}' → OK")
        except Exception as e:
            print(f"  'native' + '{sn}' → ERROR: {e}")

    # 测试 namespace 类型
    print(f"\n--- Namespace 类型测试 ---")
    for ns_name, ns in namespaces:
        print(f"  {ns_name}: type={type(ns).__name__}")

    print("\n✅ oapy Lab 8-1 (Namespaces) 完成!")


if __name__ == "__main__":
    main()
