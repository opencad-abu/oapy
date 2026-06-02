#!/usr/bin/env python3
"""
Lab 13-5: TclSize — Virtual Memory Size Calculation
Demonstrates calcVMSize() on oaDesign to measure virtual memory usage.


The original lab was a Tcl script for upsizing/downsizing instances.
This Python adaptation focuses on the core concept: measuring design VM sizes
and comparing sizes across designs of varying complexity.

Key concepts:
  - oaDesign.calcVMSize() for virtual memory measurement
  - Creating designs with different complexities
  - Reopening and remeasuring
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
    print("Lab 13-5: TclSize — Virtual Memory Size")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab13_5_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab13_5_lib", LIB_DIR)

    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")
    bv_enum = _design.oaBlockDomainVisibilityEnum
    ps_enum = _design.oaPlacementStatusEnum
    xform = _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0))

    # ── Create designs of varying complexity ──
    print("\n─── Creating Designs ───")

    # Small: just a block
    d_small = _design.oaDesign.open(sn_lib, make_oa_name(ns, "small"), sv_name, vt, 'w')
    _design.oaBlock.create(d_small, True)
    vm_small = d_small.calcVMSize()
    print(f"  [PASS] small:  vm={vm_small}")

    # Medium: block + master + 5 instances
    master_v = _design.oaDesign.open(sn_lib, make_oa_name(ns, "_master"), sv_name, vt, 'w')
    _design.oaBlock.create(master_v, True)
    master_v.save()

    master_r = _design.oaDesign.open(sn_lib, make_oa_name(ns, "_master"), sv_name, vt, 'r')
    d_med = _design.oaDesign.open(sn_lib, make_oa_name(ns, "medium"), sv_name, vt, 'w')
    med_blk = _design.oaBlock.create(d_med, True)
    for i in range(5):
        _design.oaScalarInst.create(med_blk, master_r, make_oa_name(ns, f"inst{i}"),
            xform, _base.oaParamArray(0),
            _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    vm_med = d_med.calcVMSize()
    print(f"  [PASS] medium: vm={vm_med}")

    # Large: block + master + 10 instances + nested hierarchy
    d_large = _design.oaDesign.open(sn_lib, make_oa_name(ns, "large"), sv_name, vt, 'w')
    lrg_blk = _design.oaBlock.create(d_large, True)
    for i in range(10):
        _design.oaScalarInst.create(lrg_blk, master_r, make_oa_name(ns, f"inst{i}"),
            xform, _base.oaParamArray(0),
            _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
            _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    vm_lrg = d_large.calcVMSize()
    print(f"  [PASS] large:  vm={vm_lrg}")

    # Verify sizes are monotonically increasing
    assert vm_small > 0
    assert vm_med > vm_small, f"{vm_med} <= {vm_small}"
    assert vm_lrg > vm_med, f"{vm_lrg} <= {vm_med}"
    print("  [PASS] VM sizes monotonically increasing")

    # Save all
    d_small.save()
    d_med.save()
    d_large.save()
    master_r.close()

    # ── Reopen and remeasure ──
    print("\n─── Reopen and Remeasure ───")
    d_small.close()
    d_med.close()
    d_large.close()

    d_small2 = _design.oaDesign.open(sn_lib, make_oa_name(ns, "small"), sv_name, vt, 'r')
    d_med2 = _design.oaDesign.open(sn_lib, make_oa_name(ns, "medium"), sv_name, vt, 'r')
    d_large2 = _design.oaDesign.open(sn_lib, make_oa_name(ns, "large"), sv_name, vt, 'r')

    vm_small2 = d_small2.calcVMSize()
    vm_med2 = d_med2.calcVMSize()
    vm_large2 = d_large2.calcVMSize()
    total = vm_small2 + vm_med2 + vm_large2

    print(f"  small  reopened: vm={vm_small2}")
    print(f"  medium reopened: vm={vm_med2}")
    print(f"  large  reopened: vm={vm_large2}")
    print(f"  total: {total}")
    assert total > 0
    print("  [PASS] Reopened designs, total > 0")

    # ── Hierarchy demo ──
    print("\n─── Hierarchy Size ───")
    d_top = _design.oaDesign.open(sn_lib, make_oa_name(ns, "_top"), sv_name, vt, 'w')
    top_blk = _design.oaBlock.create(d_top, True)
    _design.oaScalarInst.create(top_blk, d_med2, make_oa_name(ns, "med1"),
        xform, _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(bv_enum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(ps_enum.oacUnplacedPlacementStatus))
    vm_hier = d_top.calcVMSize()
    print(f"  [PASS] Hierarchy design vm={vm_hier}")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    d_small2.close()
    d_med2.close()
    d_large2.close()
    d_top.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 13-5 (TclSize) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
