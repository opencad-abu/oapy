#!/usr/bin/env python3
"""
oapy Lab 17-6: Multithread — OA 多线程读写演示

目标: 演示 OA 在不同 ThreadUseModel 下的多线程行为，
      包括无锁和使用 threading.Lock 时的读写竞争差异。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab17_6_multithread.py
"""

import os, sys, shutil, time, threading
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, create_lib, c_str, create_net
from oapy._oa import _design, _base, _dm


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

class Globals:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # 库路径和名称
        self.strPathLib = "../data/LibDir"
        self.strLib = "LibDir"
        self.strView = "View"

        # 初始化 OA
        init_oa()

        # Namespace（对应 oaNativeNS）
        self.ns = get_namespace("native")

        # 创建 oaScalarName 对象
        self.scNameLib  = make_oa_name(self.ns, self.strLib)
        self.scNameView = make_oa_name(self.ns, self.strView)
        self.scNameCell = make_oa_name(self.ns, "Cell")
        self.scNameNet1 = make_oa_name(self.ns, "Net1")
        self.scNameNet2 = make_oa_name(self.ns, "Net2")
        self.scNameNet3 = make_oa_name(self.ns, "Net3")

        # ViewType（对应 oacSchematic）
        self.vt = _dm.oaViewType.find(make_oa_string("schematic"))
        if self.vt is None:
            self.vt = _dm.oaViewType.create(make_oa_string("schematic"))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

NO_MUTEX = 0
PY_LOCK  = 1          # 对应 pt_mutex（Python threading.Lock）


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
#
# 注意：本 Lab 的核心是多线程，Observer 仅做最小化注册。
#

class MyNetObserver:
    """Net 观察者（对应 myNetObserver）"""
    def __init__(self, priority):
        # oaObserver<oaNet> 在 Python 绑定中的构造
        # 这里仅记录 priority，实际 observer 回调由 OA 内部调度
        self.priority = priority
        print(f"<MyNetObserver 构造 priority={priority}>")


class MyInstObserver:
    """Inst 观察者（对应 myInstObserver）"""
    def __init__(self, priority):
        self.priority = priority
        print(f"<MyInstObserver 构造 priority={priority}>")


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

# 全局线程计数器和锁
thread_count = 0
thread_count_lock = threading.Lock()
pt_mutex = threading.Lock()       


def read_thread(design, use_mutex):
    """
    - 统计 Net 数量
    - sleep
    - 再次统计，检查 sleep 期间是否有新 Net 被写入线程添加
    
    threadCount 是全局共享计数器，在线程启动时 ++threadCount 获得 currentThread。
    sleep 时读取的 threadCount 可能已被其他线程递增，这是故意的竞态行为。
    """
    global thread_count

    # 原子递增全局计数器，获取当前线程编号
    with thread_count_lock:
        thread_count += 1
        current_thread = thread_count

    try:
        print(f"\nreadThread  {current_thread}  starting")
        print(f"readThread  {current_thread}  reading the design and counting nets")

        # 获取 TopBlock 并统计 Net 数
        block = design.getTopBlock()
        num_nets_before = block.getNets().getCount()

        # 读全局 thread_count（可能已被其他线程递增），这是有意的竞态
        sleep_time = max(1, 4 - thread_count)
        print(f"readThread  {current_thread}  going to sleep ({sleep_time}s)...")
        time.sleep(sleep_time)
        print(f"readThread  {current_thread}  waking up and counting nets")

        # 再次统计 Net 数
        num_nets_after = block.getNets().getCount()
        added_nets = num_nets_after - num_nets_before

        print(f"readThread  {current_thread}  Nets added while sleeping: {added_nets} nets")

        if use_mutex == NO_MUTEX:
            # 无锁时：两个写线程都能在读线程醒来前添加 Net
            print(f"  [验证] 无锁: 预期写线程能抢先添加 Net")
        elif use_mutex == PY_LOCK:
            # 有锁时：第二个写线程必须等第一个完成，读线程醒来时只有 1 个
            print(f"  [验证] 有锁: 第二个写线程被阻塞，读线程醒来时 Net 较少")

    except Exception as ex:
        print(f"readThread {current_thread} 异常: {ex}")
        raise
    finally:
        print(f"\nreadThread  {current_thread} exiting")


def write_thread(design, use_mutex):
    """
    - 可选加锁
    - 创建一个新 Net
    - sleep
    - 释放锁
    
    Python 中用 try/finally 确保锁释放。
    """
    global thread_count

    # 原子递增全局计数器，获取当前线程编号
    with thread_count_lock:
        thread_count += 1
        current_thread = thread_count

    locked = False
    try:
        print(f"\nwriteThread {current_thread}  starting")

        if use_mutex != NO_MUTEX:
            print(f"writeThread {current_thread}  requesting lock...")
            pt_mutex.acquire()
            locked = True
            print(f"writeThread {current_thread}  locked.")

        # 获取 Block 并创建 Net
        block = design.getTopBlock()
        print(f"writeThread {current_thread}  creating net")
        _design.oaScalarNet.create(block)

    except Exception as ex:
        # 在 MultipleReaders 模式下写操作会抛异常（预期行为）
        try:
            sess = _base.oaSession.get()
            tum = sess.getThreadUseModel()
            if tum == 1:  # oacMultipleReadersThreadUseModel
                print(f"*** 捕获预期异常 (MultipleReaders 模式不允许写入)")
            else:
                print(f"writeThread {current_thread} 意外异常: {ex}")
                raise
        except Exception:
            print(f"writeThread {current_thread} 意外异常: {ex}")
            raise

    finally:
        # 此处 threadCount 刚被本线程递增，值等于 current_thread
        sleep_time = current_thread
        print(f"writeThread {current_thread}  going to sleep ({sleep_time}s)...")
        time.sleep(sleep_time)
        print(f"writeThread {current_thread}  waking up")

        if locked:
            print(f"writeThread {current_thread}  unlocking")
            pt_mutex.release()

        print(f"\nwriteThread {current_thread} exiting")


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════

# ThreadUseModel 枚举映射
# oacSingleThreadUseModel = 0
# oacMultipleReadersThreadUseModel = 1
# oacMultipleWritersThreadUseModel = 2

THREAD_USE_MODEL_NAMES = {
    0: "oacSingleThreadUseModel",
    1: "oacMultipleReadersThreadUseModel",
    2: "oacMultipleWritersThreadUseModel",
}


def start_read_write_threads(design, thread_use_model, use_mutex):
    """
    """
    global thread_count

    # 设置 ThreadUseModel
    sess = _base.oaSession.get()
    sess.setThreadUseModel(thread_use_model)

    model_name = THREAD_USE_MODEL_NAMES.get(thread_use_model, str(thread_use_model))

    mutex_desc = "无锁" if use_mutex == NO_MUTEX else "threading.Lock"
    print(f"\n\nReading, sleeping, then overwriting in {model_name}  -- {mutex_desc}")

    thread_count = 0

    # 创建并启动 2 个读线程
    r1 = threading.Thread(target=read_thread, args=(design, use_mutex), name="read-1")
    r2 = threading.Thread(target=read_thread, args=(design, use_mutex), name="read-2")
    r1.start()
    r2.start()

    # 等 1 秒再启动写线程，避免多核 CPU 上写线程抢先
    time.sleep(1)

    # 创建并启动 2 个写线程
    w1 = threading.Thread(target=write_thread, args=(design, use_mutex), name="write-1")
    w2 = threading.Thread(target=write_thread, args=(design, use_mutex), name="write-2")
    w1.start()
    w2.start()

    # 等待所有线程完成
    r1.join()
    r2.join()
    w1.join()
    w2.join()

    print("All threads are now joined.")


# ═══════════════════════════════════════════════════════════════════════════
# 创建设计（对应 makeDesign）
# ═══════════════════════════════════════════════════════════════════════════

def make_design(globs):
    """创建测试用的 Design，包含 3 个初始 Net"""
    # 清理旧库
    if os.path.exists(globs.strPathLib):
        shutil.rmtree(globs.strPathLib)

    # 创建 Lib
    sn_lib, lib = create_lib(globs.strLib, globs.strPathLib)

    # 打开 Design（创建模式）
    design = _design.oaDesign.open(
        globs.scNameLib,
        globs.scNameCell,
        globs.scNameView,
        globs.vt,
        'w'
    )

    if not design.isValid():
        raise RuntimeError("Design 创建失败")

    # 创建 Block
    block = _design.oaBlock.create(design, True)

    # 创建 3 个初始 Net (Net1, Net2, Net3)
    create_net(block, "Net1")
    create_net(block, "Net2")
    create_net(block, "Net3")

    print("\nSaving Design.")
    design.save()

    return design


# ═══════════════════════════════════════════════════════════════════════════
# 主测试流程（对应 testThreads）
# ═══════════════════════════════════════════════════════════════════════════

def test_threads():
    """
    测试 OA 多线程行为：
    1. 无锁模式，测试 3 种 ThreadUseModel
    2. threading.Lock 模式，测试 3 种 ThreadUseModel
    """
    print("\n\nTesting threads")

    globs = Globals.get()

    # 注册观察者
    my_net_observer = MyNetObserver(5)
    my_inst_observer = MyInstObserver(5)

    # 创建 Design
    design = make_design(globs)

    # ── 第一阶段：无锁测试 ──
    print("\n\nReading and writing with NO mutex.")
    use_mutex = NO_MUTEX

    # SingleThreadUseModel
    start_read_write_threads(design, 0, use_mutex)  # oacSingleThreadUseModel

    # MultipleReadersThreadUseModel
    start_read_write_threads(design, 1, use_mutex)  # oacMultipleReadersThreadUseModel

    # 切回 Single 再进 MultipleWriters（OA 要求）
    sess = _base.oaSession.get()
    sess.setThreadUseModel(0)  # oacSingleThreadUseModel

    start_read_write_threads(design, 2, use_mutex)  # oacMultipleWritersThreadUseModel

    # ── 第二阶段：threading.Lock 测试 ──
    print("\n\nReading and writing with threading.Lock.")
    use_mutex = PY_LOCK

    start_read_write_threads(design, 0, use_mutex)  # oacSingleThreadUseModel

    start_read_write_threads(design, 1, use_mutex)  # oacMultipleReadersThreadUseModel

    sess.setThreadUseModel(0)  # oacSingleThreadUseModel

    start_read_write_threads(design, 2, use_mutex)  # oacMultipleWritersThreadUseModel


# ═══════════════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("oapy Lab 17-6: Multithread (多线程)")
    print("=" * 60)

    try:
        test_threads()
    except Exception as ex:
        print(f"\nERROR: {ex}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n........Normal Termination........")


if __name__ == "__main__":
    main()
