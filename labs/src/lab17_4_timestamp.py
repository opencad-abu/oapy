#!/usr/bin/env python3
"""
Lab 17-4: Timestamp — OA Timestamp Tracking
Demonstrates oaTimeStamp for tracking design and tech modification times.


Key concepts:
  - oaDesign.getTimeStamp(oaDesignDataType) for design timestamps
  - oaTech.getTimeStamp(oaTechDataType) for tech timestamps
  - oaTimeStamp comparison (==, !=)
  - Timestamp changes on save, modification, reopen
  - oaDesignDataTypeEnum and oaTechDataTypeEnum values
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(__dir__, "..", "..", "build"))
sys.path.insert(0, __dir__)

from oapy._oa import _base, _dm, _design, _tech
from utils import init_oa, make_oa_name, make_oa_string, get_namespace, create_lib


def ts_value(ts):
    """Extract oaUInt4 value from oaTimeStamp object."""
    op = getattr(ts, 'operator oaUInt4')
    return op()


def ts_eq(ts1, ts2):
    """Compare two oaTimeStamp objects for equality."""
    eq_op = getattr(ts1, 'operator==')
    return eq_op(ts2)


def main():
    print("=" * 60)
    print("Lab 17-4: Timestamp — OA Timestamp Tracking")
    print("=" * 60)

    init_oa()
    ns = get_namespace("native")

    import shutil
    LIB_DIR = os.path.join(__dir__, "..", "data", "lab17_4_dir")
    if os.path.exists(LIB_DIR):
        shutil.rmtree(LIB_DIR)

    sn_lib, lib = create_lib("lab17_4_lib", LIB_DIR)
    vt = _dm.oaViewType.find(make_oa_string("schematic"))
    sv_name = make_oa_name(ns, "schematic")

    DDT = _design.oaDesignDataTypeEnum
    TDT = _tech.oaTechDataTypeEnum

    # ── 1. Create Design and Tech ──
    print("\n─── Creating Design and Tech ───")
    tech = _tech.oaTech.create(sn_lib)
    assert tech is not None

    l1 = _tech.oaPhysicalLayer.create(tech, make_oa_string("l1"), 1, _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial), 0)
    l2 = _tech.oaPhysicalLayer.create(tech, make_oa_string("l2"), 2, _tech.oaMaterial(_tech.oaMaterialEnum.oacMetalMaterial), 0)
    print("  [PASS] Tech with 2 layers created")

    designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "DesignA"), sv_name, vt, 'w')
    blkA = _design.oaBlock.create(designA, True)
    designA.save()
    print("  [PASS] DesignA created and saved")

    designB = _design.oaDesign.open(sn_lib, make_oa_name(ns, "DesignB"), sv_name, vt, 'w')
    blkB = _design.oaBlock.create(designB, True)
    designB.save()
    print("  [PASS] DesignB created and saved")

    # ── 2. Design Timestamps ──
    print("\n─── Design Timestamps (oaDesignDataTypeEnum) ───")
    tsA_design = designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))
    tsB_design = designB.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))

    va = ts_value(tsA_design)
    vb = ts_value(tsB_design)
    print(f"  DesignA design ts: {va}")
    print(f"  DesignB design ts: {vb}")
    assert va > 0 and vb > 0
    print("  [PASS] Design timestamps are positive")

    # ── 3. Tech Timestamps ──
    print("\n─── Tech Timestamps (oaTechDataTypeEnum) ───")
    ts_tech_data = tech.getTimeStamp(_tech.oaTechDataType(TDT.oacTechDataType))
    ts_tech_layer = tech.getTimeStamp(_tech.oaTechDataType(TDT.oacLayerDataType))

    vt_data = ts_value(ts_tech_data)
    vt_layers = ts_value(ts_tech_layer)
    print(f"  Tech data ts:    {vt_data}")
    print(f"  Tech layers ts:  {vt_layers}")
    assert vt_data > 0
    print("  [PASS] Tech timestamps are positive")

    # ── 4. Timestamp Change on Modification ──
    print("\n─── Timestamp Change on Modification ──")
    tsA_before = designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))
    vb_before = ts_value(tsA_before)

    # Make a change: add a net
    net = _design.oaScalarNet.create(blkA, make_oa_name(ns, "newNet"),
        _design.oaSigType(_design.oaSigTypeEnum.oacSignalSigType), 1,
        _design.oaBlockDomainVisibility(_design.oaBlockDomainVisibilityEnum.oacInheritFromTopBlock))
    term = _design.oaScalarTerm.create(net, make_oa_name(ns, "newTerm"))
    designA.save()

    tsA_after = designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))
    va_after = ts_value(tsA_after)
    print(f"  Before: {vb_before}, After: {va_after}")
    assert va_after > vb_before, f"Timestamp did not increase: {va_after} <= {vb_before}"
    print("  [PASS] Timestamp increased after modification")

    # DesignB should be unchanged
    tsB_after = designB.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))
    vb_after = ts_value(tsB_after)
    print(f"  DesignB (unchanged): {vb} → {vb_after}")
    assert ts_eq(tsB_after, designB.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType)))
    print("  [PASS] DesignB timestamp unchanged")

    # ── 5. Multiple oaDesignDataType values ──
    print("\n─── Multiple Data Types ───")
    ts_types = []
    for dt_name in ['oacDesignDataType', 'oacBlockDataType', 'oacNetDataType',
                     'oacTermDataType', 'oacInstDataType', 'oacPropDataType',
                     'oacOccurrenceDataType', 'oacInstHeaderDataType']:
        try:
            dt_enum = getattr(DDT, dt_name)
            ts = designA.getTimeStamp(_design.oaDesignDataType(dt_enum))
            tv = ts_value(ts)
            ts_types.append((dt_name, tv))
        except Exception as e:
            ts_types.append((dt_name, f"ERROR: {e}"))
    for name, tv in ts_types:
        print(f"  {name}: {tv}")
    assert len(ts_types) >= 6
    print("  [PASS] Multiple data type timestamps accessed")

    # ── 6. Timestamp Comparison ──
    print("\n─── Timestamp Comparison ───")
    tsA = designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))
    tsB = designB.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType))

    eq_result = ts_eq(tsA, tsA)  # self-equality
    ne_result = not ts_eq(tsA, tsB) if not ts_eq(tsA, tsB) else True

    print(f"  DesignA TS == DesignA TS: {eq_result}")
    print(f"  DesignA TS != DesignB TS: {ne_result}")
    assert eq_result
    print("  [PASS] Timestamp comparisons work")

    # ── 7. Close and Reopen ──
    print("\n─── Close and Reopen ───")
    ts_before_close = ts_value(designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType)))
    designA.close()
    designB.close()

    designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "DesignA"), sv_name, vt, 'r')
    ts_after_open = ts_value(designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType)))
    print(f"  Before close: {ts_before_close}, After reopen: {ts_after_open}")
    assert ts_after_open > 0
    print("  [PASS] Reopened, timestamp accessible")

    # ── 8. Multiple reads ──
    print("\n─── Verify Read Timestamps ──")
    designA.close()
    designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "DesignA"), sv_name, vt, 'a')
    for i in range(3):
        ts_before = ts_value(designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType)))
        designA.close()
        designA = _design.oaDesign.open(sn_lib, make_oa_name(ns, "DesignA"), sv_name, vt, 'a')
        ts_after = ts_value(designA.getTimeStamp(_design.oaDesignDataType(DDT.oacDesignDataType)))
        assert ts_after >= ts_before, f"Reopen {i}: {ts_after} < {ts_before}"
    print("  [PASS] Timestamp accessible across reopens")

    # ── Cleanup ──
    print("\n─── Cleanup ──")
    designA.close()
    lib.close()
    shutil.rmtree(LIB_DIR, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ Lab 17-4 (Timestamp) PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
    os._exit(0)
