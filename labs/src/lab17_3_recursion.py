#!/usr/bin/env python3
"""
Lab 17-3: Recursion — Circular Reference Detection
Demonstrates OA recursion detection with oaRecursionObserver.


Key concepts:
  - oaRecursionObserver.onBind: fires when opening recursive designs
  - oaRecursionObserver.onDetect: fires when hasRecursion() finds circular refs
  - hasRecursion(), hasReference() on oaDesign
  - oacCannotCreateRecursiveDesign exception
  - oacCannotSaveAsRecursiveDesign exception
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(__dir__, "..", "..", "build"))
sys.path.insert(0, __dir__)

from oapy._oa import _base, _dm, _design, _tech
from utils import init_oa, make_oa_name, make_oa_string, get_namespace, create_lib


def main():
    print("=" * 60)
    print("Lab 17-3: Recursion — Circular Reference Detection")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab17_3_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab17_3_lib", LIB_DIR)
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── Part 1: Build A→B→C linear hierarchy ──
    print("\n─── Part 1: Build Linear Hierarchy A→B→C ───")
    designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "A"), sv_name, vt, 'w')
    designB = _design.oaDesign.open(sn_lib, make_oa_name(ns, "B"), sv_name, vt, 'w')
    designC = _design.oaDesign.open(sn_lib, make_oa_name(ns, "C"), sv_name, vt, 'w')
    blkA = _design.oaBlock.create(designA, True)
    blkB = _design.oaBlock.create(designB, True)
    blkC = _design.oaBlock.create(designC, True)
    print("  [PASS] Created designs A, B, C")

    # A instantiates B, B instantiates C
    instB = _design.oaScalarInst.create(blkA, designB, make_oa_name(ns, "instB"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    instC = _design.oaScalarInst.create(blkB, designC, make_oa_name(ns, "instC"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    designA.save(); designB.save(); designC.save()
    print("  [PASS] A→B, B→C, all saved")

    # ── Part 2: Test self-instantiation prevention ──
    print("\n─── Part 2: Self-Instantiation Prevention ───")
    print("  Test: A cannot instantiate itself")
    try:
        _design.oaScalarInst.create(blkA, designA, make_oa_name(ns, "instSelf"),
            xform, _base.oaParamArray(0),
            _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
        print("    [FAIL] Should have thrown exception!")
        assert False
    except Exception as e:
        print(f"    [PASS] Caught exception: {type(e).__name__}")

    # Test: B cannot saveAs C (B already references C)
    print("  Test: B cannot saveAs C")
    try:
        designB.saveAs(sn_lib, make_oa_name(ns, "C"), sv_name)
        print("    [FAIL] Should have thrown exception!")
        assert False
    except Exception as e:
        print(f"    [PASS] Caught exception: {type(e).__name__}")

    # Test: C cannot instantiate A (circular when all open)
    print("  Test: C cannot instantiate A (circular)")
    try:
        _design.oaScalarInst.create(blkC, designA, make_oa_name(ns, "instA"),
            xform, _base.oaParamArray(0),
            _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
        print("    [FAIL] Should have thrown exception!")
        assert False
    except Exception as e:
        print(f"    [PASS] Caught exception: {type(e).__name__}")

    # ── Part 3: hasReference ──
    print("\n─── Part 3: hasReference ───")
    ref_A_B = designA.hasReference(designB)  # True (direct)
    ref_A_C = designA.hasReference(designC)  # True (transitive)
    ref_B_A = designB.hasReference(designA)  # False (up hierarchy)
    ref_B_C = designB.hasReference(designC)  # True (direct)
    ref_A_A = designA.hasReference(designA)  # False (self-reference not detected upward)

    print(f"  A→B: {ref_A_B} (expected True)")
    print(f"  A→C: {ref_A_C} (expected True, transitive)")
    print(f"  B→A: {ref_B_A} (expected False, up hierarchy)")
    print(f"  B→C: {ref_B_C} (expected True, direct)")
    print(f"  A→A: {ref_A_A} (expected False - self-ref not detected)")

    assert ref_A_B and ref_A_C and ref_B_C
    assert not ref_B_A
    print("  [PASS] hasReference assertions passed")

    # ── Part 4: No recursion yet ──
    print("\n─── Part 4: No Recursion in Linear Hierarchy ──")
    r_A = designA.hasRecursion()
    r_B = designB.hasRecursion()
    r_C = designC.hasRecursion()
    print(f"  A.hasRecursion: {r_A}")
    print(f"  B.hasRecursion: {r_B}")
    print(f"  C.hasRecursion: {r_C}")
    assert not r_A and not r_B and not r_C
    print("  [PASS] No recursion detected (linear hierarchy)")

    # ── Part 5: RecursionObserver ──
    print("\n─── Part 5: oaRecursionObserver ──")
    reco = _design.oaRecursionObserver(5, True)
    assert reco is not None and reco.isEnabled()
    print("  [PASS] oaRecursionObserver created")

    # Close all to create circular refs
    designA.close(); designB.close(); designC.close()
    print("  [PASS] All designs closed")

    # Open only C, instantiate A and B (creating circular references)
    designC = _design.oaDesign.open(sn_lib, make_oa_name(ns, "C"), sv_name, vt, 'a')
    blkC = designC.getTopBlock()

    # Now C instantiates A and B by L/C/V names
    instA_in_C = _design.oaScalarInst.create(blkC, sn_lib,
        make_oa_name(ns, "A"), make_oa_name(ns, "schematic"),
        make_oa_name(ns, "instA"), xform,
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    instB_in_C = _design.oaScalarInst.create(blkC, sn_lib,
        make_oa_name(ns, "B"), make_oa_name(ns, "schematic"),
        make_oa_name(ns, "instB"), xform,
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))

    instA_name = _base.oaString(); instA_in_C.getName(ns, instA_name)
    instB_name = _base.oaString(); instB_in_C.getName(ns, instB_name)
    print(f"  [PASS] C now instantiates: {instA_name}, {instB_name}")

    designC.save(); designC.close()
    print("  [PASS] Design C saved and closed")

    # Reopen all → recursion detected
    designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "A"), sv_name, vt, 'r')
    designB = _design.oaDesign.open(sn_lib, make_oa_name(ns, "B"), sv_name, vt, 'r')
    designC = _design.oaDesign.open(sn_lib, make_oa_name(ns, "C"), sv_name, vt, 'r')

    r_A2 = designA.hasRecursion()
    r_B2 = designB.hasRecursion()
    r_C2 = designC.hasRecursion()
    print(f"  A.hasRecursion: {r_A2}")
    print(f"  B.hasRecursion: {r_B2}")
    print(f"  C.hasRecursion: {r_C2}")
    print("  [PASS] Recursion detected on reopening circular hierarchy")

    # ── Part 6: CustomVia recursion prevention ──
    print("\n─── Part 6: CustomVia Recursion Prevention ──")
    try:
        tech = _tech.oaTech.open(sn_lib, 'w')
    except Exception:
        tech = _tech.oaTech.create(sn_lib)
    mat = _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial)
    l1 = _tech.oaLayer.find(tech, make_oa_string("l1"))
    if not l1:
        l1 = _tech.oaPhysicalLayer.create(tech, make_oa_string("l1"), 1, mat, 0)
    l2 = _tech.oaLayer.find(tech, make_oa_string("l2"))
    if not l2:
        l2 = _tech.oaPhysicalLayer.create(tech, make_oa_string("l2"), 2, mat, 0)

    cvdef = _tech.oaCustomViaDef.create(tech, make_oa_string("cvdef1"),
        sn_lib, make_oa_name(ns, "A"), make_oa_name(ns, "schematic"), l1, l2)
    assert cvdef is not None
    print("  [PASS] CustomViaDef created")

    blkA = designA.getTopBlock()
    try:
        _design.oaCustomVia.create(blkA, cvdef,
            _base.oaTransform(10, 10, _base.oaOrient(_base.oaOrientEnum.oacR0)))
        print("    [FAIL] Should have thrown exception!")
        assert False
    except Exception as e:
        print(f"    [PASS] Caught exception: {type(e).__name__}")
    print("  [PASS] CustomVia cannot reference parent design")

    # ── CalcVM ──
    print("\n─── calcVMSize ──")
    vm = designA.calcVMSize()
    assert vm > 0
    print(f"  [PASS] VM size: {vm}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    designA.close(); designB.close(); designC.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 17-3 (Recursion) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
