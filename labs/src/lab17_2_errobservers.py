#!/usr/bin/env python3
"""
Lab 17-2: Error Observers — Error/Conflict Observer Pattern
Demonstrates observer callbacks for error and conflict detection.


This lab demonstrates:
  - oaPcellObserver for Pcell bind/eval/read/write errors
  - oaTechObserver for tech conflict detection and modification monitoring
  - oaLibDefListObserver for lib.defs loading warnings
  - oaLibObserver for library lifecycle monitoring
  - oaViewTypeObserver for view type changes
  - oaDerivedLayerDefObserver for derived layer definitions
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
    print("Lab 17-2: Error Observers — Error/Conflict Detection")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab17_2_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab17_2_lib", LIB_DIR)
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")

    # ── 1. oaPcellObserver ──
    print("\n─── oaPcellObserver ───")
    pcell_obs = _design.oaPcellObserver(5, True)
    assert pcell_obs is not None
    assert pcell_obs.isEnabled()
    print("  [PASS] oaPcellObserver created (priority=5, enabled=True)")
    pcell_methods = [m for m in dir(pcell_obs) if not m.startswith('_')]
    print(f"  Available methods: {pcell_methods}")

    # ── 2. oaTechObserver ──
    print("\n─── oaTechObserver ───")
    tech_obs = _tech.oaTechObserver(5)
    assert tech_obs is not None
    tech_obs.enable(True)
    assert tech_obs.isEnabled()
    tech_methods = [m for m in dir(tech_obs) if not m.startswith('_')]
    print(f"  [PASS] oaTechObserver created")
    print(f"  Available methods: {tech_methods}")

    # ── 3. oaLibObserver ──
    print("\n─── oaLibObserver ───")
    lib_obs = _dm.oaLibObserver(5, True)
    assert lib_obs is not None
    assert lib_obs.isEnabled()
    lib_methods = [m for m in dir(lib_obs) if not m.startswith('_')]
    print(f"  [PASS] oaLibObserver created")
    print(f"  Available methods: {lib_methods}")

    # ── 4. oaLibDefListObserver ──
    print("\n─── oaLibDefListObserver ──")
    ldl_obs = _dm.oaLibDefListObserver(5, True)
    assert ldl_obs is not None
    assert ldl_obs.isEnabled()
    ldl_methods = [m for m in dir(ldl_obs) if not m.startswith('_')]
    print(f"  [PASS] oaLibDefListObserver created")
    print(f"  Available methods: {ldl_methods}")

    # ── 5. oaViewTypeObserver ──
    print("\n─── oaViewTypeObserver ──")
    vt_obs = _dm.oaViewTypeObserver(5, True)
    assert vt_obs is not None
    assert vt_obs.isEnabled()
    vt_methods = [m for m in dir(vt_obs) if not m.startswith('_')]
    print(f"  [PASS] oaViewTypeObserver created")
    print(f"  Available methods: {vt_methods}")

    # ── 6. oaDerivedLayerDefObserver ──
    print("\n─── oaDerivedLayerDefObserver ──")
    dl_obs = _tech.oaDerivedLayerDefObserver(5, 1)
    assert dl_obs is not None
    assert dl_obs.isEnabled()
    dl_methods = [m for m in dir(dl_obs) if not m.startswith('_')]
    print(f"  [PASS] oaDerivedLayerDefObserver created")
    print(f"  Available methods: {dl_methods}")

    # ── 7. Create Tech ──
    print("\n─── Creating Tech ──")
    tech = _tech.oaTech.create(sn_lib)
    assert tech is not None
    print("  [PASS] Tech created")

    # Create physical layers (5 args: tech, name, number, material, maskNumber)
    mat = _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial)
    l1 = _tech.oaPhysicalLayer.create(tech, make_oa_string("metal1"), 10, mat, 0)
    l2 = _tech.oaPhysicalLayer.create(tech, make_oa_string("metal2"), 20, mat, 0)
    assert l1 is not None and l2 is not None
    print("  [PASS] Layers created: metal1(10), metal2(20)")

    # ── 8. Create Design ──
    print("\n─── Creating Design ──")
    view = _design.oaDesign.open(sn_lib, make_oa_name(ns, "cell"), sv_name, vt, 'w')
    blk = _design.oaBlock.create(view, True)
    net = _design.oaScalarNet.create(blk, make_oa_name(ns, "net"),
        _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))
    view.save()
    print(f"  [PASS] Design created")

    # ── 9. calcVM ──
    print("\n─── calcVMSize ──")
    vm = view.calcVMSize()
    assert vm > 0
    print(f"  [PASS] VM size: {vm}")

    # ── 10. Enable/Disable ──
    print("\n─── Observer Enable/Disable ──")
    for obs, name in [(pcell_obs, "Pcell"), (tech_obs, "Tech"),
                       (lib_obs, "Lib"), (ldl_obs, "LibDefList"),
                       (vt_obs, "ViewType"), (dl_obs, "DerivedLayerDef")]:
        obs.enable(False)
        assert not obs.isEnabled()
        obs.enable(True)
        assert obs.isEnabled()
    print("  [PASS] All observers toggle enable/disable")

    # ── Summary ──
    print("\n─── Observer Summary ───")
    print("  Available error/conflict observers in oapy:")
    print("    _design.oaPcellObserver          - Pcell bind/eval/read/write errors")
    print("    _tech.oaTechObserver            - Tech conflicts & modifications")
    print("    _dm.oaLibObserver               - Library lifecycle events")
    print("    _dm.oaLibDefListObserver        - lib.defs parse warnings")
    print("    _dm.oaViewTypeObserver          - View type changes")
    print("    _tech.oaDerivedLayerDefObserver - Derived layer definition events")
    print("    _tech.oaDerivedLayerParamDefObserver - Layer param definition events")
    print("    _design.oaDesignObserver        - Design lifecycle events")
    print("    _design.oaRecursionObserver     - Recursion detection (Lab 17-3)")

    # ── Cleanup ──
    print("\n─── Cleanup ───")
    view.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 17-2 (Error Observers) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
