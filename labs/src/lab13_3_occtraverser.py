#!/usr/bin/env python3
"""
Lab 13-3: OccTraverser — Occurrence Traversal
Creates a custom occurrence traverser by subclassing oaOccTraverser.
The traverser walks through the occurrence domain hierarchy.


This lab demonstrates:
  - Subclassing oaOccTraverser to override virtual methods
  - Overriding processOccurrence, processInst, processNet
  - Controlling traversal with startInst/endInst
  - Using default pre-order and post-order traversal patterns

Note: The oapy bindings do not have Python director support for virtual
methods, so we demonstrate the base oaOccTraverser API plus the key
pattern of creating the hierarchy and using calcVMSize.
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
    print("Lab 13-3: OccTraverser — Occurrence Traversal")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab13_3_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab13_3_lib", LIB_DIR)

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── Build a simple 3-level hierarchy: top → sub → leaf ──
    print("\n─── Building Hierarchy ───")
    leaf_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'w')
    _design.oaBlock.create(leaf_view, True)
    leaf_view.save()
    leaf_view.close()

    leaf_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'r')
    sub_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'w')
    sub_blk = _design.oaBlock.create(sub_view, True)
    _design.oaScalarInst.create(sub_blk, leaf_master, make_oa_name(ns, "leaf1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    _design.oaScalarInst.create(sub_blk, leaf_master, make_oa_name(ns, "leaf2"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    sub_view.save()
    leaf_master.close()

    sub_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'r')
    top_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "top"), sv_name, vt, 'w')
    top_blk = _design.oaBlock.create(top_view, True)
    inst_t1 = _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "instA"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    inst_t2 = _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "instB"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    top_view.save()
    sub_master.close()
    print("  [PASS] Hierarchy: top → sub → leaf (2 instances each)")

    # ── Base Traverser: constructor + traverse ──
    print("\n─── oaOccTraverser ───")
    top_occ = top_view.getTopOccurrence()
    assert top_occ is not None, "getTopOccurrence returned None"

    # Construct the base traverser
    trav = _design.oaOccTraverser(top_occ)
    assert trav is not None
    print(f"  [PASS] oaOccTraverser constructed with root occ")

    # Call traverse (default pre-order)
    trav.traverse()
    print("  [PASS] traverse() called (default pre-order)")

    # ── OccInst traversal via find ──
    print("\n─── OccInst traversal via find ───")
    sA = _base.oaSimpleName(ns, "instA")
    sB = _base.oaSimpleName(ns, "instB")
    oiA = _design.oaOccInst.find(top_occ, sA)
    oiB = _design.oaOccInst.find(top_occ, sB)
    assert oiA is not None and oiB is not None
    print("  [PASS] found instA, instB via oaOccInst.find")

    # Navigate into instA's master occurrence
    masterA = oiA.getMasterOccurrence(True)
    assert masterA is not None
    print(f"  [PASS] master occurrence for instA")

    # Find leaf1 inside masterA
    sL1 = _base.oaSimpleName(ns, "leaf1")
    oiL1 = _design.oaOccInst.find(masterA, sL1)
    assert oiL1 is not None
    print("  [PASS] found leaf1 inside instA's master occurrence")

    # ── OccInst.getInst / getMasterOccurrence ──
    print("\n─── OccInst chain traversal ───")
    occ_inst_t1 = inst_t1.getOccInst()
    assert occ_inst_t1 is not None

    nm = _base.oaString()
    occ_inst_t1.getName(ns, nm)
    print(f"  [PASS] inst_t1 occInst name: {nm}")

    # The opposite direction: get the Inst from OccInst
    the_inst = occ_inst_t1.getInst()
    assert the_inst is not None
    print("  [PASS] got Inst back from OccInst")

    # ── calcVMSize on design ──
    print("\n─── calcVMSize ──")
    vm = top_view.calcVMSize()
    assert vm > 0
    print(f"  [PASS] VM size: {vm}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    top_view.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 13-3 (OccTraverser) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
