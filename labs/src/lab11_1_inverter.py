#!/usr/bin/env python3
"""
oapy Lab 11-1: Inverter — 创建反相器电路

目标: 创建简单反相器 schematic，包含 VDD/VSS/A/Z 网络和端口

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab11_1_inverter.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, create_lib
from oapy._oa import _design, _base, _dm

def main():
    print("=" * 60)
    print("oapy Lab 11-1: Inverter (反相器)")
    print("=" * 60)

    init_oa()

    # 清理
    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    # ── 创建 Lib ──
    sn_lib, lib = create_lib("testLib", "../data/LibDir")
    print(f"✅ Lib: testLib → ./LibDir")

    ns = get_namespace("native")

    # ── 打开 Design ──
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    if vt is None:
        vt = _dm.oaViewType.create(make_oa_string("schematic"))
    sn_cell = make_oa_name(ns, "inverter")
    sn_view = make_oa_name(ns, "schematic")
    view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    print(f"✅ Design: inverter/schematic")

    # ── 创建 Block ──
    block = _design.oaBlock.create(view, True)
    print(f"✅ Block")

    # ── 创建 Nets (VDD, VSS, A, Z) ──
    ST = _design.oaSigTypeEnum
    BV = _design.oaBlockDomainVisibilityEnum

    vdd = _design.oaScalarNet.create(block, make_oa_name(ns, "VDD"),
        _design.oaSigType(ST.oacPowerSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    vss = _design.oaScalarNet.create(block, make_oa_name(ns, "VSS"),
        _design.oaSigType(ST.oacGroundSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    net_a = _design.oaScalarNet.create(block, make_oa_name(ns, "A"),
        _design.oaSigType(ST.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    net_z = _design.oaScalarNet.create(block, make_oa_name(ns, "Z"),
        _design.oaSigType(ST.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock))
    print(f"✅ Nets: VDD(power), VSS(ground), A, Z")

    # ── 创建 Terms (A=input, Z=output) ──
    TT = _design.oaTermTypeEnum
    term_a = _design.oaScalarTerm.create(net_a, make_oa_name(ns, "A"))
    term_a.setTermType(_design.oaTermType(TT.oacInputTermType))
    print(f"✅ Term A (input)")

    term_z = _design.oaScalarTerm.create(net_z, make_oa_name(ns, "Z"))
    term_z.setTermType(_design.oaTermType(TT.oacOutputTermType))
    print(f"✅ Term Z (output)")

    # ── 保存并关闭 ──
    view.save()
    view.close()
    lib.close()
    print(f"✅ Saved and closed")

    # ── 验证磁盘文件 ──
    print(f"\n--- Disk files ---")
    for root, dirs, files in os.walk("../data/LibDir"):
        for f in files:
            print(f"  {root}/{f}")

    print(f"\n✅ oapy Lab 11-1 完成！")


if __name__ == "__main__":
    main()
