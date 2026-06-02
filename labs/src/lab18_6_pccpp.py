#!/usr/bin/env python3
"""
Lab 18-6: Pcell CPP — Python 转换版
=====================================

本 Lab 演示 OpenAccess Pcell (Parameterized Cell) 的完整工作流程：
  1. 首次运行 (CreateDesigns):
     - 创建 top 和 pc 两个 Design
     - 注册 IPcell 生成器 (Python 子类实现，替代原生 IPcellCPPDefMgr)
     - 定义 SuperMaster (defineSuperMaster)
     - 实例化 Pcell 并触发 onEval → genPcell 回调
     - 保存设计到磁盘
  2. 二次运行 (ReadDesigns):
     - 从磁盘读取已有设计
     - 演示 Pcell 的 SubMaster 读取和评估流程
     - 验证 PcellDef 数据完整性
  3. 观察者模式:
     - oaPcellObserver: 监控 Pcell 评估前/后事件
     - oaDesignObserver: 监控 Design 首次打开和清理事件

运行方式:  ./run_lab.sh lab18_6_pccpp.py
"""

import os
import sys
import shutil
import traceback

# 确保 oapy 在路径中
_oapy_build = os.path.join(os.path.dirname(__file__), '..', 'build')
_oapy_src = os.path.join(os.path.dirname(__file__), '..')
for _p in [_oapy_build, _oapy_src]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from oapy._oa import _base, _dm, _design

# ═══════════════════════════════════════════════════════════════════════════
# 全局状态 — 用于缩进和日志输出
# ═══════════════════════════════════════════════════════════════════════════

_indent_level = 0
INDENT_INC = 2

def indent_add():
    """增加缩进"""
    global _indent_level
    _indent_level += INDENT_INC

def indent_sub():
    """减少缩进"""
    global _indent_level
    _indent_level -= INDENT_INC

def log(msg):
    """带缩进的日志输出"""
    print(" " * _indent_level, end="")
    print(msg, end="")

# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def fail(msg):
    """错误输出"""
    print(msg, file=sys.stderr)

def assert_check(expr, desc):
    """ASSERT 宏的 Python 实现"""
    result = "PASS" if expr else "FAIL"
    log(f"ASSERT [{result}] {desc}\n")

def assert_exception(exc_msg_id, action, exc_desc, action_desc):
    """ASSERT_EXCEPTION 宏的 Python 实现
    执行 action，验证是否抛出指定 oaException
    
    Args:
        exc_msg_id: 期望的异常消息 ID
        action: 要执行的 lambda
        exc_desc: 异常描述字符串
        action_desc: 动作描述字符串
    """
    result = False
    try:
        action()
    except Exception as ex:
        # 尝试匹配 oaException 的 msgId
        if hasattr(ex, 'getMsgId'):
            if ex.getMsgId() == exc_msg_id:
                result = True
        # 也尝试字符串匹配
        elif str(exc_msg_id) in str(ex):
            result = True
    log(f"ASSERT [{'PASS' if result else 'FAIL'}] {exc_desc} THROWN BY {action_desc}\n")


def master_type_str(design):
    """返回 Design 的 Master 类型字符串
    
    Args:
        design: oaDesign 对象
    Returns:
        "SUPERMASTER", "SUBMASTER", 或 "ORDINARYMASTER"
    """
    if design.isSubMaster():
        return "SUBMASTER"
    elif design.isSuperMaster():
        return "SUPERMASTER"
    else:
        return "ORDINARYMASTER"


def dump_lcv(design):
    """打印 Design 的 Lib|Cell|View 信息
    
    Args:
        design: oaDesign 对象
    """
    if design is None:
        return
    # 获取类型名
    type_obj = design.getType()
    type_name = type_obj.getName() if type_obj else "Design"
    log(f"{type_name}")
    
    # 打印对象 ID (格式化地址)
    obj_id = id(design)
    print(f"<0x{obj_id:x}>", end="")
    
    ns = _base.oaNativeNS()

    lib_name = design.getLibName(ns)
    print(f'"{lib_name}', end="")
    
    cell_name = design.getCellName(ns)
    print(f"|{cell_name}", end="")
    
    view_name = design.getViewName(ns)
    print(f'|{view_name}"', end="")


def c_str(oa_str):
    """将 oaString 转换为 Python str"""
    if isinstance(oa_str, str):
        return oa_str
    try:
        return oa_str.operator_const_oaChar_p()
    except Exception:
        return str(oa_str)


def make_oa_str(s=None):
    """创建 oaString"""
    if s is None:
        return _base.oaString()
    return _base.oaString(str(s))


def add_pcell_inst(block, design, inst_name, p_array=None):
    """实例化一个 Pcell ScalarInst
    
    Args:
        block: 父级 oaBlock
        design: Pcell master oaDesign
        inst_name: 实例名
        p_array: 参数数组 (可选)
    Returns:
        oaScalarInst
    """
    ns = _base.oaNativeNS()
    
    # 创建零偏移变换
    transform = _base.oaTransform(_base.oaPoint(0, 0),
                                  _base.oaOrient(_base.oaOrientEnum.oacR0))
    
    if p_array is not None:
        inst = _design.oaScalarInst.create(
            block,
            design,
            _base.oaScalarName(ns, inst_name),
            transform,
            p_array,
            _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacPlacedPlacementStatus)
        )
    else:
        inst = _design.oaScalarInst.create(
            block,
            _base.oaScalarName(ns, inst_name),
            _base.oaScalarName(ns, design.getCellName._oaString()),  
            _base.oaScalarName(ns, "layout"),  # placeholder
            _base.oaScalarName(ns, ""),  # placeholder
            transform,
            _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacPlacedPlacementStatus)
        )
    return inst


def log_ref_count(design, mesg):
    """打印 Design 引用计数"""
    log(f"{mesg} refCount={design.getRefCount()}\n")


def get_param_array_if_bound(design):
    getter = getattr(design, "getParamArray", None)
    if getter is None:
        return None
    return getter()


# ═══════════════════════════════════════════════════════════════════════════
# myIPcell — 自定义 IPcell 实现
# ═══════════════════════════════════════════════════════════════════════════

class MyIPcell(_design.IPcell):
    """自定义 IPcell 实现
    
    继承 oa.IPcell，实现 Pcell 生成逻辑。
    通过 DLL 插件系统注册。Python 版本直接子类化 IPcell。
    """
    
    def __init__(self):
        super().__init__()
        self._pc_def = None
    
    def getName(self, name):
        getattr(name, "operator=")("si2pcgen")
        return "si2pcgen"
    
    def onBind(self, design, pcellDef):
        pass
    
    def onUnbind(self, design, pcellDef):
        pass
    
    def onRead(self, design, mapWindow, loc, pcellDef):
        pass
    
    def onWrite(self, design, mapWindow, loc, pcellDef):
        pass
    
    def calcDiskSize(self, pcellDef):
        return 1024
    
    def onEval(self, design, pcell_def):
        """Pcell 评估回调 — 当 Pcell 需要生成内容时调用
        
        Args:
            design: SubMaster oaDesign
            pcell_def: 关联的 oaPcellDef
        """
        ns = _base.oaNativeNS()
        
        print("<genPcell>")
        
        # 打印 master type (从 PcellDef 数据中获取)
        s = _base.oaString()
        pcell_def.getDataValue("MasterType", s)
        master_type_val = c_str(s)
        print(f'  masterType = "{master_type_val}"')
        
        # 验证 design 是 SubMaster
        assert_check(design.isSubMaster(), 'design->isSubMaster()')
        
        # 验证 SuperMaster 的 PcellDef 与此 PcellDef 相同
        super_master = design.getSuperMaster()
        assert_check(super_master.getPcellDef() is pcell_def,
                      'design->getSuperMaster()->getPcellDef() == pcDef')
        
        # 打印 PcellDef 中的数据值
        pcell_def.getDataValue("MasterType", s)
        print(f'  From PcellDef MasterType    Data value = "{c_str(s)}"')
        
        pcell_def.getDataValue("PcellGenName", s)
        print(f'  From PcellDef PcellGenName  Data value = "{c_str(s)}"')
        
        # 在 SubMaster 的 Block 中创建 evalNet (演示 Pcell 内容生成)
        block = design.getTopBlock()
        if block is None:
            block = _design.oaBlock.create(design, True)
        
        net = _design.oaScalarNet.create(
            block,
            _base.oaScalarName(ns, "evalNet"),
            _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType),
            1,
            _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock)
        )
        assert_check(net.isValid(), 'net->isValid()')
        
        print("  </genPcell>")
    
    def getPcellDef(self):
        if self._pc_def is None:
            self._pc_def = _design.oaPcellDef(self)
        return self._pc_def


# ═══════════════════════════════════════════════════════════════════════════
# myPcellObs — Pcell 观察者 (监控 Pcell 评估事件)
# ═══════════════════════════════════════════════════════════════════════════

class MyPcellObs(_design.oaPcellObserver):
    """Pcell 观察者 — 监控 Pcell 评估前/后和错误事件"""
    
    def __init__(self, priority, enable=True):
        super().__init__(priority, 1 if enable else 0)
        log(f"<myPcellObs constructor>Priority={priority}</myPcellObs constructor>\n")
    
    def __del__(self):
        log("<~myPcellObs />\n")
    
    def onPreEval(self, design, pc_def):
        """Pcell 评估前回调"""
        log("<myPcellObs::onPreEval>\n")
        indent_add()
        dump_lcv(design)
        print(" ", end="")
        print(master_type_str(design), end="")
        print("  ", end="")
        # 打印参数数组
        param_array = get_param_array_if_bound(design)
        if param_array is not None:
            dump_param_array(param_array)
        print()
        indent_sub()
        log("</myPcellObs::onPreEval>\n")
    
    def onPostEval(self, design, pc_def):
        """Pcell 评估后回调"""
        log("<myPcellObs::onPostEval />\n")
    
    def onError(self, design, msg, error_type):
        """Pcell 错误回调"""
        log("<myPcellObs::onError>")
        print(f"#{error_type} {msg}", end="")
        log("</myPcellObs::onError>\n")


# ═══════════════════════════════════════════════════════════════════════════
# myDesignObs — Design 观察者 (监控 Design 打开/清理事件)
# ═══════════════════════════════════════════════════════════════════════════

class MyDesignObs(_design.oaDesignObserver):
    """Design 观察者 — 监控 Design 首次打开和清理事件"""
    
    def __init__(self, priority, enable=True):
        super().__init__(priority, 1 if enable else 0)
        log(f"<myDesignObs constructor>Priority={priority}</myDesignObs constructor>\n")
    
    def onFirstOpen(self, design):
        """Design 首次打开回调"""
        log("  <myDesignObs::onFirstOpen /> ")
        print(master_type_str(design), end="")
        dump_lcv(design)
        print(" <myDesignObs::onFirstOpen />")
    
    def onPurge(self, design):
        """Design 清理回调"""
        log("<myPcellObs::onPurge>")
        print(master_type_str(design), end="")
        dump_lcv(design)
        print("</myPcellObs::onPurge>")


# ═══════════════════════════════════════════════════════════════════════════
# dump_param_array — 打印参数数组内容
# ═══════════════════════════════════════════════════════════════════════════

def dump_param_array(p_array):
    """打印 oaParamArray 的内容
    
    Args:
        p_array: oaParamArray 对象
    """
    count = p_array.getNumElements()
    print(f" PARAMS[{count}]", end="")
    for i in range(count):
        param = p_array[i]
        param_name = c_str(param.getName())
        # 获取参数值
        val = None
        try:
            # 尝试获取字符串值
            s = _base.oaString()
            param.getValue(s)
            val = f'"{c_str(s)}"'
        except Exception:
            try:
                val = str(param.getIntValue())
            except Exception:
                try:
                    val = str(param.getDoubleValue())
                except Exception:
                    val = "?"
        print(f" {param_name}={val}", end="")


# ═══════════════════════════════════════════════════════════════════════════
# ReadDesigns — 二次运行：从磁盘读取已有设计
# ═══════════════════════════════════════════════════════════════════════════

def read_designs(sn_lib, sn_view, my_ipcell):
    """二次运行：从磁盘读取已有 Pcell 设计
    
    Args:
        sn_lib: 库名 (oaScalarName)
        sn_view: View 名 (oaScalarName)
        my_ipcell: 已注册的 IPcell 实例
    """
    log("Opening existing Design.\n")
    
    ns = _base.oaNativeNS()
    # 打开已有的 top design (append 模式)
    design_top = _design.oaDesign.open(
        sn_lib,
        _base.oaScalarName(ns, "top"),
        sn_view,
        'a'
    )
    
    block = design_top.getTopBlock()
    
    log("Find an Inst in Block just read from disk.\n")
    
    # 在 Block 中查找名为 "i1_p0=NetParamName_p1=44" 的 Inst
    i1read = _design.oaInst.find(block, _base.oaSimpleName(ns, "i1_p0=NetParamName_p1=44"))
    
    assert_check(i1read.isValid(), 'i1read->isValid()')
    assert_check(not i1read.isBound(), '! i1read->isBound()')
    
    log("Getting i1read master will fire getClassObject with PlugIn name (saved with SuperMaster),\n")
    log("  which causes myIPcell::getPcellDef, then onRead, then onEval.\n")
    
    # 获取 i1read 的 master — 这会触发 onEval
    i1master = i1read.getMaster()
    
    assert_check(i1master.isValid(), 'i1master->isValid()')
    assert_check(i1master.isSubMaster(), 'i1master->isSubMaster()')
    
    print("Can't get a PcellDef from a SubMaster:")
    # 从 SubMaster 直接获取 PcellDef 应该失败
    assert_exception(
        "oacInvalidSuperMaster",
        lambda: i1master.getPcellDef(),
        "oacInvalidSuperMaster",
        "i1master->getPcellDef()"
    )
    
    # 通过 SuperMaster 获取 PcellDef
    pc_def = i1master.getSuperMaster().getPcellDef()
    s = _base.oaString()
    
    pc_def.getDataValue("MasterType", s)
    print(f'  From PcellDef MasterType    Data value = "{c_str(s)}"')
    
    pc_def.getDataValue("PcellGenName", s)
    print(f'  From PcellDef PcellGenName  Data value = "{c_str(s)}"')
    
    # 添加一个新的 Pcell 实例 (用不同参数)
    p_array2 = _base.oaParamArray(2)
    p_array2[0] = _base.oaParam(make_oa_str("p0param"), make_oa_str("PostReadNet"))
    p_array2[1] = _base.oaParam(make_oa_str("p1param"), 88)
    p_array2.setNumElements(2)
    
    add_pcell_inst(block, i1master.getSuperMaster(), "postReadInst", p_array2)
    
    # 打印当前打开的设计
    dump_open_designs()
    
    print()
    log("Purge top design.\n")
    design_top.purge()


# ═══════════════════════════════════════════════════════════════════════════
# dump_open_designs — 打印当前打开的所有 Design
# ═══════════════════════════════════════════════════════════════════════════

def dump_open_designs():
    """打印当前打开的所有 Design 及其内容"""
    print()
    print("Currently open Designs:")
    # 遍历所有打开的 Design
    designs = _design.oaDesign.getOpenDesigns()
    for i in range(designs.getCount()):
        design = designs[i]
        print()
        print("_" * 30, end="")
        dump_lcv(design)
        print()
        
        # 检查是否为 SuperMaster/SubMaster
        if design.isSuperMaster():
            print("  SUPERMASTER<>", end="")
            p_array = get_param_array_if_bound(design)
            if p_array is not None:
                dump_param_array(p_array)
            print()
        
        if design.isSubMaster():
            super_master = design.getSuperMaster()
            if super_master is not None:
                print("    SUBMASTER<>", end="")
                p_array = get_param_array_if_bound(design)
                if p_array is not None:
                    dump_param_array(p_array)
                print()
        
        # 打印 Block 域
        block = design.getTopBlock()
        if block is not None:
            print()
            print("=" * 20, "BLOCK DOMAIN", "=" * 20)
            print()
            dump_block_summary(block)
        
        print()


def dump_block_summary(block):
    """打印 Block 的简要信息"""
    print("[1]BLOCK")
    print("Block<>")
    
    # 打印 Instances
    insts = block.getInsts(0)
    inst_count = insts.getCount()
    if inst_count > 0:
        ns = _base.oaNativeNS()
        s = _base.oaString()
        for i in range(inst_count):
            inst = insts[i]
            inst.getName(ns, s)
            inst_name = c_str(s)
            bound = "BOUND" if inst.isBound() else "UNBOUND"
            print(f'  [{inst_count}]INST')
            print(f'  ScalarInst<>"{inst_name}"')
    
    # 打印 Nets
    nets = block.getNets()
    net_count = nets.getCount()
    if net_count > 0:
        ns = _base.oaNativeNS()
        s = _base.oaString()
        for i in range(net_count):
            net = nets[i]
            net.getName(ns, s)
            net_name = c_str(s)
            print(f'  [{net_count}]NET')
            print(f'  ScalarNet<>"{net_name}"')


# ═══════════════════════════════════════════════════════════════════════════
# CreateDesigns — 首次运行：创建设计并注册 Pcell
# ═══════════════════════════════════════════════════════════════════════════

def create_designs(sn_lib, sn_view, class_id, gen_name, my_ipcell):
    """首次运行：创建设计、注册 Pcell 生成器、定义 SuperMaster
    
    Args:
        sn_lib: 库名 (oaScalarName)
        sn_view: View 名 (oaScalarName)
        class_id: Pcell 生成器 ID 字符串
        gen_name: Pcell 生成器名称
        my_ipcell: MyIPcell 实例
    """
    ns = _base.oaNativeNS()
    
    log("Creating Designs.\n")
    
    # 获取 ViewType (Schematic)
    vt_str = make_oa_str("schematic")
    vt = _dm.oaViewType.find(vt_str)
    if vt is None:
        vt = _dm.oaViewType.create(vt_str)
    
    # 打开/创建 top 和 pc 设计
    design_top = _design.oaDesign.open(
        sn_lib,
        _base.oaScalarName(ns, "top"),
        sn_view,
        vt,
        'w'
    )
    design_pc = _design.oaDesign.open(
        sn_lib,
        _base.oaScalarName(ns, "pc"),
        sn_view,
        vt,
        'w'
    )
    
    # 创建 Block
    block_top = _design.oaBlock.create(design_top, True)
    _design.oaBlock.create(design_pc, True)
    
    print()
    log("Created top and pc Designs\n\n")
    
    # 创建参数数组
    p_array = _base.oaParamArray(2)
    p_array[0] = _base.oaParam(make_oa_str("p0param"), make_oa_str("NetParamName"))
    p_array[1] = _base.oaParam(make_oa_str("p1param"), 595)
    p_array.setNumElements(2)
    
    log("So pArray for before defineSuperMaster now is:")
    dump_param_array(p_array)
    print("\n\n")
    
    # 通过 oaPcellLink 注册 IPcell 并获取 PcellDef
    # 在 Python 中，我们直接使用 oaPcellLink.create() 注册 IPcell
    # 而不是原生的 IPcellCPPDefMgr
    pc_link = _design.oaPcellLink.create(my_ipcell)
    pc_def = my_ipcell.getPcellDef()
    
    # 将 name/value 对添加到 PcellDef (保存时会写入 SuperMaster)
    pc_def.addData(make_oa_str("PcellGenName"), make_oa_str(class_id))
    pc_def.addData(make_oa_str("MasterType"), make_oa_str("macro13"))
    
    log("About to defineSuperMaster; API will call IPcell callbacks:\n")
    print("<oaDesign::defineSuperMaster>")
    
    # 将 design_pc 转换为 Pcell SuperMaster
    design_pc.defineSuperMaster(pc_def, p_array)
    
    print("</oaDesign::defineSuperMaster>")
    log_ref_count(design_pc, "After defineSuperMaster, pc")
    print()
    
    log("Design data before any Insts created.\n")
    dump_open_designs()
    
    # 修改参数值并实例化第一个 Pcell
    p_array[1] = _base.oaParam(make_oa_str("p1param"), 44)
    p_array.setNumElements(2)
    
    log("About to instantiate 1st inst i1. No CB fire since no binding occurs yet.\n")
    i1 = add_pcell_inst(block_top, design_pc, "i1_p0=NetParamName_p1=44", p_array)
    log_ref_count(design_pc, "After instantiation, pc")
    
    assert_check(i1.isValid(), 'i1->isValid()')
    
    s = _base.oaString()
    i1.getName(ns, s)
    assert_check(c_str(s) == "i1_p0=NetParamName_p1=44",
                  '(i1->getName(ns,str),str) == "i1_p0=NetParamName_p1=44"')
    
    log("Getting i1 master will cause onEval to fire.\n")
    i1master = i1.getMaster()
    
    log_ref_count(design_pc, "After eval, pc")
    
    assert_check(i1master.isSubMaster(), 'i1master->isSubMaster()')
    assert_check(i1master is not design_pc, 'i1master != design_pc')
    
    # 打印 SuperHeader 中的 inst 数量
    inst_header = i1.getHeader()
    if inst_header is not None:
        super_header = inst_header.getSuperHeader()
        if super_header is not None and hasattr(super_header, "getInsts"):
            insts = super_header.getInsts(0)
            if insts is not None:
                print(f"SuperHeader has #insts = {insts.getCount()}")
    
    dump_open_designs()
    
    # 再次打印 SuperHeader 的 inst 数量
    inst_header = i1.getHeader()
    if inst_header is not None:
        super_header = inst_header.getSuperHeader()
        if super_header is not None and hasattr(super_header, "getInsts"):
            insts = super_header.getInsts(0)
            if insts is not None:
                print(f"SuperHeader has #insts = {insts.getCount()}")
    
    log("Save designs.\n")
    design_top.save()
    design_pc.save()
    print()
    
    # 打印保存后 supermaster block 中的 inst 数量
    top_block = design_top.getTopBlock()
    if top_block is not None:
        print(f"#insts in supermaster block = {top_block.getInsts(0).getCount()}")
    
    design_pc.close()
    design_top.close()


# ═══════════════════════════════════════════════════════════════════════════
# main — 主入口
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """主函数 — 两遍运行模式
    
    第一遍: 创建 Library、Design、Pcell 定义和实例
    第二遍: 从磁盘读取已有设计，验证 Pcell 功能
    
    命令行参数:
      lab18_6_pccpp.py <LibName> <LibPath> <ClassID> <GenName>
    
    默认值:
      LibName=LibPcell, LibPath=LibDir, ClassID=si2pcgID, GenName=si2pcgen
    """
    # 初始化 OA
    _base.oaBaseInitAppBuild('22.61.d003')
    _design.oaDesignInit(6, 651, 6)
    
    # 解析命令行参数
    args = sys.argv[1:]
    if len(args) < 4:
        print("\n***Use:   lab18_6_pccpp.py  LibName  LibPath  PlugIn-classID  pcgen-name\n")
        print("  Using defaults: LibPcell LibDir si2pcgID si2pcgen\n")
        str_name_lib = "LibPcell"
        str_path_lib = "../data/LibDir"
        str_class_id = "si2pcgID"
        str_gen_name = "si2pcgen"
    else:
        str_name_lib = args[0]
        str_path_lib = args[1]
        str_class_id = args[2]
        str_gen_name = args[3]
    
    log("Declaring myPcellObs\n")
    indent_add()
    
    # 创建 Pcell 观察者 (优先级 56)
    eval_obs = MyPcellObs(56)
    
    # 创建 Design 观察者 (优先级 50)
    open_obs = MyDesignObs(50)
    
    indent_sub()
    
    # 创建 IPcell 实例
    my_ipcell = MyIPcell()
    
    # 创建或打开 Library
    ns = _base.oaNativeNS()
    sn_lib = _base.oaScalarName(ns, str_name_lib)
    
    lib = None
    lib_path = str_path_lib  # 已经是相对路径，CWD = src/
    if os.path.isdir(lib_path):
        # 清理残留数据，避免 Non-empty Directory 错误
        shutil.rmtree(lib_path)
        os.makedirs(lib_path, exist_ok=True)
    
    if lib is None:
        lib = _dm.oaLib.create(
            sn_lib,
            make_oa_str(lib_path),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_str("oaDMFileSys")
        )
    
    # 确定 View 名
    sn_view = _base.oaScalarName(ns, "optimized")
    
    # 判断是首次运行还是二次运行
    design_exists = _design.oaDesign.exists(
        sn_lib,
        _base.oaScalarName(ns, "top"),
        sn_view
    )
    
    if design_exists:
        # 二次运行：从磁盘读取已有设计
        read_designs(sn_lib, sn_view, my_ipcell)
    else:
        # 首次运行：创建设计和 Pcell
        create_designs(sn_lib, sn_view, str_class_id, str_gen_name, my_ipcell)
    
    log("\n.............normal termination\n")
    os._exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        log(f"***Exception: {ex}\n")
        traceback.print_exc()
        sys.exit(1)
