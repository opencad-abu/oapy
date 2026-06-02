#!/usr/bin/env python3
"""
Lab 13-4: OccProducer — Occurrence Producer
Demonstrates the oaOccProducer class for producing occurrence-domain objects.
The producer generates occurrence objects for a given root occurrence.


Key concepts:
  - Constructing oaOccProducer with a root occurrence
  - Calling produce() to generate occurrence objects
  - Setting a new occurrence with setOccurrence() and producing again

Note: The oapy bindings do not have Python director support for process*()
virtuals, so we demonstrate the base API pattern.
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
    print("Lab 13-4: OccProducer — Occurrence Producer")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab13_4_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab13_4_lib", LIB_DIR)

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── Build hierarchy: top → sub (2 inst) → leaf (2 inst each) ──
    print("\n─── Building Hierarchy ───")
    leaf_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'w')
    _design.oaBlock.create(leaf_view, True)
    leaf_view.save()
    leaf_view.close()

    leaf_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "leaf"), sv_name, vt, 'r')
    sub_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'w')
    sub_blk = _design.oaBlock.create(sub_view, True)
    _design.oaScalarInst.create(sub_blk, leaf_master, make_oa_name(ns, "subLeaf1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    _design.oaScalarInst.create(sub_blk, leaf_master, make_oa_name(ns, "subLeaf2"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    sub_view.save()
    leaf_master.close()

    sub_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "sub"), sv_name, vt, 'r')
    top_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "top"), sv_name, vt, 'w')
    top_blk = _design.oaBlock.create(top_view, True)
    _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "topSub1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    _design.oaScalarInst.create(top_blk, sub_master, make_oa_name(ns, "topSub2"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    top_view.save()
    print("  [PASS] 3-level hierarchy created")

    # ── oaOccProducer: construct and produce ──
    print("\n─── oaOccProducer ───")
    top_occ = top_view.getTopOccurrence()
    assert top_occ is not None

    prod = _design.oaOccProducer(top_occ)
    assert prod is not None
    print(f"  [PASS] oaOccProducer constructed with root occ")

    prod.produce()
    print("  [PASS] produce() called on top occurrence")

    # ── setOccurrence: produce from a different occurrence ──
    print("\n─── setOccurrence to sub-level ──")
    sTopSub1 = _base.oaSimpleName(ns, "topSub1")
    oi_topSub1 = _design.oaOccInst.find(top_occ, sTopSub1)
    assert oi_topSub1 is not None

    sub1_master = oi_topSub1.getMasterOccurrence(True)
    assert sub1_master is not None

    # Set the producer to sub1's master occurrence
    prod.setOccurrence(sub1_master)
    prod.produce()
    print("  [PASS] produce() called on topSub1's master occurrence")

    # Verify we can access the inner instances
    sSubLeaf = _base.oaSimpleName(ns, "subLeaf1")
    oi_subLeaf = _design.oaOccInst.find(sub1_master, sSubLeaf)
    assert oi_subLeaf is not None
    print("  [PASS] Found subLeaf1 inside topSub1's master")

    # ── CalcVM ──
    print("\n─── Design size ──")
    vm = top_view.calcVMSize()
    assert vm > 0
    print(f"  [PASS] VM size: {vm}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    top_view.close()
    sub_master.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 13-4 (OccProducer) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
