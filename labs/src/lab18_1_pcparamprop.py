#!/usr/bin/env python3
"""Lab 18-1: PCell parameter and property smoke test."""

import os
import sys
import traceback

from oapy._oa import _base
from pcell_smoke_utils import setup_library, scalar, oa_str, param_array, create_design_with_block


def main():
    print("=" * 60)
    print("Lab 18-1: PCell Param/Prop")
    print("=" * 60)

    ns, sn_lib, lib, vt = setup_library("Lib18_1_ParamProp", "../data/Lib18_1_ParamProp")
    des, block = create_design_with_block(sn_lib, ns, "top", "schematic", vt)

    params = param_array([("width", 10), ("netName", "sigA"), ("enabled", 1)])
    out = _base.oaParam()
    index = params.find(oa_str("width"), out)
    print(f"  ParamArray length={len(params)} width_index={index}")
    assert index >= 0

    _base.oaStringProp.create(des, oa_str("pcellName"), oa_str("paramPropDemo"))
    prop = _base.oaProp.find(des, oa_str("pcellName"))
    assert prop is not None
    print("  Design string property created and found")

    des.save()
    print("✅ Lab 18-1 完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"*** Exception: {exc}")
        traceback.print_exc()
        sys.exit(1)
    os._exit(0)
