#!/usr/bin/env python3
"""
Lab 14-1: Ext — oaAppObject 扩展系统示例


功能:
  - 注册自定义 AppObjectDef（扩展对象类型）
  - 定义 InterPointerAppDef 和 FloatAppDef 属性
  - 创建 AppObject 并设置属性
  - 查询 isUsedIn()、遍历 AppObject、remove() 等生命周期管理

运行: python3 lab14_1_ext.py
"""
import os
import sys
from oapy._oa import _base, _design, _dm

# 全局常量
MODE_TRUNC = 'w'
IS_NOT_GLOBAL = False
PERSISTENT = True

# 扩展名称（使用唯一前缀避免冲突）
name_netCoupling = "OpenAccess_hopefully_unique_NetCoupling_v1.0.0"
name_netA = "OpenAccess_hopefully_unique_netA_v1.0.0"
name_netB = "OpenAccess_hopefully_unique_netB_v1.0.0"
name_cap = "OpenAccess_hopefully_unique_cap_v1.0.0"

defaultCapValue = -1.1

# 全局变量
couplingType = None
netA = None
netB = None
cap = None


def getNetName(net):
    """获取 Net 的名称（Native NameSpace）"""
    # 从 oaObject downcast 到 oaNet
    if not isinstance(net, _design.oaNet):
        net = _design.oaNet.cast(net)
    ns = _base.oaNativeNS()
    str_name = _base.oaString()
    net.getName(ns, str_name)
    return getattr(str_name, 'operator const oaChar *')()


def setAttributes(appObj, net1, net2, capValue):
    """设置 AppObject 的属性"""
    print(f"Creating coupling between Net \"{getNetName(net1)}\" and \"{getNetName(net2)}\" = {capValue}")

    # 验证默认值
    assert netA.getValue(appObj) is None, "netA 默认值应为 NULL"
    assert netB.getValue(appObj) is None, "netB 默认值应为 NULL"
    assert abs(cap.getValue(appObj) - defaultCapValue) < 0.00001, "cap 默认值应接近 defaultCapValue"

    # 设置属性
    netA.set(appObj, net1)
    netB.set(appObj, net2)
    cap.set(appObj, capValue)


def createCouplings(net1, net2, capValue):
    """创建耦合对象"""
    # 在 Net 所在的 Design 中创建 AppObject
    design = net1.getDesign()
    coupling = _base.oaAppObject.create(design, couplingType)
    
    # 设置属性
    setAttributes(coupling, net1, net2, capValue)


def destroyCapValue(coupling):
    """销毁 cap 属性值"""
    assert abs(cap.getValue(coupling) - defaultCapValue) > 0.00001, "cap 不应是默认值"
    
    # 销毁 cap 值
    cap.destroy(coupling)
    
    # 验证对象仍然有效
    assert coupling.isValid(), "AppObject 应该仍然有效"
    
    # 验证 cap 恢复为默认值
    assert abs(cap.getValue(coupling) - defaultCapValue) < 0.00001, "cap 应恢复为默认值"


def dumpAttributes(coupling):
    """打印 AppObject 的属性"""
    net1 = netA.getValue(coupling)
    net2 = netB.getValue(coupling)
    capValue = cap.getValue(coupling)
    
    print(f"Found coupling between Net \"{getNetName(net1)}\" and \"{getNetName(net2)}\" = {capValue}")
    
    # 实验：销毁 cap 值
    destroyCapValue(coupling)


def dumpCouplings(design):
    """遍历并打印所有耦合对象"""
    # 通过 oaDesign.getAppObjectIter() 获取迭代器，绕过 collection 类型不匹配
    it = design.getAppObjectIter(couplingType)
    coupling = it.getNext()
    while coupling:
        dumpAttributes(coupling)
        coupling = it.getNext()


def createNet(block, netName):
    """创建非全局的信号类型 ScalarNet"""
    ns = _base.oaNativeNS()
    ST = _design.oaSigTypeEnum
    BV = _design.oaBlockDomainVisibilityEnum
    
    net = _design.oaScalarNet.create(
        block,
        _base.oaScalarName(ns, netName),
        _design.oaSigType(ST.oacSignalSigType),
        1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)
    )
    return net


def initAppObjects():
    """初始化 AppObject 系统"""
    global couplingType, netA, netB, cap
    
    # 注册自定义 AppObjectDef
    couplingType = _base.oaAppObjectDef.get(_base.oaString(name_netCoupling))
    
    # 定义 3 个属性
    netA = _base.oaInterPointerAppDef.get(_base.oaString(name_netA), couplingType, PERSISTENT)
    netB = _base.oaInterPointerAppDef.get(_base.oaString(name_netB), couplingType, PERSISTENT)
    cap = _base.oaFloatAppDef.get(_base.oaString(name_cap), couplingType, defaultCapValue, PERSISTENT)


def main():
    print("=" * 60)
    print("Lab 14-1: oaAppObject 扩展系统示例")
    print("=" * 60)
    
    # 1. 初始化 OA
    print("\n── 1. 初始化 OA ──")
    _base.oaBaseInitAppBuild('22.61.d003')
    _design.oaDesignInit(6, 651, 6)
    
    # 2. 初始化 AppObject 系统
    print("\n── 2. 初始化 AppObject 系统 ──")
    initAppObjects()
    
    # 3. 创建库和设计
    print("\n── 3. 创建库和设计 ──")
    ns = _base.oaNativeNS()
    lib_name = _base.oaScalarName(ns, "testLib")
    cell_name = _base.oaScalarName(ns, "testCell")
    view_name = _base.oaScalarName(ns, "testView")
    lib_path = "../data/Lib1"
    
    # 清理旧库
    import shutil
    if os.path.exists(lib_path):
        shutil.rmtree(lib_path)
    os.makedirs(lib_path, exist_ok=True)
    
    # 创建库（简化版，与 utils.create_lib 一致）
    lib = _dm.oaLib.create(lib_name, _base.oaString(lib_path))
    print(f"Created library: testLib")
    
    # 打开设计（写模式）
    vt = _dm.oaViewType.find(_base.oaString("schematic"))
    if not vt:
        vt = _dm.oaViewType.create(_base.oaString("schematic"))
    
    design = _design.oaDesign.open(lib_name, cell_name, view_name, vt, MODE_TRUNC)
    print(f"Opened design: testLib/testCell/testView")
    
    # 创建 top block
    block = _design.oaBlock.create(design, True)
    
    # 4. 验证 AppObjectDef 注册
    print("\n── 4. 验证 AppObjectDef 注册 ──")
    strNameDef = _base.oaString()
    strNameNetA = _base.oaString()
    strNameNetB = _base.oaString()
    strNameCap = _base.oaString()
    
    couplingType.getName(strNameDef)
    netA.getName(strNameNetA)
    netB.getName(strNameNetB)
    cap.getName(strNameCap)
    
    # 使用 operator const oaChar * 转换为 Python 字符串
    strNameDef_val = getattr(strNameDef, 'operator const oaChar *')()
    strNameNetA_val = getattr(strNameNetA, 'operator const oaChar *')()
    strNameNetB_val = getattr(strNameNetB, 'operator const oaChar *')()
    strNameCap_val = getattr(strNameCap, 'operator const oaChar *')()
    
    assert strNameDef_val == name_netCoupling
    assert strNameNetA_val == name_netA
    assert strNameNetB_val == name_netB
    assert strNameCap_val == name_cap
    print(f"AppObjectDef: {strNameDef_val}")
    print(f"  - netA: {strNameNetA_val}")
    print(f"  - netB: {strNameNetB_val}")
    print(f"  - cap: {strNameCap_val}")
    
    # 5. 验证 find() 方法
    print("\n── 5. 验证 find() 方法 ──")
    netA1 = _base.oaInterPointerAppDef.find(_base.oaString(name_netA), couplingType)
    netB1 = _base.oaInterPointerAppDef.find(_base.oaString(name_netB), couplingType)
    cap1 = _base.oaFloatAppDef.find(_base.oaString(name_cap), couplingType)
    
    assert netA1 == netA
    assert netB1 == netB
    assert cap1 == cap
    print("find() 方法工作正常")
    
    # 6. 创建 4 个 Net
    print("\n── 6. 创建 4 个 Net ──")
    net1 = createNet(block, "Net1")
    net2 = createNet(block, "Net2")
    net3 = createNet(block, "Net3")
    net4 = createNet(block, "Net4")
    print(f"Created: Net1, Net2, Net3, Net4")
    
    # 7. 验证 isUsedIn()（创建前应为 False）
    print("\n── 7. 验证 isUsedIn()（创建前）──")
    usedDef = couplingType.isUsedIn(design)
    usedNetA = netA.isUsedIn(design)
    usedNetB = netB.isUsedIn(design)
    usedCap = cap.isUsedIn(design)
    
    assert not usedDef, "创建前 couplingType 应未被使用"
    assert not usedNetA, "创建前 netA 应未被使用"
    assert not usedNetB, "创建前 netB 应未被使用"
    assert not usedCap, "创建前 cap 应未被使用"
    print("所有 isUsedIn() 均为 False（正确）")
    
    # 8. 创建 6 个耦合对象
    print("\n── 8. 创建 6 个耦合对象 ──")
    cap_1_2 = 0.002
    cap_1_3 = 0.003
    cap_1_4 = 0.004
    cap_2_3 = 0.006
    cap_2_4 = 0.008
    cap_3_4 = 0.012
    
    createCouplings(net1, net2, cap_1_2)
    createCouplings(net1, net3, cap_1_3)
    createCouplings(net1, net4, cap_1_4)
    createCouplings(net2, net3, cap_2_3)
    createCouplings(net2, net4, cap_2_4)
    createCouplings(net3, net4, cap_3_4)
    
    # 9. 验证 isUsedIn()（创建后应为 True）
    print("\n── 9. 验证 isUsedIn()（创建后）──")
    usedDef = couplingType.isUsedIn(design)
    usedNetA = netA.isUsedIn(design)
    usedNetB = netB.isUsedIn(design)
    usedCap = cap.isUsedIn(design)
    
    assert usedDef, "创建后 couplingType 应被使用"
    assert usedNetA, "创建后 netA 应被使用"
    assert usedNetB, "创建后 netB 应被使用"
    assert usedCap, "创建后 cap 应被使用"
    print("所有 isUsedIn() 均为 True（正确）")
    
    # 10. 遍历并打印所有耦合
    print("\n── 10. 遍历并打印所有耦合 ──")
    dumpCouplings(design)
    
    # 11. 从 Design 中移除 AppObjectDef
    print("\n── 11. 从 Design 中移除 AppObjectDef ──")
    couplingType.remove(design)
    print("AppObjectDef 已移除")
    
    # 12. 验证 isUsedIn()（移除后应为 False）
    print("\n── 12. 验证 isUsedIn()（移除后）──")
    usedDef = couplingType.isUsedIn(design)
    usedNetA = netA.isUsedIn(design)
    usedNetB = netB.isUsedIn(design)
    usedCap = cap.isUsedIn(design)
    
    assert not usedDef, "移除后 couplingType 应未被使用"
    assert not usedNetA, "移除后 netA 应未被使用"
    assert not usedNetB, "移除后 netB 应未被使用"
    assert not usedCap, "移除后 cap 应未被使用"
    print("所有 isUsedIn() 均为 False（正确）")
    
    # 13. 关闭设计
    design.close()
    
    print("\n" + "=" * 60)
    print("Lab 14-1 完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
