#!/usr/bin/env python3
"""
Lab 17-5: 线程使用模型 (Thread Use Model)

本示例演示 OpenAccess 的线程使用模型。
注意：这里不使用多线程，仅展示如何设置和重置线程模型。

线程模型类型：
- oacSingleThreadUseModel: 单线程模式
- oacMultipleReadersThreadUseModel: 多读线程模式（只读）
- oacMultipleWritersThreadUseModel: 多写线程模式
"""

import os
import sys
import shutil

# 导入工具函数和 OA 绑定
from utils import init_oa, c_str, make_oa_string, make_oa_name, get_namespace
from oapy._oa import _base, _dm, _design


# ============================================================================
# 全局配置
# ============================================================================

class Globals:
    """全局配置类，管理库路径和名称"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取全局单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """初始化全局配置"""
        # 初始化设计数据库
        _design.oaDesignInit()
        ns = get_namespace("native")
        
        # 库路径和名称
        self.lib_path_str = "../data/LibDir"
        self.lib_name_str = "LibDir"
        self.cell_name_str = "Cell"
        self.view_name_str = "View"
        self.sn_lib = make_oa_name(ns, self.lib_name_str)
        self.sn_cell = make_oa_name(ns, self.cell_name_str)
        self.sn_view = make_oa_name(ns, self.view_name_str)
        self.str_lib_path = make_oa_string(self.lib_path_str)
        
        # 网络名称
        self.sn_net1 = make_oa_name(ns, "Net1")
        self.sn_net2 = make_oa_name(ns, "Net2")
        self.sn_net3 = make_oa_name(ns, "Net3")
        
        # 获取视图类型（原理图）
        self.view_type = _dm.oaViewType.get(_dm.oaReservedViewType(_dm.oaReservedViewTypeEnum.oacSchematic))
        
        # 获取构建版本号
        packages = _base.oaBuildInfoArray()
        _base.oaBuildInfo.getPackages(packages)
        self.build_number = packages[0].getBuildNumber()
        
        print(f"\n*** 使用 OA 构建版本: {self.build_number} ***\n")


# ============================================================================
# 线程模型管理函数
# ============================================================================

def log_setting_thread_use_model(new_model):
    """记录线程模型设置操作"""
    model_name = new_model.getName()
    print(f"session.setThreadUseModel({model_name})")


def set_thread_use_model(new_model_enum):
    """
    设置线程使用模型
    
    参数:
        new_model_enum: oaThreadUseModelEnum 枚举值
    """
    session = _base.oaSession.get()
    current_model = session.getThreadUseModel()
    new_model = _base.oaThreadUseModel(new_model_enum)
    
    print(f"\n切换线程模型: {current_model.getName()} -> {new_model.getName()}")
    
    # 特殊处理：OA 22.41p004 版本的限制
    # 从 MultipleReaders 切换到其他模型时，必须先回到 SingleThread
    OA22_41_p004 = 25346
    globals_obj = Globals.get_instance()
    
    if globals_obj.build_number == OA22_41_p004:
        if (new_model_enum == _base.oaThreadUseModelEnum.oacMultipleReadersThreadUseModel and
            new_model_enum != _base.oaThreadUseModelEnum.oacSingleThreadUseModel):
            print("\n[警告] OA 22.41p004 版本限制:")
            print("  从 MultipleReaders 切换到其他模型时，必须先回到 SingleThread")
            print("  否则 API 会抛出 oacInternalError 异常")
            
            # 先切换到单线程模式
            log_setting_thread_use_model(_base.oaThreadUseModel(_base.oaThreadUseModelEnum.oacSingleThreadUseModel))
            session.setThreadUseModel(_base.oaThreadUseModel(_base.oaThreadUseModelEnum.oacSingleThreadUseModel))
    
    # 设置新的线程模型
    log_setting_thread_use_model(new_model)
    session.setThreadUseModel(new_model)
    
    # 确认当前模型
    final_model = session.getThreadUseModel()
    print(f"当前线程模型: {final_model.getName()}\n")


# ============================================================================
# 设计操作函数
# ============================================================================

def create_original_designs():
    """创建初始设计（库、单元、视图和网络）"""
    globals_obj = Globals.get_instance()
    
    # 清理并创建库目录
    if os.path.exists(globals_obj.lib_path_str):
        shutil.rmtree(globals_obj.lib_path_str)
    os.makedirs(globals_obj.lib_path_str, exist_ok=True)
    
    # 创建库（共享模式，使用 DMFileSys 插件）
    lib = _dm.oaLib.create(
        globals_obj.sn_lib,
        make_oa_string(globals_obj.lib_path_str),
        _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
        make_oa_string("oaDMFileSys"),
        _dm.oaDMAttrArray(0)
    )
    
    # 打开设计进行写入
    design = _design.oaDesign.open(
        globals_obj.sn_lib,
        globals_obj.sn_cell,
        globals_obj.sn_view,
        globals_obj.view_type,
        'w'
    )
    
    assert design.isValid(), "设计打开失败"
    
    # 创建顶层 block
    block = _design.oaBlock.create(design, True)
    
    # 创建三个标量网络
    net1 = _design.oaScalarNet.create(block, globals_obj.sn_net1)
    net2 = _design.oaScalarNet.create(block, globals_obj.sn_net2)
    net3 = _design.oaScalarNet.create(block, globals_obj.sn_net3)
    
    print(f"\n已创建网络: {net1.getName()}, {net2.getName()}, {net3.getName()}")
    
    # 保存设计
    print("\n保存设计...")
    design.save()


def count_invalid_nets(block):
    """
    统计无效的 net 数量
    
    参数:
        block: 要检查的 block
        
    返回:
        无效 net 的数量
    """
    invalid_count = 0
    nets = block.getNets()
    
    for net in nets:
        if not net.isValid():
            invalid_count += 1
    
    return invalid_count


def modify_designs():
    """
    修改设计（创建新网络）
    
    行为取决于当前线程模型：
    - MultipleReaders 模式：尝试创建网络会失败（设计为只读）
    - 其他模式：正常创建网络
    """
    globals_obj = Globals.get_instance()
    
    # 查找已存在的设计
    design = _design.oaDesign.find(
        globals_obj.sn_lib,
        globals_obj.sn_cell,
        globals_obj.sn_view
    )
    
    assert design.isValid(), "设计查找失败"
    
    # 获取顶层 block
    block = design.getTopBlock()
    
    print("在设计中创建新标量网络...")
    
    session = _base.oaSession.get()
    current_model = session.getThreadUseModel()
    
    if current_model == _base.oaThreadUseModelEnum.oacMultipleReadersThreadUseModel:
        # MultipleReaders 模式下，设计为只读
        print("\n[警告] 当前为 MultipleReaders 模式，设计为只读")
        print("  尝试修改设计会导致未定义行为")
        print("  在 debug 模式下会抛出 oacInternalError 异常")
        print("  在 opt 模式下可能创建无效对象")
        
        # 统计修改前的状态
        before_invalid = count_invalid_nets(block)
        before_total = block.getNets().getCount()
        
        # 尝试创建网络（预期会失败）
        try:
            new_net = _design.oaScalarNet.create(block)
            print("  [注意] 网络创建成功（可能是 opt 模式）")
        except _base.oaException as e:
            print(f"  [预期] 创建失败: {e.getMsg()}")
        
        # 统计修改后的状态
        after_invalid = count_invalid_nets(block)
        after_total = block.getNets().getCount()
        
        print(f"  修改前: {before_total} 个网络 ({before_invalid} 个无效)")
        print(f"  修改后: {after_total} 个网络 ({after_invalid} 个无效)")
        
    else:
        # 其他模式下可以正常创建网络
        print(f"  当前模型: {current_model.getName()}，可以创建网络")
        new_net = _design.oaScalarNet.create(block)
        
        assert new_net.isValid(), "新网络创建失败"
        print(f"  成功创建网络: {c_str(new_net.getName())}")


# ============================================================================
# 测试函数
# ============================================================================

def test_thread_use_model():
    """
    测试不同的线程使用模型
    
    测试流程：
    1. SingleThread 模式：创建初始设计
    2. MultipleReaders 模式：尝试修改（预期失败）
    3. MultipleWriters 模式：修改设计
    4. 多次切换模型并修改
    """
    print("=" * 70)
    print("测试线程使用模型")
    print("=" * 70)
    
    # 测试 1: 单线程模式 - 创建初始设计
    print("\n[测试 1] 单线程模式 - 创建初始设计")
    set_thread_use_model(_base.oaThreadUseModelEnum.oacSingleThreadUseModel)
    create_original_designs()
    
    # 测试 2: 多读模式 - 尝试修改（应该失败）
    print("\n[测试 2] 多读模式 - 尝试修改设计")
    set_thread_use_model(_base.oaThreadUseModelEnum.oacMultipleReadersThreadUseModel)
    modify_designs()
    
    # 测试 3: 多写模式 - 可以修改
    print("\n[测试 3] 多写模式 - 修改设计")
    set_thread_use_model(_base.oaThreadUseModelEnum.oacMultipleWritersThreadUseModel)
    set_thread_use_model(_base.oaThreadUseModelEnum.oacMultipleWritersThreadUseModel)  # 重复设置测试
    modify_designs()
    
    # 测试 4: 切换回多读模式
    print("\n[测试 4] 多读模式 - 再次尝试修改")
    set_thread_use_model(_base.oaThreadUseModelEnum.oacMultipleReadersThreadUseModel)
    set_thread_use_model(_base.oaThreadUseModelEnum.oacMultipleReadersThreadUseModel)  # 重复设置测试
    modify_designs()
    
    # 测试 5: 回到单线程模式
    print("\n[测试 5] 单线程模式 - 最终修改")
    set_thread_use_model(_base.oaThreadUseModelEnum.oacSingleThreadUseModel)
    modify_designs()
    
    print("\n" + "=" * 70)
    print("线程模型测试完成")
    print("=" * 70)


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("Lab 17-5: OpenAccess 线程使用模型演示")
    print("=" * 70)
    
    # 初始化 OA 子系统
    init_oa()
    
    try:
        # 运行测试
        test_thread_use_model()
        
        print("\n........正常终止........\n")
        return 0
        
    except Exception as ex:
        print(f"\n[错误] 未预期的异常: {ex}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
