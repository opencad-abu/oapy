#!/usr/bin/env python3
"""
oapy Lab 22-1: DetPara — Parasitic Network with Devices and Analysis

参考 py4oa: py4oa/pylabs/lab22_1_detpara.py

功能:
  - 创建包含电阻、电容、电感的寄生物网络
  - 创建分析点 (AnalysisPoint)
  - 创建子网络 (SubNetwork)
  - 设置 device 参数并验证

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab22_1_detpara.py
"""

import os, shutil
from utils import init_oa, get_namespace, make_oa_name, make_oa_string, create_lib
from oapy._oa import _design, _base, _dm, _tech


LIB_NAME = "Lib22"
LIB_DIR = "../data/Lib22_dir"
CELL_NAME = "detPara"
VIEW_NAME = "abstract"


def main():
    print("=" * 60)
    print("oapy Lab 22-1: DetPara — Parasitic Network and Analysis")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    # Clean up
    for d in [LIB_DIR, "../data/lib.defs"]:
        p = d
        if os.path.isfile(p):
            os.remove(p)
        elif os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)

    sn_lib, lib = create_lib(LIB_NAME, LIB_DIR)
    print(f"✅ Library {LIB_NAME} created")

    # Create tech
    tech = _tech.oaTech.create(lib)
    tech.save()
    tech.close()

    # ViewType
    vt = _dm.oaViewType.find(make_oa_string("netlist"))
    if not vt:
        vt = _dm.oaViewType.create(make_oa_string("netlist"))

    # Open design
    des = _design.oaDesign.open(sn_lib,
                                make_oa_name(ns, CELL_NAME),
                                make_oa_name(ns, VIEW_NAME),
                                vt, 'w')
    block = _design.oaBlock.create(des, True)
    print(f"  Created design: {CELL_NAME}/{VIEW_NAME}")

    # Create nets
    ST = _design.oaSigTypeEnum
    BV = _design.oaBlockDomainVisibilityEnum
    n1_net = _design.oaScalarNet.create(
        block, make_oa_name(ns, "n1"),
        _design.oaSigType(ST.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    n2_net = _design.oaScalarNet.create(
        block, make_oa_name(ns, "n2"),
        _design.oaSigType(ST.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    print("  Created nets: n1, n2")

    # Create analysis point
    ac_pt = _design.oaAnalysisPoint.create(des, make_oa_string("ac1"))
    print("  Created AC analysis point: ac1")

    # Create parasitic network on n1_net
    pnet = _design.oaParasiticNetwork.create(n1_net, ac_pt)
    pnet.setName(make_oa_string(f"Parasitic-{CELL_NAME}"))
    print("  Created ParasiticNetwork on n1")

    # Create nodes
    node1 = _design.oaNode.create(pnet, 1)
    node2 = _design.oaNode.create(pnet, 2)
    gnd = _design.oaGroundedNode.create(pnet, 0)
    print("  Created nodes: node1(1), node2(2), gnd(0)")

    # Create resistors
    r1 = _design.oaResistor.create(node1, node2)
    r1.setName(make_oa_string("r1"))
    r1.setValue(ac_pt, 1.2e3)
    print(f"  Created resistor r1 = {r1.getValue(ac_pt)} ohm")

    r2 = _design.oaResistor.create(node2, gnd)
    r2.setName(make_oa_string("r2"))
    r2.setValue(ac_pt, 3.4e3)
    print(f"  Created resistor r2 = {r2.getValue(ac_pt)} ohm")

    # Create coupling capacitor
    c1 = _design.oaCouplingCap.create(node1, node2)
    c1.setName(make_oa_string("c1"))
    c1.setValue(ac_pt, 2.3e-12)
    print(f"  Created coupling cap c1 = {c1.getValue(ac_pt)} F")

    # Create inductor
    l1 = _design.oaInductor.create(node1, gnd)
    l1.setName(make_oa_string("l1"))
    print("  Created inductor l1")

    # Create series RL
    rl = _design.oaSeriesRL.create(node1, node2)
    rl.setValue(ac_pt, 50.0, 100.0e-6)
    print("  Created series RL rl1: R=50, L=100uH")

    # Create sub-network
    sub_net = _design.oaSubNetwork.create(pnet, make_oa_string("mySubNet"))
    r1.addToSubNetwork(sub_net)
    r2.addToSubNetwork(sub_net)
    print("  Created sub-network: mySubNet (with r1, r2)")

    # Save and close
    des.save()
    des.close()
    lib.close()

    # Verify output
    print(f"\n--- Output Files ---")
    for root, dirs, files in os.walk(LIB_DIR):
        for f in sorted(files):
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 22-1 完成！")


if __name__ == "__main__":
    main()
