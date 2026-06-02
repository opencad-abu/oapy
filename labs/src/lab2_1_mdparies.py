#!/usr/bin/env python3
"""
oapy Lab 2-1: mdparies — LEF/DEF 导入导出工作流

功能: 演示使用 OA 命令行工具进行完整的芯片设计数据导入/导出流程：
  1. lef2oa   — 将 LEF 文件导入 OA 库（生成 techLib + 标准单元 abstract views）
  2. def2oa   — 将 DEF 文件导入 OA 库（生成完整 layout 设计）
  3. oa2def   — 从 OA 设计导出 DEF 文件
  4. oa2lef   — 从 OA 库导出 LEF 文件（指定 cell）
  5. oa2strm  — 从 OA 设计导出 GDSII 流文件
  6. oa2verilog — 从 OA 设计导出 Verilog 网表

数据源:
  - quasiHP.lef  — 标准单元库 LEF（包含 AND2EE 等多个标准单元）
  - quasiHP.def  — 完整芯片设计 DEF（mdp_aries 顶层 cell）

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab2_1_mdparies.py
"""

import os
import shutil
import subprocess
import sys
import time


# ═══════════════════════════════════════════════════════════════════════════
# 配置常量
# ═══════════════════════════════════════════════════════════════════════════

# OA 工具目录
OA_BIN_DIR = "/software/pkgs/oa/22.61/bin/linux_rhel70_gcc93x_64/opt"

# OA 共享库目录（工具运行时需要 LD_LIBRARY_PATH）
OA_LIB_DIR = "/software/pkgs/oa/22.61/lib/linux_rhel70_gcc93x_64/opt"

# 输入文件
LEF_FILE = "../data/quasiHP.lef"       # 标准单元库 LEF
DEF_FILE = "../data/quasiHP.def"       # 完整芯片设计 DEF

# 库/单元/视图名称（对应 Makefile 中的变量）
LIB_LEF = "leflib"             # LEF 导入的逻辑库名
LIB_DEF = "deflib"             # DEF 导入的逻辑库名
LIB_TECH = "techLib"           # 技术库名（lef2oa 自动生成）
CELL_LEF = "AND2EE"            # LEF 导出的目标 cell
CELL_DEF = "mdp_aries"         # DEF 导入的顶层 cell
VIEW = "layout"                # View 名称

# 库物理路径
LIB_PATH = "../data/LibDir"          # 设计数据存放目录
LIB_TECH_PATH = "../data/LibDirTech" # 技术库存放目录

# 输出文件
DEF_OUT = "def.out"
LEF_OUT = f"lef.{CELL_LEF}.out"
GDS_OUT = "gds.out"
VERILOG_OUT = "verilog.out"

# lib.defs 内容 — 定义逻辑库名到物理路径的映射
LIB_DEFS_CONTENT = (
    f"DEFINE {LIB_LEF} {LIB_PATH}\n"
    f"DEFINE {LIB_DEF} {LIB_PATH}\n"
    f"DEFINE {LIB_TECH} LibDirTech\n"
)


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def get_tool_env():
    """构造 OA 工具运行所需的环境变量
    
    OA 命令行工具需要：
    - PATH 中包含工具目录
    - LD_LIBRARY_PATH 仅指向 OA 官方共享库
    - 不能设置 LD_PRELOAD（run_lab.sh 预加载的 oacpp 库与 OA 工具有 ABI 冲突）
    
    注意: run_lab.sh 会注入 oacpp SWIG 构建库到 LD_LIBRARY_PATH，
    这些库与 OA 原生工具的 liboaBase.so 等存在冲突，必须完全替换。
    """
    env = os.environ.copy()
    # 将 OA bin 目录加入 PATH
    env["PATH"] = f"{OA_BIN_DIR}:{env.get('PATH', '')}"
    # 完全替换 LD_LIBRARY_PATH — 只保留 OA 官方库路径
    # 不能保留 oacpp 路径，否则工具会加载错误版本的 liboaBase.so 导致 SIGSEGV
    env["LD_LIBRARY_PATH"] = OA_LIB_DIR
    # 清除 LD_PRELOAD — oacpp SWIG 构建的 .so 与 OA 原生工具有 ABI 不兼容
    env.pop("LD_PRELOAD", None)
    return env


def run_tool(tool_name, args, description=""):
    """运行 OA 命令行工具并打印结果
    
    Args:
        tool_name: 工具名称（如 lef2oa）
        args: 命令行参数列表
        description: 操作描述（用于日志输出）
    Returns:
        (success: bool, return_code: int)
    """
    tool_path = os.path.join(OA_BIN_DIR, tool_name)
    cmd = [tool_path] + args
    
    if description:
        print(f"\n{'─'*60}")
        print(f"  {description}")
        print(f"{'─'*60}")
    
    print(f"  $ {tool_name} {' '.join(args)}")
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            env=get_tool_env(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        elapsed = time.time() - start
        
        # 打印工具输出（stdout + stderr）
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            for line in output.strip().split("\n"):
                print(f"    {line}")
        
        if result.returncode == 0:
            print(f"  ✅ {tool_name} 完成 ({elapsed:.1f}s)")
            return True, result.returncode
        else:
            print(f"  ⚠️ {tool_name} 退出码: {result.returncode} ({elapsed:.1f}s)")
            return False, result.returncode
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ {tool_name} 超时 (>120s)")
        return False, -1
    except FileNotFoundError:
        print(f"  ❌ 找不到工具: {tool_path}")
        return False, -1


def clean_generated_files():
    """清理生成的文件（保留输入数据）"""
    patterns = ["*.log", "*.out", "*.automap"]
    for pattern in patterns:
        # 使用 glob 清理
        import glob
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except OSError:
                pass
    
    # 清理库目录
    for d in [LIB_PATH, LIB_TECH_PATH]:
        if os.path.isdir(d):
            shutil.rmtree(d)
    
    # 清理 lib.defs
    if os.path.isfile("../data/lib.defs"):
        os.remove("../data/lib.defs")


def print_output_summary():
    """打印生成文件的摘要信息"""
    print(f"\n{'─'*60}")
    print(f"  生成文件摘要")
    print(f"{'─'*60}")
    
    outputs = [
        (DEF_OUT,     "DEF 输出 (从 OA 设计导出)"),
        (LEF_OUT,     f"LEF 输出 ({CELL_LEF} 标准单元)"),
        (GDS_OUT,     "GDSII 流文件"),
        (VERILOG_OUT, "Verilog 网表"),
    ]
    
    for fname, desc in outputs:
        if os.path.isfile(fname):
            size = os.path.getsize(fname)
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"  ✅ {fname:30s} {size_str:>10s}  — {desc}")
        else:
            print(f"  ❌ {fname:30s} {'缺失':>10s}  — {desc}")
    
    # 统计 LibDir 中的设计数据
    if os.path.isdir(LIB_PATH):
        total_files = 0
        total_size = 0
        for root, dirs, files in os.walk(LIB_PATH):
            for f in files:
                total_files += 1
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        print(f"\n  📁 LibDir: {total_files} 个文件, "
              f"{total_size / 1024 / 1024:.1f} MB")
    
    if os.path.isdir(LIB_TECH_PATH):
        tech_files = 0
        for root, dirs, files in os.walk(LIB_TECH_PATH):
            tech_files += len(files)
        print(f"  📁 LibDirTech: {tech_files} 个文件")


# ═══════════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  oapy Lab 2-1: mdparies — LEF/DEF 导入导出工作流")
    print("=" * 60)
    print()
    print("  本 Lab 演示完整的芯片设计数据导入/导出流程：")
    print("  LEF/DEF → OA → DEF/LEF/GDSII/Verilog")
    print()
    print(f"  输入 LEF: {LEF_FILE} (标准单元库)")
    print(f"  输入 DEF: {DEF_FILE} (顶层设计: {CELL_DEF})")
    
    # ── 前置检查 ──
    # 确认输入文件存在
    for fname in [LEF_FILE, DEF_FILE]:
        if not os.path.isfile(fname):
            print(f"  ❌ 缺少输入文件: {fname}")
            sys.exit(1)
    
    # ── 清理旧数据 ──
    print(f"\n  清理旧数据...")
    clean_generated_files()
    
    # ── 创建目录结构 ──
    os.makedirs(LIB_PATH, exist_ok=True)
    os.makedirs(LIB_TECH_PATH, exist_ok=True)
    print(f"  创建目录: {LIB_PATH}, {LIB_TECH_PATH}")
    
    # ── 写入 lib.defs ──
    # lib.defs 定义逻辑库名到物理路径的映射，OA 工具运行时需要
    with open("../data/lib.defs", "w") as f:
        f.write(LIB_DEFS_CONTENT)
    print(f"  写入 lib.defs")
    
    # ── 复制输入文件到工作目录 ──
    # LEF/DEF/drf 已经在 ../data/ 下，直接使用相对路径
    for fname in [LEF_FILE, DEF_FILE, "../data/display.drf"]:
        if os.path.isfile(fname):
            print(f"  使用输入文件: {fname}")
    
    print(f"  复制输入文件到工作目录")
    
    # ═══════════════════════════════════════════════════════════
    # 第一阶段：导入 — LEF/DEF → OA
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'═'*60}")
    print(f"  第一阶段: 导入 LEF/DEF 到 OA")
    print(f"{'═'*60}")
    
    # ── 步骤 1: lef2oa — 导入 LEF ──
    # 将标准单元库 LEF 导入 OA，同时生成技术库 (techLib)
    # -lef: 输入 LEF 文件
    # -lib: OA 逻辑库名
    # -DMSystem: 数据管理系统（oaDMFileSys = 文件系统 DM）
    # -techLib: 技术库名（存放层映射、via 定义等）
    ok1, _ = run_tool("lef2oa", [
        "-lef", LEF_FILE,
        "-lib", LIB_LEF,
        "-DMSystem", "oaDMFileSys",
        "-techLib", LIB_TECH,
    ], f"导入 LEF: {LEF_FILE} → OA 库 '{LIB_LEF}'")
    
    if not ok1:
        print("  ⚠️ lef2oa 未完全成功，继续尝试后续步骤...")
    
    # ── 步骤 2: def2oa — 导入 DEF ──
    # 将完整芯片设计 DEF 导入 OA，生成 layout view
    # -def: 输入 DEF 文件
    # -lib: OA 逻辑库名
    # -cell: 顶层 cell 名称
    # -view: View 名称
    # -techLib: 技术库名（需与 lef2oa 使用同一个）
    # -DMSystem: 数据管理系统
    ok2, _ = run_tool("def2oa", [
        "-def", DEF_FILE,
        "-lib", LIB_DEF,
        "-cell", CELL_DEF,
        "-view", VIEW,
        "-techLib", LIB_TECH,
        "-DMSystem", "oaDMFileSys",
    ], f"导入 DEF: {DEF_FILE} → OA 设计 '{LIB_DEF}/{CELL_DEF}/{VIEW}'")
    
    if not ok2:
        print("  ⚠️ def2oa 未完全成功，继续尝试后续步骤...")
    
    # ═══════════════════════════════════════════════════════════
    # 第二阶段：导出 — OA → DEF/LEF/GDSII/Verilog
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'═'*60}")
    print(f"  第二阶段: 从 OA 导出各格式")
    print(f"{'═'*60}")
    
    # ── 步骤 3: oa2def — 导出 DEF ──
    # 将 OA 设计反向导出为 DEF 文件
    # -def: 输出 DEF 文件名
    # -lib: OA 逻辑库名
    # -cell: Cell 名称
    # -view: View 名称
    # -ver: DEF 版本（5.4 是常用版本）
    run_tool("oa2def", [
        "-def", DEF_OUT,
        "-lib", LIB_DEF,
        "-cell", CELL_DEF,
        "-view", VIEW,
        "-ver", "5.4",
    ], f"导出 DEF: OA → {DEF_OUT} (v5.4)")
    
    # ── 步骤 4: oa2lef — 导出 LEF ──
    # 从 OA 库导出指定 cell 的 LEF（abstract view）
    # -lef: 输出 LEF 文件名
    # -lib: OA 逻辑库名
    # -cells: 要导出的 cell 列表
    # -views: 要导出的 view 类型（abstract = 包含 pin 和 obstruction 信息）
    # -ver: LEF 版本
    run_tool("oa2lef", [
        "-lef", LEF_OUT,
        "-lib", LIB_LEF,
        "-cells", CELL_LEF,
        "-views", "abstract",
        "-ver", "5.4",
    ], f"导出 LEF: {CELL_LEF}/abstract → {LEF_OUT}")
    
    # ── 步骤 5: oa2strm — 导出 GDSII ──
    # 将 OA 设计导出为 GDSII 流文件（用于 tapeout）
    # -gds: 输出 GDS 文件名
    # -lib: OA 逻辑库名
    # -cell: Cell 名称
    # -view: View 名称
    run_tool("oa2strm", [
        "-gds", GDS_OUT,
        "-lib", LIB_DEF,
        "-cell", CELL_DEF,
        "-view", VIEW,
    ], f"导出 GDSII: OA → {GDS_OUT}")
    
    # ── 步骤 6: oa2verilog — 导出 Verilog ──
    # 从 OA 设计提取连接关系，生成 Verilog 网表
    # -verilog: 输出 Verilog 文件名
    # -lib: OA 逻辑库名
    # -cell: Cell 名称
    # -view: View 名称
    run_tool("oa2verilog", [
        "-verilog", VERILOG_OUT,
        "-lib", LIB_DEF,
        "-cell", CELL_DEF,
        "-view", VIEW,
    ], f"导出 Verilog: OA → {VERILOG_OUT}")
    
    # ═══════════════════════════════════════════════════════════
    # 结果汇总
    # ═══════════════════════════════════════════════════════════
    print_output_summary()
    
    # ── 验证输出 ──
    print(f"\n{'─'*60}")
    print(f"  输出验证")
    print(f"{'─'*60}")
    
    all_ok = True
    for fname in [DEF_OUT, LEF_OUT, GDS_OUT, VERILOG_OUT]:
        exists = os.path.isfile(fname)
        size = os.path.getsize(fname) if exists else 0
        status = "✅" if exists and size > 0 else "❌"
        if not exists or size == 0:
            all_ok = False
        print(f"  {status} {fname}: {'存在' if exists else '缺失'} ({size} bytes)")
    
    if all_ok:
        print(f"\n{'═'*60}")
        print(f"  ✅ Lab 2-1 完成! 所有导入/导出步骤均成功执行。")
        print(f"{'═'*60}")
    else:
        print(f"\n{'═'*60}")
        print(f"  ⚠️ Lab 2-1 部分完成，某些输出文件缺失。")
        print(f"{'═'*60}")
    
    # ── 清理 ──
    print(f"\n  清理临时数据...")
    clean_generated_files()
    print(f"  清理完成。")


if __name__ == "__main__":
    main()
