#!/usr/bin/env python3
"""
Lab 17-7: ThreadWriters — 多线程写入测试

功能:
  - 使用 Python threading 模块创建多个工作线程
  - 每个线程独立编辑自己的 Design（创建 Net、Term、Pin、Module、Inst）
  - 所有线程共享同一个 AND gate Design 进行实例化（测试 OA 的 MT 安全性）
  - 使用 oacMultipleWritersThreadUseModel 启用多线程写入
  - 两轮线程执行，每轮 10 个线程并发写入
  - 打印各对象类别的计数以观察线程交错

运行: cd /workarea/ai/openclaw/oapy && bash labs/run_lab.sh labs/lab17_7_threadwriters.py
"""

import os
import sys
import threading
import sched as _sched

# 路径设置
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from oapy._oa import _base, _design, _dm


# ============================================================================
# 常量定义
# ============================================================================
MAX_THREADS = 10           # 线程数量（也是每线程的迭代次数）
INSTS_PER_ITER = 20        # 每次迭代创建的实例数 (2 * MAX_THREADS)
CELL_NAME = "somecell"     # 每个线程使用的 cell 名称
VIEW_PREFIX = "someview"   # view 名称前缀


# ============================================================================
# ============================================================================
class SharedData:
    """
    线程共享数据：
    - andgate: 所有线程共享的 AND gate Design（用于实例化）
    - isOAbuildBefore011: OA 构建版本是否早于 22.41.011（用于 bug workaround）
    - isOAbuildBefore008: OA 构建版本是否早于 22.41.008（用于 bug workaround）
    """
    andgate = None
    isOAbuildBefore011 = False
    isOAbuildBefore008 = False


# ============================================================================
# 辅助函数
# ============================================================================
def print_count(thread_id: int, descrip: str, count: int):
    """
    打印指定线程的对象计数。
    格式: "类别{线程ID}=数量 "。
    """
    print(f"{descrip}{{{thread_id}}}={count} ", end="", flush=True)


def print_error_message(thread_id: int, exc):
    """
    打印线程中的异常信息。
    """
    print(f"thread[{thread_id}] UNEXPECTED EXCEPTION: {exc}", flush=True)


# ============================================================================
# 线程函数
# ============================================================================
def thread_func(thread_id: int, design):
    """

    每个线程：
    1. 获取自己被分配的 Design 和对应的 Block
    2. 在 10 次迭代中，每次创建：
       - 1 个 oaScalarNet（网络）
       - 1 个 oaScalarTerm（端口，基于当前 Term 数量命名）
       - 1 个 oaPin（引脚）
       - 1 个 oaModule（模块）
       - 1 个 oaRect（矩形形状，如果 OA 版本 >= 22.41.008）
       - 20 个 oaScalarInst（AND gate 实例）
    3. 打印各类别的当前计数

    但 OA 的 MultipleWritersThreadUseModel 保证了多线程写入的安全性。
    """
    try:
        # 获取线程对应的 Design 和 Block
        ns = _base.oaNativeNS()
        block = design.getTopBlock()

        # 如果 Block 尚未创建（在 OA 早期版本中可能已在主线程创建）
        if block is None:
            block = _design.oaBlock.create(design, True)

        # 获取 view 名称用于打印标识
        # getViewName(ns) 返回 str，getViewName() 返回 oaScalarName
        view_name = design.getViewName(ns)

        # 打印线程开始标识: [view名{线程ID}
        print(f"\n[{view_name}{{{thread_id}}}\n", end="", flush=True)

        # 主循环：迭代 MAX_THREADS 次
        # 注意：oapy 的 getTerms/getNets/getInsts 需要域索引参数 (domain=0)
        for ix in range(MAX_THREADS):
            # 基于当前 Term 数量生成端口名称（oapy 的 oaScalarName 需要 Python str）
            term_count = block.getTerms(0).getCount()
            name_count = str(term_count)

            # --- 创建各类 OA 对象 ---

            # 创建网络（Net）
            net = _design.oaScalarNet.create(block)

            # 创建端口（Term），以当前 Term 数量命名
            term = _design.oaScalarTerm.create(
                net, _base.oaScalarName(ns, name_count)
            )

            # 创建引脚（Pin）
            pin = _design.oaPin.create(term)

            # 创建模块（Module）
            _design.oaModule.create(design)

            # 创建矩形形状（Rect），仅在 OA 版本 >= 22.41.008 时
            # 早期版本存在 oaLPPHeaderTbl::find() 断言失败的 bug
            if not SharedData.isOAbuildBefore008:
                rect = _design.oaRect.create(
                    block, 6, 7, _base.oaBox(-10, -11, 20, 23)
                )
                rect.addToPin(pin)

            # 创建多个 AND gate 实例（Inst）
            # 所有线程共享同一个 AND gate Design，测试 OA 的 MT 安全性
            xform000 = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))
            param_arr = _base.oaParamArray(0)
            bv_enum = _design.oaBlockDomainVisibilityEnum
            ps_enum = _design.oaPlacementStatusEnum
            for _ in range(INSTS_PER_ITER):
                inst_count = block.getInsts(0).getCount()
                inst_name = str(inst_count)
                _design.oaScalarInst.create(
                    block,
                    SharedData.andgate,
                    _base.oaScalarName(ns, inst_name),
                    xform000,
                    param_arr,
                    _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
                    _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus)
                )

            # --- 打印各类别计数 ---
            print_count(thread_id, "Modules", design.getModules().getCount())
            print_count(thread_id, "Nets", block.getNets(0).getCount())
            print_count(thread_id, "Terms", block.getTerms(0).getCount())
            print_count(thread_id, "Shapes", block.getShapes().getCount())
            print_count(thread_id, "Pins", block.getPins().getCount())
            print_count(thread_id, "Insts", block.getInsts(0).getCount())

        # 打印线程结束标识: {线程ID}]
        print(f"\n{{{thread_id}}}]\n", end="", flush=True)

    except _base.OAException as exc:
        print_error_message(thread_id, exc)
        sys.exit(1)
    except Exception as exc:
        print_error_message(thread_id, exc)
        sys.exit(1)


# ============================================================================
# 线程管理
# ============================================================================
def run_bunch_of_threads(threads_data: list):
    """
    启动一批工作线程并等待它们全部完成。



    步骤：
    1. 设置 OA 线程使用模型为 oacMultipleWritersThreadUseModel
    2. 创建并启动所有线程
    3. 等待所有线程完成（join）
    4. 打印 join 进度指示符 "Nj"

    参数:
        threads_data: 包含 (thread_id, design) 元组的列表
    """
    # 设置 OA 多线程写入模型
    # 这告诉 OA 允许多个线程同时写入不同的 Design
    session = _base.oaSession.get()
    tmodel = _base.oaThreadUseModel(
        _base.oaThreadUseModelEnum.oacMultipleWritersThreadUseModel
    )
    session.setThreadUseModel(tmodel)

    # 创建并启动所有线程
    threads = []
    for thread_id, design in threads_data:
        t = threading.Thread(target=thread_func, args=(thread_id, design))
        threads.append((thread_id, t))
        t.start()

    # 等待所有线程完成
    for thread_id, t in threads:
        t.join()
        # 打印 join 进度: "0j1j2j..."
        print(f"{thread_id}j", end="", flush=True)
    print()  # 换行


# ============================================================================
# 主函数
# ============================================================================
def main():
    """


    流程：
    1. 初始化 OA 设计系统
    2. 创建/打开库，创建共享的 AND gate Design
    3. 为每个线程创建独立的 Design
    4. 检查 OA 构建版本以启用 bug workaround
    5. 运行两轮多线程写入测试
    """
    print("=" * 60)
    print("oapy Lab 17-7: ThreadWriters — 多线程写入测试")
    print("=" * 60)

    try:
        # --- 初始化 OA ---
        _design.oaDesignInit()
        ns = _base.oaNativeNS()

        # --- 设置库路径和名称 ---
        lib_dir = os.path.join(
            os.path.dirname(__file__), "../data/LibDir"
        )
        os.makedirs(lib_dir, exist_ok=True)
        lib_name = "LibTest"

        st_lib = _base.oaScalarName(ns, lib_name)
        str_path_lib = _base.oaString(lib_dir)

        # 打开或创建库
        lib_mode = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
        if _dm.oaLib.exists(str_path_lib):
            # oaLib.open 需要 (name, path, accessPath, mode)
            lib = _dm.oaLib.open(st_lib, str_path_lib, str_path_lib, lib_mode)
        else:
            lib = _dm.oaLib.create(
                st_lib, str_path_lib,
                lib_mode,
                _base.oaString("oaDMFileSys")
            )

        # --- 获取或创建 Netlist 视图类型 ---
        vt = _dm.oaViewType.find(_base.oaString("netlist"))
        if vt is None:
            vt = _dm.oaViewType.create(_base.oaString("netlist"))

        # --- 创建共享的 AND gate Design ---
        # 所有线程将实例化这个 Design，测试 OA 的 MT 安全性
        sn_and = _base.oaScalarName(ns, "and")
        sn_abstract = _base.oaScalarName(ns, "abstract")
        SharedData.andgate = _design.oaDesign.open(
            st_lib, sn_and, sn_abstract, vt, 'w'
        )
        _design.oaBlock.create(SharedData.andgate, True)
        SharedData.andgate.save()

        # --- 检查 OA 构建版本 ---
        # OA 22.61 远晚于 22.41.011，无需早期版本的 bug workaround
        SharedData.isOAbuildBefore011 = False
        SharedData.isOAbuildBefore008 = False
        print("\nNOTE: OA 22.61 - Create Block in MultipleWritersThreadUseModel")
        print("NOTE: OA 22.61 - Create Rect in MultipleWritersThreadUseModel")

        # --- 为每个线程创建独立的 Design ---
        sn_cell = _base.oaScalarName(ns, CELL_NAME)
        threads_data = []  # 存储 (thread_id, design) 元组

        for ix in range(MAX_THREADS):
            view_name = f"{VIEW_PREFIX}{ix}"
            sn_view = _base.oaScalarName(ns, view_name)

            # 打开 Design 用于写入
            design = _design.oaDesign.open(st_lib, sn_cell, sn_view, vt, 'w')

            # 在 OA 早期版本中，Block 必须在切换到多线程模型之前创建
            # 以避免断言崩溃
            if SharedData.isOAbuildBefore011:
                _design.oaBlock.create(design, True)

            threads_data.append((ix, design))
            design.save()

        # --- 运行两轮多线程写入 ---
        # 第一轮
        print("\n--- 第一轮多线程写入 ---")
        run_bunch_of_threads(threads_data)

        # 第二轮
        print("\n--- 第二轮多线程写入 ---")
        run_bunch_of_threads(threads_data)

    except _base.OAException as exc:
        print(f"UNEXPECTED EXCEPTION[{exc.getMsgId()}]: {exc.getMsg()}")
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED EXCEPTION: {exc}")
        sys.exit(1)

    print("\n.........end.......")
    print("=" * 60)
    print("✅ Lab 17-7 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
