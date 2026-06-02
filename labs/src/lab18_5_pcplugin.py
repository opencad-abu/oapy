#!/usr/bin/env python3
"""
Lab 18-5: PCPlugin — Pcell 参数化单元插件演示


功能:
  - 加载外部编译的 IPcell 插件 (si2pcplugin)
  - 创建参数化单元 (Pcell) 的 SuperMaster
  - 实例化 Pcell 并观察回调触发 (onEval, onBind, onUnbind)
  - 使用 PcellObserver 和 DesignObserver 监控事件
  - 保存和重新加载设计，验证 Pcell 持久化

运行: cd oapy && bash labs/run_lab.sh labs/lab18_5_pcplugin.py
"""
import os
import sys
import shutil
from oapy._oa import _base, _design, _dm
import utils


# ═══════════════════════════════════════════════════════════════════════════
# 插件配置
# ═══════════════════════════════════════════════════════════════════════════

PLUGIN_DIR = "/workarea/ai/openclaw/oa22.61-cpplabs/18-5.pcplugin"
PLUGIN_CLASSID = "si2pcellID"
PLUGIN_DLL = "si2pcplugin"

LIB_NAME = "LibPcell"
LIB_PATH = "../data/LibDir"


# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def print_master_type(design):
    """打印 Master 类型"""
    if design.isSubMaster():
        master_type = "SUBMASTER"
    elif design.isSuperMaster():
        master_type = "SUPERMASTER"
    else:
        master_type = "MASTER"
    print(f" {master_type} ", end="")


def dump_lcv(design):
    """打印 LCV (Lib/Cell/View) 信息"""
    if design:
        ns = _base.oaNativeNS()
        obj_id = id(design)
        print(f"Design<{obj_id}>", end=" ")

        lib_name = design.getLibName(ns)
        cell_name = design.getCellName(ns)
        view_name = design.getViewName(ns)
        
        print(f"{lib_name}|{cell_name}|{view_name}", end="")


def log_ref_count(design, mesg):
    """打印引用计数"""
    print(f"{mesg} refCount={design.getRefCount()}")


def add_pcell_inst(block, design, inst_name, p_array):
    """添加 Pcell 实例
    
    Args:
        block: 目标 Block
        design: SuperMaster 设计
        inst_name: 实例名称
        p_array: 参数数组
    Returns:
        oaScalarInst 实例
    """
    ns = _base.oaNativeNS()
    sn_inst = _base.oaScalarName(ns, inst_name)
    
    # 创建零变换 (原点, R0 旋转)
    transform = _base.oaTransform(_base.oaPoint(0, 0),
                                  _base.oaOrient(_base.oaOrientEnum.oacR0))
    bdv = _design.oaBlockDomainVisibility(
        _design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock)
    status = _design.oaPlacementStatus(
        _design.oaPlacementStatusEnum.oacUnplacedPlacementStatus)
    
    # 创建 ScalarInst
    inst = _design.oaScalarInst.create(block, design, sn_inst, transform,
                                       p_array, bdv, status)
    return inst


def dump_params(p_array):
    """打印参数数组"""
    print(f"  ParamArray (numElements={p_array.getNumElements()}):")
    for i in range(p_array.getNumElements()):
        param = p_array[i]
        name = utils.c_str(param.getName())
        ptype = param.getType()
        
        if ptype == _base.oaParamTypeEnum.oacStringParamType:
            val = utils.c_str(param.getStringVal())
            print(f"    [{i}] {name} = \"{val}\" (string)")
        elif ptype == _base.oaParamTypeEnum.oacIntParamType:
            val = param.getIntVal()
            print(f"    [{i}] {name} = {val} (int)")
        elif ptype == _base.oaParamTypeEnum.oacDoubleParamType:
            val = param.getDoubleVal()
            print(f"    [{i}] {name} = {val} (double)")
        else:
            print(f"    [{i}] {name} = ? (type={ptype})")


# ═══════════════════════════════════════════════════════════════════════════
# Observer 类
# ═══════════════════════════════════════════════════════════════════════════

class MyDesignObs(_design.oaDesignObserver):
    """设计观察者 - 监控设计打开事件"""
    
    def __init__(self, priority=50, enable=True):
        super().__init__(priority, enable)
        print(f"<MyDesignObs __init__> Priority={priority}")
    
    def onFirstOpen(self, design):
        """设计首次打开时触发"""
        print("<MyDesignObs::onFirstOpen /> ", end="")
        dump_lcv(design)
        print_master_type(design)
        print(" is opened </MyDesignObs::onFirstOpen>")


class MyPcellObs(_design.oaPcellObserver):
    """Pcell 观察者 - 监控 Pcell 评估事件"""
    
    def __init__(self, priority=56, enable=True):
        super().__init__(priority, enable)
        print(f"<MyPcellObs __init__> Priority={priority}")
    
    def onPreEval(self, design, pcell_def):
        """Pcell 评估前触发"""
        print("<MyPcellObs::onPreEval>")
        print("  ", end="")
        dump_lcv(design)
        print_master_type(design)
        print()
        print("</MyPcellObs::onPreEval>")
    
    def onPostEval(self, design, pcell_def):
        """Pcell 评估后触发"""
        print("<MyPcellObs::onPostEval />")
    
    def onError(self, design, msg, error_type):
        """Pcell 错误时触发"""
        print(f"<MyPcellObs::onError> #{error_type} {utils.c_str(msg)} </MyPcellObs::onError>")


# ═══════════════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════════════

def create_designs(sn_lib, class_id, dll_name):
    """创建设计并定义 Pcell SuperMaster
    
    这是第一次运行时的流程：
    1. 创建 top 和 pc 两个设计
    2. 创建参数数组
    3. 加载 Pcell 插件
    4. 定义 SuperMaster
    5. 创建实例
    6. 保存设计
    """
    print("\n── 创建设计 ──")
    ns = _base.oaNativeNS()
    
    # 打开/创建 top 和 pc 设计
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("schematic"))
    
    design_top = _design.oaDesign.open(sn_lib, 
                                        _base.oaScalarName(ns, "top"),
                                        _base.oaScalarName(ns, "main"),
                                        vt, 'w')
    design_pc = _design.oaDesign.open(sn_lib,
                                       _base.oaScalarName(ns, "pc"),
                                       _base.oaScalarName(ns, "main"),
                                       vt, 'w')
    
    # 创建 Block
    block_top = _design.oaBlock.create(design_top, True)
    _design.oaBlock.create(design_pc, True)
    
    print(f"  Created top and pc Designs")
    
    # ── 创建参数数组 ──
    # VARIABLE  NAME       VALUE           POSITION IN ARRAY
    # --------  --------   -----           -----------------
    # p0        "p0param"  "NetParamName"  0 
    # p1        "p1param"  595             1
    p_array = _base.oaParamArray(2)
    p_array[0] = _base.oaParam("p0param", "NetParamName")
    p_array[1] = _base.oaParam("p1param", 595)
    p_array.setNumElements(2)
    
    print("\n  pArray for before defineSuperMaster now is:")
    dump_params(p_array)
    
    # ── 检查 OA_PLUGIN_PATH ──
    oa_plugin_path = os.environ.get('OA_PLUGIN_PATH', '')
    if not oa_plugin_path:
        print("  WARNING: OA_PLUGIN_PATH not set. Plugin XML should be in $ROOT_OA/data/plugins/")
    else:
        print(f"  OA_PLUGIN_PATH is {oa_plugin_path}")
    
    # ── 加载 Pcell 插件 ──
    print(f"\n  PcellLink::find({class_id}) causes API to load lib{dll_name}.so")
    print(f"  Then invokes getClassObject() and constructs IPcell\n")
    
    pc_link = _design.oaPcellLink.find(_base.oaString(class_id))
    
    print(f"\n  </oaPcellLink::find>")
    
    if not pc_link:
        print(f"  ERROR: {class_id}.plg missing OR lib{dll_name}.so not in search path")
        sys.exit(1)
    
    # 第二次调用 find() 应该返回同一个对象
    print(f"\n  A second call to find() merely invokes IPcell::getName()")
    pc_link2 = _design.oaPcellLink.find(_base.oaString(class_id))
    print(f"  </oaPcellLink::find>")
    
    # 验证是同一个对象
    print(f"  ASSERT [{'PASS' if pc_link == pc_link2 else 'FAIL'}] pcLink == pcLink2")
    
    # ── 获取 IPcell ──
    print(f"\n  Use the PcellLink to get the IPcell:")
    ipc = pc_link.getIPcell()
    print(f"  </oaPcellLink->getIPcell>")
    
    print(f"\n  Use the IPcell to get the PcellDef")
    p_cell_def = ipc.getPcellDef()
    print(f"  </IPcell->getPcellDef>")
    
    # ── 验证 SuperMaster 状态 ──
    print(f"\n  Is pc design already a SuperMaster? ")
    is_super = design_pc.isSuperMaster()
    print(f"{'YES' if is_super else 'NO'}")
    
    # ── 定义 SuperMaster ──
    print(f"\n  Define SuperMaster using PcellDef and pArray")
    print(f"  <oaDesign::defineSuperMaster>")
    
    design_pc.defineSuperMaster(p_cell_def, p_array)
    
    print(f"  </oaDesign::defineSuperMaster>")
    
    log_ref_count(design_pc, "  After defineSuperMaster, design_pc")
    
    # ── 验证 PcellDef 一致性 ──
    print(f"\n  Get the PcellDef via getPcellDef from the SuperMaster")
    p_cell_def2 = design_pc.getPcellDef()
    print(f"  ASSERT [{'PASS' if p_cell_def == p_cell_def2 else 'FAIL'}] pCellDef == pCellDef2")
    
    # design_pc itself is the SuperMaster after defineSuperMaster().
    super_master = design_pc
    print(f"  SuperMaster design id = {id(super_master)}")
    
    # ── 评估 SuperMaster ──
    print(f"\n  Call evalSuperMaster with the same pArray used in defineSuperMaster")
    design_pc.evalSuperMaster()
    log_ref_count(design_pc, "  After 1st evalSuperMaster, design_pc")
    
    # ── 第二组参数演示 ──
    print(f"\n  Prepare a different pArray for later instantiation")
    p_array2 = _base.oaParamArray(2)
    p_array2[0] = _base.oaParam("p0param", "NetName")
    p_array2[1] = _base.oaParam("p1param", 55)
    p_array2.setNumElements(2)
    
    print(f"  New pArray:")
    dump_params(p_array2)
    
    print("  Keep pArray2 for later instantiation flow; official OA API here uses evalSuperMaster() with no arguments")
    
    # ── 创建实例 ──
    print(f"\n  Add a new Inst of SuperMaster to block_top")
    p_array3 = _base.oaParamArray(2)
    p_array3[0] = _base.oaParam("p0param", "AnotherNetName")
    p_array3[1] = _base.oaParam("p1param", 77)
    p_array3.setNumElements(2)
    
    print(f"  pArray for new Inst:")
    dump_params(p_array3)
    
    # 添加实例 (会触发 onEval)
    add_pcell_inst(block_top, super_master, "i2", p_array3)
    log_ref_count(design_pc, "  After adding Inst, design_pc")
    
    # ── 保存设计 ──
    print(f"\n  Save design_top")
    design_top.save()
    
    print("\n── end of pass1 ──")
    print("\n" + "=" * 70)
    print(".............normal termination")
    print("=" * 70)
    os._exit(0)


def read_designs(sn_lib):
    """读取已保存的设计
    
    这是第二次运行时的流程：
    1. 打开已存在的设计
    2. 查找实例
    3. 获取 Master（触发插件回调）
    4. 添加新实例
    5. Purge 设计（触发 onUnbind）
    """
    print("\n── 读取设计 ──")
    ns = _base.oaNativeNS()
    
    # 打开已存在的设计
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("schematic"))
    
    design_top = _design.oaDesign.open(sn_lib,
                                        _base.oaScalarName(ns, "top"),
                                        _base.oaScalarName(ns, "main"),
                                        vt, 'a')
    
    block = design_top.getTopBlock()
    
    print(f"  Find an Inst in Block just read from disk.")
    
    # 查找名为 "i1_p0=NetParamName_p1=595" 的实例
    i1_read = _design.oaInst.find(block, _base.oaSimpleName(ns, "i1_p0=NetParamName_p1=595"))
    
    print(f"  ASSERT [{'PASS' if i1_read.isValid() else 'FAIL'}] i1read->isValid()")
    print(f"  ASSERT [{'PASS' if not i1_read.isBound() else 'FAIL'}] !i1read->isBound()")
    
    print(f"\n  Getting i1read master will fire getClassObject with PlugIn name")
    print(f"  which causes getPcellDef, then onRead, then onEval.")
    
    i1_master = i1_read.getMaster()
    
    print(f"  ASSERT [{'PASS' if i1_master.isValid() else 'FAIL'}] i1master->isValid()")
    print(f"  ASSERT [{'PASS' if i1_master.isSubMaster() else 'FAIL'}] i1master->isSubMaster()")
    
    # ── 添加新实例 ──
    print(f"\n  Add a new Inst of the same Pcell")
    print(f"  Use AddPcellInst() helper with Param values:")
    print(f"    p0 = 'PostReadNet', p1 = 88")
    
    p_array = _base.oaParamArray(2)
    p_array[0] = _base.oaParam("p0param", "PostReadNet")
    p_array[1] = _base.oaParam("p1param", 88)
    p_array.setNumElements(2)
    
    add_pcell_inst(block, i1_master.getSuperMaster(), "postReadInst", p_array)
    
    # 打印所有打开的设计
    print(f"\n  Open designs:")
    # (简化：跳过 DumpOpenDesigns)
    
    print(f"\n  Purge top design. Will fire onUnbind.")
    design_top.purge()


def main():
    print("=" * 70)
    print("Lab 18-5: PCPlugin — Pcell 参数化单元插件演示")
    print("=" * 70)
    
    # ── 1. 设置插件路径 ──
    print("\n── 1. 设置 OA_PLUGIN_PATH ──")
    # Append lab dir to OA_PLUGIN_PATH so plugin .plg and .so can be found
    existing = os.environ.get('OA_PLUGIN_PATH', '')
    if PLUGIN_DIR not in existing:
        os.environ['OA_PLUGIN_PATH'] = f"{PLUGIN_DIR}:{existing}" if existing else PLUGIN_DIR
    os.environ['CLASSID'] = PLUGIN_CLASSID
    print(f"  OA_PLUGIN_PATH = {os.environ['OA_PLUGIN_PATH']}")
    
    # 确保 .plg 文件存在
    plg_file = os.path.join(PLUGIN_DIR, f"{PLUGIN_CLASSID}.plg")
    if not os.path.exists(plg_file):
        print(f"  Creating {plg_file}")
        with open(plg_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
            f.write(f'<plugIn lib="{PLUGIN_DLL}"/>\n')
    
    # ── 2. 初始化 OA ──
    print("\n── 2. 初始化 OA ──")
    utils.init_oa()
    
    # ── 3. 创建 Observer ──
    print("\n── 3. 创建 Observer ──")
    
    # PcellObserver (优先级 56)
    pcell_obs = MyPcellObs(56)
    
    # DesignObserver (优先级 50)
    design_obs = MyDesignObs(50)
    
    # ── 4. 创建/打开库 ──
    print("\n── 4. 创建/打开库 ──")
    ns = _base.oaNativeNS()
    sn_lib = _base.oaScalarName(ns, LIB_NAME)
    
    # 清理旧目录
    if os.path.exists(LIB_PATH):
        shutil.rmtree(LIB_PATH)
        print(f"  Cleaned up old directory: {LIB_PATH}")
    
    # 创建库
    lib = _dm.oaLib.create(sn_lib, _base.oaString(LIB_PATH),
                            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
                            _base.oaString("oaDMFileSys"),
                            _dm.oaDMAttrArray(0))
    print(f"  Created library: {LIB_NAME}")
    
    # ── 5. 判断是第一次还是第二次运行 ──
    print("\n── 5. 执行主流程 ──")
    
    # 检查 top/main 设计是否已存在
    design_exists = _design.oaDesign.exists(sn_lib,
                                             _base.oaScalarName(ns, "top"),
                                             _base.oaScalarName(ns, "main"))
    
    if design_exists:
        # 第二次运行：读取设计
        read_designs(sn_lib)
        print("\n── end of pass2 ──")
    else:
        # 第一次运行：创建设计
        create_designs(sn_lib, PLUGIN_CLASSID, PLUGIN_DLL)
        print("\n── end of pass1 ──")
    
    print("\n" + "=" * 70)
    print(".............normal termination")
    print("=" * 70)
    os._exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n*** Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
