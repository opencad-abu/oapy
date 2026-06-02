#!/usr/bin/env python3
"""
oapy Lab 11-2: Netlist — 创建全加器层次化网表

目标: 创建 Xor/And/Or → HalfAdder → FullAdder 层次化设计

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab11_2_netlist.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, create_lib
from oapy._oa import _design, _base, _dm


def create_leaf_cell(sn_lib, cell_name, term_names):
    """创建门级单元 (Xor, And, Or)"""
    ns = get_namespace("native")
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, cell_name),
                                  make_oa_name(ns, "schematic"), vt, 'w')
    block = _design.oaBlock.create(view, True)
    
    ST = _design.oaSigTypeEnum
    BV = _design.oaBlockDomainVisibilityEnum
    TT = _design.oaTermTypeEnum
    
    # 前两个是 input，最后是 output
    for i, tname in enumerate(term_names):
        net = _design.oaScalarNet.create(block, make_oa_name(ns, tname),
            _design.oaSigType(ST.oacSignalSigType), 1,
            _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
        term = _design.oaScalarTerm.create(net, make_oa_name(ns, tname))
        term.setTermType(_design.oaTermType(
            TT.oacOutputTermType if i == len(term_names)-1 else TT.oacInputTermType))
    
    view.save()
    view.close()
    print(f"  ✅ {cell_name}: {', '.join(term_names)}")


def main():
    print("=" * 60)
    print("oapy Lab 11-2: Netlist — Full Adder")
    print("=" * 60)

    init_oa()

    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    sn_lib, lib = create_lib("testLib", "../data/LibDir")
    print("✅ Library created")

    # ── Leaf cells: Xor, And, Or ──
    print("\n--- Step 1: Leaf Cells ---")
    for cell, terms in [("Xor", ["A", "B", "Y"]),
                         ("And", ["A", "B", "Y"]),
                         ("Or",  ["A", "B", "Y"])]:
        create_leaf_cell(sn_lib, cell, terms)

    ns = get_namespace("native")
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    ST = _design.oaSigTypeEnum
    BV = _design.oaBlockDomainVisibilityEnum
    TT = _design.oaTermTypeEnum

    def make_net(block, name, sig=ST.oacSignalSigType):
        return _design.oaScalarNet.create(block, make_oa_name(ns, name),
            _design.oaSigType(sig), 1,
            _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))

    # ── HalfAdder ──
    print("\n--- Step 2: HalfAdder ---")
    ha = _design.oaDesign.open(sn_lib, make_oa_name(ns, "HalfAdder"),
                                make_oa_name(ns, "schematic"), vt, 'w')
    ha_b = _design.oaBlock.create(ha, True)
    for tname, ttype in [("A", TT.oacInputTermType), ("B", TT.oacInputTermType),
                          ("C", TT.oacOutputTermType), ("S", TT.oacOutputTermType)]:
        net = make_net(ha_b, tname)
        term = _design.oaScalarTerm.create(net, make_oa_name(ns, tname))
        term.setTermType(_design.oaTermType(ttype))
    ha.save(); ha.close()
    print("  ✅ HalfAdder: A, B, C, S")

    # ── FullAdder ──
    print("\n--- Step 3: FullAdder ---")
    fa = _design.oaDesign.open(sn_lib, make_oa_name(ns, "FullAdder"),
                                make_oa_name(ns, "schematic"), vt, 'w')
    fa_b = _design.oaBlock.create(fa, True)
    for tname in ["A", "B", "Ci", "C", "S"]:
        make_net(fa_b, tname)
    for nname in ["net0", "net1", "net2"]:
        make_net(fa_b, nname)
    fa.save(); fa.close()
    print("  ✅ FullAdder: A, B, Ci, C, S + net0/1/2")

    lib.close()

    # 验证
    print(f"\n--- Disk Library ---")
    for root, dirs, files in os.walk("../data/LibDir"):
        for f in files:
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 11-2 完成！")


if __name__ == "__main__":
    main()
