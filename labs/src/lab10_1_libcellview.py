#!/usr/bin/env python3
"""
oapy Lab 10-1: libcellview — 创建 Technology Library, Design Library, Cell, View

功能: 创建 Tech Library、创建 Cell、View、Design，演示 DM 对象操作。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab10_1_libcellview.py
"""

import os, shutil
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm, _tech


LIB = "lab10_1"
LIB_PATH = "../data/LibDir10_1"
CELL = "myCell"
VIEW = "schematic"


def main():
    print("=" * 60)
    print("oapy Lab 10-1: libcellview")
    print("=" * 60)

    init_oa()

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    os.makedirs(LIB_PATH, exist_ok=True)
    ns = get_namespace("native")

    # ── Step 1: Create Lib ──
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string(LIB_PATH),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))
    print(f"\nStep 1: Created Lib '{LIB}' at '{LIB_PATH}'")

    # ── Step 2: Create Tech ──
    tech = _tech.oaTech.create(lib)
    print(f"Step 2: Created Tech for lib '{LIB}'")
    _tech.oaTech.save(tech)
    tech.close()
    print("  Tech saved and closed")

    # ── Step 3: Create Design (创建 Cell + View 隐式) ──
    sn_cell = make_oa_name(ns, CELL)
    sn_view = make_oa_name(ns, VIEW)
    vt = _dm.oaViewType.find(make_oa_string("schematic"))

    view = _design.oaDesign.open(sn_lib, sn_cell, sn_view, vt, 'w')
    vs = make_oa_string(); vt.getName(vs)
    print(f"Step 3: Created Design '{LIB}/{CELL}/{VIEW}' [{c_str(vs)}]")
    print(f"  Mode: {view.getMode()}")

    # ── Step 4: Create Block ──
    block = _design.oaBlock.create(view, True)
    print(f"Step 4: Created Block")
    bb = block.getBBox()
    print(f"  Initial BBox: ({bb.left()},{bb.bottom()})-({bb.right()},{bb.top()})")

    # ── Step 5: Create some content (Nets + Rects) ──
    ST = _design.oaSigTypeEnum; BV = _design.oaBlockDomainVisibilityEnum
    sig = _design.oaSigType(ST.oacSignalSigType)
    vis = _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)

    for i in range(3):
        name = f"sig_{i}"
        _design.oaScalarNet.create(block, make_oa_name(ns, name), sig, 1, vis)
    print(f"  Created 3 nets: sig_0, sig_1, sig_2")

    _design.oaRect.create(block, 1, 0, _base.oaBox(-100, -100, 100, 100))
    print(f"  Created 1 Rect")

    # ── Save & Close ──
    view.save()
    view.close()
    lib.close()
    print(f"\n  Design saved and closed")

    # ── Verify disk contents ──
    print(f"\n--- Disk Contents ({LIB_PATH}) ---")
    for root, dirs, files in os.walk(LIB_PATH):
        level = root.replace(LIB_PATH, '').count(os.sep)
        indent = '  ' * level
        print(f"  {indent}{os.path.basename(root)}/")
        for f in sorted(files):
            print(f"  {indent}  {f}")

    for d in [LIB_PATH, "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print(f"\n✅ oapy Lab 10-1 完成!")


if __name__ == "__main__":
    main()
