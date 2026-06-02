#!/usr/bin/env python3
"""
oapy Lab 3-1: Sample — OA 对象模型遍历与创建

目标: 创建完整层次化设计 (Inv → Or → Nand → Gate → Sample)

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab3_1_sample.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace
from oapy._oa import _design, _base, _dm

# 常用枚举
ST = _design.oaSigTypeEnum
BV = _design.oaBlockDomainVisibilityEnum
TT = _design.oaTermTypeEnum
ORIENT = _base.oaOrientEnum


def make_net(block, name, sig=None):
    ns = get_namespace("native")
    if sig is None:
        nm = name.upper(); sig = ST.oacPowerSigType if nm in ('VDD','VCC') else ST.oacGroundSigType if nm in ('VSS','GND') else ST.oacSignalSigType
    return _design.oaScalarNet.create(block, make_oa_name(ns, name),
        _design.oaSigType(sig), 1, _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))


def make_term(net, name, ttype):
    term = _design.oaScalarTerm.create(net, make_oa_name(get_namespace("native"), name))
    term.setTermType(_design.oaTermType(ttype))
    return term


def make_rect(block, x1, y1, x2, y2, l=1, p=1):
    return _design.oaRect.create(block, l, p, _base.oaBox(x1, y1, x2, y2))


def open_design_w(sn_lib, cell):
    ns = get_namespace("native")
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, cell),
                                  make_oa_name(ns, "schematic"), vt, 'w')
    return view, _design.oaBlock.create(view, True)


def make_inst(block, sn_lib, cell, inst_name, x=0, y=0):
    ns = get_namespace("native")
    master = _design.oaDesign.find(sn_lib, make_oa_name(ns, cell),
                                   make_oa_name(ns, "schematic"))
    if master is None:
        vt = _dm.oaViewType.find(make_oa_string("schematic"))
        master = _design.oaDesign.open(sn_lib, make_oa_name(ns, cell),
                                        make_oa_name(ns, "schematic"), vt, 'r')
    xform = _base.oaTransform(x, y, _base.oaOrient(ORIENT.oacR0))
    return _design.oaScalarInst.create(block, master,
        make_oa_name(ns, inst_name), xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock),
        _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacUnplacedPlacementStatus))


def create_inv(sn_lib):
    print("  Inv...", end=" ")
    view, block = open_design_w(sn_lib, "Inv")
    make_net(block, "VDD"); make_net(block, "VSS")
    make_term(make_net(block, "A"), "A", TT.oacInputTermType)
    make_term(make_net(block, "Z"), "Z", TT.oacOutputTermType)
    make_rect(block, -500, -500, 500, 500, 231, 252)
    view.save(); view.close(); print("✅")


def create_or(sn_lib):
    print("  Or...", end=" ")
    view, block = open_design_w(sn_lib, "Or")
    make_net(block, "VDD"); make_net(block, "VSS")
    for p in ["A", "B"]: make_term(make_net(block, p), p, TT.oacInputTermType)
    make_term(make_net(block, "Z"), "Z", TT.oacOutputTermType)
    view.save(); view.close(); print("✅")


def create_nand(sn_lib):
    print("  Nand...", end=" ")
    view, block = open_design_w(sn_lib, "Nand")
    make_net(block, "VDD"); make_net(block, "VSS")
    for p in ["A", "B"]: make_term(make_net(block, p), p, TT.oacInputTermType)
    make_term(make_net(block, "Z"), "Z", TT.oacOutputTermType)
    view.save(); view.close(); print("✅")


def create_gate(sn_lib):
    print("  Gate...", end=" ")
    view, block = open_design_w(sn_lib, "Gate")
    
    # 实例化 Or + 2×Nand + Inv
    make_inst(block, sn_lib, "Or", "OrInst")
    make_inst(block, sn_lib, "Nand", "NandInst1", 0, -500)
    make_inst(block, sn_lib, "Nand", "NandInst2", 0, -1000)
    make_inst(block, sn_lib, "Inv", "InvInst", 500, -500)
    
    # 互联
    make_term(make_net(block, "N1"), "A", TT.oacInputTermType)
    make_term(make_net(block, "N2"), "B", TT.oacInputTermType)
    make_term(make_net(block, "OUT"), "Z", TT.oacOutputTermType)
    make_net(block, "VDD"); make_net(block, "VSS")
    
    view.save(); view.close(); print("✅")


def create_hierarchy(sn_lib):
    print("  Sample hierarchy...", end=" ")
    view, block = open_design_w(sn_lib, "Sample")
    view.setCellType(_design.oaCellType(_design.oaCellTypeEnum.oacSoftMacroCellType))
    
    for i in range(3):
        make_inst(block, sn_lib, "Gate", f"GateInst{i+1}", i * 1500, 0)
    
    make_net(block, "VDD"); make_net(block, "VSS")
    view.save(); view.close(); print("✅")


def main():
    print("=" * 60)
    print("oapy Lab 3-1: Sample — 层次化设计")
    print("=" * 60)

    init_oa()
    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    # Library
    ns = get_namespace("native")
    sn_lib = make_oa_name(ns, "MyLib")
    lm = _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode)
    path = make_oa_string("../data/LibDir")
    
    # oaLib.create 直接创建并打开 Lib
    lib = _dm.oaLib.create(sn_lib, path, lm, make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))
    print("✅ Library: MyLib")

    # Cells
    print("\n--- Leaf Cells ---")
    create_inv(sn_lib)
    create_or(sn_lib)
    create_nand(sn_lib)

    print("\n--- Composite ---")
    create_gate(sn_lib)
    create_hierarchy(sn_lib)

    lib.close()

    # Verify
    print(f"\n--- Disk Contents ---")
    for root, dirs, files in os.walk("../data/LibDir"):
        for f in sorted(files):
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 3-1 完成！")


if __name__ == "__main__":
    main()
