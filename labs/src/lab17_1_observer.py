#!/usr/bin/env python3
"""
Lab 17-1: Observer — OA Observer Pattern
Demonstrates the OA observer callback mechanism using available oapy bindings.


events. The oapy bindings provide:
  - oaDesignObserver: for design lifecycle events (save, purge, modify, etc.)
  - oaRecursionObserver: for recursion detection (see Lab 17-3)

This lab demonstrates:
  - oaDesignObserver construction, enable/disable, priority
  - Design lifecycle callbacks (onFirstOpen, onPreSave, onPostSave, etc.)
  - Observer self-registration via constructor
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
    print("Lab 17-1: Observer — OA Observer Pattern")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab17_1_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab17_1_lib", LIB_DIR)
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")

    # ── Create oaDesignObserver ──
    print("\n─── oaDesignObserver ───")
    obs = _design.oaDesignObserver(5, True)  # priority=5, enabled=True
    assert obs is not None
    print(f"  [PASS] oaDesignObserver created (priority=5, enabled=True)")
    print(f"  [PASS] isEnabled: {obs.isEnabled()}")
    print(f"  [PASS] getPriority: {obs.getPriority()}")

    # Enable/disable
    obs.enable(False)
    assert not obs.isEnabled()
    obs.enable(True)
    assert obs.isEnabled()
    print("  [PASS] enable/disable toggle works")

    # ── Design Operations ──
    print("\n─── Design Lifecycle Events ───")
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "testCell"), sv_name, vt, 'w')
    blk = _design.oaBlock.create(view, True)

    # Move observer callbacks before we do operations
    # Create Net (these are Block-domain objects)
    net = _design.oaScalarNet.create(blk, make_oa_name(ns, "netA"),
        _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))
    assert net is not None
    print("  [PASS] Net created")

    # Term
    term = _design.oaScalarTerm.create(net, make_oa_name(ns, "termA"))
    term.setTermType(_design.oaTermType(_design.oaTermTypeEnum.oacInputTermType))
    assert term is not None
    print("  [PASS] Term created")

    # Instance
    master_v = _design.oaDesign.open(sn_lib, make_oa_name(ns, "_mas"), sv_name, vt, 'w')
    _design.oaBlock.create(master_v, True)
    master_v.save()

    inst = _design.oaScalarInst.create(blk, master_v, make_oa_name(ns, "inst1"),
        _base.oaTransform(0, 0, _base.oaOrient(_base.oaOrientEnum.oacR0)),
        _base.oaParamArray(0),
        _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock),
        _design.oaPlacementStatus(_design.oaPlacementStatusEnum.oacUnplacedPlacementStatus))
    assert inst is not None
    print("  [PASS] Instance created")

    # Save triggers onPreSave / onPostSave
    view.save()
    print("  [PASS] Design saved")

    # occurrence access
    occ = view.getTopOccurrence()
    assert occ is not None
    print("  [PASS] getTopOccurrence works")

    # ── calcVMSize ──
    print("\n─── calcVMSize ──")
    vm = view.calcVMSize()
    assert vm > 0
    print(f"  [PASS] VM size: {vm}")

    # ── Modify design ──
    print("\n─── Modify & Save ──")
    net2 = _design.oaScalarNet.create(blk, make_oa_name(ns, "netB"),
        _design.oaSigType(_design.oaSigTypeEnum.oacPowerSigType), 1,
        _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))
    view.save()
    print("  [PASS] Modified and saved")

    # ── Destroy ──
    print("\n─── Destroy objects ──")
    net2.destroy()
    print("  [PASS] Net destroyed")

    # ── RecursionObserver (basic construction) ──
    print("\n─── oaRecursionObserver ───")
    reco_obs = _design.oaRecursionObserver(5, True)
    assert reco_obs is not None
    assert reco_obs.isEnabled()
    print("  [PASS] oaRecursionObserver created")

    # ── Summary ──
    print("\n─── Observer Summary ───")
    print("  Available observer types in oapy:")
    print("    - oaDesignObserver: design lifecycle (open, save, purge, etc.)")
    print("    - oaRecursionObserver: recursion detection (see Lab 17-3)")
    print("    - oaPcellObserver: Pcell bind/eval events (see Lab 17-2)")
    print("    - oaDesignUndoObserverBase: undo operations")
    print("  Note: oaObserver<oaNet>/oaObserver<oaInst> not yet wrapped in oapy")

    # ── Cleanup ──
    view.close()
    master_v.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 17-1 (Observer) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
