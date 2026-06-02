#!/usr/bin/env python3
"""
Lab 13-1: OccInsts — Occurrence Instances
Illustrates finding and using Occurrence-level Instances (oaOccInst) using oapy.


This lab:
  1. Creates a design hierarchy: top → sub → leaf
  2. Opens the top occurrence and demonstrates oaOccInst API
  3. Uses oaOccInst.find, getName, getMasterOccurrence, getInst
  4. Verifies calcVMSize on the design

Note: the oapy bindings do not currently wrap oaCollection<oaOccInst,oaOccurrence>,
so we work through the getOccInst() on individual block Inst objects and
oaOccInst.find for direct lookup.
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(__dir__, "..", "..", "build"))
sys.path.insert(0, __dir__)

from oapy._oa import _base, _dm, _design
from utils import init_oa, make_oa_name, make_oa_string, get_namespace, create_lib


def main():
    print("=" * 60)
    print("Lab 13-1: OccInsts — Occurrence Instances")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    LIB_NAME = "lab13_1_lib"
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab13_1_dir")

    import shutil
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib(LIB_NAME, LIB_DIR)

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    st_enum = _design.oaSigTypeEnum

    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── 1a. Create Leaf Design ──
    print("\n─── Creating Leaf Design ───")
    leaf_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'w')
    leaf_blk = _design.oaBlock.create(leaf_view, True)
    _design.oaScalarNet.create(leaf_blk, make_oa_name(ns, "leaf_net"),
        _design.oaSigType(st_enum.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock))
    leaf_view.save()
    leaf_view.close()
    print("  [PASS] leaf design created")

    # ── 1b. Create Sub Design with leaf instance ──
    print("\n─── Creating Sub Design (1 leaf instance) ───")
    leaf_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'r')
    sub_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'w')
    sub_blk = _design.oaBlock.create(sub_view, True)
    inst_leaf = _design.oaScalarInst.create(sub_blk, leaf_master, make_oa_name(ns, "leaf1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    sub_view.save()
    sub_view.close()
    leaf_master.close()
    print("  [PASS] sub design with leaf1 instance created")

    # ── 1c. Create Top Design with two sub instances ──
    print("\n─── Creating Top Design (2 sub instances) ───")
    sub_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'r')
    top_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "top"), sv_name, vt, 'w')
    top_blk = _design.oaBlock.create(top_view, True)
    inst_sub1 = _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "sub1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    inst_sub2 = _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "sub2"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    top_view.save()
    print("  [PASS] top design with sub1, sub2 created")

    # ── 2. Get Top Occurrence ──
    print("\n─── Get Top Occurrence ───")
    top_occ = top_view.getTopOccurrence()
    assert top_occ is not None
    blk_from_occ = top_occ.getBlock()
    print(f"  [PASS] topOcc = {hex(id(top_occ))}, block = {hex(id(blk_from_occ))}")

    # ── 3. Get OccInst from Inst ──
    print("\n─── Get OccInst from Inst objects ──")
    oi1 = inst_sub1.getOccInst()  # no-arg overload
    oi2 = inst_sub2.getOccInst()
    assert oi1 is not None and oi2 is not None

    oi1_name = _base.oaString()
    oi1.getName(ns, oi1_name)
    oi2_name = _base.oaString()
    oi2.getName(ns, oi2_name)
    print(f"  [PASS] OccInst from inst_sub1: {oi1_name}")
    print(f"  [PASS] OccInst from inst_sub2: {oi2_name}")

    # ── 4. Find OccInst by SimpleName ──
    print("\n─── Find OccInst by SimpleName ──")
    simp = _base.oaSimpleName(ns, "sub1")
    found_oi = _design.oaOccInst.find(top_occ, simp)
    assert found_oi is not None

    found_name = _base.oaString()
    found_oi.getName(ns, found_name)
    print(f"  [PASS] oaOccInst.find('sub1') -> {found_name}")

    # ── 5. getMasterOccurrence ──
    print("\n─── getMasterOccurrence ──")
    master_occ = found_oi.getMasterOccurrence(True)
    assert master_occ is not None
    print(f"  [PASS] masterOcc = {hex(id(master_occ))}")

    # ── 6. getInst ──
    print("\n─── getInst from OccInst ──")
    the_inst = found_oi.getInst()
    assert the_inst is not None
    inst_name2 = _base.oaString()
    the_inst.getName(ns, inst_name2)
    print(f"  [PASS] getInst -> {inst_name2}")

    # ── 7. getName on OccInst (2-arg) ──
    print("\n─── getName on OccInst ──")
    nm = _base.oaString()
    found_oi.getName(ns, nm)
    print(f"  [PASS] getName -> {nm}")

    # ── 8. calcVMSize ──
    print("\n─── calcVMSize ──")
    vm = top_view.calcVMSize()
    assert vm > 0, f"calcVMSize returned {vm}"
    print(f"  [PASS] VM size: {vm}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    top_view.close()
    sub_master.close()
    lib.close()

    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 13-1 (OccInsts) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
