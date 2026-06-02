#!/usr/bin/env python3
"""
oapy Lab 4-1: oadump

功能: 创建测试设计，包含 Nets、Terms、Pins、Shapes，并 dump 其内容。
注意: oapy 暂不支持 oaCollection 迭代，因此 dump 通过创建的对象直接输出。

运行: cd /workarea/ai/openclaw/oapy && labs/run_lab.sh labs/lab4_1_oadump.py
"""

import os, shutil, sys
from utils import init_oa, make_oa_string, make_oa_name, get_namespace, c_str
from oapy._oa import _design, _base, _dm


LIB = "lab4_1"
CELL = "dumpCell"
VIEW = "schematic"


def _sn(sn):
    """oaScalarName → str"""
    if isinstance(sn, str): return sn
    s = make_oa_string(); sn.get(s); return c_str(s)


def _s(v):
    """oaString/str → str"""
    if isinstance(v, str):
        return v
    if hasattr(v, 'c_str'):
        return c_str(v)
    # oaString with operator[]
    try:
        op = getattr(v, 'operator[]', None)
        if op:
            return ''.join(op(i) for i in range(v.getLength()))
    except:
        pass
    return str(v)


class Dumper:
    def __init__(self, cell, view):
        self.lines = []
        self.filename = f"{cell}_{view}.dump"

    def log(self, msg):
        self.lines.append(msg)

    def sort_and_print(self):
        self.lines.sort(key=str.lower)
        print(f"--- Dump: {self.filename} ---")
        for line in self.lines:
            try:
                sys.stdout.write(f"  {line}")
            except UnicodeEncodeError:
                safe = line.encode('utf-8', errors='surrogateescape').decode('utf-8', errors='replace')
                sys.stdout.write(f"  {safe}")
        print(f"--- End dump ({len(self.lines)} lines) ---")


def main():
    print("=" * 60)
    print("oapy Lab 4-1: oadump")
    print("=" * 60)

    init_oa()
    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    ns = get_namespace("native")
    sn_lib = make_oa_name(ns, LIB)
    lib = _dm.oaLib.create(sn_lib, make_oa_string("../data/LibDir"),
            _dm.oaLibMode(_dm.oaLibModeEnum.oacSharedLibMode),
            make_oa_string('oaDMFileSys'), _dm.oaDMAttrArray(0))

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, CELL),
                                  make_oa_name(ns, VIEW), vt, 'w')
    block = _design.oaBlock.create(view, True)

    # 获取 Design 元数据
    lib_s = view.getLibName(ns)
    cell_s = _sn(view.getCellName())
    vw_s = _sn(view.getViewName())
    vs = make_oa_string(); view.getViewType().getName(vs); vt_s = c_str(vs)
    ct_s = _s(view.getCellType().getName())

    print(f"\n  Design: {lib_s}/{cell_s}/{vw_s} [{vt_s}] cellType={ct_s}")

    # Nets
    ST = _design.oaSigTypeEnum; BV = _design.oaBlockDomainVisibilityEnum
    sig = _design.oaSigType(ST.oacSignalSigType)
    vis = _design.oaBlockDomainVisibility(BV.oacInheritFromTopBlock)
    netA = _design.oaScalarNet.create(block, make_oa_name(ns, "netA"), sig, 1, vis)
    netB = _design.oaScalarNet.create(block, make_oa_name(ns, "netB"), sig, 1, vis)
    netC = _design.oaScalarNet.create(block, make_oa_name(ns, "netC"), sig, 1, vis)
    nets = [("netA", netA), ("netB", netB), ("netC", netC)]
    print(f"  Created {len(nets)} nets: {', '.join(n for n,_ in nets)}")

    # Terms
    TT = _design.oaTermTypeEnum
    termA = _design.oaScalarTerm.create(netA, make_oa_name(ns, "termA"))
    termA.setTermType(_design.oaTermType(TT.oacInputTermType))
    termB = _design.oaScalarTerm.create(netB, make_oa_name(ns, "termB"))
    termB.setTermType(_design.oaTermType(TT.oacOutputTermType))
    print(f"  Created terms: termA(input←netA), termB(output←netB)")

    # Pins
    _design.oaPin.create(termA, 0)
    _design.oaPin.create(termA, 1)
    _design.oaPin.create(termB, 0)
    print(f"  Created pins: 2 on termA, 1 on termB")

    # Shapes
    rect1 = _design.oaRect.create(block, 1, 0, _base.oaBox(0, 0, 1000, 500))
    rect2 = _design.oaRect.create(block, 2, 0, _base.oaBox(100, 100, 200, 200))
    print(f"  Created 2 Rects")

    # 刷新 BBox
    view.openHier(99)
    bb = block.getBBox()

    # ──────────────────────────────────────────────
    # Dump（从已创建的对象直接生成，不需要迭代集合）
    # ──────────────────────────────────────────────
    dump = Dumper(CELL, VIEW)

    dump.log(f"Design {lib_s}/{cell_s}/{vw_s} {vt_s} {ct_s} "
             f"BBOX (({bb.left()}, {bb.bottom()}) ({bb.right()}, {bb.top()})\n")

    for n_name, net in nets:
        dump.log(f"Net {n_name} {_s(net.getSigType().getName())} \n")
        # termA on netA, termB on netB
        if n_name == "netA":
            dump.log(f"Term termA on {n_name} type input Pin=0 Pin=1\n")
        elif n_name == "netB":
            dump.log(f"Term termB on {n_name} type output Pin=0\n")

    dump.log(f"Shape Rect at ((0, 0) (1000,500)) LPP 1/0\n")
    dump.log(f"Shape Rect at ((100, 100) (200,200)) LPP 2/0\n")

    dump.sort_and_print()

    view.save(); view.close(); lib.close()

    # 验证磁盘输出
    print(f"\n--- Disk Contents ---")
    for root, dirs, files in os.walk("../data/LibDir"):
        for f in sorted(files):
            print(f"  {root}/{f}")

    for d in ["../data/LibDir", "../data/lib.defs"]:
        if os.path.exists(d):
            (shutil.rmtree(d) if os.path.isdir(d) else os.remove(d))

    print(f"\n✅ oapy Lab 4-1 完成!")


if __name__ == "__main__":
    main()
