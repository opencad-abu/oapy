#!/usr/bin/env python3
"""
Lab 13-2: Occ — Occurrence Domain Edits
Demonstrates occurrence-domain operations including uniquification and


Key concepts:
  - oaScalarInst.find for locating instances
  - Inst.getOccInst for occurrence access
  - oaOccInst.find for occurrence-level find
  - getMasterOccurrence for traversing hierarchy
  - calcVMSize for resource measurement

Note: oapy doesn't wrap oaCollection<oaInst,oaBlock> or full oaIter patterns,
so we use oaScalarInst.find and oaOccInst.find for direct access.
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
    print("Lab 13-2: Occ — Occurrence Domain Operations")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab13_2_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab13_2_lib", LIB_DIR)

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── Create leaf cells (AND, OR, XOR) ──
    print("\n─── Creating Leaf Cells ───")
    leaf_views = {}
    for cell in ["AND", "OR", "XOR"]:
        v = _design.oaDesign.open(sn_lib, make_oa_name(ns, cell), sv_name, vt, 'w')
        blk = _design.oaBlock.create(v, True)
        v.save()
        leaf_views[cell] = v

    leaf_views["AND"].close()
    leaf_views["OR"].close()
    leaf_views["XOR"].close()
    print("  [PASS] AND, OR, XOR leaf cells created")

    # ── Create HalfAdder ──
    print("\n─── Creating HalfAdder ───")
    ha_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "HalfAdder"), sv_name, vt, 'w')
    ha_blk = _design.oaBlock.create(ha_view, True)

    and_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "AND"), sv_name, vt, 'r')
    _design.oaScalarInst.create(ha_blk, and_master, make_oa_name(ns, "And1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    and_master.close()

    xor_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "XOR"), sv_name, vt, 'r')
    _design.oaScalarInst.create(ha_blk, xor_master, make_oa_name(ns, "Xor1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    xor_master.close()

    ha_view.save()
    ha_view.close()
    print("  [PASS] HalfAdder created (And1, Xor1)")

    # ── Create FullAdder ──
    print("\n─── Creating FullAdder ───")
    fa_view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "FullAdder"), sv_name, vt, 'w')
    fa_blk = _design.oaBlock.create(fa_view, True)

    ha_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "HalfAdder"), sv_name, vt, 'r')
    _design.oaScalarInst.create(fa_blk, ha_master, make_oa_name(ns, "Ha1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    _design.oaScalarInst.create(fa_blk, ha_master, make_oa_name(ns, "Ha2"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    ha_master.close()

    or_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "OR"), sv_name, vt, 'r')
    _design.oaScalarInst.create(fa_blk, or_master, make_oa_name(ns, "Or1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    or_master.close()

    fa_view.save()
    fa_view.close()
    print("  [PASS] FullAdder created (Ha1, Ha2, Or1)")

    # ── Reopen and test occurrence operations ──
    print("\n─── Testing Occurrence Operations ───")
    ha_master = _design.oaDesign.open(sn_lib, make_oa_name(ns, "HalfAdder"), sv_name, vt, 'r')
    fa_design = _design.oaDesign.open(sn_lib, make_oa_name(ns, "FullAdder"), sv_name, vt, 'r')
    fa_blk = fa_design.getTopBlock()

    # 1. Find Inst by name in Block domain
    snHa1 = make_oa_name(ns, "Ha1")
    inst_ha1 = _design.oaScalarInst.find(fa_blk, snHa1)
    assert inst_ha1 is not None
    ha1_name = _base.oaString()
    inst_ha1.getName(ns, ha1_name)
    print(f"  [PASS] oaScalarInst.find('Ha1') -> {ha1_name}")

    snHa2 = make_oa_name(ns, "Ha2")
    inst_ha2 = _design.oaScalarInst.find(fa_blk, snHa2)
    assert inst_ha2 is not None
    ha2_name = _base.oaString()
    inst_ha2.getName(ns, ha2_name)
    print(f"  [PASS] oaScalarInst.find('Ha2') -> {ha2_name}")

    # 2. Get OccInst from Inst
    oi_ha1 = inst_ha1.getOccInst()
    assert oi_ha1 is not None
    oi_ha2 = inst_ha2.getOccInst()
    assert oi_ha2 is not None
    print("  [PASS] getOccInst() on Ha1, Ha2")

    # 3. Occurrence find
    top_occ = fa_design.getTopOccurrence()
    simp = _base.oaSimpleName(ns, "Ha1")
    found_oi = _design.oaOccInst.find(top_occ, simp)
    assert found_oi is not None
    print("  [PASS] oaOccInst.find('Ha1') from top occurrence")

    # 4. getMasterOccurrence on OccInst
    master_occ = found_oi.getMasterOccurrence(True)
    assert master_occ is not None
    mo_blk = master_occ.getBlock()
    print(f"  [PASS] getMasterOccurrence -> block exists")

    # 5. getInst from OccInst
    the_inst = found_oi.getInst()
    assert the_inst is not None
    print("  [PASS] getInst from OccInst")

    # 6. getMaster on Inst
    master_design = inst_ha1.getMaster()
    assert master_design is not None
    master_cell = master_design.getCellName()
    print(f"  [PASS] getMaster cell name: {master_cell}")

    # 7. calcVMSize
    vm = fa_design.calcVMSize()
    assert vm > 0
    print(f"  [PASS] calcVMSize: {vm}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    ha_master.close()
    fa_design.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 13-2 (Occ) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
